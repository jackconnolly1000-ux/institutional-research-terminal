"""Smoke tests for ui.py: every component renders from the shapes analysis.py produces, and AI text is escaped.
No network. Streamlit is imported by ui.py but no page is drawn.

Run from app/:  .venv/bin/python -m unittest discover -s tests -p "test_*.py"
"""
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
                + ui.question_list(s["questions"]["items"]) + ui.impact_criteria() + ui.trend_note(self.r["comparison"])
                + ui.unchanged_list(self.r["comparison"]) + ui.analysis_banner(self.r) + ui.skeleton("AAPL", "Queued"))
        self.assertIn("Figures to check", html)
        self.assertIn("Changed since the prior 10-K: edited", html)
        self.assertIn("Potential implication:", html)

    def test_ai_text_is_escaped_and_kept_in_one_block(self):
        row = ui.finding_row(self.r["sections"]["catalysts"]["items"][0], "catalyst")
        self.assertIn("&lt;b&gt;after&lt;/b&gt;", row)
        self.assertNotIn("\n", row)                      # a blank line would end st.markdown's HTML block

    def test_every_category_has_a_label(self):
        import analysis
        self.assertEqual(set(analysis.CATEGORIES + analysis.EVENT_CATEGORIES) - set(ui.CATEGORY_LABELS), set())


if __name__ == "__main__":
    unittest.main()
