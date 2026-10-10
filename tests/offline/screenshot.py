"""Drive the offline app in headless Chromium and screenshot each state: home, loading, results,
after clicking Download. Prints a JSON report (run time, page height, whether results survive the download).

Usage (with run_offline.py already running on port 8501):
    python tests/offline/screenshot.py 8501 tests/offline/shots/run 2
The last number is how many seconds after clicking Run to capture the loading state."""
import json, os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

port, prefix = sys.argv[1], sys.argv[2]
Path(prefix).parent.mkdir(parents=True, exist_ok=True)
RUN = os.environ.get("RUN_LABEL", "Run analysis")
mid = float(sys.argv[3]) if len(sys.argv) > 3 else 0
report = {}

TALL_JS = """() => { let h = 0; document.querySelectorAll('*').forEach(e => {
  const cs = getComputedStyle(e); if ((cs.overflowY === 'auto' || cs.overflowY === 'scroll') && e.scrollHeight > h) h = e.scrollHeight; });
  return h; }"""

def tall_shot(page, path):
    h = page.evaluate(TALL_JS)
    page.set_viewport_size({"width": 1440, "height": max(900, h + 40)})
    page.wait_for_timeout(1200)
    page.screenshot(path=path)
    page.set_viewport_size({"width": 1440, "height": 900})
    return h
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    page.goto(f"http://localhost:{port}/")
    page.get_by_role("button", name=RUN).wait_for(timeout=60000)
    page.wait_for_timeout(1500)
    page.screenshot(path=f"{prefix}_home.png")

    # add FAST to the ticker picker (AAPL is the default)
    page.locator('[data-testid="stMultiSelect"] input').click()
    page.keyboard.type("FAST"); page.wait_for_timeout(600); page.keyboard.press("Enter"); page.keyboard.press("Escape")
    page.wait_for_timeout(800)
    page.screenshot(path=f"{prefix}_picked.png")

    t0 = time.time()
    page.get_by_role("button", name=RUN).click()
    if mid:
        page.wait_for_timeout(int(mid * 1000))
        report["loading_height"] = tall_shot(page, f"{prefix}_loading.png")
    page.locator('[data-testid="stDownloadButton"]').wait_for(timeout=120000)
    page.wait_for_timeout(2500)
    report["run_seconds"] = round(time.time() - t0, 1)
    report["page_height_px"] = tall_shot(page, f"{prefix}_results.png")
    report["buttons"] = page.locator("button").evaluate_all(
        "els => els.map(e => [e.innerText.trim(), e.getAttribute('kind'), getComputedStyle(e).backgroundColor]).filter(x => x[0])")

    # Does clicking the download button wipe the results?
    with page.expect_download() as dl:
        page.locator('[data-testid="stDownloadButton"] button').click()
    report["download_filename"] = dl.value.suggested_filename
    page.wait_for_timeout(3000)
    report["results_still_visible_after_download"] = page.locator('[data-testid="stDownloadButton"]').count() > 0
    page.screenshot(path=f"{prefix}_after_download.png")
    report["errors"] = errs
    print(json.dumps(report, indent=1))
    b.close()
