"""Oracle's dated cash reconciliation and commitments, read from its saved 10-Q.

Historical exclusions isolate disclosed funding contributions. They do not establish recurring
cash generation, forecast cash, covenant compliance or currently drawable credit.
"""
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import filing_xbrl as fx
import oracle_financing as of
import oracle_revolver
import oracle_interest

SAMPLE = Path(__file__).parent / "samples/oracle_liquidity.json"
WORKBOOK = SAMPLE.with_suffix(".xlsx")
START = "2026-06-01"
END = of.ANCHOR
CREDIT_URL = of.BASE + "000119312526101045/orcl-ex10_17.htm"
CREDIT_ACCESSION = "0001193125-26-101045"
PREPAY = "orcl:IncreaseDecreaseInDeferredRevenuesFromCustomerPrepaymentsWithSignificantFinancingComponent"

# Sign multipliers below describe cash uses; the reader preserves each fact's filed XBRL sign.
FLOWS = {
    "ocf": ("Reported operating cash flow", "us-gaap:NetCashProvidedByUsedInOperatingActivities"),
    "prepay": ("Customer prepayments with a significant financing component", PREPAY),
    "capex": ("Cash capital expenditures", "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"),
    "investment_purchases": ("Purchases of investments", "us-gaap:PaymentsToAcquireInvestments"),
    "investment_proceeds": ("Sales and maturities of investments", "us-gaap:ProceedsFromSaleAndMaturityOfAvailableForSaleSecurities"),
    "investing": ("Reported net investing cash flow", "us-gaap:NetCashProvidedByUsedInInvestingActivities"),
    "equity": ("ATM common-stock proceeds, net", "us-gaap:ProceedsFromIssuanceOfCommonStock"),
    "employee": ("Net employee stock-program proceeds", "us-gaap:ProceedsFromIssuanceOfSharesUnderIncentiveAndShareBasedCompensationPlans"),
    "dividends": ("Cash dividends to stockholders", "us-gaap:PaymentsOfDividendsCommonStock"),
    "cp": ("Commercial-paper repayments, cash-flow row", "us-gaap:RepaymentsOfCommercialPaper"),
    "capex_financing": ("Net capex-financing cash flow", "orcl:ProceedsFromRepaymentsOfShort-TermFinancingRelatedToCapitalExpendituresNet"),
    "debt_repayments": ("Senior notes, term loans and other repayments", "us-gaap:RepaymentsOfDebt"),
    "other_financing": ("Other financing cash flow, net", "us-gaap:ProceedsFromPaymentsForOtherFinancingActivities"),
    "financing": ("Reported net financing cash flow", "us-gaap:NetCashProvidedByUsedInFinancingActivities"),
    "fx": ("Exchange-rate effect on cash", "us-gaap:EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations"),
    "change": ("Reported increase in cash including restricted cash", "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect"),
    "unpaid_capex": ("Unpaid capital expenditures, noncash disclosure", "us-gaap:CapitalExpendituresIncurredButNotYetPaid"),
}
CASH_TAG = "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations"
INSTANTS = {
    "opening_total": ("Opening cash including restricted cash", CASH_TAG, of.AS_OF),
    "closing_total": ("Closing cash including restricted cash", CASH_TAG, END),
    "closing_cash": ("Cash and equivalents excluding restricted cash", "us-gaap:CashAndCashEquivalentsAtCarryingValue", END),
    "not_commenced": ("Operating leases not yet commenced", "orcl:LesseeOperatingLeaseLeaseNotYetCommencedLeaseCommitments", END),
}
DUE = (
    ("Remainder FY2027", "2026-09-01", "2027-05-31"),
    ("FY2028", "2027-06-01", "2028-05-31"),
    ("FY2029", "2028-06-01", "2029-05-31"),
    ("FY2030", "2029-06-01", "2030-05-31"),
    ("FY2031", "2030-06-01", "2031-05-31"),
    ("FY2032", "2031-06-01", "2032-05-31"),
    ("Thereafter", "2032-06-01", None),
)
# The filing's printed fiscal-year headings control these dates. Some standard tag names
# say "next twelve months" despite the table explicitly labelling the bucket fiscal 2028.
OPERATING = ["LesseeOperatingLeaseLiabilityPayments" + s for s in (
    "RemainderOfFiscalYear", "DueNextTwelveMonths", "DueYearTwo", "DueYearThree", "DueYearFour", "DueYearFive", "DueAfterYearFive")]
FINANCE = ["FinanceLeaseLiabilityPayments" + s for s in (
    "RemainderOfFiscalYear", "DueNextTwelveMonths", "DueYearTwo", "DueYearThree", "DueYearFour", "DueYearFive", "DueAfterYearFive")]
PURCHASE = ["UnrecordedUnconditionalPurchaseObligation" + s for s in (
    "DueInRemainderOfFiscalYear", "BalanceOnFirstAnniversary", "BalanceOnSecondAnniversary", "BalanceOnThirdAnniversary",
    "BalanceOnFourthAnniversary", "BalanceOnFifthAnniversary", "DueAfterFiveYears")]
SCHEDULES = {"operating": OPERATING, "finance": FINANCE, "purchase": PURCHASE}
CONTROLS = {
    "operating_total": "LesseeOperatingLeaseLiabilityPaymentsDue",
    "operating_interest": "LesseeOperatingLeaseLiabilityUndiscountedExcessAmount",
    "operating_liability": "OperatingLeaseLiability",
    "finance_total": "FinanceLeaseLiabilityPaymentsDue",
    "finance_interest": "FinanceLeaseLiabilityUndiscountedExcessAmount",
    "finance_liability": "FinanceLeaseLiability",
    "purchase_total": "UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount",
}

FACILITY = {
    "commitment": 10_000_000_000, "agreement_date": "2026-03-06", "original_maturity": "2031-03-06",
    "drawn": 0, "drawn_as_of": of.AS_OF, "available": None, "available_as_of": END,
    "covenant_minimum": 3.0, "headroom": None, "source_url": CREDIT_URL,
    "accession": CREDIT_ACCESSION, "filed": "2026-03-11", "form": "10-Q Ex. 10.17",
    "location": "Sections 1.01, 2.01, 2.06, 4.02 and 6.02(c)",
    "detail": "Draws require accurate representations and no default. Commitments can change or terminate. "
              "Extensions require lender consent and conditions. The covenant uses contract-defined EBITDA "
              "and cash interest net of cash interest income, including specified adjustments. "
              "A generic operating-income/interest ratio cannot establish compliance. August drawn amounts, "
              "drawable capacity and covenant headroom are Unavailable. The May 31 10-K reports no drawings "
              "and compliance then. Commercial-paper capacity is not added to the revolver.",
}


def build(document: Path) -> dict:
    """Require exact periods, Oracle CIK and full reconciliations before deriving the cash analysis."""
    result = {"ticker": "ORCL", "accession": of.QUARTER_ACCESSION, "period_start": START,
              "period_end": END, "checked_as_of": "2026-10-15", "source_url": of.QUARTER_SOURCE,
              "status": "Unavailable", "detail": "", "inputs": {}, "cash": None,
              "schedules": {}, "facility": FACILITY}
    try:
        contexts = fx._contexts(ET.parse(document).getroot())
    except (OSError, ET.ParseError) as exc:
        return {**result, "detail": f"Saved Oracle 10-Q could not be read: {type(exc).__name__}."}

    def read(key, label, tag, instant=None, location="10-Q cash flows, p. 5"):
        fact = (fx.read_instant(document, of.QUARTER_ACCESSION, tag, instant) if instant else
                fx.read_duration(document, of.QUARTER_ACCESSION, tag, START, END))
        if fact["value"] is not None:
            cik = contexts[fact["context_id"]]["entity_identifier"] or ""
            if cik.lstrip("0") != "1341439":
                fact.update(value=None, detail="The selected fact's entity CIK does not match Oracle.")
        fact.update(label=label, period_start=None if instant else START, period_end=instant or END,
                    document="orcl-20260831.htm", form="10-Q", filed="2026-09-11",
                    source_url=of.QUARTER_SOURCE, location=location)
        result["inputs"][key] = fact
        return fact

    for key, (label, tag) in FLOWS.items():
        read(key, label, tag)
    for key, (label, tag, instant) in INSTANTS.items():
        read(key, label, tag, instant, "10-Q balance sheet p. 1; cash reconciliation pp. 5–6" if key != "not_commenced" else "10-Q Note 6, p. 13")
    for kind, tags in SCHEDULES.items():
        rows = []
        for i, ((label, start, end), tag) in enumerate(zip(DUE, tags)):
            fact = read(f"{kind}_{i}", f"{kind.title()} payments: {label}", "us-gaap:" + tag, END,
                        "10-Q Note 6, pp. 12–13")
            rows.append({"key": f"{kind}_{i}", "label": label, "due_start": start, "due_end": end, "value": fact["value"]})
        result["schedules"][kind] = {"status": "Unavailable", "detail": "", "rows": rows}
    for key, tag in CONTROLS.items():
        read(key, key.replace("_", " ").capitalize(), "us-gaap:" + tag, END, "10-Q Note 6, pp. 12–13")

    for kind, schedule in result["schedules"].items():
        keys = [r["key"] for r in schedule["rows"]] + [kind + "_total"]
        if kind != "purchase":
            keys += [kind + "_interest", kind + "_liability"]
        fs = [result["inputs"][k] for k in keys]
        if any(f["value"] is None or f["value"] < 0 for f in fs):
            schedule["detail"] = "A payment or reconciliation input is missing or negative."
            continue
        v = lambda k: result["inputs"][k]["value"]
        if sum(r["value"] for r in schedule["rows"]) != v(kind + "_total"):
            schedule["detail"] = "Payment buckets do not equal the reported total."
        elif kind != "purchase" and v(kind + "_total") - v(kind + "_interest") != v(kind + "_liability"):
            schedule["detail"] = "Payments less imputed interest do not equal the reported liability."
        else:
            schedule["status"] = "Checked"

    required = [k for k in FLOWS if k != "unpaid_capex"] + ["opening_total", "closing_total", "closing_cash"]
    missing = [k for k in required if result["inputs"][k]["value"] is None]
    if missing:
        return {**result, "detail": "Cash analysis inputs Unavailable: " + "; ".join(
            result["inputs"][k]["label"] + ": " + result["inputs"][k]["detail"] for k in missing)}
    v = {k: f["value"] for k, f in result["inputs"].items()}
    magnitudes = ["prepay", "capex", "investment_purchases", "investment_proceeds", "equity",
                  "dividends", "cp", "debt_repayments", "opening_total", "closing_total", "closing_cash"]
    if any(v[k] < 0 for k in magnitudes) or v["closing_cash"] > v["closing_total"]:
        return {**result, "detail": "Cash-flow direction or restricted-cash reconciliation needs review."}
    investing = -v["investment_purchases"] + v["investment_proceeds"] - v["capex"]
    financing = (v["equity"] + v["employee"] - v["dividends"] - v["cp"]
                 + v["capex_financing"] - v["debt_repayments"] + v["other_financing"])
    change = v["ocf"] + investing + financing + v["fx"]
    if (investing != v["investing"] or financing != v["financing"] or change != v["change"]
            or v["opening_total"] + change != v["closing_total"]):
        return {**result, "detail": "The detailed cash flows do not reconcile to reported investing, financing or ending cash."}
    other = (-v["investment_purchases"] + v["investment_proceeds"] + v["employee"]
             - v["dividends"] - v["cp"] + v["capex_financing"] + v["other_financing"] + v["fx"])
    cash = {"ocf_less_prepay": v["ocf"] - v["prepay"], "fcf": v["ocf"] - v["capex"],
            "fcf_less_prepay": v["ocf"] - v["prepay"] - v["capex"],
            "change_without_equity": change - v["equity"],
            "change_without_equity_and_prepay": change - v["equity"] - v["prepay"],
            "restricted_at_end": v["closing_total"] - v["closing_cash"], "other_net": other,
            "prepay_share_ocf": v["prepay"] / v["ocf"] if v["ocf"] > 0 else None}
    return {**result, "status": "Checked", "cash": cash}


def for_snapshot(snapshot: dict) -> dict | None:
    """Only attach this review to the Oracle filing it was checked against."""
    anchor = snapshot.get("metrics", {}).get("cash", {})
    if (snapshot.get("ticker"), anchor.get("accession"), anchor.get("period_end")) != ("ORCL", of.QUARTER_ACCESSION, END):
        return None
    try:
        review = json.loads(SAMPLE.read_text(encoding="utf-8"))
        if (review["ticker"], review["accession"], review["period_start"], review["period_end"]) != ("ORCL", of.QUARTER_ACCESSION, START, END):
            raise ValueError("Unexpected filing metadata")
        if review["inputs"]["closing_cash"]["value"] != anchor.get("value"):
            raise ValueError("Cash does not match the filing snapshot")
        return review
    except (OSError, ValueError, KeyError, TypeError):
        return {"status": "Unavailable", "detail": "The saved Oracle liquidity analysis is missing or does not match this filing."}


def workbook_bytes(review: dict) -> bytes | None:
    """Refuse a stale workbook when the source review changes without rebuilding its evidence."""
    try:
        content = WORKBOOK.read_bytes()
        metadata = json.loads(WORKBOOK.with_suffix(".manifest.json").read_text())
        import core_charts
        if metadata.get("charts_sha256") != core_charts.fingerprint():
            return None
        import company_history
        if metadata.get("history_sha256") != company_history.fingerprint():
            return None
        import ratio_review
        if metadata.get("ratios_sha256") != ratio_review.fingerprint():
            return None
        import borrowing_leases
        if metadata.get("borrowing_leases_sha256") != borrowing_leases.fingerprint():
            return None
        import funding_conclusions as funding
        if metadata.get("funding_sha256") != funding.fingerprint() or funding.load("ORCL") is None:
            return None
        if (metadata["review_sha256"] != hashlib.sha256(SAMPLE.read_bytes()).hexdigest()
                or metadata["workbook_sha256"] != hashlib.sha256(content).hexdigest()
                or metadata["financing_sha256"] != hashlib.sha256(of.SAMPLE.read_bytes()).hexdigest()
                or metadata["revolver_sha256"] != hashlib.sha256(oracle_revolver.SAMPLE.read_bytes()).hexdigest()
                or metadata["interest_sha256"] != hashlib.sha256(oracle_interest.SAMPLE.read_bytes()).hexdigest()
                or oracle_interest.load() is None
                or oracle_revolver.load().get("status") != "Checked"
                or review != json.loads(SAMPLE.read_text()) or review.get("status") != "Checked"):
            return None
        return content
    except (OSError, ValueError, KeyError):
        return None
