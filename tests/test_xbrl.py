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


class CurrentRatioPilots(unittest.TestCase):
    """Expected values from docs/pilot_evidence_*.md (balance sheets of each pilot's latest 10-Q)."""

    def check(self, ticker, assets_m, liabilities_m, ratio_2dp, end, accession):
        r = xbrl.current_ratio(load(ticker))
        a, l = r["inputs"]["current_assets"], r["inputs"]["current_liabilities"]
        self.assertEqual((a["value"], l["value"]), (assets_m * M, liabilities_m * M))
        self.assertEqual((a["tag"], l["tag"]), ("us-gaap:AssetsCurrent", "us-gaap:LiabilitiesCurrent"))
        for x in (a, l):
            self.assertEqual((x["period_end"], x["accession"], x["form"], x["unit"], x["selection_rule"]),
                             (end, accession, "10-Q", "USD", xbrl.RULE_ANCHOR))
        self.assertAlmostEqual(r["value"], assets_m / liabilities_m, places=12)
        self.assertEqual(round(r["value"], 2), ratio_2dp)
        self.assertEqual((r["tag"], r["unit"], r["formula"], r["note"], r["period_end"]),
                         (None, "ratio", "AssetsCurrent / LiabilitiesCurrent", None, end))

    def test_lilly(self):
        self.check("LLY", 64_672, 47_741, 1.35, "2026-06-30", "0000059478-26-000081")

    def test_oracle(self):
        self.check("ORCL", 55_630, 47_514, 1.17, "2026-08-31", "0001193125-26-389274")

    def test_vistra(self):
        self.check("VST", 10_276, 10_557, 0.97, "2026-06-30", "0001692819-26-000019")


def balance_sheet(rows):
    """Synthetic company facts anchored, like facts(), by a fiscal 2026 Q2 10-Q (accession q2) for Jun 30, 2026.
    rows are (tag, end, val, form, filed, accn[, fy, fp]) USD instants."""
    gaap = {"Revenues": {"units": {"USD": [{"start": "2026-01-01", "end": "2026-06-30", "val": 1, "form": "10-Q",
                                            "filed": "2026-08-01", "accn": "q2"}]}}}
    for tag, end, val, form, filed, accn, *meta in rows:
        fy, fp = meta or (2026, "Q2")
        gaap.setdefault(tag, {"units": {"USD": []}})["units"]["USD"].append(
            {"end": end, "val": val, "form": form, "filed": filed, "accn": accn, "fy": fy, "fp": fp})
    return {"cik": 1, "entityName": "X", "facts": {"us-gaap": gaap}}


CA, CL = xbrl.CURRENT_ASSETS, xbrl.CURRENT_LIABILITIES
ASSETS = (CA, "2026-06-30", 300, "10-Q", "2026-08-01", "q2")
LIABILITIES = (CL, "2026-06-30", 200, "10-Q", "2026-08-01", "q2")


class CurrentRatioRules(unittest.TestCase):
    def test_ratio_from_the_anchor_filing(self):
        r = xbrl.current_ratio(balance_sheet([ASSETS, LIABILITIES]))
        self.assertEqual((r["value"], r["note"], r["inputs"]["current_assets"]["accession"]), (1.5, None, "q2"))

    def test_missing_input_is_unavailable_not_zero(self):
        r = xbrl.current_ratio(balance_sheet([ASSETS]))
        self.assertEqual((r["value"], r["note"]), (None, xbrl.UNAVAILABLE))
        self.assertIn("current liabilities: no LiabilitiesCurrent tag", r["detail"])
        self.assertEqual(r["inputs"]["current_assets"]["value"], 300)   # the input that exists is still shown

    def test_input_at_a_different_date_is_not_combined(self):
        # Liabilities only at Mar 31 in the anchor filing: not paired with Jun 30 assets
        r = xbrl.current_ratio(balance_sheet([ASSETS, (CL, "2026-03-31", 200, "10-Q", "2026-08-01", "q2")]))
        self.assertIsNone(r["value"])
        self.assertIn("reports current liabilities only at Mar 31, 2026", r["detail"])

    def test_input_from_another_filing_is_not_combined(self):
        # Only a later 10-Q reports Jun 30 liabilities: not substituted into the anchor's pair
        r = xbrl.current_ratio(balance_sheet([ASSETS, (CL, "2026-06-30", 200, "10-Q", "2026-11-01", "q3", 2026, "Q3")]))
        self.assertIsNone(r["value"])
        self.assertIn("other filings that do are not substituted (q3)", r["detail"])

    def test_amendment_restating_both_inputs_is_used_for_both(self):
        rows = [ASSETS, LIABILITIES, (CA, "2026-06-30", 330, "10-Q/A", "2026-09-01", "qa"),
                (CL, "2026-06-30", 220, "10-Q/A", "2026-09-01", "qa")]
        r = xbrl.current_ratio(balance_sheet(rows))
        a, l = r["inputs"]["current_assets"], r["inputs"]["current_liabilities"]
        self.assertEqual((a["accession"], l["accession"], r["value"]), ("qa", "qa", 1.5))

    def test_amendment_changing_one_input_takes_the_other_from_the_same_amendment(self):
        # The 10-Q/A changes assets and repeats liabilities unchanged: both inputs come from the 10-Q/A
        rows = [ASSETS, LIABILITIES, (CA, "2026-06-30", 360, "10-Q/A", "2026-09-01", "qa"),
                (CL, "2026-06-30", 200, "10-Q/A", "2026-09-01", "qa")]
        r = xbrl.current_ratio(balance_sheet(rows))
        a, l = r["inputs"]["current_assets"], r["inputs"]["current_liabilities"]
        self.assertEqual((a["accession"], l["accession"], r["value"]), ("qa", "qa", 1.8))
        self.assertIn("so both current-ratio inputs come from one filing", l["notes"][-1])

    def test_repeated_input_with_a_different_fiscal_period_gives_no_ratio(self):
        # The 10-Q/A's assets carry fiscal 2026 Q2 (so they replace the anchor's), but its liabilities row carries
        # Q3: it cannot be established that the repeated figure covers the anchor's period
        rows = [ASSETS, LIABILITIES, (CA, "2026-06-30", 360, "10-Q/A", "2026-09-01", "qa"),
                (CL, "2026-06-30", 200, "10-Q/A", "2026-09-01", "qa", 2026, "Q3")]
        r = xbrl.current_ratio(balance_sheet(rows))
        self.assertEqual((r["value"], r["note"]), (None, xbrl.UNAVAILABLE))
        self.assertIn("could not be established that its current liabilities figure covers the anchor's fiscal period",
                      r["detail"])

    def test_repeated_input_without_fiscal_period_gives_no_ratio(self):
        rows = [ASSETS, LIABILITIES, (CA, "2026-06-30", 360, "10-Q/A", "2026-09-01", "qa"),
                (CL, "2026-06-30", 200, "10-Q/A", "2026-09-01", "qa", None, None)]
        r = xbrl.current_ratio(balance_sheet(rows))
        self.assertIsNone(r["value"])
        self.assertIn("could not be established", r["detail"])

    def test_partial_amendment_is_not_mixed_with_the_original(self):
        # The 10-Q/A restates assets but does not report liabilities: no ratio across two filings
        rows = [ASSETS, LIABILITIES, (CA, "2026-06-30", 360, "10-Q/A", "2026-09-01", "qa")]
        r = xbrl.current_ratio(balance_sheet(rows))
        self.assertIsNone(r["value"])
        self.assertIn("comes from 10-Q/A (accession qa), which does not report current liabilities", r["detail"])
        self.assertIn("inputs from different filings are not combined", r["detail"])

    def test_amendment_with_conflicting_values_for_the_other_input_is_unavailable(self):
        rows = [ASSETS, LIABILITIES, (CA, "2026-06-30", 360, "10-Q/A", "2026-09-01", "qa"),
                (CL, "2026-06-30", 200, "10-Q/A", "2026-09-01", "qa"), (CL, "2026-06-30", 210, "10-Q/A", "2026-09-01", "qa")]
        r = xbrl.current_ratio(balance_sheet(rows))
        self.assertIsNone(r["value"])
        # Liabilities' own selection already finds the amendment's two values
        self.assertIn("reports more than one current liabilities value", r["detail"])

    def test_amendment_for_another_period_does_not_change_the_pair(self):
        rows = [ASSETS, LIABILITIES, (CA, "2026-06-30", 360, "10-Q/A", "2026-12-01", "qa3", 2026, "Q3")]
        r = xbrl.current_ratio(balance_sheet(rows))
        self.assertEqual((r["value"], r["inputs"]["current_assets"]["accession"]), (1.5, "q2"))
        self.assertIn("could not be established", r["inputs"]["current_assets"]["notes"][0])

    def test_zero_liabilities_explained_not_divided(self):
        r = xbrl.current_ratio(balance_sheet([ASSETS, (CL, "2026-06-30", 0, "10-Q", "2026-08-01", "q2")]))
        self.assertEqual((r["value"], r["note"]), (None, xbrl.UNAVAILABLE))
        self.assertIn("current liabilities are 0 USD; a ratio with a zero or negative denominator is not meaningful",
                      r["detail"])

    def test_negative_liabilities_explained_not_divided(self):
        r = xbrl.current_ratio(balance_sheet([ASSETS, (CL, "2026-06-30", -5, "10-Q", "2026-08-01", "q2")]))
        self.assertIsNone(r["value"])
        self.assertIn("current liabilities are -5 USD", r["detail"])


class GrossDebtLilly(unittest.TestCase):
    """Lilly's balance-sheet presentation (docs/pilot_evidence_lly.md): short-term borrowings and current maturities
    (DebtCurrent) plus long-term debt (LongTermDebtNoncurrent)."""

    def test_jun_30_2026(self):
        r = xbrl.baseline_gross_debt(load("LLY"), "LLY")
        self.assertEqual((r["value"], r["period_end"], r["note"], r["tag"], r["unit"]),
                         (54_908 * M, "2026-06-30", None, None, "USD"))
        self.assertEqual(r["formula"], "DebtCurrent + LongTermDebtNoncurrent")
        self.assertEqual([(x["tag"], x["value"], x["accession"], x["form"], x["filed"], x["period_end"])
                          for x in r["inputs"]],
                         [("us-gaap:DebtCurrent", 7_050 * M, "0000059478-26-000081", "10-Q", "2026-08-05", "2026-06-30"),
                          ("us-gaap:LongTermDebtNoncurrent", 47_858 * M, "0000059478-26-000081", "10-Q", "2026-08-05",
                           "2026-06-30")])
        self.assertIn("fair-value-table carrying amounts", r["not_added"])
        self.assertEqual(r["notes"], [])   # the 10-Q reports no combined total to check against
        # The overlap finding is stated for this 10-Q, with its amounts
        self.assertEqual(len(r["caveats"]), 1)
        self.assertIn("In this 10-Q, the Note 8 fair-value table", r["caveats"][0])

    def test_dec_31_2025_matches_the_10k_total(self):
        # 1,635 + 40,868 = 42,503, which the 10-K also reports as DebtLongtermAndShorttermCombinedAmount
        r = xbrl.baseline_gross_debt(load("LLY"), "LLY", filed_by="2026-03-01")
        self.assertEqual((r["value"], r["period_end"]), (42_503 * M, "2025-12-31"))
        self.assertEqual({x["accession"] for x in r["inputs"]}, {"0000059478-26-000013"})
        self.assertIn("Matches the filing's own total", r["notes"][0])
        self.assertEqual(r["caveats"], [])   # checked; the 10-Q's Note 8 finding does not carry over


class GrossDebtOracle(unittest.TestCase):
    """Oracle's balance-sheet presentation (docs/pilot_evidence_oracle.md): notes payable and other borrowings,
    current (NotesPayableCurrent) plus non-current (LongTermNotesAndLoans)."""

    def test_aug_31_2026(self):
        r = xbrl.baseline_gross_debt(load("ORCL"), "ORCL")
        self.assertEqual((r["value"], r["period_end"], r["note"], r["tag"]), (125_337 * M, "2026-08-31", None, None))
        self.assertEqual(r["formula"], "NotesPayableCurrent + LongTermNotesAndLoans")
        self.assertEqual([(x["tag"], x["value"], x["accession"], x["form"], x["filed"]) for x in r["inputs"]],
                         [("us-gaap:NotesPayableCurrent", 7_625 * M, "0001193125-26-389274", "10-Q", "2026-09-11"),
                          ("us-gaap:LongTermNotesAndLoans", 117_712 * M, "0001193125-26-389274", "10-Q", "2026-09-11")])
        self.assertEqual(r["notes"], [])   # the 10-Q reports no combined total
        for words in ("rounded fair-value disclosures", "lease liabilities", "short-term financing related to capital"):
            self.assertIn(words, r["not_added"])
        # The rule has no dates or amounts in it; the findings are scoped to this 10-Q in the caveats
        self.assertNotIn("125.0", r["not_added"])
        self.assertNotIn("Unavailable", r["not_added"])
        self.assertEqual(len(r["caveats"]), 3)
        self.assertIn("This 10-Q does not split the total by instrument: commercial paper at Aug 31, 2026 is "
                      "Unavailable", r["caveats"][0])
        self.assertIn("This 10-Q's rounded $125.0 billion", r["caveats"][1])
        self.assertIn("no balance is disclosed in this 10-Q (Unavailable)", r["caveats"][2])

    def test_may_31_2026_matches_the_10k_note_6_total(self):
        # 7,199 + 122,342 = 129,541, which the 10-K's Note 6 reports as DebtLongtermAndShorttermCombinedAmount
        r = xbrl.baseline_gross_debt(load("ORCL"), "ORCL", filed_by="2026-07-01")
        self.assertEqual((r["value"], r["period_end"]), (129_541 * M, "2026-05-31"))
        self.assertEqual({x["accession"] for x in r["inputs"]}, {"0001193125-26-277521"})
        self.assertIn("Matches the filing's own total", r["notes"][0])
        # The 10-K itemizes commercial paper; the 10-Q's "Unavailable" finding must not appear here
        self.assertEqual(len(r["caveats"]), 2)
        self.assertIn("In this 10-K, Note 6 itemizes the total, including commercial paper notes of 1,468M",
                      r["caveats"][0])
        self.assertFalse(any("commercial paper at" in c for c in r["caveats"]))
        self.assertIn("in the sections of this 10-K checked (Unavailable)", r["caveats"][1])

    def test_unchecked_filing_is_unavailable_with_components_kept(self):
        # The Feb 28, 2026 10-Q (filed Mar 11, 2026) is not among the filings reviewed: no total, and no findings
        # from the checked filings, but the selected component facts stay in the result for review
        r = xbrl.baseline_gross_debt(load("ORCL"), "ORCL", filed_by="2026-04-01")
        self.assertEqual((r["period_end"], r["value"], r["note"], r["caveats"], r["notes"]),
                         ("2026-02-28", None, xbrl.UNAVAILABLE, [], []))
        self.assertIn("presentation not checked for this filing: 10-Q accession 0001193125-26-101045", r["detail"])
        self.assertEqual([x["tag"] for x in r["inputs"]], ["us-gaap:NotesPayableCurrent", "us-gaap:LongTermNotesAndLoans"])
        self.assertEqual({x["accession"] for x in r["inputs"]}, {"0001193125-26-101045"})
        self.assertTrue(all(x["value"] is not None for x in r["inputs"]))

    def test_lilly_is_unchanged(self):
        self.assertEqual(xbrl.baseline_gross_debt(load("LLY"), "LLY")["value"], 54_908 * M)


class GrossDebtVistra(unittest.TestCase):
    """Vistra's presentation (docs/pilot_evidence_vistra.md, borrowing source audit): long-term debt due currently
    + long-term debt less amounts due currently + short-term borrowings + accounts receivable financing. The last is
    tagged only with the extension vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed, which companyfacts
    does not carry. Its document must be supplied by the checked accession before a total can be calculated."""

    def setUp(self):
        self.r = xbrl.baseline_gross_debt(load("VST"), "VST")

    def test_unavailable_without_the_checked_filing_document(self):
        self.assertEqual((self.r["value"], self.r["note"], self.r["caveats"], self.r["notes"]),
                         (None, xbrl.UNAVAILABLE, [], []))
        self.assertIn("vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed", self.r["detail"])
        self.assertIn("filing-level reader needs the main document", self.r["detail"])
        self.assertIn("never counted as zero", self.r["detail"])

    def test_readable_components_are_kept_for_review(self):
        got = [(x["tag"], x["value"], x["accession"], x["period_end"]) for x in self.r["inputs"]]
        self.assertEqual(got, [
            ("us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent", 1_876 * M, "0001692819-26-000019", "2026-06-30"),
            ("us-gaap:LongTermDebtAndCapitalLeaseObligations", 17_719 * M, "0001692819-26-000019", "2026-06-30"),
            ("us-gaap:ShortTermBorrowings", 0, "0001692819-26-000019", "2026-06-30")])   # reported as zero ("—")
        # 1,876 + 17,719 = 19,595, Note 12's long-term debt including amounts due currently (no lease line)
        self.assertEqual(sum(x["value"] for x in self.r["inputs"][:2]), 19_595 * M)
        self.assertIn("lease liabilities", self.r["not_added"])

    def test_checked_filing_document_completes_the_four_component_total(self):
        accession = "0001692819-26-000019"
        document = FIXTURES / "VST_2026Q2_ixbrl.htm"
        r = xbrl.baseline_gross_debt(load("VST"), "VST", filing_documents={accession: document})
        self.assertEqual((r["value"], r["note"], r["period_end"]), (19_895 * M, None, "2026-06-30"))
        self.assertEqual([x["value"] for x in r["inputs"]], [1_876 * M, 17_719 * M, 0, 300 * M])
        self.assertEqual({x["accession"] for x in r["inputs"]}, {accession})
        self.assertEqual({x["period_end"] for x in r["inputs"]}, {"2026-06-30"})
        extension = r["inputs"][3]
        self.assertEqual((extension["context_id"], extension["document"], extension["facts_found"]),
                         ("c-8", document.name, 2))
        self.assertEqual((extension["unit"], extension["scale"], extension["decimals"]), ("USD", 6, "-6"))
        self.assertEqual(extension["tag"], "vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed")
        self.assertIn(extension["tag"], r["formula"])

    def test_document_for_another_accession_is_not_used(self):
        r = xbrl.baseline_gross_debt(load("VST"), "VST", filing_documents={
            "0001692819-25-000085": FIXTURES / "VST_2026Q2_ixbrl.htm"})
        self.assertIsNone(r["value"])
        self.assertIn("checked accession 0001692819-26-000019", r["detail"])
        self.assertEqual(len(r["inputs"]), 3)

    def test_reader_rejection_does_not_add_partial_debt(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            document = Path(directory) / "wrong.htm"
            document.write_text('<root xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"/>', encoding="utf-8")
            r = xbrl.baseline_gross_debt(load("VST"), "VST", filing_documents={
                "0001692819-26-000019": document})
        self.assertIsNone(r["value"])
        self.assertIn("no vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed fact", r["detail"])
        self.assertEqual([x["value"] for x in r["inputs"]], [1_876 * M, 17_719 * M, 0])

    def test_unchecked_presentation_stays_unavailable_with_document(self):
        presentations = {"VST": {**xbrl.BORROWING_PRESENTATIONS["VST"], "checked": {}}}
        r = xbrl.baseline_gross_debt(load("VST"), "VST", presentations=presentations,
                                     filing_documents={"0001692819-26-000019": FIXTURES / "VST_2026Q2_ixbrl.htm"})
        self.assertIsNone(r["value"])
        self.assertIn("presentation not checked for this filing", r["detail"])

    def test_other_pilots_are_unchanged(self):
        self.assertEqual(xbrl.baseline_gross_debt(load("LLY"), "LLY")["value"], 54_908 * M)
        self.assertEqual(xbrl.baseline_gross_debt(load("ORCL"), "ORCL")["value"], 125_337 * M)


NPC, LTNL = xbrl.NOTES_PAYABLE_CURRENT, xbrl.LONG_TERM_NOTES_AND_LOANS


def checked(ticker, *accessions):
    """The company's real presentation, with the synthetic filings listed as checked (no caveats)."""
    return {ticker: {**xbrl.BORROWING_PRESENTATIONS[ticker], "checked": {a: [] for a in accessions}}}


class GrossDebtOracleRules(unittest.TestCase):
    def debt(self, rows):
        return xbrl.baseline_gross_debt(balance_sheet(rows), "ORCL", presentations=checked("ORCL", "q2", "qa"))

    def test_rounded_subset_leases_and_capex_financing_are_not_added(self):
        rows = [(NPC, "2026-06-30", 76, "10-Q", "2026-08-01", "q2"), (LTNL, "2026-06-30", 1177, "10-Q", "2026-08-01", "q2"),
                ("DebtInstrumentCarryingAmount", "2026-06-30", 1250, "10-Q", "2026-08-01", "q2"),
                ("OperatingLeaseLiability", "2026-06-30", 346, "10-Q", "2026-08-01", "q2"),
                ("FinanceLeaseLiability", "2026-06-30", 92, "10-Q", "2026-08-01", "q2")]
        self.assertEqual(self.debt(rows)["value"], 1253)

    def test_missing_component_is_unavailable(self):
        r = self.debt([(LTNL, "2026-06-30", 1177, "10-Q", "2026-08-01", "q2")])
        self.assertIsNone(r["value"])
        self.assertIn("notes payable and other borrowings, current: no NotesPayableCurrent tag", r["detail"])

    def test_another_companys_tags_are_not_used(self):
        # Lilly-style tags in an Oracle filing are not Oracle's verified components
        r = self.debt([(xbrl.DEBT_CURRENT, "2026-06-30", 76, "10-Q", "2026-08-01", "q2"),
                       (xbrl.LONG_TERM_DEBT_NONCURRENT, "2026-06-30", 1177, "10-Q", "2026-08-01", "q2")])
        self.assertIsNone(r["value"])
        self.assertIn("no NotesPayableCurrent tag", r["detail"])

    def test_component_split_across_filings_is_not_combined(self):
        rows = [(NPC, "2026-06-30", 76, "10-Q", "2026-08-01", "q2"), (LTNL, "2026-06-30", 1177, "10-Q", "2026-08-01", "q2"),
                (NPC, "2026-06-30", 80, "10-Q/A", "2026-09-01", "qa")]
        r = self.debt(rows)
        self.assertIsNone(r["value"])
        self.assertIn("which does not report notes payable and other borrowings, non-current", r["detail"])


DC, LTD = xbrl.DEBT_CURRENT, xbrl.LONG_TERM_DEBT_NONCURRENT
CURRENT_DEBT = (DC, "2026-06-30", 70, "10-Q", "2026-08-01", "q2")
LONG_DEBT = (LTD, "2026-06-30", 480, "10-Q", "2026-08-01", "q2")


class GrossDebtRules(unittest.TestCase):
    def debt(self, rows, ticker="LLY", checked_accessions=("q2", "qa"), **kw):
        presentations = (checked(ticker, *checked_accessions) if ticker in xbrl.BORROWING_PRESENTATIONS
                         else xbrl.BORROWING_PRESENTATIONS)
        return xbrl.baseline_gross_debt(balance_sheet(rows), ticker, presentations=presentations, **kw)

    def test_unchecked_filing_returns_components_but_no_total(self):
        r = self.debt([CURRENT_DEBT, LONG_DEBT], checked_accessions=())
        self.assertEqual((r["value"], r["note"], r["caveats"]), (None, xbrl.UNAVAILABLE, []))
        self.assertIn("presentation not checked for this filing: 10-Q accession q2", r["detail"])
        self.assertEqual([x["value"] for x in r["inputs"]], [70, 480])

    def test_amendment_to_a_checked_filing_must_itself_be_checked(self):
        # q2 was checked, the 10-Q/A that replaces both components was not
        rows = [CURRENT_DEBT, LONG_DEBT, (DC, "2026-06-30", 90, "10-Q/A", "2026-09-01", "qa"),
                (LTD, "2026-06-30", 480, "10-Q/A", "2026-09-01", "qa")]
        r = self.debt(rows, checked_accessions=("q2",))
        self.assertIsNone(r["value"])
        self.assertIn("10-Q/A accession qa is not among the filings reviewed", r["detail"])
        self.assertEqual({x["accession"] for x in r["inputs"]}, {"qa"})

    def test_component_needing_a_filing_reader_blocks_the_total(self):
        # Both readable components are present and the filing is checked, but a verified extension-tag component
        # cannot be read from companyfacts: no total, and it is not treated as zero
        presentations = checked("LLY", "q2")
        presentations["LLY"]["filing_reader_components"] = ["x:ExtensionBorrowings"]
        r = xbrl.baseline_gross_debt(balance_sheet([CURRENT_DEBT, LONG_DEBT]), "LLY", presentations=presentations)
        self.assertIsNone(r["value"])
        self.assertIn("x:ExtensionBorrowings is part of the verified presentation", r["detail"])
        self.assertEqual([x["value"] for x in r["inputs"]], [70, 480])

    def test_real_mapping_does_not_check_synthetic_filings(self):
        r = xbrl.baseline_gross_debt(balance_sheet([CURRENT_DEBT, LONG_DEBT]), "LLY")
        self.assertIsNone(r["value"])
        self.assertIn("presentation not checked for this filing", r["detail"])

    def test_sum_from_the_anchor_filing(self):
        r = self.debt([CURRENT_DEBT, LONG_DEBT])
        self.assertEqual((r["value"], r["note"]), (550, None))

    def test_company_without_a_verified_presentation_is_unavailable(self):
        r = self.debt([CURRENT_DEBT, LONG_DEBT], ticker="XYZ")
        self.assertEqual((r["value"], r["note"], r["inputs"]), (None, xbrl.UNAVAILABLE, []))
        self.assertIn("no verified borrowing presentation for XYZ", r["detail"])

    def test_missing_component_is_unavailable_not_zero(self):
        r = self.debt([CURRENT_DEBT])
        self.assertIsNone(r["value"])
        self.assertIn("long-term debt: no LongTermDebtNoncurrent tag", r["detail"])

    def test_component_at_another_date_is_not_added(self):
        r = self.debt([CURRENT_DEBT, (LTD, "2026-03-31", 480, "10-Q", "2026-08-01", "q2")])
        self.assertIsNone(r["value"])
        self.assertIn("reports long-term debt only at Mar 31, 2026", r["detail"])

    def test_zero_component_is_a_reported_zero(self):
        r = self.debt([(DC, "2026-06-30", 0, "10-Q", "2026-08-01", "q2"), LONG_DEBT])
        self.assertEqual(r["value"], 480)

    def test_negative_component_is_refused(self):
        r = self.debt([(DC, "2026-06-30", -5, "10-Q", "2026-08-01", "q2"), LONG_DEBT])
        self.assertIsNone(r["value"])
        self.assertIn("cannot be negative", r["detail"])

    def test_overlapping_presentation_is_not_added(self):
        # The fair-value table's tags for the same debt are present but are not components
        rows = [CURRENT_DEBT, LONG_DEBT, ("CommercialPaper", "2026-06-30", 50, "10-Q", "2026-08-01", "q2"),
                ("LongTermDebt", "2026-06-30", 500, "10-Q", "2026-08-01", "q2")]
        self.assertEqual(self.debt(rows)["value"], 550)

    def test_filer_total_that_matches_is_noted(self):
        r = self.debt([CURRENT_DEBT, LONG_DEBT, (xbrl.DEBT_TOTAL, "2026-06-30", 550, "10-Q", "2026-08-01", "q2")])
        self.assertEqual(r["value"], 550)
        self.assertIn("Matches the filing's own total", r["notes"][0])

    def test_filer_total_that_differs_stops_the_calculation(self):
        r = self.debt([CURRENT_DEBT, LONG_DEBT, (xbrl.DEBT_TOTAL, "2026-06-30", 600, "10-Q", "2026-08-01", "q2")])
        self.assertIsNone(r["value"])
        self.assertIn("components sum to 550 USD but the same filing", r["detail"])
        self.assertIn("overlap or a missing component", r["detail"])

    def test_filer_total_in_another_filing_is_not_used_for_the_check(self):
        rows = [CURRENT_DEBT, LONG_DEBT, (xbrl.DEBT_TOTAL, "2026-06-30", 600, "10-Q", "2026-11-01", "q3", 2026, "Q3")]
        r = self.debt(rows)
        self.assertEqual((r["value"], r["notes"]), (550, []))

    def test_amendment_changing_one_component_takes_the_other_from_it(self):
        rows = [CURRENT_DEBT, LONG_DEBT, (DC, "2026-06-30", 90, "10-Q/A", "2026-09-01", "qa"),
                (LTD, "2026-06-30", 480, "10-Q/A", "2026-09-01", "qa")]
        r = self.debt(rows)
        self.assertEqual((r["value"], [x["accession"] for x in r["inputs"]]), (570, ["qa", "qa"]))
        self.assertIn("so both gross-debt inputs come from one filing", r["inputs"][1]["notes"][-1])

    def test_partial_amendment_is_not_mixed_with_the_original(self):
        r = self.debt([CURRENT_DEBT, LONG_DEBT, (DC, "2026-06-30", 90, "10-Q/A", "2026-09-01", "qa")])
        self.assertIsNone(r["value"])
        self.assertIn("which does not report long-term debt", r["detail"])

    def test_repeated_component_with_another_fiscal_period_is_not_used(self):
        rows = [CURRENT_DEBT, LONG_DEBT, (DC, "2026-06-30", 90, "10-Q/A", "2026-09-01", "qa"),
                (LTD, "2026-06-30", 480, "10-Q/A", "2026-09-01", "qa", 2026, "Q3")]
        r = self.debt(rows)
        self.assertIsNone(r["value"])
        self.assertIn("could not be established that its long-term debt figure covers the anchor's fiscal period",
                      r["detail"])


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
