"""Build the test fixtures from full company facts saved outside the repo.

Download data.sec.gov/api/xbrl/companyfacts/CIK##########.json for each company into
Stock Project/data/raw/xbrl/<TICKER>_companyfacts.json, then run from app/:
    .venv/bin/python tests/fixtures/make_fixtures.py [TICKER ...]        (Windows: .venv\\Scripts\\python)

With no tickers it rebuilds all of them. Each fixture keeps only the tags xbrl.trim keeps, from 10-K and 10-Q
filings, for periods ending on or after SINCE: STRL needs 2022 for its restated quarter; the others need only the
last two years. LLY, ORCL and VST are the debt and liquidity pilots (downloaded Oct 14, 2026); their expected
values are in docs/pilot_evidence_*.md.
"""
import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(APP))
import xbrl  # noqa: E402

RAW = APP.parent / "data" / "raw" / "xbrl"
SINCE = {"AAPL": "2024-01-01", "STRL": "2022-01-01", "JPM": "2024-01-01",
         "LLY": "2024-01-01", "ORCL": "2024-01-01", "VST": "2024-01-01"}

for ticker in sys.argv[1:] or SINCE:
    full = json.loads((RAW / f"{ticker}_companyfacts.json").read_text(encoding="utf-8"))
    out = Path(__file__).parent / f"{ticker}_companyfacts.json"
    out.write_text(json.dumps(xbrl.trim(full, since=SINCE[ticker]), indent=0), encoding="utf-8")
    print(f"{ticker}: {out.stat().st_size:,} bytes")
