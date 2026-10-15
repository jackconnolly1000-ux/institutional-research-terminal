"""Oracle's checked May 31 principal schedule and dated financing evidence.

This is a saved filing review, not a forecast or a reconstructed August maturity schedule.
Amounts are read with the production inline-XBRL selector; text findings are checked per filing.
"""
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import filing_xbrl as fx

SAMPLE = Path(__file__).parent / "samples/oracle_financing.json"
AS_OF = "2026-05-31"
ANCHOR = "2026-08-31"
ACCESSION = "0001193125-26-277521"
QUARTER_ACCESSION = "0001193125-26-389274"
BASE = "https://www.sec.gov/Archives/edgar/data/1341439/"
SOURCE = BASE + "000119312526277521/orcl-20260531.htm"
QUARTER_SOURCE = BASE + "000119312526389274/orcl-20260831.htm"
CHECKED = "2026-10-14"
BUCKETS = (
    ("Fiscal 2027", "2026-06-01", "2027-05-31", "LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths"),
    ("Fiscal 2028", "2027-06-01", "2028-05-31", "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo"),
    ("Fiscal 2029", "2028-06-01", "2029-05-31", "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearThree"),
    ("Fiscal 2030", "2029-06-01", "2030-05-31", "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFour"),
    ("Fiscal 2031", "2030-06-01", "2031-05-31", "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFive"),
    ("Thereafter", "2031-06-01", None, "LongTermDebtMaturitiesRepaymentsOfPrincipalAfterYearFive"),
)
CONTROLS = {
    "principal_total": "DebtInstrumentFaceAmount",
    "discount_and_costs": "DebtInstrumentUnamortizedDiscountPremiumAndDebtIssuanceCostsNet",
    "carrying_debt": "DebtLongtermAndShorttermCombinedAmount",
}
QUARTER_FLOWS = {
    "Equity proceeds, net of issuance costs": "ProceedsFromIssuanceOfCommonStock",
    "Debt repayments": "RepaymentsOfDebt",
}

# These are factual reviews of the saved 8-K and its Exhibit 99.1, not form-based classifications.
FILINGS = {
    "0001193125-26-387905": {
        "form": "8-K", "filed": "2026-09-10", "period": "2026-09-10",
        "items": "2.02,8.01,9.01", "event_date": "2026-09-10",
        "kind": "Quarterly results and dividends; no new borrowing established",
        "finding": ("The earnings exhibit reports a $20 billion common-stock sale before commissions "
                    "completed during Q1 FY2027, which ended August 31. The 10-Q reports $19.909 billion "
                    "net proceeds. This is equity already reflected in the balance sheet. The 8-K also "
                    "declares preferred and common dividends; it does not establish later borrowing."),
        "source_url": BASE + "000119312526387905/orcl-20260910.htm",
        "related": [("Earnings release, Ex. 99.1", BASE + "000119312526387905/orcl-ex99_1.htm")],
    },
    "0001193125-26-389753": {
        "form": "8-K", "filed": "2026-09-14", "period": "2026-09-12",
        "items": "8.01,9.01", "event_date": "2026-09-12",
        "kind": "Insider trading-plan cancellation; no financing event identified",
        "finding": ("The Executive Chair cancelled his Rule 10b5-1 sale plan. The filing and exhibit "
                    "say no stock was sold under it. This is not a corporate debt issuance or repayment."),
        "source_url": BASE + "000119312526389753/d20034d8k.htm",
        "related": [("Press release, Ex. 99.1", BASE + "000119312526389753/d20034dex991.htm")],
    },
}

TERMS = [
    {"label": "Revolving credit facility", "as_of": AS_OF, "capacity": 10_000_000_000,
     "drawn": 0, "maturity": "2031-03-06", "source_url": SOURCE, "location": "10-K Note 6, p. 85",
     "detail": ("Five-year unsecured facility entered March 6, 2026, with no borrowing outstanding at "
                "May 31. August 31 availability is not established by the saved 10-Q. Capacity is not cash "
                "or additional debt. The facility and commercial-paper program are not added together "
                "as available liquidity.")},
    {"label": "Revolver interest covenant", "as_of": AS_OF, "capacity": None,
     "drawn": None, "maturity": None, "source_url": SOURCE, "location": "10-K Note 6, p. 85",
     "detail": ("The agreement requires Consolidated EBITDA / Consolidated Net Interest Expense of at "
                "least 3.0x, as those terms are defined in the agreement. The 10-K reports compliance at "
                "May 31. Current compliance and covenant headroom have not been calculated. This is "
                "not the planned operating-income / reported-interest ratio.")},
]


def build(document: Path, quarter_document: Path | None = None) -> dict:
    """Read the six checked annual buckets and reconcile principal to carrying debt.

    The caller pairs the saved document with ACCESSION. Exact date, USD, dimensions, duplicates
    and entity CIK must pass before any total or concentration is available.
    """
    result = {"ticker": "ORCL", "as_of": AS_OF, "anchor": ANCHOR, "accession": ACCESSION,
              "form": "10-K", "filed": "2026-06-22", "document": "orcl-20260531.htm",
              "source_url": SOURCE, "location": "10-K Note 6, pp. 83–85", "checked_as_of": CHECKED,
              "basis": "Future principal payments for all borrowings, excluding interest and leases",
              "status": "Unavailable", "detail": "", "buckets": [], "controls": {},
              "total": None, "first_five_years": None, "first_five_share": None,
              "quarter_flows": [],
              "current_schedule": None,
              "current_schedule_detail": "An August 31 debt maturity schedule is not disclosed in the saved 10-Q. "
                  "The May 31 schedule is historical and has not been rolled forward by subtracting repayments."}
    try:
        contexts = fx._contexts(ET.parse(document).getroot())
        for label, start, end, local in BUCKETS:
            fact = fx.read_instant(document, ACCESSION, "us-gaap:" + local, AS_OF)
            result["buckets"].append({**fact, "label": label, "due_start": start, "due_end": end})
        for key, local in CONTROLS.items():
            result["controls"][key] = fx.read_instant(document, ACCESSION, "us-gaap:" + local, AS_OF)
    except (OSError, ET.ParseError) as exc:
        return {**result, "detail": f"Saved 10-K could not be read: {type(exc).__name__}."}
    facts = [*result["buckets"], *result["controls"].values()]
    for fact in facts:
        if fact["value"] is None:
            return {**result, "detail": fact["detail"]}
        entity = contexts[fact["context_id"]]["entity_identifier"] or ""
        if not entity.isdigit() or int(entity) != 1341439:
            return {**result, "detail": "The selected fact's entity CIK does not match Oracle."}
        if fact["value"] < 0:
            return {**result, "detail": "A negative schedule or reconciliation input needs review."}
    total = sum(f["value"] for f in result["buckets"])
    c = result["controls"]
    if total != c["principal_total"]["value"]:
        return {**result, "detail": "The maturity buckets do not equal the filing's principal total."}
    if total - c["discount_and_costs"]["value"] != c["carrying_debt"]["value"]:
        return {**result, "detail": "Principal less discounts and costs does not equal carrying debt."}
    first = sum(f["value"] for f in result["buckets"][:5])
    for label, local in QUARTER_FLOWS.items():
        fact = {"label": label, "tag": "us-gaap:" + local, "value": None,
                "detail": "The saved quarterly document was not supplied."}
        if quarter_document is not None:
            try:
                fact.update(fx.read_duration(quarter_document, QUARTER_ACCESSION, fact["tag"],
                                             "2026-06-01", ANCHOR))
                if fact["value"] is not None and (fact.get("entity_identifier") or "").lstrip("0") != "1341439":
                    fact.update(value=None, detail="The quarterly fact's entity CIK does not match Oracle.")
                if fact["value"] is not None and fact["value"] < 0:
                    fact.update(value=None, detail="A negative financing input needs presentation review.")
            except (OSError, ET.ParseError) as exc:
                fact.update(detail=f"Saved quarterly filing could not be read: {type(exc).__name__}.")
        result["quarter_flows"].append({**fact, "form": "10-Q", "filed": "2026-09-11",
            "accession": QUARTER_ACCESSION, "source_url": QUARTER_SOURCE, "location": "10-Q cash flows, p. 5",
            "period_start": "2026-06-01", "period_end": ANCHOR})
    return {**result, "status": "Checked", "total": total, "first_five_years": first,
            "first_five_share": first / total if total > 0 else None}


def for_snapshot(snapshot: dict) -> dict | None:
    """Never attach a checked schedule to another company's or another period's review."""
    if (snapshot.get("ticker") != "ORCL"
            or snapshot["metrics"]["cash"].get("accession") != QUARTER_ACCESSION
            or snapshot["metrics"]["cash"].get("period_end") != ANCHOR):
        return None
    try:
        saved = json.loads(SAMPLE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"status": "Unavailable", "detail": "The saved Oracle maturity review could not be loaded."}
    if (saved.get("accession"), saved.get("as_of"), saved.get("anchor")) != (ACCESSION, AS_OF, ANCHOR):
        return {"status": "Unavailable", "detail": "The saved maturity review has unexpected filing metadata."}
    return saved
