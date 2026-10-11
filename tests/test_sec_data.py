"""Tests for sec_data.py (filing selection and section boundaries). No network.

Run from app/:  .venv/bin/python -m unittest discover -s tests -p "test_*.py"
"""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sec_data  # noqa: E402
from sec_data import Filing, find_section, select_filings  # noqa: E402

FILLER = "The Company sells products in many markets and depends on suppliers for components. " * 30


def f(form, filed, period="", acc=None):
    return Filing(form, filed, period, acc or f"0000000000-{filed[2:4]}-{filed[5:7]}{filed[8:]}", "doc.htm", "1")


class SelectFilings(unittest.TestCase):
    TODAY = date(2026, 10, 10)

    def test_annual_pair_and_quarterly_updates_since_latest_10k(self):
        filings = [f("8-K", "2026-09-18"), f("10-Q", "2026-08-01", "2026-06-30"), f("4", "2026-08-15"),
                   f("10-Q", "2026-05-01", "2026-03-31"), f("10-K", "2026-02-26", "2025-12-31"),
                   f("10-Q", "2025-11-04", "2025-09-30"), f("10-K/A", "2025-04-01", "2024-12-31"),
                   f("10-K", "2025-02-27", "2024-12-31"), f("8-K", "2025-01-02")]
        s = select_filings(filings, self.TODAY)
        self.assertEqual((s.annual_current.filed, s.annual_prior.filed), ("2026-02-26", "2025-02-27"))
        self.assertTrue(s.comparison_available)
        self.assertEqual([q.filed for q in s.quarterly_updates], ["2026-05-01", "2026-08-01"])  # oldest first
        self.assertEqual(s.mdna_source.filed, "2026-08-01")
        self.assertEqual([k.filed for k in s.eight_ks], ["2026-09-18"])  # 2025-01-02 is outside the window

    def test_one_10k_means_no_comparison_with_a_reason(self):
        s = select_filings([f("10-Q", "2026-08-01"), f("10-K", "2026-02-26")], self.TODAY)
        self.assertFalse(s.comparison_available)
        self.assertIn("Only one 10-K", s.notes[0])

    def test_no_10q_since_10k(self):
        s = select_filings([f("10-K", "2026-09-01"), f("10-Q", "2026-05-01"), f("10-K", "2025-09-01")], self.TODAY)
        self.assertEqual(s.quarterly_updates, [])
        self.assertEqual(s.mdna_source.form, "10-K")

    def test_foreign_filer_has_nothing(self):
        s = select_filings([f("20-F", "2026-04-01"), f("6-K", "2026-05-01")], self.TODAY)
        self.assertIsNone(s.annual_current)
        self.assertIsNone(s.mdna_source)

    def test_period_comes_from_edgar_report_date(self):
        subs = {"filings": {"recent": {"form": ["10-K"], "filingDate": ["2026-02-26"], "reportDate": ["2025-12-31"],
                                       "accessionNumber": ["0000874238-26-000024"], "primaryDocument": ["strl.htm"],
                                       "items": [""]}}}
        filing = sec_data.filings_from_submissions(subs, "0000874238")[0]
        self.assertEqual(filing.label, "10-K for the period ended 2025-12-31, filed 2026-02-26")
        self.assertEqual(filing.url, "https://www.sec.gov/Archives/edgar/data/874238/000087423826000024/strl.htm")


class FindSection(unittest.TestCase):
    TOC = ("TABLE OF CONTENTS Page PART I Item 1. Business 1 Item 1A. Risk Factors 5 Item 1B. Unresolved Staff "
           "Comments 17 Item 2. Properties 18 PART II Item 7. Management's Discussion and Analysis of Financial "
           "Condition and Results of Operations 20 Item 7A. Quantitative Disclosures 30 Item 8. Financial Statements 31 ")

    def test_real_heading_not_toc_or_cross_reference(self):
        text = (self.TOC + "Forward-looking statements are discussed in Part I, Item 1A of this Form 10-K under the "
                "heading “Risk Factors.” Item 1. Business We make things. " + FILLER +
                "Item 1A. Risk Factors The Company's business can be affected by many factors. " + FILLER +
                "For cybersecurity, see Item 1A of this Form 10-K. " + FILLER +
                "Item 1B. Unresolved Staff Comments None. Item 2. Properties We own buildings.")
        s = find_section(text, "1a", "10-K")
        self.assertEqual(s.status, "found")
        self.assertTrue(s.text.startswith("The Company's business can be affected"))
        self.assertTrue(s.text.endswith("see Item 1A of this Form 10-K. " + FILLER.strip()))
        self.assertNotIn("Unresolved", s.text)

    def test_quoted_cross_reference_is_not_a_heading(self):
        text = (self.TOC + "See Item 1A “Risk Factors” for further discussion. " + FILLER +
                "Refer to 'Item 1A. Risk Factors' of this Form 10-K. " + FILLER)
        s = find_section(text, "1a", "10-K")
        self.assertEqual(s.status, "missing")
        self.assertIn("xref", s.note)

    def test_split_first_letter_heading(self):
        text = self.TOC + "I tem 1A. Risk Factors The following discussion of risk factors applies. " + FILLER + "Item 1B. Unresolved Staff Comments None."
        self.assertEqual(find_section(text, "1a", "10-K").status, "found")

    def test_title_with_split_letters_and_running_headers(self):
        text = (self.TOC + "investor website. 13 PART I Item 1A ITEM 1A. RIS K FACTORS Our operations are subject to risks. "
                + FILLER + " 14 PART I Item 1A Demand is difficult to forecast. " + FILLER +
                " 28 PART I Item 1B, 1C ITEM 1B. UNRESOLVE D STAFF COMMENTS None.")
        s = find_section(text, "1a", "10-K")
        self.assertEqual(s.status, "found")
        self.assertTrue(s.text.startswith("Our operations are subject to risks."))
        self.assertIn("Demand is difficult to forecast.", s.text)   # running page headers don't end the section

    def test_10q_no_material_changes(self):
        text = ("PART II OTHER INFORMATION ITEM 1. LEGAL PROCEEDINGS 25 ITEM 1A. RISK FACTORS 25 ITEM 2. UNREGISTERED "
                "SALES 25 " + FILLER + "ITEM 1A — RISK FACTORS There have been no material changes from the risk "
                "factors described in Part I, Item 1A, Risk Factors of our most recently filed annual report on Form "
                "10-K. ITEM 2 — UNREGISTERED SALES OF EQUITY SECURITIES None.")
        s = find_section(text, "1a", "10-Q")
        self.assertEqual(s.status, "no_material_changes")
        self.assertTrue(s.text.startswith("There have been no material changes"))

    def test_not_applicable_smaller_reporting_company(self):
        text = "Item 1A. Risk Factors Not applicable for smaller reporting companies. Item 1B. Unresolved Staff Comments None."
        self.assertEqual(find_section(text, "1a", "10-K").status, "not_applicable")

    def test_10q_mdna_is_part_i_item_2_not_part_ii_item_2(self):
        text = ("Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations "
                "Revenue grew. " + FILLER + "Item 3. Quantitative and Qualitative Disclosures About Market Risk None. "
                "PART II Item 2. Unregistered Sales of Equity Securities None. Item 3. Defaults None.")
        s = find_section(text, "2", "10-Q")
        self.assertEqual(s.status, "found")
        self.assertTrue(s.text.startswith("Revenue grew."))

    def test_incorporated_earlier_10q_is_flagged(self):
        text = ("Item 1A. Risk Factors Except as set forth below and those disclosed in Part II, Item 1A of the "
                "second quarter 2026 Form 10-Q, which are incorporated by reference herein, there have been no "
                "material changes. " + FILLER + " Item 2. Unregistered Sales None.")
        self.assertTrue(find_section(text, "1a", "10-Q").references_earlier_10q)

    def test_missing_section_never_substitutes_text(self):
        s = find_section(FILLER, "1a", "10-K")
        self.assertEqual((s.status, s.text), ("missing", ""))


RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "sec"
# Expected results on real filings cached on Jack's Mac (outside the repo). Checked by eye Oct 10, 2026.
REAL = {
    ("AAPL", "aapl-20250927.htm", "10-K", "1a"): ("found", "The following summarizes factors", "1B"),
    ("AAPL", "aapl-20250927.htm", "10-K", "7"): ("found", "The following discussion should be read", "7A"),
    ("AAPL", "aapl-20260627.htm", "10-Q", "1a"): ("found", "The Company’s business, reputation", "2"),
    ("FAST", "fast-20251231.htm", "10-K", "1a"): ("found", "In addition to the other information", "1B"),
    ("FAST", "fast-20260630.htm", "10-Q", "1a"): ("no_material_changes", "There have been no material changes", "2"),
    ("STRL", "strl-20241231.htm", "10-K", "1a"): ("found", "The following discussion of risk factors", "1B"),
    ("STRL", "strl-20251231.htm", "10-K", "1a"): ("found", "The following discussion of risk factors", "1B"),
    ("STRL", "strl-20260630.htm", "10-Q", "1a"): ("no_material_changes", "There have not been any material changes", "2"),
    ("STRL", "strl-20260630.htm", "10-Q", "2"): ("found", "Cautionary Statement Regarding", "3"),
    ("MSFT", "msft-20260630.htm", "10-K", "1a"): ("found", "Our operations and financial results", "1B"),
}


@unittest.skipUnless(RAW.exists(), "real filings are cached only on Jack's Mac")
class RealFilings(unittest.TestCase):
    def test_cached_filings(self):
        for (ticker, suffix, form, item), (status, starts, ends_at) in REAL.items():
            with self.subTest(ticker=ticker, doc=suffix, item=item):
                path = next((RAW / ticker).glob(f"*_{suffix}"))
                s = find_section(sec_data.html_to_text(path.read_bytes()), item, form)
                self.assertEqual(s.status, status)
                self.assertTrue(s.text.startswith(starts), s.text[:80])
                self.assertIn(f"ends at Item {ends_at}.", s.note)

    def test_aapl_q3_incorporates_q2(self):
        path = next((RAW / "AAPL").glob("*_aapl-20260627.htm"))
        self.assertTrue(find_section(sec_data.html_to_text(path.read_bytes()), "1a", "10-Q").references_earlier_10q)


if __name__ == "__main__":
    unittest.main()
