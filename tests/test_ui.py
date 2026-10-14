"""Smoke tests for ui.py: every component renders from the shapes analysis.py produces, and AI text is escaped.
No network. Streamlit is imported by ui.py but no page is drawn.

Run from app/:  .venv/bin/python -m unittest discover -s tests -p "test_*.py"
"""
import html
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ui  # noqa: E402
import filing_review  # noqa: E402
from analysis import check_response  # noqa: E402
from test_analysis import answer, finding, sources  # noqa: E402


class Components(unittest.TestCase):
    def setUp(self):
        bad = finding(source_id="MDA", paragraph_id="", quote="Net sales increased 8% to $5.2 billion",
                      summary="Income fell to $14.7 million <b>after</b> costs\n\nrose.")
        self.r = check_response("tool_use", answer(catalysts=[bad]), sources())

    def test_every_section_renders(self):
        s = self.r["sections"]
        html = (ui.findings_list(s["catalysts"]["items"], "catalyst") + ui.findings_list(s["risks"]["items"], "risk")
                + ui.findings_list(s["other_risks"]["items"], "other_risk") + ui.event_list(s["events"]["items"])
                + ui.impact_criteria() + ui.trend_note(self.r["comparison"])
                + ui.unchanged_list(self.r["comparison"]) + ui.analysis_banner(self.r) + ui.skeleton("AAPL", "Queued"))
        self.assertIn("Figures to check", html)
        self.assertIn("Changed since the prior 10-K: edited", html)
        self.assertIn("Potential implication</div>", html)

    def test_ai_text_is_escaped_and_kept_in_one_block(self):
        row = ui.finding_row(self.r["sections"]["catalysts"]["items"][0], "catalyst")
        self.assertIn("&lt;b&gt;after&lt;/b&gt;", row)
        self.assertNotIn("\n", row)                      # a blank line would end st.markdown's HTML block

    def test_impact_is_plain_text_and_rows_are_ordered(self):
        items = [dict(i, impact=imp) for i, imp in zip(self.r["sections"]["catalysts"]["items"] * 4,
                                                      ["LOW", "HIGH", "NOT_ASSESSED", "HIGH"])]
        for n, it in enumerate(items):
            it["headline"] = f"Row {n}"
        html = ui.findings_list(items, "catalyst")
        self.assertIn('<div class="row-meta">Impact: High', html)
        self.assertNotIn("irt-chip", html)                       # no pills or badges anywhere in a row
        self.assertIn('<div class="sub-label">Potential implication</div>', html)   # its own labeled block
        order = [html.index(f"Row {n}") for n in (1, 3, 0, 2)]                       # High, High, Low, Not assessed
        self.assertEqual(order, sorted(order))

    def test_metrics_panel(self):
        html = ui.metric_tiles([("Price and valuation", "Yahoo Finance · retrieved Oct 10, 2026, 2:04 PM ET",
                                 [("Price", "$254.32", "Quote as of Oct 9, 2026, 4:00 PM ET")]),
                                ("Profitability", "Yahoo Finance · retrieved Oct 10, 2026, 2:04 PM ET",
                                 [("Gross margin", "48.65%", "Period not stated")])])
        self.assertEqual(html.count('class="irt-group '), 2)
        # Column counts are classes, not inline CSS variables (Streamlit drops those), so every tile gets equal width
        self.assertIn('class="irt-metrics irt-cols-2"', html)
        self.assertEqual(html.count("irt-span-1"), 2)
        self.assertNotIn("--tiles", html)
        self.assertIn("Period not stated", html)
        self.assertEqual(ui.metric_tiles([]), "")

    def test_sentences_keep_every_word(self):
        text = "Beginning in 2025, new U.S. tariffs applied to imports. Apple Inc. expects costs to rise. Timing is uncertain."
        parts = ui.sentences(text)
        self.assertEqual(parts, ["Beginning in 2025, new U.S. tariffs applied to imports.", "Apple Inc. expects costs to rise.",
                                 "Timing is uncertain."])
        self.assertEqual(" ".join(parts), text)
        self.assertEqual(ui.sentences("One sentence only."), ["One sentence only."])

    def test_metrics_panel_states_source_once(self):
        cap = "Yahoo Finance · retrieved Oct 10, 2026, 2:04 PM ET"
        html = ui.metric_tiles([("Price and valuation", cap, [("Price", "$1.00", "p")]), ("Profitability", cap, [("Gross margin", "48.7%", "p")])])
        self.assertEqual(html.count("Yahoo Finance"), 1)
        self.assertIn('class="irt-metrics-foot">Source: Yahoo Finance', html)
        self.assertEqual(ui.format_metric(0.48651, "fraction"), "48.7%")

    def test_two_sources_are_each_named_once(self):
        yahoo, sec = "Yahoo Finance · retrieved Oct 10, 2026, 2:04 PM ET", "SEC XBRL company facts · retrieved Oct 11, 2026"
        html = ui.metric_tiles([("Price and valuation", yahoo, [("Price", "$1.00", "p")] * 3),
                                ("From SEC filings · TTM to Jun 27, 2026", sec, [("Revenue", "$466.82B", "10-Q")] * 4)])
        self.assertIn(f"Source: {yahoo}; {sec}</div>", html)
        self.assertIn('class="irt-metrics irt-cols-7"', html)
        self.assertIn(".irt-cols-7 {", ui._GRID_CSS)   # 3 + 4 tiles need a seven-column class

    def test_eight_k_items_come_from_edgar(self):
        self.assertEqual(ui.eight_k_items("5.02,9.01"), "Item 5.02 Director or officer change")
        self.assertEqual(ui.eight_k_items("2.02,7.01,9.01"), "Item 2.02 Results of operations · Item 7.01 Regulation FD disclosure")
        self.assertEqual(ui.eight_k_items("9.01"), "Item 9.01 Financial statements and exhibits")   # shown when it's the only item
        self.assertEqual(ui.eight_k_items("6.99"), "Item 6.99")                                       # unknown code: number only
        self.assertEqual(ui.eight_k_items(""), "")

    def test_filing_index_never_claims_content_was_reviewed(self):
        inventory = {"status": "incomplete", "since": "2026-06-30", "through": "2026-10-14",
                     "notes": ["Older filing page was unavailable."],
                     "filings": [{"form": "8-K", "filed": "2026-09-24", "items": "2.03,9.01",
                                  "accession": "0000000001-26-000001", "url": "https://www.sec.gov/test-index.htm",
                                  "review": "Not checked"}]}
        rendered = filing_review.render(inventory)
        self.assertIn("Filing index incomplete", rendered)
        self.assertIn("Document contents and exhibits: Not checked", rendered)
        self.assertIn("8-K filed 2026-09-24", rendered)
        self.assertIn("Item 2.03 New financial obligation", rendered)
        self.assertIn("Not checked: Older filing page", rendered)
        self.assertIn("Not checked: this saved result", filing_review.render(None))

    def test_rows_say_what_a_click_does(self):
        html = ui.findings_list(self.r["sections"]["risks"]["items"][:1], "risk")
        self.assertIn('class="toggle"', html)
        self.assertNotIn('class="chev"', html)

    def test_excerpt_note_depends_on_the_check(self):
        item = self.r["sections"]["risks"]["items"][0]
        matched = html.unescape(ui._excerpt_block(item))
        self.assertIn("The quoted words appear in this filing", matched)
        missed = html.unescape(ui._excerpt_block(dict(item, excerpt={"status": "not_matched", "found_in": []})))
        self.assertIn("The code couldn't find these words in the cited filing.", missed)
        self.assertNotIn("The quoted words appear in this filing", missed)
        short = html.unescape(ui._excerpt_block(dict(item, excerpt={"status": "too_short"})))
        self.assertNotIn("The quoted words appear", short)

    def test_no_input_message_per_section(self):
        none = {"status": "no_input", "items": [], "dropped": []}
        state = lambda name: html.unescape(ui.section_state(none, name))
        self.assertIn("No usable risk-factor section", state("risks"))
        self.assertIn("(MD&A) wasn't found", state("other_risks"))
        self.assertIn("No 8-Ks filed", state("events"))

    def test_skipped_is_its_own_state(self):
        self.assertEqual(ui.SKIP_MESSAGES["daily"], "Today's limit for live analyses is reached. It resets at midnight ET. "
                                                    "The saved AAPL and STRL sample works now.")
        self.assertEqual(ui.SKIP_MESSAGES["monthly"], "The monthly AI budget for this demo is used up.")
        strip = ui.progress_strip({"AAPL": ("done", "41s"), "STRL": ("skipped", ui.SKIP_LABELS["daily"])})
        self.assertIn("skipped, daily limit reached", strip)
        self.assertNotIn('prog problem"><b>STRL', strip)          # skipped isn't styled as a failure

    def test_every_category_has_a_label(self):
        import analysis
        self.assertEqual(set(analysis.CATEGORIES + analysis.EVENT_CATEGORIES) - set(ui.CATEGORY_LABELS), set())


if __name__ == "__main__":
    unittest.main()
