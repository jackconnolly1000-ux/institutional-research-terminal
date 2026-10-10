"""Stand-in network for rendering app.py offline: fake SEC EDGAR, Yahoo (yfinance) and Anthropic responses.

Nothing here reaches the internet and no Anthropic call is made, so a render costs nothing.
All text is placeholder, sized and structured like real filings (table of contents, cross-references,
real section headings). It is not real company data.

Scenarios (environment variables, comma-separated tickers or components):
  MOCK_DELAY=3              each fake Claude call takes 3 seconds, so loading states stay on screen
  MOCK_CUTOFF=STRL          Claude's answer for STRL stops at max_tokens after the catalysts
  MOCK_FAIL_ONCE=yahoo,8k,prior   the first Yahoo call / first 8-K download / first prior 10-K download
                            fails, later ones succeed (shows that failures aren't cached)
  MOCK_ONE_10K=FAST         FAST has only one 10-K, so there is no annual comparison
  MOCK_NO_8K=STRL           STRL filed no 8-K in the last 180 days
  MOCK_EMPTY_EVENTS=AAPL    a complete answer that genuinely reports no 8-K events
AAP has no 10-K or 10-Q (foreign-issuer style), to show a whole-ticker failure."""
import json
import os
import re
import time
from types import SimpleNamespace

import numpy as np
import pandas as pd

DELAY = float(os.environ.get("MOCK_DELAY", "0"))
_env = lambda name: {x.strip().upper() for x in os.environ.get(name, "").split(",") if x.strip()}
CUTOFF, FAIL_ONCE, ONE_10K, NO_8K, EMPTY_EVENTS = (_env(n) for n in
    ("MOCK_CUTOFF", "MOCK_FAIL_ONCE", "MOCK_ONE_10K", "MOCK_NO_8K", "MOCK_EMPTY_EVENTS"))
_failures = {}

COMPANIES = {
    "AAPL": (320193, "Apple Inc.", "Electronic Computers"),
    "MSFT": (789019, "Microsoft Corp", "Services-Prepackaged Software"),
    "NVDA": (1045810, "Nvidia Corp", "Semiconductors & Related Devices"),
    "FAST": (815556, "Fastenal Co", "Wholesale-Durable Goods"),
    "STRL": (874238, "Sterling Infrastructure, Inc.", "Heavy Construction Other Than Bldg Const"),
    "AAP": (1158449, "Advance Auto Parts Inc", "Retail-Auto & Home Supply Stores"),
}
BY_CIK = {str(v[0]): k for k, v in COMPANIES.items()}

SUPPLY = "The Company depends on a limited number of suppliers for certain components, and a disruption could reduce net sales. "
DEMAND = "Demand for the Company's products can change quickly with economic conditions and customer budgets. "
MDA_LINE = "Net sales increased 8% to $5.2 billion during the quarter, driven by higher volumes in the services segment. "
FILLER = "The Company operates in a competitive environment and its results depend on the timing of customer orders. "
TOC = ("TABLE OF CONTENTS Page PART I Item 1. Business 1 Item 1A. Risk Factors 5 Item 1B. Unresolved Staff Comments 17 "
       "Item 2. Properties 18 PART II Item 7. Management's Discussion and Analysis of Financial Condition and Results "
       "of Operations 20 Item 7A. Quantitative and Qualitative Disclosures About Market Risk 30 Item 8. Financial Statements 31 ")


class FakeResponse:
    def __init__(self, status=200, payload=None, content=b""):
        self.status_code, self._payload = status, payload
        self.content = content if payload is None else json.dumps(payload).encode()

    def json(self):
        return self._payload


def _filings(ticker):
    """(form, filed, reportDate, items), newest first."""
    if ticker == "AAP":
        return [("8-K", "2026-09-18", "2026-09-17", "5.02"), ("20-F", "2026-03-01", "2025-12-31", ""), ("6-K", "2026-05-01", "", "")]
    rows = [("8-K", "2026-09-18", "2026-09-17", "5.02,9.01"), ("4", "2026-08-20", "2026-08-18", ""),
            ("10-Q", "2026-08-01", "2026-06-30", ""), ("8-K", "2026-07-30", "2026-07-30", "2.02,9.01"),
            ("4", "2026-07-15", "2026-07-13", ""), ("8-K", "2026-06-11", "2026-06-10", "1.01"),
            ("10-Q", "2026-05-01", "2026-03-31", ""), ("10-K", "2026-02-26", "2025-12-31", ""),
            ("8-K", "2026-01-29", "2026-01-29", "2.02"), ("10-Q", "2025-11-04", "2025-09-30", ""),
            ("10-K", "2025-02-27", "2024-12-31", "")]
    if ticker in ONE_10K:
        rows = rows[:-1]
    if ticker in NO_8K:
        rows = [r for r in rows if r[0] != "8-K"]
    return rows


def _doc(ticker, form, i):
    if form == "10-K":
        return (f"<html><body><p>{TOC}</p><p>Forward-looking statements are discussed in Part I, Item 1A of this "
                f"Form 10-K under the heading “Risk Factors.”</p><p>Item 1. Business {FILLER * 20}</p>"
                f"<p>Item 1A. Risk Factors {SUPPLY}{DEMAND}{FILLER * 60}</p><p>For cybersecurity, see Item 1A of this Form 10-K.</p>"
                f"<p>Item 1B. Unresolved Staff Comments None.</p><p>Item 2. Properties We lease offices.</p>"
                f"<p>Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations "
                f"{MDA_LINE}{FILLER * 60}</p><p>Item 7A. Quantitative and Qualitative Disclosures About Market Risk None.</p>"
                f"<p>Item 8. Financial Statements</p></body></html>").encode()
    if form == "10-Q":
        risk = (f"Except as set forth below, there have been no material changes to the risk factors in the 2025 Form 10-K. "
                f"{DEMAND}{FILLER * 20}" if ticker == "AAPL" and i == 2 else
                "There have been no material changes from the risk factors described in Part I, Item 1A of our most recent annual report on Form 10-K.")
        return (f"<html><body><p>PART I Item 2. Management's Discussion and Analysis 13 Item 3. Market Risk 20 PART II "
                f"Item 1A. Risk Factors 21 Item 2. Unregistered Sales 21</p><p>Item 2. Management's Discussion and Analysis of "
                f"Financial Condition and Results of Operations {MDA_LINE}{FILLER * 40}</p><p>Item 3. Quantitative and "
                f"Qualitative Disclosures About Market Risk None.</p><p>PART II OTHER INFORMATION</p><p>Item 1A. Risk Factors "
                f"{risk}</p><p>Item 2. Unregistered Sales of Equity Securities None.</p></body></html>").encode()
    return (f"<html><body>Item 5.02 Departure of Directors or Certain Officers. On September 18, 2026 the Board "
            f"appointed a new Chief Financial Officer, effective October 1, 2026. {FILLER * 6}</body></html>").encode()


def _fail_once(component, attempts=1):
    """Fail the first `attempts` calls for a component. SEC downloads use 3, matching app.sec_get's
    retries, so the failure lasts for one whole run and then recovers."""
    if component in FAIL_ONCE and _failures.get(component, 0) < attempts:
        _failures[component] = _failures.get(component, 0) + 1
        return True
    return False


def fake_get(url, headers=None, timeout=None, **kw):
    if url.endswith("company_tickers.json"):
        return FakeResponse(payload={str(i): {"cik_str": c[0], "ticker": t, "title": c[1]}
                                     for i, (t, c) in enumerate(COMPANIES.items())})
    if "/submissions/CIK" in url:
        cik = str(int(url.split("CIK")[1][:10]))
        ticker = BY_CIK[cik]
        rows = _filings(ticker)
        return FakeResponse(payload={"name": COMPANIES[ticker][1], "sicDescription": COMPANIES[ticker][2],
                                     "filings": {"recent": {
                                         "form": [r[0] for r in rows], "filingDate": [r[1] for r in rows],
                                         "reportDate": [r[2] for r in rows], "items": [r[3] for r in rows],
                                         "accessionNumber": [f"0000{cik:0>6}-26-{i:06d}" for i in range(len(rows))],
                                         "primaryDocument": [f"{r[0].replace('-', '').lower()}_{i}.htm" for i, r in enumerate(rows)]}}})
    if "/Archives/edgar/data/" in url:
        cik, doc = url.split("/")[-3], url.rsplit("/", 1)[1]
        ticker = BY_CIK[cik]
        form_slug, i = re.match(r"(\w+?)_(\d+)\.htm", doc).groups()
        form = {"10k": "10-K", "10q": "10-Q"}.get(form_slug, "8-K")
        if form == "8-K" and _fail_once("8K", 3):
            return FakeResponse(status=503)
        if form == "10-K" and int(i) == len(_filings(ticker)) - 1 and _fail_once("PRIOR", 3):
            return FakeResponse(status=503)
        return FakeResponse(content=_doc(ticker, form, int(i)))
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
    return pd.DataFrame({"Open": open_, "High": np.maximum(open_, close) * 1.008,
                         "Low": np.minimum(open_, close) * 0.992, "Close": close,
                         "Volume": rng.lognormal(16.5, 0.3, len(days)), "Dividends": 0.0, "Stock Splits": 0.0},
                        index=days.tz_localize("America/New_York"))


class FakeTicker:
    def __init__(self, ticker):
        self.ticker = ticker

    @property
    def info(self):
        if _fail_once("YAHOO"):
            raise ConnectionError("simulated Yahoo outage")
        return {"marketCap": 3.41e12 if self.ticker == "AAPL" else 4.1e10,
                "currentPrice": 254.32 if self.ticker == "AAPL" else 71.18, "regularMarketTime": 1791576000,
                "forwardPE": 30.4, "revenueGrowth": 0.081, "grossMargins": 0.4865, "operatingMargins": 0.317,
                "profitMargins": 0.243, "returnOnEquity": 1.38, "freeCashflow": 9.6e10, "ebitda": 1.39e11}

    def history(self, *a, **kw):
        return _history(self.ticker, *a, **kw)


def _finding(headline, source_id, quote, impact="MEDIUM", category="DEMAND", trend=None, summary=None):
    f = {"headline": headline, "source_id": source_id, "quote": quote, "impact": impact, "category": category,
         "summary": summary or "Placeholder summary of what the filing states, with the figure and period it gives.",
         "implication": "Placeholder potential implication for revenue or margins, stated with appropriate hedging.",
         "detail": "Placeholder supporting explanation, about two sentences long, drawn from the cited source.",
         "impact_basis": "Placeholder basis: the effect is stated for one segment and its timing is not given."}
    if trend:
        f["trend"] = trend
    return f


def _ai_payload(ticker, ids):
    k8 = [i for i in ids if i.startswith("K8_")]
    qu = [i for i in ids if i.startswith("QU")]
    catalysts = [
        _finding("Quarterly net sales rose 8% on services volume", "MDA", MDA_LINE.strip(), "HIGH", "DEMAND",
                 summary="First paragraph.\n\nSecond paragraph.\n\n    Indented third paragraph."),
        _finding("Services pricing changes announced", "MDA", "Net sales increased 8% to $5.2 billion during the quarter",
                 "MEDIUM", "PRICING_MARGINS",
                 summary="Placeholder: spend of $5.2 billion in 2026 and $3 billion in 2027, R&D <10% of revenue & rising."),
        _finding("Paraphrased quote should not match", "MDA", "Net sales also increased 8% to $5.2 billion during the quarter",
                 "LOW", "OTHER"),
    ]
    risks = [_finding("Supplier concentration remains a stated risk", "R_CUR", SUPPLY.strip(), "HIGH", "COSTS_SUPPLY_CHAIN", "UNCHANGED"),
             _finding("Demand sensitivity to economic conditions", "R_CUR", DEMAND.strip(), "MEDIUM", "DEMAND", "ESCALATED"),
             _finding("Not enough information to rate", "R_CUR", "its results depend on the timing of customer orders",
                      "NOT_ASSESSED", "OPERATIONS", "NEW")]
    if qu:
        risks.append(_finding("Quarterly update repeats demand risk", qu[-1], DEMAND.strip(), "LOW", "DEMAND", "NEW"))
    events = [] if ticker in EMPTY_EVENTS else [
        {"source_id": k8[0], "category": "LEADERSHIP", "headline": "New Chief Financial Officer appointed",
         "summary": "The Board appointed a new CFO effective October 1, 2026.",
         "quote": "the Board appointed a new Chief Financial Officer, effective October 1, 2026"}] if k8 else []
    questions = [{"question": "Placeholder question about how supplier concentration is being reduced?", "source_id": "R_CUR"},
                 {"question": "Placeholder question about what drove services volume this quarter?", "source_id": "MDA"},
                 {"question": "Placeholder question about the CFO transition timeline?", "source_id": k8[0] if k8 else "MDA"}]
    return {"catalysts": catalysts, "risks": risks, "events": events, "questions": questions}


def _source_ids(tools):
    schema = tools[0]["input_schema"]["properties"]["catalysts"]["items"]["properties"]["source_id"]
    return schema["enum"]


class FakeMessages:
    def create(self, **kw):
        if DELAY:
            time.sleep(DELAY)
        ticker = re.search(r"\(([A-Z.]+)\)", kw["messages"][0]["content"]).group(1)
        payload = _ai_payload(ticker, _source_ids(kw["tools"]))
        stop = "tool_use"
        if ticker in CUTOFF:
            payload, stop = {"catalysts": payload["catalysts"][:2]}, "max_tokens"
        return SimpleNamespace(content=[SimpleNamespace(type="tool_use", input=payload)], stop_reason=stop,
                               usage=SimpleNamespace(input_tokens=len(kw["messages"][0]["content"]) // 4, output_tokens=3100))

    def count_tokens(self, **kw):
        return SimpleNamespace(input_tokens=(len(kw["messages"][0]["content"]) + len(json.dumps(kw["tools"]))) // 4)


class FakeAnthropic:
    def __init__(self, *a, **kw):
        self.messages = FakeMessages()

    def with_options(self, **kw):  # app.py sets timeout and max_retries per call
        return self


def install():
    import anthropic
    import requests
    import yfinance
    requests.get = fake_get
    yfinance.Ticker = FakeTicker
    anthropic.Anthropic = FakeAnthropic
