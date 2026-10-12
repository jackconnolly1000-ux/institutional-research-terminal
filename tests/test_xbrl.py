"""Tests for xbrl.py on real SEC company facts, trimmed to the six tags it reads (tests/fixtures/*_companyfacts.json,
built by tests/fixtures/make_fixtures.py from data.sec.gov downloads on Oct 11, 2026).

Expected values were worked out by hand from the raw records, not from xbrl.py's output.
Dollar figures in comments are $ millions; the data is in dollars.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import xbrl  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
M = 1_000_000


def load(ticker):
    return json.loads((FIXTURES / f"{ticker}_companyfacts.json").read_text(encoding="utf-8"))


def accessions(metric):
    return [f["accession"] for f in metric["filings"]]


class Apple(unittest.TestCase):
    """September fiscal year; the latest periodic filing is the 10-Q for the quarter ended Jun 27, 2026."""

    def setUp(self):
        self.r = xbrl.ttm_metrics(load("AAPL"))

    def test_gross_margin_ttm_to_jun_27_2026(self):
        # Gross profit 195,201 + 178,782 - 146,860 = 227,123; revenue 416,161 + 364,357 - 313,695 = 466,823
        gm = self.r["metrics"]["gross_margin"]
        self.assertEqual(self.r["period_end"], "2026-06-27")
        self.assertEqual(gm["period_end"], "2026-06-27")
        self.assertEqual(gm["unit"], "fraction")
        self.assertAlmostEqual(gm["value"], 227_123 / 466_823, places=10)
        self.assertEqual(round(gm["value"] * 100, 2), 48.65)
        rev = self.r["metrics"]["revenue"]
        self.assertEqual(rev["value"], 466_823 * M)
        self.assertEqual(rev["unit"], "USD")
        self.assertEqual(rev["tags"], ["RevenueFromContractWithCustomerExcludingAssessedTax"])

    def test_filings_used(self):
        # FY2025 from the 10-K; both year-to-date values from the newest 10-Q (the prior year is its comparative,
        # and the most recently filed value wins)
        gm = self.r["metrics"]["gross_margin"]
        self.assertEqual(gm["filings"], [
            {"form": "10-K", "period": "2025-09-27", "filed": "2025-10-31", "accession": "0000320193-25-000079"},
            {"form": "10-Q", "period": "2026-06-27", "filed": "2026-07-31", "accession": "0000320193-26-000020"},
        ])

    def test_gross_profit_ttm_to_mar_28_2026(self):
        # As of the Q2 10-Q (filed May 1, 2026): 195,201 + 124,012 - 103,142 = 216,071
        r = xbrl.ttm_metrics(load("AAPL"), filed_by="2026-05-01")
        self.assertEqual(r["period_end"], "2026-03-28")
        parts = {c["role"]: c["value"] for c in r["metrics"]["gross_margin"]["components"] if c["tag"] == "GrossProfit"}
        self.assertEqual(parts, {"fiscal year": 195_201 * M, "current year to date": 124_012 * M,
                                 "prior year to date": 103_142 * M})
        self.assertEqual(sum(v if role != "prior year to date" else -v for role, v in parts.items()), 216_071 * M)

    def test_latest_filing_is_a_10k_means_ttm_is_that_fiscal_year(self):
        r = xbrl.ttm_metrics(load("AAPL"), filed_by="2025-11-15")
        self.assertEqual(r["period_end"], "2025-09-27")
        self.assertEqual(r["basis"], "10-K")
        self.assertEqual(r["metrics"]["revenue"]["value"], 416_161 * M)
        self.assertEqual(accessions(r["metrics"]["revenue"]), ["0000320193-25-000079"])

    def test_free_cash_flow_is_operating_cash_flow_minus_capex(self):
        fcf = self.r["metrics"]["free_cash_flow"]
        self.assertEqual(fcf["tags"], ["NetCashProvidedByUsedInOperatingActivities", "PaymentsToAcquirePropertyPlantAndEquipment"])
        ttm = {}
        for c in fcf["components"]:
            ttm[c["tag"]] = ttm.get(c["tag"], 0) + (-c["value"] if c["role"] == "prior year to date" else c["value"])
        self.assertEqual(fcf["value"], ttm["NetCashProvidedByUsedInOperatingActivities"]
                         - ttm["PaymentsToAcquirePropertyPlantAndEquipment"])
        self.assertIsNone(fcf["note"])


class Sterling(unittest.TestCase):
    """December fiscal year; the latest periodic filing is the 10-Q for the quarter ended Jun 30, 2026."""

    def test_december_fiscal_year(self):
        r = xbrl.ttm_metrics(load("STRL"))
        self.assertEqual(r["period_end"], "2026-06-30")
        # Revenue 2,490.049 + 1,993.854 - 1,045.417; gross profit 572.314 + 484.253 - 237.980
        self.assertEqual(r["metrics"]["revenue"]["value"], 3_438_486_000)
        self.assertAlmostEqual(r["metrics"]["gross_margin"]["value"], 818_587 / 3_438_486, places=10)
        fiscal_year = [c for c in r["metrics"]["revenue"]["components"] if c["role"] == "fiscal year"][0]
        self.assertEqual((fiscal_year["start"], fiscal_year["end"]), ("2025-01-01", "2025-12-31"))

    def test_restated_prior_period_uses_the_most_recently_filed_value(self):
        # Q1 2022 revenue was 410.320 in the 10-Q filed May 3, 2022 and restated to 365.962 in the comparative
        # column of the 10-Q filed May 2, 2023. TTM to Mar 31, 2023 = 1,769.436 + 403.579 - 365.962 = 1,807.053
        r = xbrl.ttm_metrics(load("STRL"), filed_by="2023-05-02")
        rev = r["metrics"]["revenue"]
        self.assertEqual(rev["value"], 1_807_053_000)
        prior = [c for c in rev["components"] if c["role"] == "prior year to date"][0]
        self.assertEqual((prior["value"], prior["accession"]), (365_962_000, "0000874238-23-000067"))
        self.assertNotIn("0000874238-22-000048", accessions(rev))

    def test_filed_by_hides_later_filings(self):
        # A day before the restating 10-Q, the latest periodic filing is the FY2022 10-K
        r = xbrl.ttm_metrics(load("STRL"), filed_by="2023-05-01")
        self.assertEqual((r["period_end"], r["basis"]), ("2022-12-31", "10-K"))
        self.assertEqual(r["metrics"]["revenue"]["value"], 1_769_436_000)


class Bank(unittest.TestCase):
    """JPMorgan files no GrossProfit, OperatingIncomeLoss or capex tag, and tags Revenues only in its 10-K."""

    def test_missing_tags_are_not_reported_with_no_fallback(self):
        r = xbrl.ttm_metrics(load("JPM"))
        self.assertEqual(r["period_end"], "2026-06-30")
        for key in ("revenue", "gross_margin", "operating_margin", "free_cash_flow"):
            m = r["metrics"][key]
            self.assertIsNone(m["value"], key)
            self.assertEqual(m["note"], xbrl.NOT_REPORTED, key)
            self.assertEqual(m["filings"], [], key)
        # FY2025 Revenues exist, but the TTM period ends Jun 30, 2026, so the older year is not shown in its place
        self.assertIn("year to date", r["metrics"]["revenue"]["detail"])
        self.assertIn("GrossProfit", r["metrics"]["gross_margin"]["detail"])

    def test_second_revenue_tag_is_recorded(self):
        r = xbrl.ttm_metrics(load("JPM"), filed_by="2026-02-20")
        rev = r["metrics"]["revenue"]
        self.assertEqual((r["basis"], rev["value"], rev["tags"]), ("10-K", 182_447 * M, ["Revenues"]))


class Plumbing(unittest.TestCase):
    def test_url_pads_the_cik(self):
        self.assertEqual(xbrl.companyfacts_url("320193"),
                         "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json")

    def test_trim_keeps_only_the_six_tags_and_periodic_forms(self):
        raw = {"cik": 1, "entityName": "X", "facts": {"dei": {"EntityCommonStockSharesOutstanding": {}}, "us-gaap": {
            "GrossProfit": {"units": {"USD": [
                {"start": "2025-01-01", "end": "2025-12-31", "val": 5, "accn": "a", "form": "10-K", "filed": "2026-02-01"},
                {"start": "2025-01-01", "end": "2025-12-31", "val": 5, "accn": "b", "form": "8-K", "filed": "2026-01-20"}]}},
            "Assets": {"units": {"USD": []}}}}}
        t = xbrl.trim(raw)
        self.assertEqual(list(t["facts"]["us-gaap"]), ["GrossProfit"])
        self.assertEqual([r["accn"] for r in t["facts"]["us-gaap"]["GrossProfit"]["units"]["USD"]], ["a"])

    def test_no_periodic_filing_raises(self):
        with self.assertRaises(xbrl.XbrlError):
            xbrl.ttm_metrics({"cik": 1, "entityName": "X", "facts": {"us-gaap": {}}})


if __name__ == "__main__":
    unittest.main()
