import os
import json
import requests
import re
import base64
import time
import concurrent.futures
import openpyxl
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from openpyxl.styles import Font, PatternFill, Alignment
from io import BytesIO
from datetime import datetime
from bs4 import BeautifulSoup
from anthropic import Anthropic
import streamlit as st

# --- STREAMLIT PAGE CONFIG ---
st.set_page_config(page_title="Institutional Research Terminal", layout="wide", initial_sidebar_state="collapsed")

# Secure Key Retrieval via Streamlit Secrets
try:
    API_KEY = st.secrets["ANTHROPIC_API_KEY"]
    client = Anthropic(api_key=API_KEY, timeout=60.0)
except Exception as e:
    st.error("ANTHROPIC_API_KEY secret not detected. Please add it to Streamlit Secrets.")
    st.stop()

# --- BACKEND FUNCTIONS (Unchanged logic, wrapped in st.cache_data for speed) ---
@st.cache_data(ttl=3600)
def get_comprehensive_financials(ticker: str) -> dict:
    try:
        tkr = yf.Ticker(ticker)
        info = tkr.info
        
        mcap = info.get('marketCap', 0)
        if mcap >= 1e12: mcap_str = f"${mcap/1e12:.2f}T"
        elif mcap >= 1e9: mcap_str = f"${mcap/1e9:.2f}B"
        elif mcap > 0: mcap_str = f"${mcap/1e6:.2f}M"
        else: mcap_str = "N/A"
        
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
        
        return {
            "mcap": mcap_str, "price": price_str, "fpe": fpe_str, "rev_growth": rev_str,
            "gross_margin": gross_margin, "op_margin": op_margin, "profit_margin": profit_margin,
            "roe": roe, "debt_to_equity": debt_to_equity, "fcf": fcf_str, "ebitda": ebitda_str
        }
    except Exception:
        return {k: "N/A" for k in ["mcap", "price", "fpe", "rev_growth", "gross_margin", "op_margin", "profit_margin", "roe", "debt_to_equity", "fcf", "ebitda"]}

def sec_get_request(url: str, headers: dict, retries: int = 3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200: return resp
            elif resp.status_code == 429: time.sleep(1.5 * (attempt + 1))
        except Exception: time.sleep(1.0)
    return None

@st.cache_data(ttl=3600)
def fetch_firm_data(ticker: str) -> dict:
    headers = {'User-Agent': f'ResearchAnalytics analyst_{ticker.lower()}@firmanalytics.org'}
    tickers_url = "https://www.sec.gov/files/company_tickers.json"
    
    try:
        resp = sec_get_request(tickers_url, headers)
        if not resp: return None
        data = resp.json()
        
        cik_padded = next((str(v['cik_str']).zfill(10) for v in data.values() if v['ticker'].upper() == ticker.upper()), None)
        if not cik_padded: return None
            
        subs_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        time.sleep(0.15)
        subs_resp = sec_get_request(subs_url, headers)
        if not subs_resp: return None
        subs_data = subs_resp.json()
        filings = subs_data['filings']['recent']
        
        company_name = subs_data.get('name', ticker.upper()).title()
        industry_desc = subs_data.get('sicDescription', 'Public Issuer').title()
        form_list = filings['form']
        
        form_4_dates = [filings['filingDate'][i] for i, f in enumerate(form_list) if f in ['4', '4/A']]
        recent_4s = [d for d in form_4_dates if (datetime.now() - datetime.strptime(d, '%Y-%m-%d')).days <= 90]
        insider_velocity = len(recent_4s)
        
        idx_curr = next((i for i, f in enumerate(form_list) if f in ['10-K', '10-Q']), -1)
        if idx_curr == -1: return None
            
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
        html_curr = resp_curr.content if resp_curr else b""
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
    except Exception as e: return None

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

@st.cache_data(ttl=3600)
def extract_unified_profile(sec_payload: dict) -> dict:
    if not sec_payload: return None
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
        return None
    except Exception: return None

def generate_interactive_chart(ticker, events):
    try:
        hist = yf.Ticker(ticker).history(period="6mo")
        if hist.empty: return None
        
        fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], increasing_line_color='#4ade80', decreasing_line_color='#f87171', name='Price')])
        
        if events:
            e_dates, e_labels, y_vals = [], [], []
            for date_str, label in events:
                try:
                    dt = pd.to_datetime(date_str).tz_localize(hist.index.tz)
                    if dt in hist.index: y_val = hist.loc[dt]['High'] * 1.02
                    else: y_val = hist['High'].max()
                    e_dates.append(dt); e_labels.append(label); y_vals.append(y_val)
                except: pass
            
            if e_dates:
                fig.add_trace(go.Scatter(x=e_dates, y=y_vals, mode='markers+text', marker=dict(symbol='triangle-down', size=12, color='#60a5fa'), text=e_labels, textposition='top center', textfont=dict(color='#60a5fa', size=11, family="monospace"), name='SEC Event'))
                
        fig.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=10, b=0), height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_rangeslider_visible=False, showlegend=False, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#27272a'))
        return fig
    except Exception: return None

def generate_excel(profiles):
    wb = openpyxl.Workbook()
    header_fill, header_font = PatternFill(start_color="18181b", end_color="18181b", fill_type="solid"), Font(color="ffffff", bold=True)
    
    ws_quant = wb.active
    ws_quant.title = "Financial Model Feed"
    ws_quant.append(['Ticker', 'Company Name', 'Gross Margin', 'Operating Margin', 'Net Margin', 'ROE', 'Debt to Equity', 'Free Cash Flow', 'EBITDA'])
    for p in profiles: ws_quant.append([p['ticker'], p['company_name'], p['financials']['gross_margin'], p['financials']['op_margin'], p['financials']['profit_margin'], p['financials']['roe'], p['financials']['debt_to_equity'], p['financials']['fcf'], p['financials']['ebitda']])

    ws_bull = wb.create_sheet(title="CapEx & Catalysts")
    ws_bull.append(['Ticker', 'Category', 'Target Initiative', 'Impact', 'Strategic Thesis', 'Filing Excerpt'])
    for p in profiles:
        for b in p['bull']: ws_bull.append([p['ticker'], b.get('category',''), b.get('target',''), b.get('impact',''), b.get('description',''), b.get('quote','')])

    ws_bear = wb.create_sheet(title="Supply Chain & Risks")
    ws_bear.append(['Ticker', 'Category', 'Target Risk', 'Impact', 'YoY Trend', 'Vulnerability', 'Filing Excerpt'])
    for p in profiles:
        for b in p['bear']: ws_bear.append([p['ticker'], b.get('category',''), b.get('target',''), b.get('impact',''), b.get('trend','STABLE'), b.get('description',''), b.get('quote','')])

    for ws in wb.worksheets:
        for cell in ws[1]: cell.fill, cell.font = header_fill, header_font
        for col in ws.columns: ws.column_dimensions[col[0].column_letter].width = 25
    
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

# --- STREAMLIT UI ---
st.title("Institutional Research Terminal V5.0")
st.markdown("Event-Driven Interactive Charting + Form 4 Insider Tracking + CapEx/Supply Chain Engine", unsafe_allow_html=True)

tickers_input = st.text_input("Target Equities (comma separated):", value="FAST, STRL")

if st.button("Generate Tear Sheet"):
    raw_list = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
    if raw_list:
        with st.spinner("Compiling institutional SEC disclosures and mapping event logic..."):
            profiles = []
            for t in raw_list:
                sec_data = fetch_firm_data(t)
                if sec_data:
                    prof = extract_unified_profile(sec_data)
                    if prof: profiles.append(prof)
            
            if profiles:
                st.success("Analysis Complete.")
                
                # Render UI
                for p in profiles:
                    f = p['financials']
                    ins_vel = p['insider_velocity']
                    ins_col = "red" if ins_vel > 5 else ("orange" if ins_vel > 0 else "gray")
                    
                    with st.container():
                        st.markdown(f"### {p['ticker']} - {p['company_name']}")
                        cols = st.columns(6)
                        cols[0].metric("Insider 90D", str(ins_vel))
                        cols[1].metric("Price", f['price'])
                        cols[2].metric("Fwd P/E", f['fpe'])
                        cols[3].metric("Gross Mgn", f['gross_margin'])
                        cols[4].metric("FCF", f['fcf'])
                        cols[5].metric("Source", p['form_type'])
                        
                        chart_fig = generate_interactive_chart(p['ticker'], p['event_markers'])
                        if chart_fig: st.plotly_chart(chart_fig, use_container_width=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("CapEx & Growth Catalysts")
                            for item in p['bull']:
                                st.info(f"**{item['target']}** ({item['impact']})\n\n{item['description']}\n\n*{item['quote']}*")
                        with col2:
                            st.subheader("Supply Chain & Vulnerabilities")
                            for item in p['bear']:
                                st.warning(f"**{item['target']}** ({item['impact']} | {item.get('trend', 'STABLE')})\n\n{item['description']}\n\n*{item['quote']}*")
                        
                        st.subheader("SEC Form 8-K Material Events")
                        if not p['eight_k']:
                            st.write("No recent material events found.")
                        else:
                            e_cols = st.columns(min(3, len(p['eight_k'])))
                            for idx, event in enumerate(p['eight_k']):
                                with e_cols[idx % 3]:
                                    st.success(f"**{event['event_date']}** | {event['category']}\n\n{event['takeaway']}")
                        
                        st.subheader("Executive Q&A / Meeting Prep")
                        for q in p['questions']: st.markdown(f"- {q}")
                        
                        st.divider()

                # Generate Excel
                excel_data = generate_excel(profiles)
                st.download_button(label="📊 Download Quant Workbook (.xlsx)", data=excel_data, file_name="Institutional_Model.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
