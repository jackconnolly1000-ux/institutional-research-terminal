import hashlib
import hmac
import json
import os
import platform
import requests
import time
import traceback
from importlib import reload
import openpyxl
import yfinance as yf
import pandas as pd
from openpyxl.styles import Font, PatternFill
from io import BytesIO
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic, APIError
from zoneinfo import ZoneInfo
import streamlit as st

import analysis
import budget
import filing_review
import reviewed_financing
import liquidity_simulation
import scenario_export
import simulation_view
import core_charts
import company_review
import funding_conclusions
import oracle_financing
import oracle_liquidity
import oracle_interest
import oracle_interest_view
import oracle_liquidity_view
import lly_liquidity
import lly_financing
import lly_interest
import lly_interest_view
import lly_liquidity_view
import oracle_principal
import oracle_principal_view
import oracle_repayment
import oracle_revolver
import vistra_liquidity
import vistra_interest
import vistra_interest_view
import vistra_liquidity_view
import market_data
import sec_data
import theme
import ui
import xbrl
from charts import CHART_CONFIG, build_price_chart

# A Cloud worker can retain imported views across entry-point reruns after deployment.
# These modules have no network calls or state to preserve; load the current view and review registry.
reload(theme)   # ui reads its colors from theme; reloading ui alone kept old tokens (Oct 17 outage)
reload(ui)
reload(oracle_financing)
reload(oracle_liquidity)
reload(oracle_interest)
reload(oracle_interest_view)
reload(oracle_revolver)
reload(oracle_principal)
reload(oracle_principal_view)
reload(oracle_repayment)
reload(oracle_liquidity_view)
reload(reviewed_financing)
reload(vistra_liquidity)
reload(vistra_interest)
reload(vistra_interest_view)
reload(vistra_liquidity_view)
reload(lly_liquidity)
reload(lly_financing)
reload(lly_interest)
reload(lly_interest_view)
reload(lly_liquidity_view)
reload(liquidity_simulation)
reload(scenario_export)
reload(simulation_view)
reload(core_charts)   # imported lazily by company_review, so a reload of that module alone keeps old chart HTML
reload(company_review)
reload(funding_conclusions)

ET = ZoneInfo("America/New_York")

# --- STREAMLIT PAGE CONFIG + STYLING (colors live in theme.py, CSS in ui.py) ---
st.set_page_config(
    page_title="Debt & Liquidity Research Terminal",
    layout="wide",
    initial_sidebar_state="collapsed"
)
ui.inject_css()


@st.cache_resource(show_spinner=False)
def log_versions() -> None:
    """Print the versions actually running, once per server process, to the server log (not the page). On Oct 11
    the live site ran Streamlit 1.65.0 while requirements.txt pinned 1.32.0; this line makes that checkable in the
    Cloud log after every deploy."""
    print(f"[versions] Python {platform.python_version()}, streamlit {st.__version__}, pandas {pd.__version__}", flush=True)


log_versions()

# --- API KEY AND SEC CONTACT (from Streamlit Secrets) ---
# Read only by general filing research. The saved debt and liquidity reviews are the default page and need
# neither, so a deployment without these secrets still serves them.
def secret(name: str) -> str | None:
    try:
        return st.secrets.get(name)
    except Exception:   # no secrets file at all
        return None

def sec_contact() -> str | None:
    """SEC EDGAR asks every automated request to name a real contact (its fair-access policy).
    The environment fallback exists for the offline test harness, which has no secrets file."""
    return secret("SEC_CONTACT_EMAIL") or os.environ.get("SEC_CONTACT_EMAIL")

@st.cache_resource(show_spinner=False)
def _anthropic_client(clean_key: str) -> Anthropic:
    return Anthropic(api_key=clean_key, timeout=60.0)

def anthropic_client() -> Anthropic:
    """Built on first use by a live analysis, never on page load. Raises KeyError when the key isn't set."""
    raw_key = secret("ANTHROPIC_API_KEY")
    if not raw_key:
        raise KeyError("ANTHROPIC_API_KEY")
    return _anthropic_client(str(raw_key).strip().replace("\n", "").replace(" ", "").replace("\r", ""))

def live_setup_problems() -> list[str]:
    """What a live run would be missing. An empty list means Run analysis can work."""
    return [f"{name} is not set in Streamlit Secrets" for name, ok in
            (("ANTHROPIC_API_KEY", secret("ANTHROPIC_API_KEY")), ("SEC_CONTACT_EMAIL", sec_contact())) if not ok]

# --- BACKEND ---
# Cached functions RAISE on failure instead of returning None or a fallback:
# st.cache_data stores return values, not exceptions, so a failure is retried on the next run
# instead of being served from cache. Pure logic lives in sec_data.py, analysis.py and market_data.py.
class TickerFailure(Exception):
    """A per-ticker failure whose message is safe to show the user."""

class TickerSkipped(Exception):
    """A ticker not analyzed because of the spending guard: kind is "daily" (this app's cap) or "monthly"
    (the Anthropic account's limit). Shown as skipped, not failed: nothing went wrong with the data."""
    def __init__(self, kind: str):
        super().__init__(kind)
        self.kind = kind

FALLBACK_DIRECTORY = pd.DataFrame([
    {"ticker": "AAPL", "name": "Apple Inc.", "cik": "320193"},
    {"ticker": "MSFT", "name": "Microsoft Corp.", "cik": "789019"},
    {"ticker": "NVDA", "name": "Nvidia Corp.", "cik": "1045810"},
    {"ticker": "FAST", "name": "Fastenal Co.", "cik": "815556"},
    {"ticker": "STRL", "name": "Sterling Infrastructure Inc.", "cik": "874238"},
    {"ticker": "AAP", "name": "Advance Auto Parts Inc.", "cik": "1158449"}
], columns=["ticker", "name", "cik"])

def sec_get(url: str, retries: int = 3) -> bytes:
    """GET from SEC EDGAR with retries. Raises if every attempt fails."""
    last = "no response"
    headers = {"User-Agent": f"SEC Filing Research Terminal {sec_contact()}"}
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                return resp.content
            last = f"HTTP {resp.status_code}"
            time.sleep(1.5 * (attempt + 1) if resp.status_code == 429 else 0.5)
        except requests.RequestException as e:
            last = type(e).__name__
            time.sleep(1.0)
    raise RuntimeError(f"SEC EDGAR request failed ({last})")

@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_sec_directory() -> pd.DataFrame:
    rows = [{"ticker": v['ticker'].upper(), "name": v['title'].title(), "cik": str(v['cik_str'])}
            for v in json.loads(sec_get("https://www.sec.gov/files/company_tickers.json", retries=1)).values()]
    return pd.DataFrame(rows).drop_duplicates("ticker")

def load_sec_directory() -> tuple[pd.DataFrame, bool]:
    """Returns (directory, used_fallback). Not cached itself, so the fallback is never cached.
    Without a contact email no SEC request is allowed, so the short list is used."""
    if not sec_contact():
        return FALLBACK_DIRECTORY, True
    try:
        return _fetch_sec_directory(), False
    except Exception:
        return FALLBACK_DIRECTORY, True

@st.cache_data(ttl=3600, show_spinner=False)
def cached_submissions(cik: str) -> dict:
    return json.loads(sec_get(f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"))

@st.cache_data(ttl=86400, show_spinner=False)
def cached_json(url: str) -> dict:
    """EDGAR's older filing pages; a page of past filings doesn't change."""
    return json.loads(sec_get(url))

@st.cache_data(ttl=86400, show_spinner=False)
def cached_filing_text(url: str) -> str:
    """A filed document never changes, so a successful download is kept for a day.
    A failed one raises and is retried on the next run."""
    return sec_data.html_to_text(sec_get(url))

def gather_evidence(ticker: str, cik: str) -> dict:
    """Pick the filings, download them (each separately, so one failure doesn't sink the rest),
    and extract their sections. Not cached itself: it reassembles from cached pieces every run."""
    try:
        subs = cached_submissions(cik)
    except Exception as e:
        raise TickerFailure(f"SEC EDGAR didn't return the filing history ({e}), try again") from e
    try:
        selection = sec_data.select_with_older_pages(subs, cik, datetime.now(ET).date(), cached_json)
    except Exception as e:
        print(f"[sec] {ticker}: older filing pages failed: {e}", flush=True)
        selection = sec_data.select_filings(sec_data.filings_from_submissions(subs, cik), datetime.now(ET).date())
        selection.notes.append(f"EDGAR's older filing pages couldn't be read ({e}), so the prior 10-K may be missing.")
    if selection.mdna_source is None:
        raise TickerFailure("no 10-K or 10-Q in recent SEC filings (foreign issuers file 20-F instead)")
    wanted = [f for f in [selection.annual_current, selection.annual_prior, selection.mdna_source,
                          *selection.quarterly_updates, *selection.eight_ks] if f]
    texts = {}
    for f in {f.accession: f for f in wanted}.values():
        try:
            texts[f.accession] = cached_filing_text(f.url)
        except Exception as e:
            print(f"[sec] {ticker}: {f.label} failed: {e}", flush=True)
            texts[f.accession] = e
    sources = analysis.build_sources(selection, texts)
    if not any(s.sendable for s in sources):
        raise TickerFailure("no usable text could be extracted from its SEC filings")
    inventory = sec_data.filing_review_inventory(
        subs, cik, selection.mdna_source.period, datetime.now(ET).date().isoformat(), cached_json)
    inventory = reviewed_financing.annotate(inventory, ticker)
    return {"company_name": subs.get("name", ticker).title(), "industry": subs.get("sicDescription", "Public issuer").title(),
            "selection": selection, "sources": sources,
            "filing_review": inventory,
            "event_markers": [(f.filed, f.form) for f in wanted]}

@st.cache_data(ttl=900, show_spinner=False)
def cached_financials(ticker: str) -> dict:
    return market_data.fetch_financials(ticker, yf.Ticker)

def load_financials(ticker: str) -> dict:
    try:
        return {"status": "ok", **cached_financials(ticker)}
    except market_data.MarketDataError as e:
        return {"status": "failed", "reason": str(e)}

@st.cache_data(ttl=86400, show_spinner=False)
def cached_companyfacts(cik: str) -> dict:
    """SEC XBRL company facts, trimmed to the tags xbrl.py reads (a full file is 3 to 8 MB). They change only
    when the company files, so a day is fresh enough. sec_get raises on failure, so a failure is never cached."""
    return {"retrieved_at": datetime.now(ET).isoformat(timespec="seconds"),
            **xbrl.trim(json.loads(sec_get(xbrl.companyfacts_url(cik))))}

def load_sec_metrics(cik: str) -> dict:
    try:
        facts = cached_companyfacts(cik)
        return {"status": "ok", "retrieved_at": facts["retrieved_at"], **xbrl.ttm_metrics(facts)}
    except Exception as e:
        print(f"[xbrl] CIK {cik}: {e}", flush=True)
        return {"status": "failed", "reason": f"SEC company facts couldn't be read: {e}"}

@st.cache_resource(show_spinner=False)
def analysis_store() -> dict:
    """Complete Claude answers, keyed by a hash of the exact request. Written only when
    analysis.is_cacheable() says every section is usable, so a cut-off or malformed answer is
    never served again as if it were complete."""
    return {}

ANALYSIS_TTL = 3600
ANALYSIS_TIMEOUT = 300  # seconds; an answer of up to 12,000 tokens can take minutes

@st.cache_resource(show_spinner=False)
def spend_ledger() -> budget.Ledger:
    """One daily spend ledger shared by every visitor (st.cache_resource is per server process, not per
    session). It lives in memory, so it resets when the app restarts or wakes from sleep; the Anthropic
    account's monthly limit is the hard stop behind it."""
    return budget.Ledger(budget.DAILY_CAP_USD)

def is_owner() -> bool:
    return bool(st.session_state.get("owner"))
# Local diagnostics only: set SAVE_AI_RESPONSES_DIR to keep each raw Claude answer and the profile built from it
SAVE_DIR = os.environ.get("SAVE_AI_RESPONSES_DIR")

def count_request_tokens(client: Anthropic, prompt: str, tool: dict, method: dict) -> int:
    """Token count for the whole request from Anthropic's free counting endpoint.
    Falls back to a conservative estimate (3 characters per token) if that call fails."""
    try:
        return client.messages.count_tokens(model=analysis.MODEL, tools=[tool],
                                            tool_choice={"type": "tool", "name": analysis.TOOL_NAME},
                                            messages=[{"role": "user", "content": prompt}]).input_tokens
    except APIError as e:
        method["method"] = f"estimated ({type(e).__name__} from the counting endpoint)"
        return (len(prompt) + len(json.dumps(tool))) // 3

def run_analysis(ticker: str, evidence: dict) -> dict:
    sources = evidence["sources"]
    method = {"method": "measured"}
    client = anthropic_client()
    try:
        req = analysis.fit_to_budget(ticker, evidence["company_name"], sources,
                                     lambda p, t: count_request_tokens(client, p, t, method))
    except ValueError as e:
        return analysis.failed_result(sources, str(e))
    key = hashlib.sha256(analysis.request_fingerprint(req["prompt"], req["tool"]).encode()).hexdigest()
    store = analysis_store()
    hit = store.get(key)
    from_cache = bool(hit and time.time() - hit["at"] < ANALYSIS_TTL)
    if from_cache:
        raw = hit["raw"]   # costs nothing, so the ledger isn't touched
    else:
        # Reserve the worst case (measured input + the full output allowance) before calling
        worst = budget.cost_usd(analysis.MODEL, req["input_tokens"], analysis.MAX_OUTPUT_TOKENS)
        ledger = spend_ledger()
        hold = ledger.reserve(worst, enforce=not is_owner())
        if hold is None:
            raise TickerSkipped("daily")
        try:
            # One attempt only: an SDK retry after a timeout could bill the same request twice.
            response = client.with_options(timeout=ANALYSIS_TIMEOUT, max_retries=0).messages.create(
                model=analysis.MODEL, max_tokens=analysis.MAX_OUTPUT_TOKENS, tools=[req["tool"]],
                tool_choice={"type": "tool", "name": analysis.TOOL_NAME},
                messages=[{"role": "user", "content": req["prompt"]}])
        except Exception as e:
            # A 4xx means the API refused the request, so it wasn't billed. Anything else (5xx, timeout,
            # connection error, an unexpected error) may have been billed, so it counts at the worst case.
            if budget.rejected_before_billing(e):
                ledger.release(hold)
            else:
                ledger.settle(hold, worst)
            if budget.monthly_limit_error(e):
                raise TickerSkipped("monthly") from e
            if isinstance(e, APIError):
                return analysis.failed_result(sources, f"Anthropic API error ({type(e).__name__}); try again")
            raise
        # Every response that comes back is billed for what it used, including a cut-off one (max_tokens)
        ledger.settle(hold, budget.cost_usd(analysis.MODEL, response.usage.input_tokens, response.usage.output_tokens))
        raw = {"stop_reason": response.stop_reason,
               "tool_input": next((b.input for b in response.content if b.type == "tool_use"), None),
               "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}}
        # stop_reason says why Claude stopped: "tool_use" means it finished filling in the tool,
        # "max_tokens" means it hit the cap mid-answer and the later fields are missing.
        print(f"[claude] {ticker}: stop_reason={raw['stop_reason']} output_tokens={raw['usage']['output_tokens']} "
              f"input_tokens={raw['usage']['input_tokens']} max_tokens={analysis.MAX_OUTPUT_TOKENS}", flush=True)
    checked = analysis.check_response(raw["stop_reason"], raw["tool_input"], sources)
    if SAVE_DIR and not from_cache:
        saved = {"ticker": ticker, "saved_at": datetime.now(ET).isoformat(timespec="seconds"), "model": analysis.MODEL,
                 "max_tokens": analysis.MAX_OUTPUT_TOKENS, "raw": raw, "request": req,
                 "evidence": [s.coverage() for s in sources], "checked": checked}
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(os.path.join(SAVE_DIR, f"{ticker}_{datetime.now(ET):%Y%m%d_%H%M%S}.json"), "w") as fh:
            json.dump(saved, fh, indent=1, default=str)
    if not from_cache and analysis.is_cacheable(checked):
        store[key] = {"at": time.time(), "raw": raw}
    return checked | {"usage": raw.get("usage"), "from_cache": from_cache,
                      "budget": {"input_tokens": req["input_tokens"], "limit": req["budget"],
                                 "output_reserve": analysis.MAX_OUTPUT_TOKENS, "count": method["method"]}}

# Local only: set SAVE_SAMPLE_DIR to write each finished profile to JSON (tests/offline/build_sample.py uses them)
SAMPLE_OUT = os.environ.get("SAVE_SAMPLE_DIR")

def analyze_ticker(ticker: str, cik: str, progress) -> dict:
    # No spending check here: a cached answer costs nothing, and that's only known once the request is built.
    # run_analysis reserves right before the Claude call.
    progress("Reading SEC filings (step 1 of 3)")
    evidence = gather_evidence(ticker, cik)
    progress("Fetching market data and SEC figures (step 2 of 3)")
    financials = load_financials(ticker)
    sec_metrics = load_sec_metrics(cik)
    progress("Summarizing filings with Claude (step 3 of 3)")
    result = run_analysis(ticker, evidence)
    profile = {"ticker": ticker, "company_name": evidence["company_name"], "industry": evidence["industry"],
               "financials": financials, "sec_metrics": sec_metrics,
               "evidence": [s.coverage() for s in evidence["sources"]], "analysis": result,
               "filing_review": evidence["filing_review"],
               "event_markers": evidence["event_markers"]}
    if SAMPLE_OUT:
        os.makedirs(SAMPLE_OUT, exist_ok=True)
        with open(os.path.join(SAMPLE_OUT, f"{ticker}.json"), "w") as fh:
            json.dump(profile, fh, indent=1, default=str)
    return profile

# --- ARCHIVED EXAMPLE: the frozen AAPL + STRL filing-research run in samples/, rendered with no network calls ---
SAMPLES = Path(__file__).parent / "samples"

def load_sample() -> None:
    manifest = json.loads((SAMPLES / "manifest.json").read_text(encoding="utf-8"))
    profiles = {}
    for t in manifest["tickers"]:
        p = json.loads((SAMPLES / f"{t}.json").read_text(encoding="utf-8"))
        p["sample_prices"] = str(SAMPLES / f"{t}_prices.csv")
        profiles[t] = p
    st.session_state.results = {"tickers": manifest["tickers"], "profiles": profiles, "failures": {}, "skipped": {},
                                "run_at": datetime.fromisoformat(manifest["run_at"]), "sample": manifest}

def sample_prices(path: str) -> pd.DataFrame:
    return pd.read_csv(path, index_col=0, parse_dates=True)

@st.cache_data(ttl=3600, show_spinner=False)
def get_price_history(ticker: str) -> pd.DataFrame:
    """Five years of daily OHLCV bars from Yahoo Finance via yfinance.
    auto_adjust=True is the yfinance default, written out so it's visible: past prices are
    adjusted for splits and dividends. Raises instead of returning an empty frame, so a failure
    is never cached."""
    hist = yf.Ticker(ticker).history(period="5y", interval="1d", auto_adjust=True)
    if hist.empty:
        raise TickerFailure("Yahoo Finance returned no price history")
    hist = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
    if hist.index.tz is not None:
        hist.index = hist.index.tz_localize(None)  # keep the New York trading date, drop the time zone
    hist.index = hist.index.normalize()
    return hist

def generate_excel(profiles):
    """One row per record, one header per column, numbers stored as numbers."""
    wb = openpyxl.Workbook()
    header_fill, header_font = PatternFill(start_color="1e222d", end_color="1e222d", fill_type="solid"), Font(color="ffffff", bold=True)
    formats = {"USD": '"$"#,##0', "fraction": "0.00%", "multiple": '0.0"x"'}

    ws = wb.active
    ws.title = "Market data"
    ws.append(["Ticker", "Metric", "Value", "Unit", "Period", "Source", "Retrieved at", "Filings used"])
    for p in profiles:
        f = p["financials"]
        if f["status"] != "ok":
            ws.append([p["ticker"], "All Yahoo metrics", None, None, None, f"Failed: {f['reason']}", None])
        else:
            for m in f["metrics"].values():
                ws.append([p["ticker"], m["label"], m["value"], m["unit"], m["period"] or "Period not stated",
                           f"{f['source']}: {m['field']}", f["retrieved_at"]])
                if m["value"] is not None:
                    ws.cell(ws.max_row, 3).number_format = '"$"#,##0.00' if m["field"] in ("currentPrice", "regularMarketPrice") else formats[m["unit"]]
        sec = p.get("sec_metrics")
        if sec and sec["status"] != "ok":
            ws.append([p["ticker"], "All SEC metrics", None, None, None, f"Failed: {sec['reason']}", None])
        elif sec:
            for key, m in sec["metrics"].items():
                op = " minus " if key == "free_cash_flow" else " / "   # FCF subtracts capex; the margins divide by revenue
                tags = op.join(m["tags"]) if m["tags"] else f"{xbrl.NOT_REPORTED} ({m['detail']})"
                ws.append([p["ticker"], m["label"], m["value"], m["unit"], f"TTM to {m['period_end']}",
                           f"{sec['source']}: {tags}", sec["retrieved_at"],
                           "; ".join(f"{x['form']} {x['accession']} (period {x['period']}, filed {x['filed']})" for x in m["filings"])])
                if m["value"] is not None:
                    ws.cell(ws.max_row, 3).number_format = formats[m["unit"]]

    ws = wb.create_sheet("Findings")
    ws.append(["Ticker", "Type", "Headline", "Summary", "Potential implication", "Detail", "Impact (AI assessment)",
               "Impact basis", "Change vs prior 10-K (code)", "Category", "Source", "Form", "Filed", "Period", "Quote",
               "Excerpt check", "Figures not in cited source", "Wording flags", "Filing URL", "Other sources for figures"])
    for p in profiles:
        for kind in ("catalysts", "risks", "other_risks"):
            for i in p["analysis"]["sections"][kind]["items"]:
                s = i["source"]
                ws.append([p["ticker"], {"catalysts": "Catalyst", "risks": "Risk factor change",
                                         "other_risks": "Other risk (management's discussion)"}[kind], i["headline"], i["summary"], i["implication"], i["detail"],
                           i["impact"], i["impact_basis"], ui.trend_text(i) if kind == "risks" else "", i["category"],
                           s["role"], s["form"], s["filed"], s["period"], i["quote"], i["excerpt"]["status"],
                           "; ".join(i.get("unsupported_figures", [])), "; ".join(i.get("wording_flags", [])), s["url"],
                           "; ".join(f"{o['label']} {o['url']}" for o in i.get("other_sources", []))])

    ws = wb.create_sheet("8-K events")
    ws.append(["Ticker", "Filed", "Event date", "8-K items", "Category", "Headline", "Summary", "Quote", "Excerpt check", "Filing URL"])
    for p in profiles:
        for e in p["analysis"]["sections"]["events"]["items"]:
            s = e["source"]
            ws.append([p["ticker"], s["filed"], s["period"], s.get("items", ""), e["category"], e["headline"],
                       e["summary"], e["quote"], e["excerpt"]["status"], s["url"]])

    ws = wb.create_sheet("Evidence")
    ws.append(["Ticker", "Source ID", "Source", "Status", "Form", "Filed", "Period", "Characters found",
               "Characters sent", "Characters omitted", "Note", "Filing URL"])
    for p in profiles:
        for c in p["evidence"]:
            ws.append([p["ticker"], c["id"], c["role"], c["status"], c.get("form"), c.get("filed"), c.get("period"),
                       c["chars"], c["sent_chars"], c["omitted_chars"], c["note"], c.get("url")])

    ws = wb.create_sheet("Filing review")
    ws.append(["Ticker", "Balance-sheet date", "Index through", "Index status", "Form", "Filed", "Report date",
               "8-K items", "Accession", "Content review", "EDGAR index", "Index note",
               "Event date", "Amount type", "Checked finding", "Source document", "Related documents"])
    for p in profiles:
        inv = p.get("filing_review")
        if not inv:
            ws.append([p["ticker"], None, None, "Not checked", None, None, None, None, None, None, None,
                       "Saved result has no subsequent-filing index."])
            continue
        for f in inv["filings"]:
            ws.append([p["ticker"], inv["since"], inv["through"], inv["status"], f["form"], f["filed"],
                       f["period"], f["items"], f["accession"], f["review"], f["url"], "; ".join(inv["notes"]),
                       f.get("event_date"), f.get("kind"), f.get("finding"), f.get("source_url"),
                       "; ".join(url for _, url in f.get("related", []))])
        if not inv["filings"]:
            ws.append([p["ticker"], inv["since"], inv["through"], inv["status"], None, None, None, None, None,
                       "Not checked", None, "; ".join(inv["notes"]) or "No candidate forms indexed; contents not reviewed."])

    for ws in wb.worksheets:
        for cell in ws[1]: cell.fill, cell.font = header_fill, header_font
        for col in ws.columns: ws.column_dimensions[col[0].column_letter].width = 25
        ws.freeze_panes = "A2"

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

# --- RESULTS RENDERING ---
def _when(iso: str) -> str:
    t = datetime.fromisoformat(iso)
    return f"{t:%b} {t.day}, {t:%Y}, {t.strftime('%I').lstrip('0')}:{t:%M %p} ET"

def _day(iso_date: str) -> str:
    d = datetime.fromisoformat(iso_date)
    return f"{d:%b} {d.day}, {d:%Y}"

def metric_groups(p: dict) -> list:
    """[(heading, caption, [(label, value, period line), ...]), ...]. Yahoo gives price, market cap and forward P/E;
    revenue, margins and free cash flow come from the company's own SEC filings, so each states its period and filings.
    A group whose source failed is left out (its notice says why)."""
    groups = []
    f = p["financials"]
    if f["status"] == "ok":
        m = f["metrics"]
        tile = lambda k: (m[k]["label"], ui.format_metric(m[k]["value"], m[k]["unit"]), m[k]["period"] or "Period not stated")
        groups.append(("Price and valuation", f"Yahoo Finance · retrieved {_when(f['retrieved_at'])}",
                       [tile("price"), tile("market_cap"), tile("forward_pe")]))
    sec = p.get("sec_metrics")   # absent in profiles saved before Oct 11, 2026
    if sec and sec["status"] == "ok":
        def tile(m):
            if m["value"] is None:
                return m["label"], "Not reported", "Not in SEC data for this period"
            return (m["label"], ui.format_metric(m["value"], m["unit"]),
                    "\n".join(f"{x['form']} filed {_day(x['filed'])}" for x in m["filings"]))   # one filing per line
        groups.append((f"From SEC filings · TTM to {_day(sec['period_end'])}",
                       f"SEC XBRL company facts · retrieved {_when(sec['retrieved_at'])}",
                       [tile(m) for m in sec["metrics"].values()]))
    return groups


SHOW = ["All", "Catalysts", "Risk factor changes", "Other risks"]


def render_profile(p: dict) -> None:
    a, secs = p["analysis"], p["analysis"]["sections"]
    st.markdown(ui.company_header(p["ticker"], p["company_name"], p["industry"])
                + ui.metric_tiles(metric_groups(p))
                + (ui.notice("Market data unavailable", f"{p['financials']['reason']}. It is retried on the next run.", "caution")
                   if p["financials"]["status"] != "ok" else "")
                + (ui.notice("SEC figures unavailable", f"{p['sec_metrics']['reason']}. They are retried on the next run.", "caution")
                   if p.get("sec_metrics", {}).get("status") == "failed" else ""), unsafe_allow_html=True)

    try:
        hist = sample_prices(p["sample_prices"]) if p.get("sample_prices") else get_price_history(p["ticker"])
        st.plotly_chart(build_price_chart(hist, p["event_markers"]), width="stretch", theme=None, config=CHART_CONFIG)
        st.caption(f"Daily bars through {hist.index[-1]:%Y-%m-%d}, adjusted for splits and dividends. "
                   "Source: Yahoo Finance via yfinance. Diamonds: SEC filing dates from EDGAR.")
    except TickerFailure as e:
        st.caption(f"Price chart unavailable: {e}")
    except Exception as e:
        traceback.print_exc()
        st.caption(f"Price chart unavailable ({type(e).__name__})")

    st.markdown(ui.analysis_banner(a) + ui.evidence_list(p["evidence"], a["comparison"], a.get("budget")), unsafe_allow_html=True)

    review = p.get("filing_review")
    with st.expander("Financing filing review since the balance sheet"):
        st.markdown(filing_review.render(review), unsafe_allow_html=True)

    counts = {"Catalysts": len(secs["catalysts"]["items"]), "Risk factor changes": len(secs["risks"]["items"]),
              "Other risks": len(secs["other_risks"]["items"])}
    counts["All"] = sum(counts.values())
    show = st.radio("Show", SHOW, horizontal=True, key=f"show_{p['ticker']}", label_visibility="collapsed",
                    format_func=lambda o: f"{o} {counts[o]}")
    html = ui.impact_criteria()
    if show in ("All", "Catalysts"):
        html += (ui.section_header("Catalysts", counts["Catalysts"]) + ui.section_state(secs["catalysts"], "catalysts")
                 + ui.findings_list(secs["catalysts"]["items"], "catalyst"))
    if show in ("All", "Risk factor changes"):
        html += (ui.section_header("What changed in the risk factors", counts["Risk factor changes"], ui.trend_note(a["comparison"]))
                 + ui.section_state(secs["risks"], "risks") + ui.findings_list(secs["risks"]["items"], "risk")
                 + ui.unchanged_list(a["comparison"]))
    if show in ("All", "Other risks"):
        html += (ui.section_header("Other risks from management's discussion (not compared to last year)", counts["Other risks"])
                 + ui.section_state(secs["other_risks"], "other_risks")
                 + ui.findings_list(secs["other_risks"]["items"], "other_risk"))
    html += (ui.section_header("8-K events", len(secs["events"]["items"]), f"Last {sec_data.EIGHT_K_WINDOW_DAYS} days · dates and item numbers from EDGAR; headlines and summaries by Claude")
             + ui.section_state(secs["events"], "events") + ui.event_list(secs["events"]["items"]))
    st.markdown(html, unsafe_allow_html=True)


def render_skipped(kind: str) -> None:
    st.markdown(ui.notice("Not analyzed", ui.SKIP_MESSAGES[kind], "neutral"), unsafe_allow_html=True)


def render_failure(ticker: str, reason: str) -> None:
    st.markdown(f"<div class='irt-card tone-negative'><div class='irt-card-title'>Couldn't analyze {ui.esc(ticker)}</div>"
                f"<p class='irt-card-body'>{ui.esc(reason)}</p></div>", unsafe_allow_html=True)


def run_state(p: dict) -> tuple:
    """Progress chip for a finished ticker: done, or partial when any piece failed or was cut off."""
    partial = (p["analysis"]["response_status"] != "complete" or p["financials"]["status"] != "ok"
               or p.get("sec_metrics", {}).get("status") == "failed"
               or any(c["status"] == "failed" for c in p["evidence"]))
    return ("partial", "partial results") if partial else ("done", "")



# --- PAGES ---
# The saved debt and liquidity reviews are the product; general filing research is the older, experimental tool.
# The page lives in session state (not a widget), so switching back and forth keeps each tool's results.
DEBT, RESEARCH = "debt", "research"
RESEARCH_LABEL = "General filing research — experimental"


def open_view(view: str) -> None:
    st.session_state.view = view


def render_header() -> None:
    st.markdown(
        "<div class='irt-header'><div class='irt-title' role='heading' aria-level='1'>Debt &amp; Liquidity Research Terminal</div>"
        "<div class='irt-sub'>Saved reviews of what Eli Lilly, Oracle and Vistra owe, the cash and cash generation "
        "behind it, and the SEC filing evidence for each figure. Every review is dated and frozen; opening one makes "
        "no live request. A research tool, not investment advice.</div></div>",
        unsafe_allow_html=True,
    )


def render_debt_view() -> None:
    st.button(RESEARCH_LABEL, type="tertiary", icon=":material/arrow_forward:", icon_position="right",
              on_click=open_view, args=(RESEARCH,))
    # Import the complete view directly: long-lived workers can retain an older model helper after deployment.
    company_review.render_app()


def render_owner_sidebar() -> None:
    """Owner bypass: only when OWNER_PASSCODE is set in Streamlit Secrets. Typed in the sidebar, kept in the
    session, never in a URL. Owner runs still count against the ledger, so visitors see a true remainder."""
    owner_passcode = secret("OWNER_PASSCODE")
    if not owner_passcode:
        return
    with st.sidebar:
        typed = st.text_input("Owner passcode", type="password")
        # Clearing the field turns owner mode off again
        st.session_state.owner = bool(typed) and hmac.compare_digest(typed.encode(), str(owner_passcode).encode())
        if typed:
            st.caption("Owner mode: the daily limit is off for this session." if st.session_state.owner else "Passcode not recognized.")


def run_live(tickers: list, ticker_ciks: dict) -> None:
    """Skeletons first, then each ticker fills in as it finishes."""
    statuses = {t: ("queued", "queued") for t in tickers}
    strip = st.empty()
    strip.markdown(ui.progress_strip(statuses), unsafe_allow_html=True)
    slots = {}
    for t, tab in zip(tickers, st.tabs(tickers)):
        with tab:
            slots[t] = st.empty()
            slots[t].markdown(ui.skeleton(t, "Queued"), unsafe_allow_html=True)

    profiles, failures, skipped = {}, {}, {}
    for t in tickers:
        started = time.time()

        def progress(step, t=t):
            statuses[t] = ("working", step.split(" (")[0].lower())
            strip.markdown(ui.progress_strip(statuses), unsafe_allow_html=True)
            slots[t].markdown(ui.skeleton(t, step), unsafe_allow_html=True)

        try:
            profiles[t] = analyze_ticker(t, ticker_ciks[t], progress)
            state, label = run_state(profiles[t])
            statuses[t] = (state, f"{label + ', ' if label else ''}{time.time() - started:.0f}s")
        except TickerSkipped as e:
            skipped[t] = e.kind
        except TickerFailure as e:
            failures[t] = str(e)
        except Exception as e:
            traceback.print_exc()  # full stack trace to the server log; the user sees only the short message
            failures[t] = f"unexpected error ({type(e).__name__}), try again"
        if t in skipped:
            statuses[t] = ("skipped", ui.SKIP_LABELS[skipped[t]])
            with slots[t].container():
                render_skipped(skipped[t])
        elif t in failures:
            statuses[t] = ("failed", "failed")
            with slots[t].container():
                render_failure(t, failures[t])
        else:
            with slots[t].container():
                render_profile(profiles[t])
        strip.markdown(ui.progress_strip(statuses), unsafe_allow_html=True)

    # Keep the results so a download, preset click, ticker change or page switch doesn't wipe them
    st.session_state.results = {
        "tickers": tickers, "profiles": profiles, "failures": failures, "skipped": skipped,
        "run_at": datetime.now(ET),
    }
    st.rerun()  # redraw once from session state: summary row and download button on top


def render_results(results: dict) -> None:
    profiles, failures, skipped = results["profiles"], results["failures"], results.get("skipped", {})
    done = [t for t in results["tickers"] if t in profiles]
    partial = [t for t in done if run_state(profiles[t])[0] == "partial"]

    col_sum, col_dl = st.columns([4, 1])
    if results.get("sample"):
        tickers = ", ".join(results["sample"]["tickers"])
        summary = f"Archived filing-research example ({tickers}). " + results["sample"]["label"].removeprefix("Saved sample. ")
    else:
        summary = (f"Results for {', '.join(results['tickers'])} · run {results['run_at']:%b %d, %I:%M %p} ET · "
                   f"{len(done)} of {len(results['tickers'])} succeeded"
                   + (f" ({len(partial)} with partial results)" if partial else "")
                   + (f" · {len(skipped)} skipped by the spending limit" if skipped else ""))
    col_sum.markdown(f"<p class='irt-subtitle irt-mark-results'>{ui.esc(summary)}</p>", unsafe_allow_html=True)
    if profiles:
        col_dl.download_button("Download Excel", data=generate_excel([profiles[t] for t in done]),
                               file_name=f"Research_Record_{'_'.join(done)}_{results['run_at']:%Y-%m-%d}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if not results.get("sample") and sorted(st.session_state.ticker_select) != sorted(results["tickers"]):
        st.caption("Your ticker selection changed. Click Run analysis to update these results.")

    for t, tab in zip(results["tickers"], st.tabs(results["tickers"])):
        with tab:
            if t in profiles:
                render_profile(profiles[t])
            elif t in skipped:
                render_skipped(skipped[t])
            else:
                render_failure(t, failures.get(t, "unknown error"))


def render_research_view() -> None:
    st.button("Debt and liquidity reviews", type="tertiary", icon=":material/arrow_back:",
              on_click=open_view, args=(DEBT,))
    st.markdown(f"<div class='irt-h' role='heading' aria-level='2'>{ui.esc(RESEARCH_LABEL)}</div>"
                "<p class='irt-note'>AI summaries of catalysts, risk-factor changes and 8-K events for any ticker, with "
                "market data. Unlike the debt and liquidity reviews, these findings are not checked by hand.</p>",
                unsafe_allow_html=True)

    problems = live_setup_problems()
    sec_directory, used_fallback = load_sec_directory()
    ticker_names = dict(zip(sec_directory["ticker"], sec_directory["name"]))
    ticker_ciks = dict(zip(sec_directory["ticker"], sec_directory["cik"]))

    # Drop any saved ticker that isn't in today's options (e.g. after a fallback), or the multiselect raises
    st.session_state.ticker_select = [t for t in st.session_state.get("ticker_select", ["AAPL"]) if t in ticker_names]

    col_pick, col_run = st.columns([5, 1])
    with col_pick:
        st.multiselect(
            "Tickers",
            options=list(ticker_names),
            format_func=lambda t: f"{t} · {ticker_names[t]}",
            key="ticker_select",
            placeholder="Search by ticker or company name",
            max_selections=5,
            label_visibility="collapsed",  # the placeholder explains it; screen readers still get the label
            persist_state="session",       # kept while the debt and liquidity page is open
        )
    with col_run:
        run_btn = st.button("Run analysis", type="primary", width="stretch", disabled=bool(problems))

    st.markdown("<p class='irt-note'>Live analysis is limited to about one ticker a day. The archived example is always available.</p>",
                unsafe_allow_html=True)
    if problems:
        st.markdown(ui.notice("Live analysis is unavailable on this deployment",
                              "; ".join(problems) + ". The archived example below still opens.", "neutral"),
                    unsafe_allow_html=True)
    elif used_fallback:
        st.warning("Couldn't reach the SEC ticker list, so only 6 tickers are available. Reload the page to retry.")
    st.button("View archived example (AAPL, STRL · Oct 10, 2026)", on_click=load_sample)
    render_owner_sidebar()

    if run_btn and not st.session_state.ticker_select:
        st.warning("Pick at least one ticker, then click Run analysis.")
    elif run_btn:
        run_live(list(st.session_state.ticker_select), ticker_ciks)

    # st.rerun() in run_live stops that run, so saved results draw on the next run (and every run after)
    results = st.session_state.get("results")
    if results:
        render_results(results)
    elif not problems:   # when live runs can't start, the notice above is the empty state
        st.markdown(
            "<div class='irt-card' style='margin-top:16px'><div class='irt-card-title'>Choose tickers and click Run analysis</div>"
            "<p class='irt-card-body'>For each stock you get price history with SEC filing dates, AI summaries of catalysts and risks "
            "with the filing excerpts behind them, and recent 8-K events, and an Excel download. "
            "A first run reads several filings and takes about a minute per ticker.</p></div>",
            unsafe_allow_html=True)


render_header()
if st.session_state.get("view") == RESEARCH:
    render_research_view()
else:
    render_debt_view()
