"""Daily spending guard for live Claude calls. No Streamlit and no network calls; app.py holds one Ledger.

Every live call reserves its worst-case cost first, then settles at the real cost. Reservations and the
daily total live in memory: they reset when the app restarts (the Anthropic monthly limit is the hard stop).
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# Public cap for live analyses. The Anthropic account has a $10/month spend limit and local testing uses the
# same key, so the public site may use at most about $7.50 of it a month (30 days x $0.25).
DAILY_CAP_USD = 0.25

# USD per million tokens (input, output), standard rates without caching or batch.
# Source: https://platform.claude.com/docs/en/about-claude/pricing (Claude Sonnet 5 row), checked 2026-10-11.
PRICES_PER_MTOK = {"claude-sonnet-5": (2.00, 10.00)}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Raises KeyError for a model with no listed price, so an unpriced model can't run outside the cap."""
    price_in, price_out = PRICES_PER_MTOK[model]
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000


@dataclass
class Reservation:
    day: str            # the ET date it was made on
    amount: float       # the worst case held for it
    open: bool = True


class Ledger:
    """Spend for the current America/New_York day. reserve() checks and holds the worst case in one step under
    a lock, so two visitors can't both take the last room under the cap."""

    def __init__(self, cap_usd: float = DAILY_CAP_USD, now=None):
        self.cap = cap_usd
        self._now = now or (lambda: datetime.now(ET))
        self._lock = threading.Lock()
        self._day = self._today()
        self._spent = 0.0          # settled calls
        self._held = 0.0           # open reservations

    def _today(self) -> str:
        return self._now().astimezone(ET).date().isoformat()

    def _roll(self) -> None:       # call with the lock held
        today = self._today()
        if today != self._day:
            self._day, self._spent, self._held = today, 0.0, 0.0

    def remaining(self) -> float:
        with self._lock:
            self._roll()
            return max(0.0, self.cap - self._spent - self._held)

    def reserve(self, worst_case_usd: float, enforce: bool = True) -> Reservation | None:
        """None when the worst case doesn't fit today. enforce=False (owner) always reserves, so the
        owner's spend still counts against what visitors have left."""
        with self._lock:
            self._roll()
            if enforce and self._spent + self._held + worst_case_usd > self.cap + 1e-12:
                return None
            self._held += worst_case_usd
            return Reservation(self._day, worst_case_usd)

    def settle(self, res: Reservation, actual_usd: float) -> None:
        """Replace the held worst case with the actual cost. A reservation from a previous day only
        drops its hold if that day is still current (a new day already started from zero)."""
        with self._lock:
            self._roll()
            if not res.open:
                return
            res.open = False
            if res.day == self._day:
                self._held -= res.amount
                self._spent += actual_usd

    def release(self, res: Reservation) -> None:
        """The request was rejected and not billed: give the hold back."""
        with self._lock:
            self._roll()
            if res.open and res.day == self._day:
                self._held -= res.amount
            res.open = False


def rejected_before_billing(exc: BaseException) -> bool:
    """True for a 4xx response: the API refused the request, so it wasn't billed and the hold is released.
    Anything else (5xx, connection error, timeout, a response the SDK couldn't validate, an unexpected error)
    may have been billed, so the caller settles at the worst case."""
    status = getattr(exc, "status_code", None)
    return isinstance(status, int) and 400 <= status < 500


def monthly_limit_error(exc: BaseException) -> bool:
    """The account's monthly spend limit, as documented at https://platform.claude.com/docs/en/api/rate-limits
    (checked 2026-10-11):
    - a limit you set: HTTP 400, invalid_request_error, message starting "You have reached your specified"
      ("...API usage limits" or "...workspace API usage limits")
    - the usage tier's cap: HTTP 429, rate_limit_error, error.details.error_code "enforced_spend_limit_reached"
    Any other 400 or 429 is an ordinary failure."""
    status = getattr(exc, "status_code", None)
    body = getattr(exc, "body", None)
    err = body.get("error", {}) if isinstance(body, dict) else {}
    message = str(err.get("message") or getattr(exc, "message", "") or "")
    if status == 400 and err.get("type", "invalid_request_error") == "invalid_request_error":
        return message.startswith("You have reached your specified")
    if status == 429:
        details = err.get("details") if isinstance(err.get("details"), dict) else {}
        return details.get("error_code") == "enforced_spend_limit_reached"
    return False
