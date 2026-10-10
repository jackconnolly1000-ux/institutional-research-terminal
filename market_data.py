"""Market data from Yahoo Finance (via yfinance) as numbers with unit, period, source and retrieval time.

No Streamlit here. Values stay numeric; ui.py formats them for display.
Yahoo does not document the period behind most Ticker.info fields (margins, free cash flow,
forward P/E), so their period is None and the page says "Period unavailable" rather than guessing TTM.
"""
from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo

SOURCE = "Yahoo Finance via yfinance (Ticker.info)"
ET = ZoneInfo("America/New_York")

# key: (label, Ticker.info field, unit). Units: USD, fraction (0.4865 = 48.65%), multiple (30.4 = 30.4x)
METRICS = {
    "price": ("Price", "currentPrice", "USD"),
    "market_cap": ("Market cap", "marketCap", "USD"),
    "forward_pe": ("Forward P/E", "forwardPE", "multiple"),
    "gross_margin": ("Gross margin", "grossMargins", "fraction"),
    "operating_margin": ("Operating margin", "operatingMargins", "fraction"),
    "profit_margin": ("Net margin", "profitMargins", "fraction"),
    "revenue_growth": ("Revenue growth", "revenueGrowth", "fraction"),
    "roe": ("Return on equity", "returnOnEquity", "fraction"),
    "free_cash_flow": ("Free cash flow", "freeCashflow", "USD"),
    "ebitda": ("EBITDA", "ebitda", "USD"),
}


class MarketDataError(Exception):
    """Yahoo returned nothing usable. Raised (not returned) so st.cache_data never stores it."""


def _number(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def fetch_financials(ticker: str, ticker_factory, now: datetime | None = None) -> dict:
    """ticker_factory is yfinance.Ticker in the app (a fake in tests)."""
    now = now or datetime.now(ET)
    try:
        info = ticker_factory(ticker).info or {}
    except Exception as e:
        raise MarketDataError(f"Yahoo Finance request failed ({type(e).__name__})") from e
    if not isinstance(info, dict) or (_number(info.get("currentPrice")) is None and _number(info.get("marketCap")) is None
                                      and _number(info.get("regularMarketPrice")) is None):
        raise MarketDataError("Yahoo Finance returned no price or market cap")

    quote_time = _number(info.get("regularMarketTime"))
    quote_period = (f"Quote as of {datetime.fromtimestamp(quote_time, ET):%b %d, %Y %I:%M %p} ET" if quote_time else None)
    metrics = {}
    for key, (label, fld, unit) in METRICS.items():
        value = _number(info.get(fld))
        if key == "price" and value is None:
            fld, value = "regularMarketPrice", _number(info.get("regularMarketPrice"))
        metrics[key] = {"label": label, "value": value, "unit": unit, "field": fld,
                        "period": quote_period if key == "price" else None}
    return {"source": SOURCE, "retrieved_at": now.isoformat(timespec="seconds"), "metrics": metrics}
