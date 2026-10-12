"""Browser check of the saved sample: it renders both tabs, its label and the Excel download with no network calls.

Start the offline app with every network call failing (from app/):
    MOCK_NO_NETWORK=1 .venv/bin/streamlit run tests/offline/run_offline.py --server.port 8601 -- app.py
Then:
    .venv/bin/python tests/offline/check_sample.py 8601 tests/offline/shots/sample
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

port, prefix = sys.argv[1], sys.argv[2]
Path(prefix).parent.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"http://localhost:{port}/")
    page.get_by_role("button", name="View saved sample").wait_for(timeout=60000)
    page.wait_for_timeout(1000)
    page.get_by_role("button", name="View saved sample").click()
    page.locator('[data-testid="stDownloadButton"]').wait_for(timeout=60000)
    page.wait_for_timeout(2500)
    out = {"label": page.locator("p.irt-subtitle", has_text="Saved sample").first.inner_text(), "tabs": {}}
    tabs = page.locator('[role="tab"]')
    for i in range(tabs.count()):
        name = tabs.nth(i).inner_text().strip()
        tabs.nth(i).click()
        page.wait_for_timeout(1500)
        panel = page.locator('[role="tabpanel"]:visible').first
        out["tabs"][name] = panel.evaluate("""p => ({rows: p.querySelectorAll('.irt-row').length,
            chart: !!p.querySelector('.js-plotly-plot'),
            groups: [...p.querySelectorAll('.irt-group-head')].map(e => e.textContent),
            tiles: [...p.querySelectorAll('.irt-tile')].map(t => [...t.children].map(c => c.textContent).join(' | ')),
            metrics_foot: (p.querySelector('.irt-metrics-foot') || {}).textContent || null,
            chart_caption: [...p.querySelectorAll('[data-testid=stCaptionContainer]')].map(c => c.textContent).find(t => t.startsWith('Daily bars')) || null,
            problems: [...p.querySelectorAll('.irt-card[role=status], .irt-state')].map(e => e.textContent.slice(0, 90))})""")
        page.screenshot(path=f"{prefix}_{name}.png", full_page=True)
    with page.expect_download() as dl:
        page.locator('[data-testid="stDownloadButton"] button').click()
    out["download"] = dl.value.suggested_filename
    out["exceptions_on_page"] = page.locator('[data-testid="stException"]').count()

    # Phone width: nothing may stick out past the right edge; screenshot the header of the first tab
    page.set_viewport_size({"width": 390, "height": 844})
    tabs.nth(0).click()
    page.wait_for_timeout(1500)
    out["mobile_overflow"] = page.evaluate("""() => [...document.querySelectorAll('[data-testid=stAppViewContainer] *')]
        .filter(e => { const r = e.getBoundingClientRect(); return r.right > window.innerWidth + 0.5 && r.width > 0; })
        .slice(0, 8).map(e => e.tagName + '.' + (typeof e.className === 'string' ? e.className.split(' ')[0] : ''))""")
    page.locator('.irt-metrics').first.scroll_into_view_if_needed()
    page.locator('.irt-metrics').first.screenshot(path=f"{prefix}_metrics_390.png")
    out["errors"] = errors
    print(json.dumps(out, indent=1))
    b.close()
