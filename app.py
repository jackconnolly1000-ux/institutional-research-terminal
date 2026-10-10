import hashlib
import json
import os
import requests
import time
import traceback
import openpyxl
import yfinance as yf
import pandas as pd
from openpyxl.styles import Font, PatternFill
from io import BytesIO
from datetime import datetime
from anthropic import Anthropic, APIError
from zoneinfo import ZoneInfo
import streamlit as st

import analysis
import market_data
import sec_data
import ui
from charts import CHART_CONFIG, build_price_chart

ET = ZoneInfo("America/New_York")

# --- STREAMLIT PAGE CONFIG + STYLING (colors live in theme.py, CSS in ui.py) ---
st.set_page_config(
    page_title="SEC Filing Research Terminal",
    layout="wide",
    initial_sidebar_state="collapsed"
)
ui.inject_css()

# --- API KEY AND SEC CONTACT (from Streamlit Secrets) ---
try:
    if "ANTHROPIC_API_KEY" not in st.secrets:
        st.error("ANTHROPIC_API_KEY was not found in Streamlit Secrets.")
        st.stop()
    raw_key = st.secrets["ANTHROPIC_API_KEY"]
    clean_key = str(raw_key).strip().replace("\n", "").replace(" ", "").replace("\r", "")
    client = Anthropic(api_key=clean_key, timeout=60.0)
except Exception as e:
    st.error(f"Initialization Error: {e}")
    st.stop()

# SEC EDGAR asks every automated request to name a real contact (its fair-access policy).
# The environment fallback exists for the offline test harness, which has no secrets file.
try:
    SEC_CONTACT = st.secrets.get("SEC_CONTACT_EMAIL") or os.environ.get("SEC_CONTACT_EMAIL")
except Exception:
    SEC_CONTACT = os.environ.get("SEC_CONTACT_EMAIL")
if not SEC_CONTACT:
    st.error("SEC_CONTACT_EMAIL is not set in Streamlit Secrets. SEC EDGAR requires a contact email on every request.")
    st.stop()

# --- BACKEND ---
# Cached functions RAISE on failure instead of returning None or a fallback:
# st.cache_data stores return values, not exceptions, so a failure is retried on the next run
# instead of being served from cache. Pure logic lives in sec_data.py, analysis.py and market_data.py.
class TickerFailure(Exception):
    """A per-ticker failure whose message is safe to show the user."""

SEC_HEADERS = {"User-Agent": f"SEC Filing Research Terminal {SEC_CONTACT}"}

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
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=SEC_HEADERS, timeout=12)
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
    """Returns (directory, used_fallback). Not cached itself, so the fallback is never cached."""
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
    return {"company_name": subs.get("name", ticker).title(), "industry": subs.get("sicDescription", "Public issuer").title(),
            "selection": selection, "sources": sources,
            "event_markers": [(f.filed, f.form) for f in wanted]}

@st.cache_data(ttl=900, show_spinner=False)
def cached_financials(ticker: str) -> dict:
    return market_data.fetch_financials(ticker, yf.Ticker)

def load_financials(ticker: str) -> dict:
    try:
        return {"status": "ok", **cached_financials(ticker)}
    except market_data.MarketDataError as e:
        return {"status": "failed", "reason": str(e)}

@st.cache_resource(show_spinner=False)
def analysis_store() -> dict:
    """Complete Claude answers, keyed by a hash of the exact request. Written only when
    analysis.is_cacheable() says every section is usable, so a cut-off or malformed answer is
    never served again as if it were complete."""
    return {}

ANALYSIS_TTL = 3600
ANALYSIS_TIMEOUT = 300  # seconds; an answer of up to 16,000 tokens can take minutes
# Local diagnostics only: set SAVE_AI_RESPONSES_DIR to keep each raw Claude answer and the profile built from it
SAVE_DIR = os.environ.get("SAVE_AI_RESPONSES_DIR")

def count_request_tokens(prompt: str, tool: dict, method: dict) -> int:
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
    try:
        req = analysis.fit_to_budget(ticker, evidence["company_name"], sources,
                                     lambda p, t: count_request_tokens(p, t, method))
    except ValueError as e:
        return analysis.failed_result(sources, str(e))
    key = hashlib.sha256(analysis.request_fingerprint(req["prompt"], req["tool"]).encode()).hexdigest()
    store = analysis_store()
    hit = store.get(key)
    from_cache = bool(hit and time.time() - hit["at"] < ANALYSIS_TTL)
    if from_cache:
        raw = hit["raw"]
    else:
        try:
            # One attempt only: an SDK retry after a timeout could bill the same request twice.
            response = client.with_options(timeout=ANALYSIS_TIMEOUT, max_retries=0).messages.create(
                model=analysis.MODEL, max_tokens=analysis.MAX_OUTPUT_TOKENS, tools=[req["tool"]],
                tool_choice={"type": "tool", "name": analysis.TOOL_NAME},
                messages=[{"role": "user", "content": req["prompt"]}])
        except APIError as e:
            return analysis.failed_result(sources, f"Anthropic API error ({type(e).__name__}); try again")
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

def analyze_ticker(ticker: str, cik: str, progress) -> dict:
    progress("Reading SEC filings (step 1 of 3)")
    evidence = gather_evidence(ticker, cik)
    progress("Fetching market data (step 2 of 3)")
    financials = load_financials(ticker)
    progress("Summarizing filings with Claude (step 3 of 3)")
    result = run_analysis(ticker, evidence)
    return {"ticker": ticker, "company_name": evidence["company_name"], "industry": evidence["industry"],
            "financials": financials, "form4_count": evidence["selection"].form4_count,
            "evidence": [s.coverage() for s in evidence["sources"]], "analysis": result,
            "event_markers": evidence["event_markers"]}

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
    ws.append(["Ticker", "Metric", "Value", "Unit", "Period", "Source", "Retrieved at"])
    for p in profiles:
        f = p["financials"]
        if f["status"] != "ok":
            ws.append([p["ticker"], "All metrics", None, None, None, f"Failed: {f['reason']}", None])
            continue
        for m in f["metrics"].values():
            ws.append([p["ticker"], m["label"], m["value"], m["unit"], m["period"] or "Period unavailable",
                       f"{f['source']}: {m['field']}", f["retrieved_at"]])
            if m["value"] is not None:
                ws.cell(ws.max_row, 3).number_format = '"$"#,##0.00' if m["field"] in ("currentPrice", "regularMarketPrice") else formats[m["unit"]]

    ws = wb.create_sheet("Findings")
    ws.append(["Ticker", "Type", "Headline", "Summary", "Potential implication", "Detail", "Impact (AI assessment)",
               "Impact basis", "Change vs prior 10-K (code)", "Category", "Source", "Form", "Filed", "Period", "Quote",
               "Excerpt check", "Figures not in cited source", "Wording flags", "Filing URL"])
    for p in profiles:
        for kind in ("catalysts", "risks", "other_risks"):
            for i in p["analysis"]["sections"][kind]["items"]:
                s = i["source"]
                ws.append([p["ticker"], {"catalysts": "Catalyst", "risks": "Risk factor change",
                                         "other_risks": "Other risk (management's discussion)"}[kind], i["headline"], i["summary"], i["implication"], i["detail"],
                           i["impact"], i["impact_basis"], ui.trend_text(i) if kind == "risks" else "", i["category"],
                           s["role"], s["form"], s["filed"], s["period"], i["quote"], i["excerpt"]["status"],
                           "; ".join(i.get("unsupported_figures", [])), "; ".join(i.get("wording_flags", [])), s["url"]])

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

    for ws in wb.worksheets:
        for cell in ws[1]: cell.fill, cell.font = header_fill, header_font
        for col in ws.columns: ws.column_dimensions[col[0].column_letter].width = 25
        ws.freeze_panes = "A2"

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

# --- HEADER ---
st.markdown(
    "<h1 class='irt-title'>SEC Filing Research Terminal</h1>"
    "<p class='irt-subtitle'>SEC filings, market data and AI summaries for up to five stocks. "
    "A research tool, not investment advice.</p>",
    unsafe_allow_html=True,
)

# --- TOOLBAR: TICKER PICKER, ONE PRIMARY ACTION, EXAMPLE PRESETS ---
sec_directory, used_fallback = load_sec_directory()
ticker_names = dict(zip(sec_directory["ticker"], sec_directory["name"]))
ticker_ciks = dict(zip(sec_directory["ticker"], sec_directory["cik"]))

def apply_preset(tickers):
    # on_click callbacks run before the rerun, so the multiselect hasn't been drawn yet: setting its key is allowed
    st.session_state.ticker_select = [t for t in tickers if t in ticker_names]

# Drop any saved ticker that isn't in today's options (e.g. after a fallback), or the multiselect raises
st.session_state.ticker_select = [t for t in st.session_state.get("ticker_select", ["AAPL"]) if t in ticker_names]

col_pick, col_run = st.columns([5, 1])
with col_pick:
    st.multiselect(
        "Tickers",
        options=list(ticker_names),
        format_func=lambda t: f"{t} · {ticker_names[t]}",
        key="ticker_select",
        placeholder="Search by ticker or company name (up to 5)",
        max_selections=5,
        label_visibility="collapsed",  # the placeholder explains it; screen readers still get the label
    )
with col_run:
    run_btn = st.button("Run analysis", type="primary", use_container_width=True)

col_ex1, col_ex2, _ = st.columns([1.3, 1.6, 5])
col_ex1.button("Example: AAPL", on_click=apply_preset, args=(["AAPL"],), use_container_width=True)
col_ex2.button("Example: FAST + STRL", on_click=apply_preset, args=(["FAST", "STRL"],), use_container_width=True)

if used_fallback:
    st.warning("Couldn't reach the SEC ticker list, so only 6 tickers are available. Reload the page to retry.")


# --- RESULTS RENDERING (Phase 1: same layout, new data; the layout itself changes in Phase 2) ---
def metric_groups(p: dict) -> list:
    f = p["financials"]
    insider = ("Insider filings", [("Form 4, last 90 days", str(p["form4_count"]), "SEC EDGAR · count of filings, not transactions")])
    if f["status"] != "ok":
        return [insider]
    m = f["metrics"]
    tile = lambda k: (m[k]["label"], ui.format_metric(m[k]["value"], m[k]["unit"]),
                      f"Yahoo Finance · {m[k]['period'] or 'Period unavailable'}")
    return [("Market", [tile("price"), tile("market_cap")]),
            ("Valuation and profitability", [tile("forward_pe"), tile("gross_margin"), tile("free_cash_flow")]),
            insider]


def render_profile(p: dict) -> None:
    a = p["analysis"]
    st.markdown(ui.company_header(p["ticker"], p["company_name"], p["industry"])
                + ui.metric_tiles(metric_groups(p))
                + (ui.notice("Market data unavailable", f"{p['financials']['reason']}. It is retried on the next run.", "caution")
                   if p["financials"]["status"] != "ok" else ""), unsafe_allow_html=True)

    try:
        hist = get_price_history(p["ticker"])
        st.plotly_chart(build_price_chart(hist, p["event_markers"]), use_container_width=True, theme=None, config=CHART_CONFIG)
        st.caption(f"Daily bars through {hist.index[-1]:%Y-%m-%d}, adjusted for splits and dividends. "
                   "Source: Yahoo Finance via yfinance. Diamonds: SEC filing dates from EDGAR.")
    except TickerFailure as e:
        st.caption(f"Price chart unavailable: {e}")
    except Exception as e:
        traceback.print_exc()
        st.caption(f"Price chart unavailable ({type(e).__name__})")

    st.markdown(ui.analysis_banner(a) + ui.evidence_list(p["evidence"], a["comparison"], a.get("budget")), unsafe_allow_html=True)

    secs = a["sections"]
    col_bull, col_bear = st.columns(2, gap="large")
    with col_bull:
        st.markdown(ui.section_header("Catalysts", len(secs["catalysts"]["items"]), ui.IMPACT_NOTE)
                    + ui.section_state(secs["catalysts"], "catalysts")
                    + "".join(ui.finding_card(i, "catalyst") for i in secs["catalysts"]["items"]), unsafe_allow_html=True)
    with col_bear:
        st.markdown(ui.section_header("What changed in the risk factors", len(secs["risks"]["items"]), ui.trend_note(a["comparison"]))
                    + ui.section_state(secs["risks"], "risks")
                    + "".join(ui.finding_card(i, "risk") for i in secs["risks"]["items"])
                    + ui.unchanged_list(a["comparison"])
                    + ui.section_header("Other risks from management's discussion (not compared to last year)",
                                        len(secs["other_risks"]["items"]))
                    + ui.section_state(secs["other_risks"], "other_risks")
                    + "".join(ui.finding_card(i, "other_risk") for i in secs["other_risks"]["items"]), unsafe_allow_html=True)

    questions = "".join(f"<li>{ui.esc(q['question'])}</li>" for q in secs["questions"]["items"])
    st.markdown(ui.section_header("8-K events", len(secs["events"]["items"])) + ui.section_state(secs["events"], "events")
                + (ui.event_rows(secs["events"]["items"]) if secs["events"]["items"] else "")
                + ui.section_header("Questions for management", len(secs["questions"]["items"]))
                + ui.section_state(secs["questions"], "questions")
                + (f"<ol class='irt-questions'>{questions}</ol>" if questions else ""), unsafe_allow_html=True)


def render_failure(ticker: str, reason: str) -> None:
    st.markdown(f"<div class='irt-card tone-negative'><div class='irt-card-title'>Couldn't analyze {ui.esc(ticker)}</div>"
                f"<p class='irt-card-body'>{ui.esc(reason)}</p></div>", unsafe_allow_html=True)


def run_state(p: dict) -> tuple:
    """Progress chip for a finished ticker: done, or partial when any piece failed or was cut off."""
    partial = (p["analysis"]["response_status"] != "complete" or p["financials"]["status"] != "ok"
               or any(c["status"] == "failed" for c in p["evidence"]))
    return ("partial", "partial results") if partial else ("done", "")


# --- RUN: SKELETONS FIRST, THEN EACH TICKER FILLS IN AS IT FINISHES ---
if run_btn and not st.session_state.ticker_select:
    st.warning("Pick at least one ticker, then click Run analysis.")
elif run_btn:
    tickers = list(st.session_state.ticker_select)
    statuses = {t: ("queued", "queued") for t in tickers}
    strip = st.empty()
    strip.markdown(ui.progress_strip(statuses), unsafe_allow_html=True)
    slots = {}
    for t, tab in zip(tickers, st.tabs(tickers)):
        with tab:
            slots[t] = st.empty()
            slots[t].markdown(ui.skeleton(t, "Queued"), unsafe_allow_html=True)

    profiles, failures = {}, {}
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
        except TickerFailure as e:
            failures[t] = str(e)
        except Exception as e:
            traceback.print_exc()  # full stack trace to the server log; the user sees only the short message
            failures[t] = f"unexpected error ({type(e).__name__}), try again"
        if t in failures:
            statuses[t] = ("failed", "failed")
            with slots[t].container():
                render_failure(t, failures[t])
        else:
            with slots[t].container():
                render_profile(profiles[t])
        strip.markdown(ui.progress_strip(statuses), unsafe_allow_html=True)

    # Keep the results so a download, preset click or ticker change doesn't wipe them
    st.session_state.results = {
        "tickers": tickers, "profiles": profiles, "failures": failures,
        "run_at": datetime.now(ET),
    }
    st.rerun()  # redraw once from session state: summary row and download button on top

# --- SAVED RESULTS ---
# st.rerun() above stops this run, so this section only draws on the next run (and every run after)
results = st.session_state.get("results")
if results:
    profiles, failures = results["profiles"], results["failures"]
    done = [t for t in results["tickers"] if t in profiles]
    partial = [t for t in done if run_state(profiles[t])[0] == "partial"]

    col_sum, col_dl = st.columns([4, 1])
    col_sum.markdown(
        f"<p class='irt-subtitle'>Results for {ui.esc(', '.join(results['tickers']))} · "
        f"run {results['run_at']:%b %d, %I:%M %p} ET · {len(done)} of {len(results['tickers'])} succeeded"
        + (f" ({len(partial)} with partial results)" if partial else "") + "</p>",
        unsafe_allow_html=True)
    if profiles:
        col_dl.download_button("Download Excel", data=generate_excel([profiles[t] for t in done]),
                               file_name="Institutional_Model.xlsx", use_container_width=True,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if sorted(st.session_state.ticker_select) != sorted(results["tickers"]):
        st.caption("Your ticker selection changed. Click Run analysis to update these results.")

    for t, tab in zip(results["tickers"], st.tabs(results["tickers"])):
        with tab:
            if t in profiles:
                render_profile(profiles[t])
            else:
                render_failure(t, failures.get(t, "unknown error"))
else:
    st.markdown(
        "<div class='irt-card' style='margin-top:16px'><div class='irt-card-title'>Pick up to five tickers and click Run analysis</div>"
        "<p class='irt-card-body'>For each stock you get price history with SEC filing dates, AI summaries of catalysts and risks "
        "with the filing excerpts behind them, recent 8-K events, questions for management, and an Excel download. "
        "A first run reads several filings and takes about a minute per ticker.</p></div>",
        unsafe_allow_html=True)
