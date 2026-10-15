"""Financial questions first; filing mechanics remain available in the evidence disclosure.

The notes are selected, manually checked disclosures, not an exhaustive obligations list. Each belongs to the
pilot's specified 10-Q and remains separate from borrowing and ratios (docs/pilot_evidence_*.md).
"""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from ui import esc

NOTES = {
    "LLY": [
        {"name": "Pending AtaiBeckley acquisition", "amount": "Approximately $2.8B",
         "date": "2026-06-30", "kind": "Future commitment", "location": "10-Q MD&A, p. 31",
         "detail": "Potential payment at closing, subject to closing conditions. Not recognized as borrowing."},
        {"name": "Venture fund commitments", "amount": "Approximately $806M",
         "date": "2026-06-30", "kind": "Unfunded commitment", "location": "10-Q MD&A, p. 31; Note 8",
         "detail": "Expected to be paid over up to ten years. Not recognized as borrowing."},
    ],
    "ORCL": [
        {"name": "Leases not yet commenced", "amount": "$288B",
         "date": "2026-08-31", "kind": "Future commitment", "location": "10-Q Note 6, p. 13",
         "detail": "Substantially all data centers; expected to commence in fiscal 2027–2029 with 15–19 year terms. Not on the balance sheet or in the lease maturities table."},
        {"name": "Operating lease liabilities", "amount": "$34.621B",
         "date": "2026-08-31", "kind": "Recognized liability", "location": "10-Q Note 6, p. 12",
         "detail": "Recognized leases, separate from borrowing and from leases not yet commenced."},
        {"name": "Finance lease liabilities", "amount": "$9.185B",
         "date": "2026-08-31", "kind": "Recognized liability", "location": "10-Q Note 6, p. 12",
         "detail": "Shown separately under this review's borrowing definition; excluded from baseline gross debt."},
        {"name": "Purchase and other obligations", "amount": "$34.150B",
         "date": "2026-08-31", "kind": "Unrecorded commitment", "location": "10-Q Note 6, p. 13",
         "detail": "Primarily cloud infrastructure components and data center power. Overlap with other commitments is not established; no combined total is presented."},
    ],
    "VST": [
        {"name": "Nuveen final payment", "amount": "$631M due Dec 31, 2026",
         "date": "2026-06-30", "kind": "Recognized purchase obligation", "location": "10-Q Note 12, p. 28",
         "detail": "Principal and interest on the minority-interest purchase. The current balance-sheet obligation is $613M. Both describe the same obligation; neither is added to baseline borrowing."},
        {"name": "Helix initial commitment", "amount": "$500M",
         "date": "2026-06-30", "kind": "Callable investment commitment", "location": "10-Q MD&A, p. 69; Note 7, p. 15",
         "detail": "Remains callable by the fund's general partner, who determines timing and amount. Amount funded to date is not separately disclosed."},
        {"name": "Helix additional commitment", "amount": "Up to $500M",
         "date": "2026-06-30", "kind": "Conditional investment commitment", "location": "10-Q MD&A, p. 69; Note 7, p. 15",
         "detail": "The specified milestones had not occurred at June 30. Vistra may also elect to fund it regardless of those milestones."},
    ],
}

LIMITS = {
    "LLY": "Lease liabilities at June 30 are Unavailable. Selection of major commitments is not complete; contingencies, tax, collaboration and investment notes need further review. Later financing findings are not loaded in this saved view.",
    "ORCL": "Commercial paper is not separately disclosed in this 10-Q. The capex-financing balance and the later status of the 10-K's $3.3B lessor guarantee remain unresolved. Later financing findings are not loaded in this saved view.",
    "VST": "June 30 lease liabilities are Unavailable. Derivatives, litigation and the remaining retirement-obligation detail need further review. Credit-support overlaps are unresolved; the selected notes below are not a complete obligations list.",
}

CSS = """<style>
.lr-review {max-width:1180px; margin:8px auto 0; color:var(--text); font-variant-numeric:tabular-nums;}
.lr-review * {box-sizing:border-box;}
.lr-review h2 {font-size:1.5rem;line-height:1.3;letter-spacing:-.02em;padding:0;margin:4px 0 7px;color:var(--text-strong);}
.lr-review h3 {font-size:1.05rem;line-height:1.4;margin:0 0 7px;padding:0;color:var(--text-strong);}
.lr-review p {font-size:.9rem;line-height:1.55;margin:8px 0;}
.lr-review .lr-meta {font-size:.78rem;color:var(--text-muted);line-height:1.5;}
.lr-lead {border-bottom:1px solid var(--border);padding:0 0 18px;}
.lr-lead .lr-answer {font-size:1.12rem;max-width:850px;color:var(--text-strong);margin-top:12px;}
.lr-summary {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;padding:18px 0;border-bottom:1px solid var(--border);}
.lr-stat-label {font-size:.8rem;color:var(--text-muted);}
.lr-stat-value {font-size:1.5rem;font-weight:650;line-height:1.5;color:var(--text-strong);}
.lr-stat-detail {font-size:.75rem;color:var(--text-muted);}
.lr-grid {display:grid;grid-template-columns:1.15fr 1fr;gap:30px;margin:24px 0;}
.lr-section {min-width:0;}
.lr-chart {margin:18px 0;}
.lr-bar-row {display:grid;grid-template-columns:115px minmax(40px,1fr) 85px;gap:12px;align-items:center;margin:12px 0;font-size:.8rem;}
.lr-bar-value {text-align:right;color:var(--text-strong);white-space:nowrap;}
.lr-track {display:grid;grid-template-columns:1fr 1fr;height:19px;}
.lr-half {display:flex;align-items:center;min-width:0;}
.lr-half:first-child {justify-content:flex-end;border-right:1px solid var(--border-strong);}
.lr-bar {display:block;height:12px;background:var(--text-muted);min-width:1px;}
.lr-row {display:flex;justify-content:space-between;gap:16px;border-bottom:1px solid var(--border);padding:10px 0;font-size:.85rem;}
.lr-row span {max-width:75%;}
.lr-row strong {white-space:nowrap;font-weight:600;}
.lr-ratios {display:grid;grid-template-columns:1fr 1fr;gap:18px;border-top:1px solid var(--border);padding-top:14px;margin-top:20px;}
.lr-ratios strong {display:block;font-size:1.2rem;color:var(--text-strong);}
.lr-obligations {border-top:1px solid var(--border);padding:22px 0 8px;}
.lr-obligation {display:grid;grid-template-columns:minmax(160px,1fr) minmax(0,2fr);gap:24px;border-bottom:1px solid var(--border);padding:14px 0;}
.lr-obligation p {margin:0 0 5px;}
.lr-obligation strong {color:var(--text-strong);}
.lr-limits {padding:15px 0 4px;}
.lr-review a {color:var(--link);}
.lr-review + .irt-evidence {max-width:1180px;margin:12px auto;}
@media(max-width:760px) {.lr-grid {grid-template-columns:1fr;gap:24px;} .lr-summary {grid-template-columns:repeat(2,minmax(0,1fr));} .lr-obligation {grid-template-columns:1fr;gap:4px;} .lr-review h2 {font-size:1.3rem;} .lr-bar-row {grid-template-columns:96px minmax(30px,1fr) 75px;gap:7px;} .lr-stat-value {font-size:1.3rem;}}
</style>"""


def money(value, digits=2):
    if value is None:
        return "Unavailable"
    magnitude = Decimal(str(abs(value)))
    if 0 < magnitude < 1_000_000_000:
        millions = (magnitude / 1_000_000).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return f"{'−' if value < 0 else ''}${millions:,.0f}M"
    billions = (magnitude / 1_000_000_000).quantize(Decimal(10) ** -digits, rounding=ROUND_HALF_UP)
    return f"{'−' if value < 0 else ''}${billions:,.{digits}f}B"


def pct(metric):
    return "Unavailable" if metric["value"] is None else f"{metric['value']:.1%}"


def headline(snapshot):
    m = snapshot["metrics"]
    fcf = m["free_cash_flow"]["value"]
    if fcf is None:
        return "Cash generation could not be established from the checked inputs."
    if fcf < 0:
        return f"Reported capital spending exceeded operating cash flow by {money(-fcf)}."
    if fcf == 0:
        return "Operating cash flow equalled reported capital spending."
    return f"Operating cash flow exceeded reported capital spending by {money(fcf)}."


def render(snapshot):
    """Deterministic, source-linked explanations; no ratings or implied repayment assumptions."""
    m = snapshot["metrics"]
    end = date.fromisoformat(m["cash"]["period_end"]).strftime("%b %d, %Y")
    source = snapshot["source_url"]
    output = CSS + '<section class="lr-review">'
    output += f'<header class="lr-lead"><div class="lr-meta">{esc(snapshot["ticker"])} · Debt and liquidity review</div>'
    output += f'<h2>{esc(snapshot["company_name"])}</h2><div class="lr-meta">Balance sheet: {esc(end)} · '
    output += f'<a href="{esc(source)}" target="_blank" rel="noopener noreferrer">Source 10-Q</a> · Saved review, Oct 14, 2026</div>'
    output += f'<p class="lr-answer">{esc(headline(snapshot))}</p>'
    output += '<p class="lr-meta">Cash flows cover the trailing twelve months to this balance-sheet date. Borrowing is at carrying amount and excludes leases. Figures are rounded; evidence retains exact inputs.</p></header>'
    output += '<div class="lr-summary">'
    for label, value, detail in (
        ("Cash and equivalents", money(m["cash"]["value"]), "Excludes restricted cash"),
        ("Baseline gross debt", money(m["gross_debt"]["value"]), "Borrowing, excluding leases"),
        ("Net debt", money(m["net_debt"]["value"]), "Gross debt less cash"),
        ("Current ratio", f'{m["current_ratio"]["value"]:.2f}x' if m["current_ratio"]["value"] is not None else "Unavailable", "Current assets / liabilities"),
    ):
        output += f'<div><div class="lr-stat-label">{esc(label)}</div><div class="lr-stat-value">{esc(value)}</div><div class="lr-stat-detail">{esc(detail)}</div></div>'
    output += '</div><div class="lr-grid"><section class="lr-section"><h3>What remained after capital spending?</h3>'
    output += f'<div class="lr-meta">TTM ended {esc(end)} · USD billions · 10-K and 10-Q cash-flow statements</div>'
    bars = [("Operating cash flow", m["operating_cash_flow"]["value"]),
            ("Capital spending", -m["capital_spending"]["value"] if m["capital_spending"]["value"] is not None else None),
            ("Free cash flow", m["free_cash_flow"]["value"])]
    maximum = max((abs(v) for _, v in bars if v is not None), default=1) or 1
    output += '<div class="lr-chart">'
    for name, value in bars:
        width = abs(value) / maximum * 100 if value is not None else 0
        bar = f'<span class="lr-bar" style="width:{width:.4f}%"></span>' if value else ''
        output += (f'<div class="lr-bar-row"><span>{esc(name)}</span><div class="lr-track" aria-hidden="true">'
                   f'<div class="lr-half">{bar if value is not None and value < 0 else ""}</div>'
                   f'<div class="lr-half">{bar if value is not None and value > 0 else ""}</div></div>'
                   f'<span class="lr-bar-value">{esc(money(value))}</span></div>')
    output += '</div>'
    output += f'<p class="lr-meta">{esc(m["free_cash_flow"]["notes"][0])}</p>'
    output += '<div class="lr-ratios">'
    for key, label in (("ocf_to_debt", "TTM operating cash flow / debt"), ("fcf_to_debt", "TTM free cash flow / debt")):
        output += f'<div><span class="lr-stat-label">{esc(label)}</span><strong>{esc(pct(m[key]))}</strong></div>'
    output += '</div><p class="lr-meta">Historical flows relative to period-end borrowing; these percentages are not repayment forecasts. FCF excludes acquisitions, dividends and other cash uses.</p></section>'
    output += '<section class="lr-section"><h3>What makes up the borrowing?</h3>'
    output += f'<div class="lr-meta">At {esc(end)} · amounts in B or M · same 10-Q as the balance sheet</div>'
    for fact in m["gross_debt"]["inputs"]:
        label = fact["label"].replace("Long-term debt, less amounts due currently", "Long-term debt, noncurrent")
        value = money(fact["value"], 3)
        if fact["value"] == 0:
            value = "$0 · reported"
        output += f'<div class="lr-row"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>'
    assets = m["current_ratio"]["inputs"]["current_assets"]
    liabilities = m["current_ratio"]["inputs"]["current_liabilities"]
    if assets["value"] is not None and liabilities["value"] is not None:
        gap = assets["value"] - liabilities["value"]
        direction = "exceeded" if gap >= 0 else "were below"
        output += (f'<p>Current assets of {esc(money(assets["value"]))} {direction} current liabilities of '
                   f'{esc(money(liabilities["value"]))} by {esc(money(abs(gap)))}.</p>')
    output += '<p class="lr-meta">Current assets include items other than cash. This comparison does not establish whether specific payments can be met; a maturity schedule and financing terms are still needed.</p></section></div>'
    output += '<section class="lr-obligations"><h3>What sits outside baseline borrowing?</h3><p class="lr-meta">Selected disclosures, each shown separately. Commitments are not all payable now and are not added to debt or to each other.</p>'
    for item in NOTES[snapshot["ticker"]]:
        output += (f'<article class="lr-obligation"><div><p><strong>{esc(item["name"])}</strong></p>'
                   f'<p>{esc(item["amount"])}</p><div class="lr-meta">As of {esc(item["date"])} · {esc(item["kind"])}</div></div>'
                   f'<div><p>{esc(item["detail"])}</p><a class="lr-meta" href="{esc(source)}" target="_blank" rel="noopener noreferrer">{esc(item["location"])}</a></div></article>')
    output += '</section><section class="lr-limits"><h3>What remains unresolved?</h3>'
    output += f'<p class="lr-meta">{esc(LIMITS[snapshot["ticker"]])} Interest coverage and a full debt maturity review are not included.</p></section></section>'
    return output


def evidence_html(snapshot: dict) -> str:
    """Read-only display; every input keeps its filing and selection information."""
    import ui
    from liquidity_pilot import leaf_inputs
    metrics = snapshot["metrics"]
    output = '<details class="irt-evidence"><summary>Calculations and filing evidence</summary>'
    for metric in metrics.values():
        output += f'<p><strong>{ui.esc(metric["label"])}</strong>'
        if metric.get("formula"):
            output += f' · {ui.esc(metric["formula"])}'
        if metric["value"] is None:
            output += f'<br>Unavailable: {ui.esc(metric["detail"])}'
        for note in metric.get("notes", []):
            output += f'<br>{ui.esc(note)}'
        output += '</p><ul class="irt-ol" style="overflow-wrap:anywhere">'
        # Ratios and net debt reference the metrics already documented above.
        facts = [] if metric.get("unit") == "fraction" or metric["label"] in {"Net debt", "Free cash flow"} else leaf_inputs(metric)
        for fact in facts:
            value = f"{fact['value']:,.0f} USD" if fact["value"] is not None else "Unavailable"
            context = (f" · Context {fact['context_id']}, scale {fact['scale']}, decimals {fact['decimals']}"
                       if fact.get("context_id") else "")
            period = ((fact["period_start"] + " to ") if fact.get("period_start") else "") + fact["period_end"]
            output += (f'<li>{ui.esc(fact["label"])}: {ui.esc(value)} · {ui.esc(fact["tag"])}<br>'
                       f'Period {ui.esc(period)} · {ui.esc(fact.get("form") or "Form unavailable")} '
                       f'filed {ui.esc(fact.get("filed") or "Unavailable")} · '
                       f'{ui.esc(fact.get("accession") or "Accession unavailable")}<br>'
                       f'{ui.esc(fact.get("selection_rule") or fact.get("detail", ""))}{ui.esc(context)}'
                       f'<br><a href="{ui.esc(fact.get("source_url") or snapshot["source_url"])}" target="_blank" rel="noopener noreferrer">Source filing</a></li>')
        output += '</ul>'
    debt = metrics["gross_debt"]
    caveats = [*debt.get("caveats", []), *debt.get("notes", [])]
    if debt.get("not_added"):
        caveats.append("Excluded from baseline debt: " + debt["not_added"])
    output += ''.join(f'<p class="irt-note">{ui.esc(n)}</p>' for n in caveats)
    return output + '</details>'



def workbook(snapshots: list[dict]) -> bytes:
    """A row per reported input, with Excel formulas referencing those rows for derived results."""
    from io import BytesIO
    from liquidity_pilot import PILOTS, leaf_inputs
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    wb = Workbook()
    ws = wb.active
    ws.title = "Debt and liquidity"
    ws.append(["Ticker", "Metric", "Value", "Unit", "Period end", "Formula", "Status", "Notes"])
    raw = wb.create_sheet("Liquidity inputs")
    raw.append(["Ticker", "Metric", "Reported input", "Value (USD)", "Period end", "Form", "Filed",
                "Accession", "Tag", "Selection rule", "Source document", "Notes",
                "Context ID", "Scale", "Decimals", "Period start", "TTM role", "Coefficient"])
    usd_format = '#,##0,,;(#,##0,,);"-"'
    for snapshot in snapshots:
        metric_rows = {}
        for key, metric in snapshot["metrics"].items():
            metric_rows[key] = ws.max_row + 1
            refs = []
            # Net debt references the two already exported metrics; no duplicate input rows.
            derived_refs = {"net_debt": ("gross_debt", "cash", "-"),
                            "free_cash_flow": ("operating_cash_flow", "capital_spending", "-"),
                            "ocf_to_debt": ("operating_cash_flow", "gross_debt", "/"),
                            "fcf_to_debt": ("free_cash_flow", "gross_debt", "/")}
            if key not in derived_refs:
                for fact in leaf_inputs(metric):
                    raw.append([snapshot["ticker"], metric["label"], fact["label"], fact["value"],
                                fact["period_end"], fact.get("form"), fact.get("filed"), fact.get("accession"),
                                fact.get("tag"), fact.get("selection_rule"), fact.get("source_url") or snapshot["source_url"],
                                "; ".join(fact.get("notes", [])) or fact.get("detail", ""),
                                fact.get("context_id"), fact.get("scale"), fact.get("decimals"),
                                fact.get("period_start"), fact.get("role"), fact.get("coefficient")])
                    raw.cell(raw.max_row, 4).number_format = usd_format
                    raw.cell(raw.max_row, 4).font = Font(name="Arial", size=10, color="0000FF")
                    refs.append((fact.get("coefficient", 1), f"'Liquidity inputs'!D{raw.max_row}"))
            value = None
            if metric["value"] is not None:
                if key in derived_refs:
                    a, b, op = derived_refs[key]
                    value = f"=C{metric_rows[a]}{op}C{metric_rows[b]}"
                elif key == "current_ratio":
                    value = "=" + "/".join(ref for _, ref in refs)
                else:
                    value = "=" + refs[0][1] + "".join(("-" if sign < 0 else "+") + ref for sign, ref in refs[1:])
            notes = [*metric.get("notes", []), *metric.get("caveats", [])]
            if metric.get("not_added"):
                notes.append("Excluded: " + metric["not_added"])
            ws.append([snapshot["ticker"], metric["label"], value,
                       "USD (displayed in millions)" if metric["unit"] == "USD" else
                       "fraction (displayed as %)" if metric["unit"] == "fraction" else "ratio",
                       metric["period_end"], metric.get("formula") or metric.get("tag"),
                       ("Reported" if key == "cash" else "Calculated") if metric["value"] is not None else "Unavailable",
                       "; ".join(notes) or metric.get("detail", "")])
            ws.cell(ws.max_row, 3).number_format = (usd_format if metric["unit"] == "USD" else
                                                   '0.0%;(0.0%);"-"' if metric["unit"] == "fraction" else '0.00"x"')
            if key == "cash":
                ws.cell(ws.max_row, 3).font = Font(name="Arial", size=10, color="008000")
    about = wb.create_sheet("About")
    about.append(["Item", "Description"])
    about.append(["Snapshot", "Saved pilot evidence checked October 14, 2026. Not live data or investment advice."])
    about.append(["Units", "Dollar inputs are stored in USD and displayed in millions. Ratios are multiples."])
    about.append(["Calculation", "Excel recalculates formulas when opened. Each formula traces to reported inputs."])
    about.append(["Colors", "Blue numbers are reported inputs. Green formulas link a reported value from another sheet. Black formulas calculate results."])
    about.append(["Scope", "Baseline borrowing excludes leases. FCF subtracts the reported capital-spending line from OCF; acquisitions are excluded. Historical flow/debt ratios are not repayment forecasts. This is not a complete obligations analysis."])
    obligations = wb.create_sheet("Other obligations")
    obligations.append(["Ticker", "Disclosure", "Amount as disclosed", "Reporting date", "Classification", "Filing location", "Accession", "Source", "Notes"])
    for snapshot in snapshots:
        for item in NOTES[snapshot["ticker"]]:
            obligations.append([snapshot["ticker"], item["name"], item["amount"], item["date"], item["kind"],
                                item["location"], PILOTS[snapshot["ticker"]]["accession"], snapshot["source_url"], item["detail"]])
    for sheet in wb:
        sheet.sheet_view.showGridLines = False
        sheet.freeze_panes = "A2"
        for row in sheet:
            for cell in row:
                color = cell.font.color.rgb if cell.font.color and cell.font.color.type == "rgb" else "000000"
                cell.font = Font(name="Arial", size=10, color=color, bold=cell.row == 1)
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = 23
    ws.column_dimensions["H"].width = 65
    raw.column_dimensions["K"].width = 55
    raw.column_dimensions["L"].width = 55
    about.column_dimensions["B"].width = 90
    out = BytesIO()
    wb.save(out)
    return out.getvalue()



def render_app() -> None:
    """Direct app entry point; the complete view loads together rather than through a cached legacy helper."""
    import json
    import streamlit as st
    from liquidity_pilot import SAMPLE, financing_html
    panel = st.expander("Debt and liquidity · company reviews",
                        key="liquidity_pilot_open", on_change="rerun")
    # Closed pilots need no workbook build and contribute no hidden tabs to the existing analysis.
    if not panel.open:
        return
    with panel:
        try:
            saved = json.loads(SAMPLE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            st.error("The saved liquidity pilot could not be loaded.")
            return
        st.caption("Saved filing review · checked Oct 14, 2026 · no live or paid request")
        st.download_button("Download review and evidence", workbook(saved["snapshots"]),
                           file_name="Liquidity_Pilot_2026-10-14.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        for snapshot, tab in zip(saved["snapshots"], st.tabs([s["ticker"] for s in saved["snapshots"]])):
            with tab:
                st.markdown(render(snapshot) + evidence_html(snapshot) + (financing_html(snapshot) if snapshot["ticker"] == "VST" else ""), unsafe_allow_html=True)
