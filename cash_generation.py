"""Checked pilot cash-flow statements, read directly from the filings without network calls.

These mappings apply to the six documents reviewed in docs/pilot_evidence_*.md. Lilly's purchases use a
different standard tag; Vistra's line includes nuclear fuel and LTSA prepayments. Neither is a universal fallback.
The caller pairs each document with its accession, as for the existing instant reader.
"""
from datetime import date, timedelta
from pathlib import Path
from xml.etree.ElementTree import ParseError

import filing_xbrl

OCF = "us-gaap:NetCashProvidedByUsedInOperatingActivities"
CAPEX = "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"
SOURCES = {
    "LLY": {"cik": 59478, "capex_tag": "us-gaap:PaymentsToAcquireOtherPropertyPlantAndEquipment",
            "capex_label": "Purchases of property and equipment",
            "annual": ("0000059478-26-000013", "lly-20251231.htm", "2026-02-12", "2025-01-01", "2025-12-31"),
            "quarter": ("0000059478-26-000081", "lly-20260630.htm", "2026-08-05", "2026-01-01", "2026-06-30"),
            "prior": ("2025-01-01", "2025-06-30"),
            "basis": "Reported purchases of property and equipment; excludes acquisitions and other investing cash flows."},
    "ORCL": {"cik": 1341439, "capex_tag": CAPEX, "capex_label": "Capital expenditures",
             "annual": ("0001193125-26-277521", "orcl-20260531.htm", "2026-06-22", "2025-06-01", "2026-05-31"),
             "quarter": ("0001193125-26-389274", "orcl-20260831.htm", "2026-09-11", "2026-06-01", "2026-08-31"),
             "prior": ("2025-06-01", "2025-08-31"),
             "basis": "Operating cash flow includes $11.4B of customer prepayments received in the quarter ended Aug 31, 2026 (10-Q p. 7 and MD&A pp. 33–34). Capital expenditures are cash payments; financing cash flows are not added."},
    "VST": {"cik": 1692819, "capex_tag": CAPEX,
            "capex_label": "Capital expenditures, including nuclear fuel and LTSA prepayments",
            "annual": ("0001692819-26-000006", "vistra-20251231.htm", "2026-02-27", "2025-01-01", "2025-12-31"),
            "quarter": ("0001692819-26-000019", "vistra-20260630.htm", "2026-08-10", "2026-01-01", "2026-06-30"),
            "prior": ("2025-01-01", "2025-06-30"),
            "basis": "The reported capex line includes nuclear fuel purchases and long-term service agreement (LTSA) prepayments. It is used as reported; acquisitions and other investing cash flows are excluded."},
}


def build(ticker: str, documents: dict[str, Path]) -> dict:
    """FY + current YTD − prior YTD, using exact durations from the checked filings only."""
    spec = SOURCES[ticker]
    end = spec["quarter"][4]
    start = (date.fromisoformat(spec["prior"][1]) + timedelta(days=1)).isoformat()

    def flow(tag, label):
        inputs = []
        for role, report, period, coefficient in (
            ("Fiscal year", "annual", spec["annual"][3:5], 1),
            ("Current year to date", "quarter", spec["quarter"][3:5], 1),
            ("Prior year to date", "quarter", spec["prior"], -1),
        ):
            acc, document, filed, _, _ = spec[report]
            source_url = (f"https://www.sec.gov/Archives/edgar/data/{spec['cik']}/"
                          f"{acc.replace('-', '')}/{document}")
            fact = {"value": None, "tag": tag, "context_id": None, "scale": None, "decimals": None,
                    "detail": "The checked filing document was not supplied.", "notes": []}
            if acc in documents:
                try:
                    fact = filing_xbrl.read_duration(documents[acc], acc, tag, *period)
                    if fact["value"] is not None and str(fact.get("entity_identifier") or "").lstrip("0") != str(spec["cik"]):
                        fact.update(value=None, note="Unavailable", detail="The selected context's entity does not match this company's CIK.")
                except (OSError, ParseError) as exc:
                    fact["detail"] = f"The supplied filing could not be read: {type(exc).__name__}."
            inputs.append({**fact, "label": f"{label} · {role.lower()}", "unit": "USD",
                           "period_start": period[0], "period_end": period[1], "coefficient": coefficient,
                           "form": "10-K" if report == "annual" else "10-Q", "filed": filed, "accession": acc,
                           "source_url": source_url, "source_document": document, "role": role,
                           "selection_rule": "Exact tag, USD duration, exact start and end dates, no dimensions"})
        missing = [f["detail"] for f in inputs if f["value"] is None]
        value = None if missing else sum(f["coefficient"] * f["value"] for f in inputs)
        return {"label": label, "unit": "USD", "tag": None, "value": value, "period_start": start,
                "period_end": end, "formula": "Fiscal year + current YTD - prior YTD", "inputs": inputs,
                "notes": [], "detail": "; ".join(missing), "note": "Unavailable" if missing else None}

    ocf = flow(OCF, "Operating cash flow")
    capex = flow(spec["capex_tag"], spec["capex_label"])
    if capex["value"] is not None and any(f["value"] < 0 for f in capex["inputs"]):
        capex.update(value=None, note="Unavailable", detail="A spending input is negative; its presentation needs review.")
    available = ocf["value"] is not None and capex["value"] is not None
    fcf = {"label": "Free cash flow", "unit": "USD", "tag": None,
           "value": ocf["value"] - capex["value"] if available else None,
           "period_start": start, "period_end": end, "formula": "Operating cash flow - reported capital spending",
           "inputs": {"operating_cash_flow": ocf, "capital_spending": capex}, "notes": [spec["basis"]],
           "note": None if available else "Unavailable", "detail": "" if available else "A checked cash-flow input is missing."}
    return {"operating_cash_flow": ocf, "capital_spending": capex, "free_cash_flow": fcf}
