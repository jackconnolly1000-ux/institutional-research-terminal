"""Dated pilot snapshots built from the tested selectors, plus their app and Excel presentation.

The website loads a frozen, reproducible sample. Opening it makes no SEC, Yahoo or Claude request.
"""

import json
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
    import company_review
    return company_review.evidence_html(snapshot)


def render_html(snapshot: dict) -> str:
    import company_review
    return company_review.render(snapshot) + evidence_html(snapshot)


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
    import company_review
    return company_review.workbook(snapshots)


def render() -> None:
    import company_review
    company_review.render_app()
