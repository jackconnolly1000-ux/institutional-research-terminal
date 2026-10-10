"""Stand-in network for rendering app.py offline: fake SEC EDGAR, Yahoo (yfinance) and Anthropic responses.

Nothing here reaches the internet and no Anthropic call is made, so a render costs nothing.
All text is placeholder, sized like real output. It is not real company data.
AAP is set up to fail (no 10-K or 10-Q), to show the failure state.
MOCK_DELAY=3 makes each fake Claude call take 3 seconds, so loading states stay on screen."""
import json
import os
import time
from types import SimpleNamespace

import numpy as np
import pandas as pd

DELAY = float(os.environ.get("MOCK_DELAY", "0"))  # seconds per Anthropic call, to make loading states visible

COMPANIES = {
    "AAPL": (320193, "Apple Inc.", "Electronic Computers"),
    "MSFT": (789019, "Microsoft Corp", "Services-Prepackaged Software"),
    "NVDA": (1045810, "Nvidia Corp", "Semiconductors & Related Devices"),
    "FAST": (815556, "Fastenal Co", "Wholesale-Durable Goods"),
    "STRL": (874238, "Sterling Infrastructure, Inc.", "Heavy Construction Other Than Bldg Const"),
    "AAP": (1158449, "Advance Auto Parts Inc", "Retail-Auto & Home Supply Stores"),
}
BY_CIK = {str(v[0]).zfill(10): k for k, v in COMPANIES.items()}

FILLER = ("The Company operates in a competitive environment and its results depend on demand for its products, "
          "supplier capacity, input costs, and the timing of customer orders across its segments. ")


class FakeResponse:
    def __init__(self, status=200, payload=None, content=b""):
        self.status_code, self._payload, self.content = status, payload, content

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code != 200:
            raise RuntimeError(self.status_code)


def _filing_html(form):
    risk = "ITEM 1A. RISK FACTORS " + FILLER * 60
    mda = ("ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS " if form == "10-K" else
           "ITEM 2. MANAGEMENT'S DISCUSSION AND ANALYSIS ") + FILLER * 60
    end = "ITEM 1B. UNRESOLVED STAFF COMMENTS ITEM 8. FINANCIAL STATEMENTS ITEM 3. ITEM 4. "
    return f"<html><body><p>{risk}</p><p>ITEM 1B.</p><p>{mda}</p><p>{end}</p></body></html>".encode()


def fake_get(url, headers=None, timeout=None, **kw):
    if url.endswith("company_tickers.json"):
        return FakeResponse(payload={str(i): {"cik_str": c[0], "ticker": t, "title": c[1]}
                                     for i, (t, c) in enumerate(COMPANIES.items())})
    if "/submissions/CIK" in url:
        cik = url.split("CIK")[1][:10]
        name, sic = COMPANIES[BY_CIK[cik]][1:]
        forms = ["8-K", "10-Q", "4", "4", "8-K", "8-K", "10-Q", "4", "8-K", "10-K"]
        if BY_CIK[cik] == "AAP":  # a failing ticker: no 10-K or 10-Q in the filing list
            forms = ["8-K", "20-F", "4", "4", "8-K", "8-K", "6-K", "4", "8-K", "20-F"]
        dates = ["2026-09-18", "2026-08-01", "2026-07-29", "2026-07-15", "2026-07-30", "2026-06-11",
                 "2026-05-01", "2026-04-20", "2026-04-30", "2025-10-31"]
        return FakeResponse(payload={"name": name, "sicDescription": sic, "filings": {"recent": {
            "form": forms, "filingDate": dates, "accessionNumber": [f"0000000000-26-{i:06d}" for i in range(len(forms))],
            "primaryDocument": [f"doc{i}.htm" for i in range(len(forms))]}}})
    if "/Archives/edgar/" in url:
        doc = url.rsplit("/", 1)[1]
        i = int(doc[3:-4])
        form = ["8-K", "10-Q", "4", "4", "8-K", "8-K", "10-Q", "4", "8-K", "10-K"][i]
        if form == "8-K":
            return FakeResponse(content=f"<html><body>Item 2.02 Results of Operations. {FILLER * 8}</body></html>".encode())
        return FakeResponse(content=_filing_html(form))
    return FakeResponse(status=404)


def _history(ticker, period="6mo", interval="1d", **kw):
    seed = sum(map(ord, ticker))
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("2021-10-11", "2026-10-09")
    start = {"6mo": "2026-04-10", "5y": "2021-10-11"}.get(period, "2026-04-10")
    days = days[days >= start]
    base = {"AAPL": 230, "FAST": 70, "STRL": 260}.get(ticker, 100)
    close = base * np.exp(np.cumsum(rng.normal(0.0004, 0.016, len(days))))
    open_ = close * np.exp(rng.normal(0, 0.006, len(days)))
    df = pd.DataFrame({"Open": open_, "High": np.maximum(open_, close) * 1.008,
                       "Low": np.minimum(open_, close) * 0.992, "Close": close,
                       "Volume": rng.lognormal(16.5, 0.3, len(days)), "Dividends": 0.0, "Stock Splits": 0.0},
                      index=days.tz_localize("America/New_York"))
    return df


class FakeTicker:
    def __init__(self, ticker):
        self.ticker = ticker
        self.info = {"marketCap": 3.41e12 if ticker == "AAPL" else 4.1e10, "currentPrice": 254.32 if ticker == "AAPL" else 71.18,
                     "forwardPE": 30.4, "revenueGrowth": 0.081, "grossMargins": 0.4865, "operatingMargins": 0.317,
                     "profitMargins": 0.243, "returnOnEquity": 1.38, "debtToEquity": 154.5, "freeCashflow": 9.6e10,
                     "ebitda": 1.39e11}

    def history(self, *a, **kw):
        return _history(self.ticker, *a, **kw)


def _ai_payload():
    bull = [{"target": t, "category": c, "impact": i,
             # n == 0 tests line breaks (blank lines, an indented line); n == 1 tests $, < and & escaping
             "description": ("First paragraph.\n\nSecond paragraph.\n\n    Indented third paragraph." if n == 0 else
                             "Placeholder thesis: spend of $5.2 billion in 2026 and $3 billion in 2027, R&D <10% of revenue & rising."
                             if n == 1 else "Placeholder thesis sentence about why this initiative could lift revenue or margins over the next few quarters, with the timing and the segment it affects."),
             "quote": ("Placeholder filing excerpt, first paragraph.\n\nPlaceholder filing excerpt, second paragraph." if n == 0 else
                       "Placeholder filing excerpt of about the length the model usually returns, quoted from the management discussion section of the filing.")}
            for n, (t, c, i) in enumerate
([("Data center capacity build-out", "CAPEX", "HIGH"), ("Services pricing actions", "PRICING", "HIGH"),
                            ("Supplier diversification", "SUPPLY CHAIN", "MEDIUM"), ("Share repurchase program", "CAPITAL RETURN", "MEDIUM"),
                            ("New product cycle", "PRODUCT", "MEDIUM")])]
    bear = [{"target": t, "category": c, "impact": i, "trend": tr,
             "description": "Placeholder risk sentence describing the exposure, what would trigger it, and how the filing says it could affect results or cash flow.",
             "quote": "Placeholder risk-factor excerpt of typical length, taken from Item 1A of the filing that the model was given."}
            for t, c, i, tr in [("Single-source component suppliers", "SUPPLY CHAIN", "HIGH", "ESCALATED"),
                                ("Tariff and trade policy changes", "REGULATORY", "HIGH", "NEW"),
                                ("Foreign currency exposure", "FINANCIAL", "MEDIUM", "STABLE"),
                                ("Customer concentration", "COMMERCIAL", "MEDIUM", "STABLE"),
                                ("Litigation and antitrust actions", "LEGAL", "HIGH", "ESCALATED"),
                                ("Inventory and working capital timing", "OPERATIONAL", "MEDIUM", "NEW")]]
    eight_k = [{"event_date": d, "category": c, "takeaway": "Placeholder takeaway summarizing what the 8-K disclosed and why it could matter to the thesis.",
                "quote": "Placeholder 8-K excerpt."}
               for d, c in [("2026-09-18", "LEADERSHIP"), ("2026-07-30", "FINANCIAL"), ("2026-06-11", "M&A / CONTRACT"), ("2026-04-30", "FINANCIAL")]]
    questions = ["Placeholder meeting question about how management is pacing capital spending against demand visibility in the next two quarters?",
                 "Placeholder meeting question about which suppliers remain single-source and what the qualification timeline is for alternates?",
                 "Placeholder meeting question about how pricing actions are expected to affect unit volumes and gross margin?"]
    return {"bull_items": bull, "bear_items": bear, "eight_k_insights": eight_k, "strategic_questions": questions}


class FakeMessages:
    def create(self, **kw):
        if DELAY:
            time.sleep(DELAY)
        return SimpleNamespace(content=[SimpleNamespace(type="tool_use", input=_ai_payload())])


class FakeAnthropic:
    def __init__(self, *a, **kw):
        self.messages = FakeMessages()


def install():
    import anthropic
    import requests
    import yfinance
    requests.get = fake_get
    yfinance.Ticker = FakeTicker
    anthropic.Anthropic = FakeAnthropic
