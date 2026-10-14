"""Tests for xbrl.py on real SEC company facts, trimmed to the tags it reads (tests/fixtures/*_companyfacts.json,
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


class CashPilots(unittest.TestCase):
    """The three debt and liquidity pilots (fixtures built from data.sec.gov downloads on Oct 14, 2026). Expected
    values and accessions come from docs/pilot_evidence_*.md, read from each filing's balance sheet."""

    def check(self, ticker, value_m, end, accession, filed):
        c = xbrl.cash_and_equivalents(load(ticker))
        self.assertEqual((c["value"], c["period_end"], c["accession"], c["form"], c["filed"]),
                         (value_m * M, end, accession, "10-Q", filed))
        self.assertEqual((c["unit"], c["tag"], c["note"], c["notes"]),
                         ("USD", "us-gaap:CashAndCashEquivalentsAtCarryingValue", None, []))
        self.assertEqual(c["selection_rule"], xbrl.RULE_ANCHOR)

    def test_lilly_jun_30_2026(self):
        self.check("LLY", 8_950, "2026-06-30", "0000059478-26-000081", "2026-08-05")

    def test_oracle_aug_31_2026(self):
        self.check("ORCL", 36_369, "2026-08-31", "0001193125-26-389274", "2026-09-11")

    def test_vistra_jun_30_2026(self):
        self.check("VST", 435, "2026-06-30", "0001692819-26-000019", "2026-08-10")

    def test_cash_uses_the_same_anchor_as_ttm(self):
        for ticker in ("LLY", "ORCL", "VST"):
            f = load(ticker)
            self.assertEqual(xbrl.cash_and_equivalents(f)["period_end"], xbrl.ttm_metrics(f)["period_end"], ticker)


def facts(cash_rows, cash_units=None):
    """Synthetic company facts: one 10-Q (accession q2, fiscal 2026 Q2) anchors Jun 30, 2026 through a revenue fact;
    cash_rows are (end, val, form, filed, accn[, fy, fp]) USD instants, where fy and fp are the filing's fiscal year
    and period (default 2026, Q2); cash_units adds rows in other units as {unit: [same tuples]}."""
    row = lambda end, val, form, filed, accn, fy=2026, fp="Q2": {
        "end": end, "val": val, "form": form, "filed": filed, "accn": accn, "fy": fy, "fp": fp}
    units = {"USD": [row(*r) for r in cash_rows]}
    for unit, rows in (cash_units or {}).items():
        units[unit] = [row(*r) for r in rows]
    revenue = [{"start": "2026-01-01", "end": "2026-06-30", "val": 1, "form": "10-Q", "filed": "2026-08-01",
                "accn": "q2"}]
    gaap = {"Revenues": {"units": {"USD": revenue}}}
    if cash_rows or cash_units:
        gaap[xbrl.CASH] = {"units": units}
    return {"cik": 1, "entityName": "X", "facts": {"us-gaap": gaap}}


ANCHOR = ("2026-06-30", 100, "10-Q", "2026-08-01", "q2")


class CashRules(unittest.TestCase):
    def test_anchor_filing_value(self):
        c = xbrl.cash_and_equivalents(facts([ANCHOR, ("2025-12-31", 90, "10-Q", "2026-08-01", "q2")]))
        self.assertEqual((c["value"], c["accession"], c["period_end"], c["notes"]), (100, "q2", "2026-06-30", []))

    def test_missing_tag_is_unavailable_not_zero(self):
        c = xbrl.cash_and_equivalents(facts([]))
        self.assertEqual((c["value"], c["note"]), (None, xbrl.UNAVAILABLE))
        self.assertIn("no CashAndCashEquivalentsAtCarryingValue tag", c["detail"])

    def test_anchor_filing_missing_the_fact_is_not_filled_from_another_filing(self):
        # Another filing reports Jun 30 (an amendment filed later); the anchor itself does not, so nothing is used
        c = xbrl.cash_and_equivalents(facts([("2026-06-30", 100, "10-Q/A", "2026-09-01", "qa")]))
        self.assertIsNone(c["value"])
        self.assertIn("other filings that do are not substituted (qa)", c["detail"])

    def test_wrong_date_is_unavailable(self):
        c = xbrl.cash_and_equivalents(facts([("2026-06-29", 100, "10-Q", "2026-08-01", "q2")]))
        self.assertIsNone(c["value"])
        self.assertIn("reports cash only at Jun 29, 2026, not at its balance-sheet date Jun 30, 2026", c["detail"])

    def test_wrong_unit_is_unavailable(self):
        c = xbrl.cash_and_equivalents(facts([], cash_units={"EUR": [ANCHOR]}))
        self.assertIsNone(c["value"])
        self.assertIn("only in EUR, not USD", c["detail"])

    def test_amendment_with_the_same_value_confirms(self):
        c = xbrl.cash_and_equivalents(facts([ANCHOR, ("2026-06-30", 100, "10-Q/A", "2026-09-01", "qa")]))
        self.assertEqual((c["value"], c["accession"], c["selection_rule"]), (100, "q2", xbrl.RULE_ANCHOR))
        self.assertEqual(len(c["notes"]), 1)
        self.assertIn("reports the same value", c["notes"][0])

    def test_amendment_to_the_same_period_replaces_and_says_so(self):
        c = xbrl.cash_and_equivalents(facts([ANCHOR, ("2026-06-30", 120, "10-Q/A", "2026-09-01", "qa")]))
        self.assertEqual((c["value"], c["accession"], c["form"], c["selection_rule"]),
                         (120, "qa", "10-Q/A", xbrl.RULE_AMENDED))
        self.assertIn("replacing 100 USD in 10-Q (accession q2)", c["notes"][0])

    def test_latest_of_two_amendments_wins_and_the_earlier_one_is_flagged(self):
        rows = [ANCHOR, ("2026-06-30", 110, "10-Q/A", "2026-09-01", "qa1"), ("2026-06-30", 120, "10-Q/A", "2026-10-01", "qa2")]
        c = xbrl.cash_and_equivalents(facts(rows))
        self.assertEqual((c["value"], c["accession"]), (120, "qa2"))
        self.assertTrue(any("Not used: 10-Q/A filed 2026-09-01 (accession qa1)" in n for n in c["notes"]))

    def test_amendment_is_hidden_before_it_was_filed(self):
        c = xbrl.cash_and_equivalents(facts([ANCHOR, ("2026-06-30", 120, "10-Q/A", "2026-09-01", "qa")]),
                                      filed_by="2026-08-15")
        self.assertEqual((c["value"], c["accession"], c["notes"]), (100, "q2", []))

    def test_amendment_to_a_later_period_is_a_comparative_not_a_replacement(self):
        # A 10-K/A for fiscal 2026 (fp FY) repeats Jun 30 with a different value: flagged, not used
        rows = [ANCHOR, ("2026-06-30", 130, "10-K/A", "2027-03-01", "ka", 2026, "FY"),
                ("2026-12-31", 140, "10-K/A", "2027-03-01", "ka", 2026, "FY")]
        c = xbrl.cash_and_equivalents(facts(rows))
        self.assertEqual((c["value"], c["accession"]), (100, "q2"))
        self.assertIn("Not used: 10-K/A filed 2027-03-01 (accession ka) reports 130 USD", c["notes"][0])

    def test_later_period_amendment_with_only_an_earlier_comparative_does_not_replace(self):
        # A 10-Q/A amending the Q3 report carries only a Jun 30 comparative. Its latest cash date is Jun 30, but its
        # filing says fiscal 2026 Q3, so it does not amend the Q2 anchor: flagged, not used
        rows = [ANCHOR, ("2026-06-30", 130, "10-Q/A", "2026-12-01", "qa3", 2026, "Q3")]
        c = xbrl.cash_and_equivalents(facts(rows))
        self.assertEqual((c["value"], c["accession"], c["selection_rule"]), (100, "q2", xbrl.RULE_ANCHOR))
        self.assertEqual(len(c["notes"]), 1)
        self.assertIn("could not be established that it amends the 10-Q for this period", c["notes"][0])

    def test_amendment_without_period_metadata_does_not_replace(self):
        rows = [ANCHOR, ("2026-06-30", 130, "10-Q/A", "2026-09-01", "qa", None, None)]
        c = xbrl.cash_and_equivalents(facts(rows))
        self.assertEqual((c["value"], c["accession"]), (100, "q2"))
        self.assertIn("could not be established", c["notes"][0])

    def test_amendment_with_conflicting_values_is_unavailable(self):
        rows = [ANCHOR, ("2026-06-30", 120, "10-Q/A", "2026-09-01", "qa"), ("2026-06-30", 125, "10-Q/A", "2026-09-01", "qa")]
        c = xbrl.cash_and_equivalents(facts(rows))
        self.assertEqual((c["value"], c["note"], c["accession"]), (None, xbrl.UNAVAILABLE, None))
        self.assertIn("amendment 10-Q/A filed 2026-09-01 (accession qa) reports more than one cash value", c["detail"])

    def test_differing_later_comparative_is_flagged_not_substituted(self):
        # A later 10-Q (period Sep 30) repeats Jun 30 with a different value
        rows = [ANCHOR, ("2026-06-30", 95, "10-Q", "2026-11-01", "q3"), ("2026-09-30", 80, "10-Q", "2026-11-01", "q3")]
        c = xbrl.cash_and_equivalents(facts(rows))
        self.assertEqual((c["value"], c["accession"], c["selection_rule"]), (100, "q2", xbrl.RULE_ANCHOR))
        self.assertEqual(len(c["notes"]), 1)
        self.assertIn("possible revision", c["notes"][0])

    def test_matching_later_comparative_adds_no_note(self):
        rows = [ANCHOR, ("2026-06-30", 100, "10-Q", "2026-11-01", "q3"), ("2026-09-30", 80, "10-Q", "2026-11-01", "q3")]
        self.assertEqual(xbrl.cash_and_equivalents(facts(rows))["notes"], [])

    def test_conflicting_values_in_the_anchor_filing_are_unavailable(self):
        c = xbrl.cash_and_equivalents(facts([ANCHOR, ("2026-06-30", 101, "10-Q", "2026-08-01", "q2")]))
        self.assertIsNone(c["value"])
        self.assertIn("more than one cash value", c["detail"])


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

    def test_trim_keeps_cash_instants_in_every_unit(self):
        cash = {"USD": [{"end": "2026-06-30", "val": 5, "accn": "a", "form": "10-Q", "filed": "2026-08-01"},
                        {"end": "2026-06-30", "val": 5, "accn": "b", "form": "8-K", "filed": "2026-07-20"}],
                "EUR": [{"end": "2026-06-30", "val": 4, "accn": "a", "form": "10-Q", "filed": "2026-08-01"}]}
        t = xbrl.trim({"cik": 1, "entityName": "X", "facts": {"us-gaap": {xbrl.CASH: {"units": cash}}}})
        kept = t["facts"]["us-gaap"][xbrl.CASH]["units"]
        self.assertEqual({u: [r["accn"] for r in rows] for u, rows in kept.items()}, {"USD": ["a"], "EUR": ["a"]})

    def test_no_periodic_filing_raises(self):
        with self.assertRaises(xbrl.XbrlError):
            xbrl.ttm_metrics({"cik": 1, "entityName": "X", "facts": {"us-gaap": {}}})


if __name__ == "__main__":
    unittest.main()
