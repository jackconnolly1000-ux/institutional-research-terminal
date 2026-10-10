"""Diagnostic: which filings the app uses for each ticker, and what each section extraction found.

Runs the production functions in sec_data.py and analysis.py (no copied logic) on live EDGAR data.
Filing documents are cached on disk by accession number in ~/Stock Project/data/raw/sec/{TICKER}/,
so reruns only fetch the filing list. Never calls the Anthropic API.

Usage (from app/):
    .venv/bin/python tests/check_risk_extraction.py                      # AAPL, FAST, STRL
    .venv/bin/python tests/check_risk_extraction.py --tickers MSFT,AAPL
    .venv/bin/python tests/check_risk_extraction.py --excerpts           # also check excerpts in the newest export
"""
import sys
import time
from datetime import date, datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analysis  # noqa: E402
import sec_data  # noqa: E402

TICKERS = ["AAPL", "FAST", "STRL"]
PROJECT = Path(__file__).resolve().parents[2]          # ~/Stock Project
RAW_DIR = PROJECT / "data" / "raw" / "sec"
EXPORT_DIR = PROJECT / "data" / "exports"
HEADERS = {"User-Agent": "InstitutionalResearch diagnostics@research-terminal.com"}
MIN_GAP = 0.15                                          # seconds between SEC requests, under SEC's 10/s
_last = [0.0]


def sec_get(url: str) -> bytes:
    for attempt in range(3):
        wait = MIN_GAP - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            return resp.content
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"HTTP {resp.status_code} for {url}")


def document_text(ticker: str, filing: sec_data.Filing):
    path = RAW_DIR / ticker / f"{filing.accession.replace('-', '')}_{filing.document}"
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(sec_get(filing.url))
        return sec_data.html_to_text(path.read_bytes())
    except Exception as e:
        return e


def run(ticker: str) -> list:
    tickers = __import__("json").loads(sec_get("https://www.sec.gov/files/company_tickers.json"))
    cik = next(str(v["cik_str"]).zfill(10) for v in tickers.values() if v["ticker"].upper() == ticker)
    subs = __import__("json").loads(sec_get(f"https://data.sec.gov/submissions/CIK{cik}.json"))
    sel = sec_data.select_with_older_pages(subs, cik, date.today(), lambda url: __import__("json").loads(sec_get(url)))
    wanted = [f for f in [sel.annual_current, sel.annual_prior, sel.mdna_source, *sel.quarterly_updates, *sel.eight_ks] if f]
    texts = {f.accession: document_text(ticker, f) for f in {f.accession: f for f in wanted}.values()}
    sources = analysis.build_sources(sel, texts)
    comp = analysis.comparison_status(sources)
    print(f"\n{'=' * 90}\n{ticker} (CIK {int(cik)})  comparison: {comp['status']}"
          + (f"  [{comp['current']}  vs  {comp['prior']}]" if comp["status"] == "available" else f"  ({comp['reason']})"))
    if comp["status"] == "available":
        print(f"  paragraph comparison (code): {comp['counts']}")
    for s in sources:
        c = s.coverage()
        where = f"{c.get('label', '')}" if c.get("form") else ""
        print(f"  {s.id or '-':<8} {s.status:<20} {c['chars']:>8,} chars  {s.role}  {where}")
        if s.note:
            print(f"           {s.note}")
        if s.text and s.id.startswith(("R_", "QU", "MDA")):
            print(f"           starts: {s.text[:90]!r}\n           ends  : {s.text[-90:]!r}")
    return sources


def check_excerpts(sources_by_ticker):
    import openpyxl
    exports = sorted(EXPORT_DIR.glob("*.xlsx"), key=lambda p: p.stat().st_mtime)
    if not exports:
        print("\nExcerpt check skipped: no .xlsx in data/exports"); return
    path = exports[-1]
    print(f"\n{'=' * 90}\nExcerpts in {path.name} (saved {datetime.fromtimestamp(path.stat().st_mtime):%Y-%m-%d %H:%M}),"
          " matched against every extracted source for that ticker:")
    wb = openpyxl.load_workbook(path, read_only=True)
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if not rows or "Ticker" not in rows[0]:
            continue
        col_q = next((rows[0].index(h) for h in ("Filing Excerpt", "Quote") if h in rows[0]), None)
        if col_q is None:
            continue
        for r in rows[1:]:
            t, q = r[rows[0].index("Ticker")], r[col_q]
            if not q or t not in sources_by_ticker:
                continue
            hits = [s.id for s in sources_by_ticker[t] if s.text and analysis.match_excerpt(q, s.text)["status"] == "matched"]
            print(f"  {t} [{ws.title}] {'matched in ' + ', '.join(hits) if hits else 'NOT MATCHED'}: {str(q)[:110]!r}")


def main():
    tickers = sys.argv[sys.argv.index("--tickers") + 1].upper().split(",") if "--tickers" in sys.argv else TICKERS
    print(f"Section extraction check, {datetime.now():%Y-%m-%d %H:%M}, tickers {tickers}. No Anthropic calls.")
    results = {t: run(t) for t in tickers}
    if "--excerpts" in sys.argv:
        check_excerpts(results)


if __name__ == "__main__":
    main()
