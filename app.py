import json
import requests
import re
import time
import traceback
import openpyxl
import yfinance as yf
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from io import BytesIO
from datetime import datetime
from bs4 import BeautifulSoup
from anthropic import Anthropic, APIError
from zoneinfo import ZoneInfo
import streamlit as st

import ui
from charts import CHART_CONFIG, build_price_chart


# --- STREAMLIT PAGE CONFIG + STYLING (colors live in theme.py, CSS in ui.py) ---
st.set_page_config(
    page_title="Institutional Research Terminal",
    layout="wide",
    initial_sidebar_state="collapsed"
)
ui.inject_css()

# --- SECURE KEY RETRIEVAL ---
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

# --- BACKEND FUNCTIONS ---
# Cached functions RAISE on failure instead of returning None or a fallback:
# st.cache_data stores return values, not exceptions, so a failure is retried on the next run
# instead of being served from cache.
class TickerFailure(Exception):
    """A per-ticker failure whose message is safe to show the user."""

FALLBACK_DIRECTORY = pd.DataFrame([
    {"ticker": "AAPL", "name": "Apple Inc."},
    {"ticker": "MSFT", "name": "Microsoft Corp."},
    {"ticker": "NVDA", "name": "Nvidia Corp."},
    {"ticker": "FAST", "name": "Fastenal Co."},
    {"ticker": "STRL", "name": "Sterling Infrastructure Inc."},
    {"ticker": "AAP", "name": "Advance Auto Parts Inc."}
], columns=["ticker", "name"])

@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_sec_directory() -> pd.DataFrame:
    headers = {'User-Agent': 'InstitutionalResearchDirectory admin@research-terminal.com'}
    resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers, timeout=5)
    resp.raise_for_status()
    rows = [{"ticker": v['ticker'].upper(), "name": v['title'].title()} for v in resp.json().values()]
    return pd.DataFrame(rows).drop_duplicates("ticker")

def load_sec_directory() -> tuple[pd.DataFrame, bool]:
    """Returns (directory, used_fallback). Not cached itself, so the fallback is never cached."""
    try:
        return _fetch_sec_directory(), False
    except Exception:
        return FALLBACK_DIRECTORY, True

@st.cache_data(ttl=3600, show_spinner=False)
def get_comprehensive_financials(ticker: str) -> dict:
    try:
        tkr = yf.Ticker(ticker)
        info = tkr.info
        mcap = info.get('marketCap', 0)
        mcap_str = f"${mcap/1e12:.2f}T" if mcap >= 1e12 else (f"${mcap/1e9:.2f}B" if mcap >= 1e9 else (f"${mcap/1e6:.2f}M" if mcap > 0 else "N/A"))
        price = info.get('currentPrice') or info.get('regularMarketPrice')
        price_str = f"${price:.2f}" if price else "N/A"
        fpe = info.get('forwardPE')
        fpe_str = f"{fpe:.1f}x" if fpe else "N/A"
        rev_growth = info.get('revenueGrowth')
        rev_str = f"{rev_growth * 100:.1f}%" if rev_growth else "N/A"
        gross_margin = f"{info.get('grossMargins', 0) * 100:.2f}%" if info.get('grossMargins') else "N/A"
        op_margin = f"{info.get('operatingMargins', 0) * 100:.2f}%" if info.get('operatingMargins') else "N/A"
        profit_margin = f"{info.get('profitMargins', 0) * 100:.2f}%" if info.get('profitMargins') else "N/A"
        roe = f"{info.get('returnOnEquity', 0) * 100:.2f}%" if info.get('returnOnEquity') else "N/A"
        debt_to_equity = f"{info.get('debtToEquity', 0):.2f}" if info.get('debtToEquity') else "N/A"
        fcf = info.get('freeCashflow', 0)
        fcf_str = f"${fcf/1e9:.2f}B" if fcf and abs(fcf) >= 1e9 else (f"${fcf/1e6:.2f}M" if fcf else "N/A")
        ebitda = info.get('ebitda', 0)
        ebitda_str = f"${ebitda/1e9:.2f}B" if ebitda and abs(ebitda) >= 1e9 else (f"${ebitda/1e6:.2f}M" if ebitda else "N/A")
        return {"mcap": mcap_str, "price": price_str, "fpe": fpe_str, "rev_growth": rev_str, "gross_margin": gross_margin, "op_margin": op_margin, "profit_margin": profit_margin, "roe": roe, "debt_to_equity": debt_to_equity, "fcf": fcf_str, "ebitda": ebitda_str}
    except Exception as e:
        return {k: "N/A" for k in ["mcap", "price", "fpe", "rev_growth", "gross_margin", "op_margin", "profit_margin", "roe", "debt_to_equity", "fcf", "ebitda"]}

def sec_get_request(url: str, headers: dict, retries: int = 3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200: return resp
            elif resp.status_code == 429: time.sleep(1.5 * (attempt + 1))
        except Exception: time.sleep(1.0)
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_firm_data(ticker: str) -> dict:
    headers = {'User-Agent': f'InstitutionalResearch analyst_{ticker.lower()}@research-terminal.com'}
    tickers_url = "https://www.sec.gov/files/company_tickers.json"
    
    resp = sec_get_request(tickers_url, headers)
    if not resp: raise TickerFailure("SEC EDGAR didn't respond, try again")
    try:
        data = resp.json()
    except json.JSONDecodeError:
        raise TickerFailure("SEC EDGAR sent an unreadable ticker list, try again")

    cik_padded = next((str(v['cik_str']).zfill(10) for v in data.values() if v['ticker'].upper() == ticker.upper()), None)
    if not cik_padded: raise TickerFailure("not found in the SEC ticker list")

    subs_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    time.sleep(0.15)
    subs_resp = sec_get_request(subs_url, headers)
    if not subs_resp: raise TickerFailure("SEC EDGAR didn't return the filing history, try again")
    subs_data = subs_resp.json()
    filings = subs_data['filings']['recent']
    
    company_name = subs_data.get('name', ticker.upper()).title()
    industry_desc = subs_data.get('sicDescription', 'Public Issuer').title()
    form_list = filings['form']
    
    form_4_dates = [filings['filingDate'][i] for i, f in enumerate(form_list) if f in ['4', '4/A']]
    recent_4s = [d for d in form_4_dates if (datetime.now() - datetime.strptime(d, '%Y-%m-%d')).days <= 90]
    insider_velocity = len(recent_4s)
    
    idx_curr = next((i for i, f in enumerate(form_list) if f in ['10-K', '10-Q']), -1)
    if idx_curr == -1: raise TickerFailure("no 10-K or 10-Q in recent SEC filings (foreign issuers file 20-F instead)")
        
    form_type = form_list[idx_curr]
    acc_curr = filings['accessionNumber'][idx_curr].replace('-', '')
    doc_curr = filings['primaryDocument'][idx_curr]
    date_curr = filings['filingDate'][idx_curr]
    cik_no_zeros = str(int(cik_padded))
    
    idx_prior = next((i for i in range(idx_curr + 1, len(form_list)) if form_list[i] in ['10-K', '10-Q']), -1)
    
    risk_regex = r'(?:item\s+1a\b[\.\:\s\-\—\xa0]*(?:risk\s+factors)?)(.*?)(?:item\s+(?:1b|2)\b[\.\:\s\-\—\xa0]|$)'
    mda_regex = r'(?:item\s+7\b[\.\:\s\-\—\xa0]*(?:management[\'\’]?s\s+discussion)?)(.*?)(?:item\s+(?:7a|8)\b[\.\:\s\-\—\xa0]|$)' if form_type == '10-K' else r'(?:item\s+2\b[\.\:\s\-\—\xa0]*(?:management[\'\’]?s\s+discussion)?)(.*?)(?:item\s+(?:3|4)\b[\.\:\s\-\—\xa0]|$)'
    
    url_curr = f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{acc_curr}/{doc_curr}"
    time.sleep(0.15)
    resp_curr = sec_get_request(url_curr, headers)
    if not resp_curr: raise TickerFailure(f"couldn't download the {form_type} filed {date_curr}, try again")
    html_curr = resp_curr.content
    text_clean_curr = re.sub(r'\s+', ' ', BeautifulSoup(html_curr, 'html.parser').get_text(separator=' ', strip=True))
    
    risk_raw_curr = max([m.group(1) for m in re.compile(risk_regex, re.I | re.S).finditer(text_clean_curr) if len(m.group(1).strip()) > 4000], key=len, default=text_clean_curr[5000:35000])
    mda_raw_curr = max([m.group(1) for m in re.compile(mda_regex, re.I | re.S).finditer(text_clean_curr) if len(m.group(1).strip()) > 4000], key=len, default=text_clean_curr[40000:80000])
    
    prior_risk_raw = "PRIOR YEAR FILING NOT AVAILABLE"
    if idx_prior != -1:
        try:
            acc_prior = filings['accessionNumber'][idx_prior].replace('-', '')
            doc_prior = filings['primaryDocument'][idx_prior]
            time.sleep(0.15)
            resp_prior = sec_get_request(f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{acc_prior}/{doc_prior}", headers)
            if resp_prior:
                text_clean_prior = re.sub(r'\s+', ' ', BeautifulSoup(resp_prior.content, 'html.parser').get_text(separator=' ', strip=True))
                prior_risk_raw = max([m.group(1) for m in re.compile(risk_regex, re.I | re.S).finditer(text_clean_prior) if len(m.group(1).strip()) > 4000], key=len, default=text_clean_prior[5000:35000])[:18000]
        except Exception: pass

    eight_k_texts, eight_k_dates, k8_count = "", [], 0
    for idx_form, f_type in enumerate(form_list):
        if f_type in ['8-K', '8-K/A'] and k8_count < 4:
            acc_8k = filings['accessionNumber'][idx_form].replace('-', '')
            doc_8k = filings['primaryDocument'][idx_form]
            date_8k = filings['filingDate'][idx_form]
            time.sleep(0.2)
            resp_8k = sec_get_request(f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{acc_8k}/{doc_8k}", headers)
            if resp_8k and resp_8k.status_code == 200:
                text_clean_8k = re.sub(r'\s+', ' ', BeautifulSoup(resp_8k.content, 'html.parser').get_text(separator=' ', strip=True))
                if len(text_clean_8k) > 100:
                    eight_k_texts += f"--- 8-K FILED ON {date_8k} ---\n{text_clean_8k[:4500]}\n\n"
                    eight_k_dates.append((date_8k, '8-K'))
                    k8_count += 1
            
    if not eight_k_texts.strip(): eight_k_texts = "NO RECENT 8-K FILINGS IDENTIFIED."
    financial_stats = get_comprehensive_financials(ticker.upper())

    return {
        "ticker": ticker.upper(), "company_name": company_name, "industry": industry_desc, "form_type": form_type,
        "risk": risk_raw_curr.strip()[:20000], "mda": mda_raw_curr.strip()[:20000], "prior_risk": prior_risk_raw.strip(),
        "eight_k": eight_k_texts, "cik": cik_no_zeros, "financials": financial_stats,
        "insider_velocity": insider_velocity, "event_markers": [(date_curr, form_type)] + eight_k_dates
    }

UNIFIED_EXTRACTION_TOOL = {
    "name": "record_comprehensive_firm_analysis",
    "description": "Record catalysts, vulnerabilities, recent 8-K material events, and executive Q&A.",
    "input_schema": {
        "type": "object",
        "properties": {
            "bull_items": {
                "type": "array",
                "items": {"type": "object", "properties": {"target": {"type": "string"}, "category": {"type": "string"}, "description": {"type": "string"}, "impact": {"type": "string", "enum": ["HIGH", "MEDIUM"]}, "quote": {"type": "string"}}, "required": ["target", "category", "description", "impact", "quote"]}
            },
            "bear_items": {
                "type": "array",
                "items": {"type": "object", "properties": {"target": {"type": "string"}, "category": {"type": "string"}, "description": {"type": "string"}, "impact": {"type": "string", "enum": ["HIGH", "MEDIUM"]}, "trend": {"type": "string", "enum": ["NEW", "ESCALATED", "STABLE"]}, "quote": {"type": "string"}}, "required": ["target", "category", "description", "impact", "trend", "quote"]}
            },
            "eight_k_insights": {
                "type": "array",
                "items": {"type": "object", "properties": {"event_date": {"type": "string"}, "category": {"type": "string", "enum": ["LEADERSHIP", "M&A / CONTRACT", "FINANCIAL", "COMPLIANCE", "OPERATIONAL"]}, "takeaway": {"type": "string"}, "quote": {"type": "string"}}, "required": ["event_date", "category", "takeaway", "quote"]}
            },
            "strategic_questions": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["bull_items", "bear_items", "eight_k_insights", "strategic_questions"]
    }
}

@st.cache_data(ttl=3600, show_spinner=False)
def extract_unified_profile(sec_payload: dict) -> dict:
    ticker, f_type = sec_payload["ticker"], sec_payload["form_type"]
    prompt = f"""
    You are an elite equity research portfolio manager evaluating SEC disclosures ({f_type}) for {ticker}.
    1. Isolate CapEx ROI, supply chain bottlenecks, vendor concentrations, tariff/working-capital timing.
    2. Perform YoY Delta analysis on Item 1A Risk Factors.
    3. Analyze Recent 8-K Filings to extract material corporate events.
    4. Generate 3 highly targeted, institutional executive meeting questions.

    === MD&A ({f_type}) ===
    {sec_payload['mda']}
    === RISK FACTORS ({f_type}) ===
    {sec_payload['risk']}
    === PRIOR PERIOD RISK FACTORS ===
    {sec_payload['prior_risk']}
    === RECENT SEC FORM 8-K ===
    {sec_payload['eight_k']}
    """
    try:
        response = client.messages.create(
            model="claude-sonnet-5", max_tokens=4000,
            tools=[UNIFIED_EXTRACTION_TOOL], tool_choice={"type": "tool", "name": "record_comprehensive_firm_analysis"},
            messages=[{"role": "user", "content": prompt}]
        )
    except APIError as e:
        raise TickerFailure(f"Anthropic API error ({type(e).__name__}), try again") from e

    for block in response.content:
        if block.type == "tool_use":
            raw_data = block.input
            bear_sorted = sorted(raw_data.get("bear_items", []), key=lambda x: {"HIGH": 0, "MEDIUM": 1}.get(x.get("impact", "MEDIUM").upper(), 2))
            bull_sorted = sorted(raw_data.get("bull_items", []), key=lambda x: {"HIGH": 0, "MEDIUM": 1}.get(x.get("impact", "MEDIUM").upper(), 2))
            high_threats = sum(1 for e in bear_sorted if e.get("impact") == "HIGH")
            return {
                "ticker": ticker, "company_name": sec_payload["company_name"], "industry": sec_payload["industry"], "form_type": f_type,
                "bear": bear_sorted, "bull": bull_sorted, "eight_k": raw_data.get("eight_k_insights", []),
                "questions": raw_data.get("strategic_questions", []), "risk_score": min(10.0, round((high_threats * 1.5) + ((len(bear_sorted) - high_threats) * 0.5), 1)),
                "financials": sec_payload["financials"], "insider_velocity": sec_payload["insider_velocity"], "event_markers": sec_payload["event_markers"]
            }
    raise TickerFailure("Anthropic returned no analysis, try again")


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
    wb = openpyxl.Workbook()
    header_fill, header_font = PatternFill(start_color="1e222d", end_color="1e222d", fill_type="solid"), Font(color="ffffff", bold=True)
    
    ws_quant = wb.active
    ws_quant.title = "Financial Model Feed"
    ws_quant.append(['Ticker', 'Company Name', 'Gross Margin', 'Operating Margin', 'Net Margin', 'ROE', 'Debt to Equity', 'Free Cash Flow', 'EBITDA'])
    for p in profiles:
        ws_quant.append([p['ticker'], p['company_name'], p['financials']['gross_margin'], p['financials']['op_margin'], p['financials']['profit_margin'], p['financials']['roe'], p['financials']['debt_to_equity'], p['financials']['fcf'], p['financials']['ebitda']])

    ws_bull = wb.create_sheet(title="CapEx & Catalysts")
    ws_bull.append(['Ticker', 'Category', 'Target Initiative', 'Impact', 'Strategic Thesis', 'Filing Excerpt'])
    for p in profiles:
        for b in p['bull']:
            ws_bull.append([p['ticker'], b.get('category',''), b.get('target',''), b.get('impact',''), b.get('description',''), b.get('quote','')])

    ws_bear = wb.create_sheet(title="Supply Chain & Risks")
    ws_bear.append(['Ticker', 'Category', 'Target Risk', 'Impact', 'YoY Trend', 'Vulnerability', 'Filing Excerpt'])
    for p in profiles:
        for b in p['bear']:
            ws_bear.append([p['ticker'], b.get('category',''), b.get('target',''), b.get('impact',''), b.get('trend','STABLE'), b.get('description',''), b.get('quote','')])

    for ws in wb.worksheets:
        for cell in ws[1]: cell.fill, cell.font = header_fill, header_font
        for col in ws.columns: ws.column_dimensions[col[0].column_letter].width = 25
    
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

# --- HEADER ---
st.markdown(
    "<h1 class='irt-title'>Institutional Research Terminal</h1>"
    "<p class='irt-subtitle'>SEC filings, market data and AI summaries for up to five stocks. "
    "A research tool, not investment advice.</p>",
    unsafe_allow_html=True,
)

# --- TOOLBAR: TICKER PICKER, ONE PRIMARY ACTION, EXAMPLE PRESETS ---
sec_directory, used_fallback = load_sec_directory()
ticker_names = dict(zip(sec_directory["ticker"], sec_directory["name"]))

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


# --- RESULTS RENDERING ---
def metric_groups(p: dict) -> list:
    f = p["financials"]
    yahoo, unstated = "Yahoo Finance", "Yahoo Finance · period not stated"
    return [
        ("Market", [("Price", f["price"], yahoo), ("Market cap", f["mcap"], yahoo)]),
        ("Valuation and profitability", [("Forward P/E", f["fpe"], yahoo), ("Gross margin", f["gross_margin"], unstated),
                                         ("Free cash flow", f["fcf"], unstated)]),
        ("Insider filings", [("Form 4, last 90 days", str(p["insider_velocity"]), "SEC EDGAR · count of filings")]),
    ]


def render_profile(p: dict) -> None:
    st.markdown(ui.company_header(p["ticker"], p["company_name"], p["industry"], p["form_type"])
                + ui.metric_tiles(metric_groups(p)), unsafe_allow_html=True)

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

    col_bull, col_bear = st.columns(2, gap="large")
    with col_bull:
        st.markdown(ui.section_header("Catalysts", len(p["bull"]), "AI summary of the filings. Open an excerpt to check it.")
                    + "".join(ui.catalyst_card(i) for i in p["bull"]), unsafe_allow_html=True)
    with col_bear:
        st.markdown(ui.section_header("Risks", len(p["bear"]), "Trend labels compare against the prior filing and aren't verified yet.")
                    + "".join(ui.risk_card(i) for i in p["bear"]), unsafe_allow_html=True)

    events_html = ui.event_rows(p["eight_k"]) if p["eight_k"] else "<p class='irt-note'>No recent material events found.</p>"
    questions = "".join(f"<li>{ui.esc(q)}</li>" for q in p["questions"])
    st.markdown(ui.section_header("8-K events", len(p["eight_k"])) + events_html
                + ui.section_header("Questions for management", len(p["questions"]))
                + f"<ol class='irt-questions'>{questions}</ol>", unsafe_allow_html=True)


def render_failure(ticker: str, reason: str) -> None:
    st.markdown(f"<div class='irt-card tone-negative'><div class='irt-card-title'>Couldn't analyze {ui.esc(ticker)}</div>"
                f"<p class='irt-card-body'>{ui.esc(reason)}</p></div>", unsafe_allow_html=True)


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
        try:
            statuses[t] = ("working", "reading SEC filings")
            strip.markdown(ui.progress_strip(statuses), unsafe_allow_html=True)
            slots[t].markdown(ui.skeleton(t, "Reading SEC filings (step 1 of 2)"), unsafe_allow_html=True)
            payload = fetch_firm_data(t)

            statuses[t] = ("working", "summarizing with Claude")
            strip.markdown(ui.progress_strip(statuses), unsafe_allow_html=True)
            slots[t].markdown(ui.skeleton(t, "Summarizing filings with Claude (step 2 of 2)"), unsafe_allow_html=True)
            profiles[t] = extract_unified_profile(payload)
            statuses[t] = ("done", f"{time.time() - started:.0f}s")
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
        "run_at": datetime.now(ZoneInfo("America/New_York")),
    }
    st.rerun()  # redraw once from session state: summary row and download button on top

# --- SAVED RESULTS ---
# st.rerun() above stops this run, so this section only draws on the next run (and every run after)
results = st.session_state.get("results")
if results:
    profiles, failures = results["profiles"], results["failures"]
    done = [t for t in results["tickers"] if t in profiles]

    col_sum, col_dl = st.columns([4, 1])
    col_sum.markdown(
        f"<p class='irt-subtitle'>Results for {ui.esc(', '.join(results['tickers']))} · "
        f"run {results['run_at']:%b %d, %I:%M %p} ET · {len(done)} of {len(results['tickers'])} succeeded</p>",
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
        "A run reads several filings and takes about 35 seconds per ticker the first time.</p></div>",
        unsafe_allow_html=True)
