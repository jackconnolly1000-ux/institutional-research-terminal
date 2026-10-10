"""Browser check of how the app reports missing, failed and incomplete pieces, and that failures aren't cached.

Start the offline app with the scenarios first (from app/):
    MOCK_DELAY=2 MOCK_CUTOFF=STRL MOCK_ONE_10K=FAST MOCK_FAIL_ONCE=yahoo,8k \\
        .venv/bin/streamlit run tests/offline/run_offline.py --server.port 8601 -- app.py
Then:
    .venv/bin/python tests/offline/check_states.py 8601 tests/offline/shots/states

Runs AAPL + FAST + STRL twice in one browser session and prints a JSON report per run and tab.
Expected: run 1 shows the simulated Yahoo and 8-K failures for AAPL, no annual comparison for FAST,
and an incomplete answer for STRL. Run 2 recovers AAPL's market data and 8-K (they weren't cached)
and still reports STRL as incomplete (a cut-off answer is never cached as complete).
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

port, prefix = sys.argv[1], sys.argv[2]
Path(prefix).parent.mkdir(parents=True, exist_ok=True)

TAB_JS = """panel => ({
  notices: [...panel.querySelectorAll('.irt-card[role=status] .irt-card-title')].map(e => e.textContent + ': ' + e.nextElementSibling.textContent),
  section_states: [...panel.querySelectorAll('.irt-state')].map(e => e.textContent),
  evidence: (panel.querySelector('.irt-evidence summary') || {}).textContent || null,
  failed_sources: [...panel.querySelectorAll('.irt-evidence li')].filter(li => /Download failed|Section not found/.test(li.textContent)).map(li => li.textContent.slice(0, 90)),
  trend_note: [...panel.querySelectorAll('.irt-note')].map(e => e.textContent).find(t => /Annual trend|Comparison unavailable/.test(t)) || null,
  findings: panel.querySelectorAll('.irt-card .irt-card-title').length,
  excerpt_labels: [...new Set([...panel.querySelectorAll('.irt-chip')].map(c => c.textContent).filter(t => t.startsWith('Excerpt')))],
  tile_sources: [...panel.querySelectorAll('.irt-tile .src')].map(e => e.textContent),
  clipped: [...panel.querySelectorAll('.irt-tile .src, .irt-chip, .irt-card-title')].filter(e => e.scrollWidth > e.clientWidth + 1).length,
})"""


def run_once(page, n):
    page.get_by_role("button", name="Run analysis").click()
    page.locator('[data-testid="stDownloadButton"]').wait_for(timeout=180000)
    page.wait_for_timeout(2500)
    report = {"summary": page.locator("p.irt-subtitle").nth(1).inner_text()}
    tabs = page.locator('[data-baseweb="tab"]')
    for i in range(tabs.count()):
        name = tabs.nth(i).inner_text().strip()
        tabs.nth(i).click()
        page.wait_for_timeout(1200)
        panel = page.locator('[data-baseweb="tab-panel"]:visible').first
        report[name] = panel.evaluate(TAB_JS)
        h = page.evaluate("() => Math.max(...[...document.querySelectorAll('*')].map(e => e.scrollHeight))")
        page.set_viewport_size({"width": 1440, "height": min(max(900, h + 40), 7000)})
        page.wait_for_timeout(800)
        page.screenshot(path=f"{prefix}_run{n}_{name}.png")
        page.set_viewport_size({"width": 1440, "height": 900})
    return report


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"http://localhost:{port}/")
    page.get_by_role("button", name="Run analysis").wait_for(timeout=60000)
    page.wait_for_timeout(1500)
    for t in ("FAST", "STRL"):
        page.locator('[data-testid="stMultiSelect"] input').click()
        page.keyboard.type(t); page.wait_for_timeout(500); page.keyboard.press("Enter"); page.keyboard.press("Escape")
        page.wait_for_timeout(500)
    out = {"run1": run_once(page, 1), "run2": run_once(page, 2)}

    with page.expect_download() as dl:
        page.locator('[data-testid="stDownloadButton"] button').click()
    xlsx = Path(prefix + "_export.xlsx")
    dl.value.save_as(xlsx)
    page.wait_for_timeout(2500)
    out["results_still_visible_after_download"] = page.locator('[data-testid="stDownloadButton"]').count() > 0

    # Phone width: one tab, full page
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(1500)
    out["mobile_horizontal_overflow_px"] = page.evaluate(
        "() => Math.max(0, ...[...document.querySelectorAll('[data-testid=stAppViewContainer] *')].map(e => e.getBoundingClientRect().right - window.innerWidth))")
    h = page.evaluate("() => Math.max(...[...document.querySelectorAll('*')].map(e => e.scrollHeight))")
    page.set_viewport_size({"width": 390, "height": min(h + 40, 9000)})
    page.wait_for_timeout(800)
    page.screenshot(path=f"{prefix}_mobile.png")
    out["export"] = str(xlsx)
    out["errors"] = errors
    print(json.dumps(out, indent=1))
    b.close()
