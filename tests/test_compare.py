"""Tests for compare.py and sec_data.split_paragraphs: paragraph labels set by code. No network.

Run from app/:  .venv/bin/python -m unittest discover -s tests -p "test_*.py"
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compare  # noqa: E402
import sec_data  # noqa: E402

BASE = ("Our business depends on the timely delivery of components from a limited number of suppliers, and any "
        "disruption in supply could delay shipments and reduce net sales in the affected quarters.")
OTHER = ("We are subject to complex and changing laws in many jurisdictions, and compliance failures could result in "
         "fines, penalties and changes to how we operate our business in those markets.")


def labels(cur, prior):
    c = compare.compare_sections(cur, prior)
    return [(p.label, p.reason) for p in c.paragraphs], [p.text for p in c.removed]


class Labels(unittest.TestCase):
    def test_unchanged_and_year_roll_forward(self):
        self.assertEqual(labels([BASE], [BASE])[0], [("UNCHANGED", "")])
        a = "At December 31, 2025, we had $5.0 billion of debt outstanding under our credit facility and notes, due in several years."
        b = a.replace("2025", "2024")
        self.assertEqual(labels([a], [b])[0], [("UNCHANGED", "")])

    def test_figures_changed(self):
        a = "At December 31, 2025, we had $371.9 million of joint venture work to complete, of which $148.8 million was our share."
        b = "At December 31, 2024, we had $150.3 million of joint venture work to complete, of which $73.6 million was our share."
        self.assertEqual(labels([a], [b])[0], [("CHANGED", "figures changed")])

    def test_minor_edit_and_edit(self):
        minor = BASE.replace("components from", "components, including chips, from")
        self.assertEqual(labels([minor], [BASE])[0], [("CHANGED", "minor edit")])
        edited = BASE + " Tariffs and counter tariffs on imported components could also raise our costs and delay deliveries."
        self.assertEqual(labels([edited], [BASE])[0], [("CHANGED", "edited")])

    def test_text_removed(self):
        self.assertEqual(labels([BASE.split(", and any")[0] + "."], [BASE])[0], [("CHANGED", "text removed")])

    def test_new_and_removed(self):
        new = "We invest in artificial intelligence tools for estimating and scheduling, and these tools may not perform as expected."
        rows, removed = labels([BASE, new], [BASE, OTHER])
        self.assertEqual(rows, [("UNCHANGED", ""), ("NEW", "")])
        self.assertEqual(removed, [OTHER])

    def test_merged_paragraphs_match_joined_prior(self):
        rows, removed = labels([BASE + " " + OTHER], [BASE, OTHER])
        self.assertEqual(rows[0][0], "UNCHANGED")
        self.assertEqual(removed, [])

    def test_render_sends_only_changes_with_ids(self):
        new = "We invest in artificial intelligence tools for estimating and scheduling, and these tools may not perform as expected."
        c = compare.compare_sections([BASE, new], [BASE, OTHER])
        text = compare.render_for_prompt(c)
        self.assertNotIn(BASE, text)
        self.assertIn("[P2] NEW (no close match in the prior 10-K)", text)
        self.assertIn("[R1] REMOVED", text)
        self.assertEqual(compare.paragraph_labels(c), {"P2": ("NEW", ""), "R1": ("REMOVED", "")})

    def test_minor_edit_is_one_line(self):
        minor = BASE.replace("components from", "components, including chips, from")
        text = compare.render_for_prompt(compare.compare_sections([minor], [BASE]))
        self.assertEqual(len(text.splitlines()), 1)
        self.assertIn("added: including chips", text)


class Paragraphs(unittest.TestCase):
    def test_one_sentence_title_joins_its_body(self):
        title = "The early termination of contracts could adversely affect our business."
        self.assertEqual(sec_data.split_paragraphs(title + "\n" + BASE + "\n" + OTHER), [title + " " + BASE, OTHER])

    def test_page_breaks_headers_and_subheadings(self):
        section = ("Risks Related to Our Business\n" + BASE[:60] + "\n12\nPART I\nItem 1A\n" + BASE[60:] + "\n"
                   "Apple Inc. | 2025 Form 10-K | 12\n" + OTHER)
        self.assertEqual(sec_data.split_paragraphs(section), [BASE[:60] + " " + BASE[60:], OTHER])


RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "sec"


def _section(ticker, doc):
    path = next((RAW / ticker).glob(f"*_{doc}.htm"))
    return sec_data.find_section(sec_data.html_to_text(path.read_bytes()), "1a", "10-K")


def _compare(ticker, cur, prior):
    return compare.compare_sections(sec_data.split_paragraphs(_section(ticker, cur).text),
                                    sec_data.split_paragraphs(_section(ticker, prior).text))


@unittest.skipUnless(RAW.exists(), "real filings are cached only on Jack's Mac")
class RealFilings(unittest.TestCase):
    """Checked by eye Oct 10, 2026. Counts may move a little if extraction improves; labels of the named cases may not."""

    def find(self, comp, needle):
        return next(p for p in comp.paragraphs + comp.removed if needle in p.text)

    def test_strl(self):
        c = _compare("STRL", "strl-20251231", "strl-20241231")
        tariff = self.find(c, "tariffs and counter tariffs")
        self.assertEqual((tariff.label, tariff.reason), ("CHANGED", "edited"))
        self.assertIn("international trade issues including tariffs and counter tariffs", tariff.added)
        goodwill = self.find(c, "of goodwill and")
        self.assertEqual((goodwill.label, goodwill.reason), ("CHANGED", "figures changed"))
        # Its title stood alone and had no close match until titles were joined to their body text
        self.assertEqual(self.find(c, "early termination of contracts and uncertainty of new project awards").label, "CHANGED")

    def test_msft_supply_changed_and_no_header_fragments(self):
        c = _compare("MSFT", "msft-20260630", "msft-20250630")
        supply = self.find(c, "We may experience supply problems")
        self.assertEqual(supply.label, "CHANGED")                     # rewritten or edited; never NEW
        self.assertFalse([p for p in c.paragraphs if p.text.upper().startswith(("PART I", "ITEM 1A"))])

    def test_jnj_separation_is_new(self):
        c = _compare("JNJ", "jnj-20251228", "jnj-20241229")
        self.assertEqual(self.find(c, "planned separation of the Company's Orthopaedics business may not be completed").label, "NEW")

    def test_wmt_flipkart_removed(self):
        c = _compare("WMT", "wmt-20260131", "wmt-20250131")
        self.assertIn("Flipkart", " ".join(p.text for p in c.removed))

    def test_jpm_item_1a_points_elsewhere(self):
        s = _section("JPM", "jpm-20251231")
        self.assertEqual(s.status, "missing")
        self.assertIn("incorporated by reference", s.note)

    def test_counts_stay_close(self):
        # Recounted Oct 10, 2026 after one-sentence titles were joined to their body text
        expected = {"AAPL": ("aapl-20250927", "aapl-20240928", 34, 4), "FAST": ("fast-20251231", "fast-20241231", 32, 1),
                    "STRL": ("strl-20251231", "strl-20241231", 65, 12), "MSFT": ("msft-20260630", "msft-20250630", 39, 13),
                    "WMT": ("wmt-20260131", "wmt-20250131", 55, 3), "JNJ": ("jnj-20251228", "jnj-20241229", 36, 7)}
        for t, (cur, prior, unchanged, new) in expected.items():
            with self.subTest(t):
                c = _compare(t, cur, prior).counts()
                self.assertAlmostEqual(c.get("UNCHANGED", 0), unchanged, delta=3)
                self.assertAlmostEqual(c.get("NEW", 0), new, delta=2)


if __name__ == "__main__":
    unittest.main()
