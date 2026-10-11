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
        self.assertIn("Potential implication:", html)

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
        self.assertIn('<span class="irt-impact">Impact: High</span>', html)
        badge_lines = re.findall(r'<div class="badges">(.*?)</div>', html)
        self.assertTrue(all("tone-positive" not in b and "tone-negative" not in b for b in badge_lines))   # no colored impact pill
        order = [html.index(f"Row {n}") for n in (1, 3, 0, 2)]                       # High, High, Low, Not assessed
        self.assertEqual(order, sorted(order))

    def test_metrics_panel(self):
        html = ui.metric_tiles([("Price and valuation", "Yahoo Finance · retrieved Oct 10, 2026, 2:04 PM ET",
                                 [("Price", "$254.32", "Quote as of Oct 9, 2026, 4:00 PM ET")]),
                                ("Profitability", "Yahoo Finance · retrieved Oct 10, 2026, 2:04 PM ET",
                                 [("Gross margin", "48.65%", "Period not stated")])])
        self.assertEqual(html.count('class="irt-group"'), 2)
        self.assertIn("Period not stated", html)
        self.assertEqual(ui.metric_tiles([]), "")

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

    def test_every_category_has_a_label(self):
        import analysis
        self.assertEqual(set(analysis.CATEGORIES + analysis.EVENT_CATEGORIES) - set(ui.CATEGORY_LABELS), set())


if __name__ == "__main__":
    unittest.main()
