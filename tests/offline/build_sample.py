"""Build app/samples/ (the saved AAPL + STRL sample) from one real run, so every part is frozen at one date.

Inputs, all from the Oct 10, 2026 run (1:49 and 1:50 PM ET):
- profiles written by the replay harness with SAVE_SAMPLE_DIR (live SEC filings, the saved Claude answers)
- the saved raw answers in ~/Stock Project/data/raw/ai_responses/ (for the real token counts of that run)
- that run's Excel export (for the Yahoo market data as retrieved then)
Price history is pulled once from Yahoo (free) and cut at the Oct 9 close, the last bar that run had.

Usage (from app/):
    .venv/bin/python tests/offline/build_sample.py <profiles_dir> <export.xlsx>
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import market_data  # noqa: E402

TICKERS = ["AAPL", "STRL"]
SAVED = {"AAPL": "AAPL_20261010_134944.json", "STRL": "STRL_20261010_135049.json"}
RUN_AT = "2026-10-10T13:49:44-04:00"
PRICES_THROUGH = "2026-10-09"
LABEL = "Saved sample. Analysis run Oct 10, 2026. Price history through the Oct 9 close, retrieved Oct 11."
OUT = Path(__file__).resolve().parents[2] / "samples"
RAW = Path(__file__).resolve().parents[3] / "data" / "raw" / "ai_responses"


def market_from_export(ws, ticker: str) -> dict:
    """The run's Yahoo values, in market_data.fetch_financials's shape."""
    by_label = {label: key for key, (label, _, _) in market_data.METRICS.items()}
    metrics, retrieved = {}, None
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] != ticker:
            continue
        _, label, value, unit, period, source, retrieved = row
        key = by_label[label]
        if period and period.startswith("Quote as of"):       # rewrite in today's format: "Oct 9, 2026, 4:00 PM ET"
            q = datetime.strptime(period, "Quote as of %b %d, %Y %I:%M %p ET")
            period = f"Quote as of {q:%b} {q.day}, {q:%Y}, {q.strftime('%I').lstrip('0')}:{q:%M %p} ET"
        else:
            period = None
        metrics[key] = {"label": label, "value": value, "unit": unit, "field": source.rsplit(": ", 1)[1], "period": period}
    return {"status": "ok", "source": market_data.SOURCE, "retrieved_at": retrieved, "metrics": metrics}


def prices(ticker: str):
    hist = yf.Ticker(ticker).history(period="5y", interval="1d", auto_adjust=True)[["Open", "High", "Low", "Close", "Volume"]]
    hist.index = hist.index.tz_localize(None).normalize()
    return hist.loc[:PRICES_THROUGH].round(4)


def main(profiles_dir: str, export_path: str) -> None:
    OUT.mkdir(exist_ok=True)
    ws = openpyxl.load_workbook(export_path)["Market data"]
    for t in TICKERS:
        p = json.loads((Path(profiles_dir) / f"{t}.json").read_text())
        saved = json.loads((RAW / SAVED[t]).read_text())
        p["financials"] = market_from_export(ws, t)
        # The replay counted tokens offline; the sample shows what the real Oct 10 request measured and allowed
        p["analysis"]["usage"] = saved["raw"]["usage"]
        p["analysis"]["budget"] = {"input_tokens": saved["request"]["input_tokens"], "limit": saved["request"]["budget"],
                                   "output_reserve": saved["max_tokens"], "count": "measured"}
        p["analysis"]["from_cache"] = False
        (OUT / f"{t}.json").write_text(json.dumps(p, indent=1, default=str))
        hist = prices(t)
        hist.to_csv(OUT / f"{t}_prices.csv")
        tile = p["financials"]["metrics"]["price"]["value"]
        print(f"{t}: price tile {tile:.2f} (Yahoo, retrieved {p['financials']['retrieved_at']}) | "
              f"chart close {hist.index[-1]:%Y-%m-%d} {hist['Close'].iloc[-1]:.2f} | "
              f"{'equal' if round(tile, 2) == round(hist['Close'].iloc[-1], 2) else 'DIFFERENT'}")
    (OUT / "manifest.json").write_text(json.dumps({
        "tickers": TICKERS, "run_at": RUN_AT, "prices_through": PRICES_THROUGH, "prices_retrieved": "2026-10-11",
        "label": LABEL}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
