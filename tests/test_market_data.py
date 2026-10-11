"""Tests for market_data.py. No network: a fake stands in for yfinance.Ticker.

Run from app/:  .venv/bin/python -m unittest discover -s tests -p "test_*.py"
"""
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from market_data import ET, MarketDataError, fetch_financials  # noqa: E402

NOW = datetime(2026, 10, 10, 10, 42, tzinfo=ET)


def fake(info=None, error=None):
    class T:
        def __init__(self, ticker):
            if error:
                raise error
            self.info = info
    return T


class Financials(unittest.TestCase):
    def test_values_stay_numeric_with_metadata(self):
        r = fetch_financials("AAPL", fake({"currentPrice": 254.32, "marketCap": 3.41e12, "grossMargins": 0.4865,
                                           "regularMarketTime": 1791902400}), now=NOW)
        m = r["metrics"]
        self.assertEqual(m["gross_margin"]["value"], 0.4865)
        self.assertEqual(m["gross_margin"]["unit"], "fraction")
        self.assertIsNone(m["gross_margin"]["period"])            # shown as "Period not stated"
        self.assertTrue(m["price"]["period"].startswith("Quote as of"))
        self.assertEqual(r["retrieved_at"], "2026-10-10T10:42:00-04:00")

    def test_missing_fields_are_none_not_zero(self):
        m = fetch_financials("X", fake({"currentPrice": 10, "forwardPE": "Infinity", "freeCashflow": None}), now=NOW)["metrics"]
        self.assertIsNone(m["forward_pe"]["value"])
        self.assertIsNone(m["free_cash_flow"]["value"])
        self.assertIsNone(m["price"]["period"])                   # no quote time given

    def test_errors_raise_instead_of_returning_na(self):
        with self.assertRaises(MarketDataError):
            fetch_financials("X", fake(error=ConnectionError("down")), now=NOW)
        with self.assertRaises(MarketDataError):
            fetch_financials("X", fake({"symbol": "X"}), now=NOW)  # Yahoo's reply for an unknown symbol


if __name__ == "__main__":
    unittest.main()
