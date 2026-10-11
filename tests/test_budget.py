"""Tests for budget.py: the daily ledger, prices, and how API errors are charged. No network.

Run from app/:  .venv/bin/python -m unittest discover -s tests -p "test_*.py"
"""
import sys
import threading
import unittest
from datetime import datetime
from pathlib import Path

import anthropic
import httpx2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import budget  # noqa: E402
from budget import ET, Ledger  # noqa: E402


class Clock:
    def __init__(self, when):
        self.when = when

    def __call__(self):
        return self.when


def api_error(cls, status, body):
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls(message=str(body), response=httpx2.Response(status, request=request), body=body)


class Prices(unittest.TestCase):
    def test_cost(self):
        self.assertAlmostEqual(budget.cost_usd("claude-sonnet-5", 64_000, 12_000), 0.248)

    def test_worst_case_request_fits_the_daily_cap(self):
        import analysis
        worst = budget.cost_usd(analysis.MODEL, analysis.REQUEST_TOKEN_BUDGET - analysis.MAX_OUTPUT_TOKENS, analysis.MAX_OUTPUT_TOKENS)
        self.assertLessEqual(worst, budget.DAILY_CAP_USD)

    def test_unknown_model_raises(self):
        with self.assertRaises(KeyError):
            budget.cost_usd("claude-unpriced", 1, 1)


class LedgerMath(unittest.TestCase):
    def test_reserve_settle_release(self):
        led = Ledger(0.25, now=Clock(datetime(2026, 10, 11, 12, tzinfo=ET)))
        r = led.reserve(0.20)
        self.assertAlmostEqual(led.remaining(), 0.05)
        led.settle(r, 0.13)
        self.assertAlmostEqual(led.remaining(), 0.12)
        r2 = led.reserve(0.10)
        led.release(r2)
        self.assertAlmostEqual(led.remaining(), 0.12)
        led.settle(r2, 0.10)                       # already closed: no effect
        self.assertAlmostEqual(led.remaining(), 0.12)

    def test_blocked_reserve(self):
        led = Ledger(0.25, now=Clock(datetime(2026, 10, 11, 12, tzinfo=ET)))
        led.settle(led.reserve(0.20), 0.15)
        self.assertIsNone(led.reserve(0.11))
        self.assertIsNotNone(led.reserve(0.10))

    def test_owner_reserve_is_counted_but_not_blocked(self):
        led = Ledger(0.25, now=Clock(datetime(2026, 10, 11, 12, tzinfo=ET)))
        led.settle(led.reserve(0.24), 0.24)
        self.assertIsNotNone(led.reserve(0.20, enforce=False))
        self.assertEqual(led.remaining(), 0.0)

    def test_rolls_over_at_midnight_eastern(self):
        clock = Clock(datetime(2026, 10, 11, 23, 59, tzinfo=ET))
        led = Ledger(0.25, now=clock)
        old = led.reserve(0.25)
        self.assertIsNone(led.reserve(0.01))
        clock.when = datetime(2026, 10, 12, 0, 1, tzinfo=ET)
        self.assertAlmostEqual(led.remaining(), 0.25)
        led.settle(old, 0.25)                      # yesterday's reservation doesn't spend today's cap
        self.assertAlmostEqual(led.remaining(), 0.25)

    def test_day_is_eastern_not_utc(self):
        # 03:00 UTC on Oct 12 is still 11 PM on Oct 11 in New York
        clock = Clock(datetime(2026, 10, 11, 22, tzinfo=ET))
        led = Ledger(0.25, now=clock)
        led.settle(led.reserve(0.20), 0.20)
        clock.when = datetime.fromisoformat("2026-10-12T03:00:00+00:00")
        self.assertAlmostEqual(led.remaining(), 0.05)

    def test_two_threads_only_one_fits(self):
        led = Ledger(0.25, now=Clock(datetime(2026, 10, 11, 12, tzinfo=ET)))
        start, results = threading.Barrier(2), []

        def worker():
            start.wait()
            results.append(led.reserve(0.20))

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sum(r is not None for r in results), 1)


class ErrorCharging(unittest.TestCase):
    def test_4xx_is_released(self):
        for cls, status in [(anthropic.BadRequestError, 400), (anthropic.AuthenticationError, 401),
                            (anthropic.RateLimitError, 429), (anthropic.RequestTooLargeError, 413)]:
            with self.subTest(cls.__name__):
                self.assertTrue(budget.rejected_before_billing(api_error(cls, status, {"error": {"message": "x"}})))

    def test_5xx_connection_timeout_and_unexpected_settle_worst_case(self):
        request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
        for exc in [api_error(anthropic.InternalServerError, 500, {}), api_error(anthropic.OverloadedError, 529, {}),
                    api_error(anthropic.ServiceUnavailableError, 503, {}),
                    anthropic.APIConnectionError(request=request), anthropic.APITimeoutError(request=request),
                    ValueError("bug after the call")]:
            with self.subTest(type(exc).__name__):
                self.assertFalse(budget.rejected_before_billing(exc))


class MonthlyLimit(unittest.TestCase):
    def test_own_spend_limit_400(self):
        for msg in ["You have reached your specified API usage limits. You will regain access on 2026-11-01 at 00:00 UTC.",
                    "You have reached your specified workspace API usage limits. You will regain access on 2026-11-01."]:
            body = {"type": "error", "error": {"type": "invalid_request_error", "message": msg}}
            self.assertTrue(budget.monthly_limit_error(api_error(anthropic.BadRequestError, 400, body)))

    def test_tier_cap_429(self):
        body = {"type": "error", "error": {"type": "rate_limit_error", "message": "You have reached your API usage limits: ...",
                                           "details": {"error_code": "enforced_spend_limit_reached"}}}
        self.assertTrue(budget.monthly_limit_error(api_error(anthropic.RateLimitError, 429, body)))

    def test_ordinary_400_and_429_are_not_monthly(self):
        bad = {"type": "error", "error": {"type": "invalid_request_error", "message": "messages: field required"}}
        rate = {"type": "error", "error": {"type": "rate_limit_error", "message": "Number of request tokens has exceeded your per-minute rate limit"}}
        self.assertFalse(budget.monthly_limit_error(api_error(anthropic.BadRequestError, 400, bad)))
        self.assertFalse(budget.monthly_limit_error(api_error(anthropic.RateLimitError, 429, rate)))
        self.assertFalse(budget.monthly_limit_error(ValueError("not an API error")))


if __name__ == "__main__":
    unittest.main()
