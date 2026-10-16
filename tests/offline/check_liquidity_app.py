"""Run the complete saved-pilot view and the existing sample with all network calls disabled."""
import os
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT))
os.environ["MOCK_NO_NETWORK"] = "1"
os.environ["SEC_CONTACT_EMAIL"] = "offline-test@example.com"
import mocks  # noqa: E402
mocks.install()
from streamlit.testing.v1 import AppTest  # noqa: E402
import liquidity_pilot  # noqa: E402


def stale_view(*args, **kwargs):
    raise AssertionError("The app called a cached legacy view instead of the directly imported review module")


# Reproduce a long-lived process retaining the previous helper's UI functions after a code update.
liquidity_pilot.render = stale_view
liquidity_pilot.render_html = stale_view
liquidity_pilot.evidence_html = stale_view
liquidity_pilot.workbook = stale_view

app = AppTest.from_file(str(ROOT / "app.py"))
app.secrets["ANTHROPIC_API_KEY"] = "offline-placeholder"
app.run(timeout=30)
assert not app.exception and not app.error
assert not app.tabs
app.session_state["liquidity_pilot_open"] = True
app.run(timeout=30)
assert not app.exception and not app.error
text = html.unescape("\n".join(m.value for m in app.markdown))
assert all(value in text for value in ("54.91B", "125.34B", "19.90B", "Financing changes after June 30",
                                      "288B", "28.72B", "What remained after capital spending?",
                                      "Historical schedule at May 31, 2026", "$10.145B", "$19.909B"))
assert all(value in text for value in ("What funded Oracle’s cash balance?", "−$16.759B", "$2.565B",
                                      "Historical funding exclusions", "6.02(c)"))
assert all(value in text for value in ("How does Vistra fund its repayments?", "$650M", "$959M",
                                      "$6.295B", "Pulaski", "Current drawable amounts are Unavailable"))
assert all(value in text for value in ("Which resources could fund the dated payments?",
                                      "expires within this bucket", "expires before this bucket",
                                      "funding coverage Unavailable"))
assert all(value in text for value in ("May 31 undrawn commitment is $10B", "not a $12B commitment",
                                      "not assumed zero", "Later saved filings and audit scope"))
assert all(value in text for value in ("What funded Lilly’s cash balance?", "$10.764B", "$12.602B", "August 2026", "Indiana manufacturing", "not principal repayment amounts"))
assert all(value in text for value in ("Which May debt maturities are documented?", "2028-05-20", "4.150%", "initial issue amounts", "SEC financing check through October 15, 2026"))
assert all(value in text for value in ("How did operating earnings cover reported interest?", "31.17x", "$33.633B", "$1.079B", "without explicitly stating its capitalization basis"))
assert all(value in text for value in ("How did Oracle’s operating earnings cover reported interest?", "4.52x", "$23.057B", "$5.104B", "Borrowing-only interest coverage is Unavailable"))
assert all(value in text for value in ("How did Vistra’s operating earnings cover reported interest?", "3.19x", "$3.563B", "$1.117B", "gain-positive", "Other's detailed composition is Unavailable"))
assert text.count('Funding conclusion</h3>') == 3
assert all(value in text for value in ('Acquisition and manufacturing spending compete',
    'Equity proceeds and specified customer prepayments contributed',
    'June reported liquidity cannot be treated as current cash available to Parent',
    'Coverage bases differ:', 'Future funding coverage: Unavailable'))
buttons=[element.proto.label for element in app.get("download_button")]
assert set(("Download LLY review and evidence", "Download ORCL review and evidence",
            "Download VST review and evidence", "Download all three company reviews (optional)")) <= set(buttons)
next(b for b in app.button if b.label == "View saved sample").click().run(timeout=30)
assert not app.exception and not app.error
assert any("Saved sample. Analysis run" in m.value for m in app.markdown)
print("Saved liquidity pilot and existing sample passed with all network calls disabled.")
