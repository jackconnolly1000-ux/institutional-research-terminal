"""Dated pilot snapshots built from the tested selectors, plus their app and Excel presentation.

The website loads a frozen, reproducible sample. Opening it makes no SEC, Yahoo or Claude request.
"""

import json
from io import BytesIO
from pathlib import Path

import xbrl
import cash_generation

SAMPLE = Path(__file__).parent / "samples" / "liquidity_pilots.json"
FILED_BY = "2026-10-14"
PILOTS = {
    "LLY": {"name": "Eli Lilly and Company", "cik": 59478,
            "accession": "0000059478-26-000081", "document": "lly-20260630.htm",
            "evidence": "docs/pilot_evidence_lly.md"},
    "ORCL": {"name": "Oracle Corporation", "cik": 1341439,
             "accession": "0001193125-26-389274", "document": "orcl-20260831.htm",
             "evidence": "docs/pilot_evidence_oracle.md"},
    "VST": {"name": "Vistra Corp.", "cik": 1692819,
            "accession": "0001692819-26-000019", "document": "vistra-20260630.htm",
            "evidence": "docs/pilot_evidence_vistra.md"},
}


def net_debt(cash: dict, debt: dict) -> dict:
    """Subtract compatible facts only; retain negative net debt and all input provenance."""
    result = {"label": "Net debt", "value": None, "unit": "USD", "tag": None,
              "period_end": debt.get("period_end"), "formula": "Baseline gross debt - cash and cash equivalents",
              "inputs": {"baseline_gross_debt": debt, "cash": cash}, "notes": [],
              "note": "Unavailable", "detail": ""}
    if cash.get("value") is None or debt.get("value") is None:
        return {**result, "detail": "Net debt needs both checked cash and baseline gross debt."}
    sources = [cash, *debt["inputs"]]
    if (len({f["period_end"] for f in sources}) != 1
            or len({f["accession"] for f in sources}) != 1
            or any(f["unit"] != "USD" for f in sources)):
        return {**result, "detail": "Cash and every borrowing component must share the date, filing version and USD unit."}
    return {**result, "value": debt["value"] - cash["value"], "note": None}


def flow_to_debt(flow: dict, debt: dict) -> dict:
    """Historical TTM cash generation relative to debt at that period end, never a repayment forecast."""
    result = {"label": f"{flow['label']} / debt", "unit": "fraction", "tag": None, "value": None,
              "period_start": flow.get("period_start"), "period_end": debt.get("period_end"),
              "formula": f"TTM {flow['label'].lower()} / period-end baseline gross debt",
              "inputs": {"flow": flow, "debt": debt}, "notes": [], "note": "Unavailable", "detail": ""}
    if flow.get("value") is None or debt.get("value") is None:
        return {**result, "detail": "Both checked flow and borrowing inputs are required."}
    if flow["period_end"] != debt["period_end"] or flow["unit"] != "USD" or debt["unit"] != "USD":
        return {**result, "detail": "The USD flow must end at the debt's balance-sheet date."}
    if debt["value"] <= 0:
        return {**result, "detail": "Debt is zero or negative; a flow-to-debt ratio is not calculated."}
    return {**result, "value": flow["value"] / debt["value"], "note": None}


def build_snapshot(facts: dict, ticker: str, filing_documents: dict | None = None,
                   cash_flow_documents: dict | None = None) -> dict:
    """Build the checked pilot's dated figures; the builder never downloads a filing."""
    company = PILOTS[ticker]
    if int(facts["cik"]) != company["cik"]:
        raise ValueError(f"Company facts CIK does not match {ticker}")
    cash = xbrl.cash_and_equivalents(facts, filed_by=FILED_BY)
    # The restricted-cash exclusion was checked for this accession, not for every possible filing.
    if cash["value"] is not None and cash["accession"] != company["accession"]:
        cash = {**cash, "value": None, "note": "Unavailable",
                "detail": "Cash excluding restricted cash has not been checked for this filing."}
    debt = xbrl.baseline_gross_debt(facts, ticker, filed_by=FILED_BY, filing_documents=filing_documents)
    ratio = xbrl.current_ratio(facts, filed_by=FILED_BY)
    flows = cash_generation.build(ticker, cash_flow_documents or {})
    if flows["operating_cash_flow"]["period_end"] != cash["period_end"]:
        flows = {key: {**metric, "value": None, "note": "Unavailable",
                       "detail": "The cash-flow presentation was checked for a different balance-sheet date."}
                 for key, metric in flows.items()}
    return {"ticker": ticker, "company_name": company["name"], "cik": company["cik"],
            "checked_as_of": FILED_BY, "evidence": company["evidence"],
            "source_url": (f"https://www.sec.gov/Archives/edgar/data/{company['cik']}/"
                           f"{company['accession'].replace('-', '')}/{company['document']}"),
            "metrics": {"cash": cash, "gross_debt": debt, "net_debt": net_debt(cash, debt),
                        "current_ratio": ratio, **flows,
                        "ocf_to_debt": flow_to_debt(flows["operating_cash_flow"], debt),
                        "fcf_to_debt": flow_to_debt(flows["free_cash_flow"], debt)}}


def leaf_inputs(metric: dict) -> list[dict]:
    """Reported facts behind a derived metric, without inventing a tag for its result."""
    inputs = metric.get("inputs")
    if inputs is None:
        return [metric]
    values = inputs.values() if isinstance(inputs, dict) else inputs
    return [fact for value in values for fact in leaf_inputs(value)]


def evidence_html(snapshot: dict) -> str:
    """Read-only display; every input keeps its filing and selection information."""
    import ui
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


def render_html(snapshot: dict) -> str:
    import liquidity_review
    return liquidity_review.render(snapshot) + evidence_html(snapshot)


def financing_html(snapshot: dict) -> str:
    """The three checked subsequent events, with the prospectus's intended use of proceeds."""
    import ui
    import reviewed_financing
    if snapshot["ticker"] != "VST":
        return ''
    result = '<details class="irt-evidence"><summary>Financing changes after June 30 · checked Oct 14, 2026</summary>'
    for accession in ("0001140361-26-028619", "0001140361-26-037577",
                      "0001140361-26-036415", "0001140361-26-038468"):
        finding = reviewed_financing.VST[accession]
        result += (f'<p><strong>{ui.esc(finding["kind"])}</strong><br>{ui.esc(finding["finding"])}<br>'
                   f'<a href="{ui.esc(finding["source_url"])}" target="_blank" rel="noopener noreferrer">'
                   f'{ui.esc(finding["form"])} filed {ui.esc(finding["filed"])} · {ui.esc(accession)}</a></p>')
    return result + '</details>'


def workbook(snapshots: list[dict]) -> bytes:
    """A row per reported input, with Excel formulas referencing those rows for derived results."""
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
    import liquidity_review
    obligations = wb.create_sheet("Other obligations")
    obligations.append(["Ticker", "Disclosure", "Amount as disclosed", "Reporting date", "Classification", "Filing location", "Accession", "Source", "Notes"])
    for snapshot in snapshots:
        for item in liquidity_review.NOTES[snapshot["ticker"]]:
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


def render() -> None:
    """Secondary, free saved-pilot view; it does not overwrite the user's analysis results."""
    import streamlit as st
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
                st.markdown(render_html(snapshot) + financing_html(snapshot), unsafe_allow_html=True)
