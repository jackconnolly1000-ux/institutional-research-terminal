"""Lilly's saved, dated funding review. Historical arithmetic is not a cash forecast."""
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import filing_xbrl as fx

SAMPLE = Path(__file__).parent / "samples/lly_liquidity.json"
END, START, ANNUAL = "2026-06-30", "2026-01-01", "2025-12-31"
SOURCES = {
    "annual": {"document": "lly-20251231.htm", "accession": "0000059478-26-000013",
               "form": "10-K", "filed": "2026-02-12",
               "sha256": "d45f8d1e0945df0b7b30254e96ff8c5dbd1df7d15b17c8ef7399c8e0206b7d7f"},
    "quarter": {"document": "lly-20260630.htm", "accession": "0000059478-26-000081",
                "form": "10-Q", "filed": "2026-08-05",
                "sha256": "8e8f10cf3af98bc12a41985a98cfde9c2b9da8a812af18515d34ce3d8e1c1b3d"},
    "release": {"document": "8k-20260805-q226lillysalesandearningsp.htm",
                "accession": "0000059478-26-000077", "form": "8-K Ex. 99.1", "filed": "2026-08-05",
                "sha256": "5397056cb6aebc1496e22de6f9c8b062b11ff0c7f5ee30428e3f68fc8aea748a"},
}
for _source in SOURCES.values():
    name = _source["document"].removeprefix("8k-20260805-")
    _source["source_url"] = ("https://www.sec.gov/Archives/edgar/data/59478/" +
                             _source["accession"].replace("-", "") + "/" + name)

FLOWS = {
    "ocf": ("Operating cash flow", "NetCashProvidedByUsedInOperatingActivities"),
    "capex": ("Cash purchases of other PP&E", "PaymentsToAcquireOtherPropertyPlantAndEquipment"),
    "investments": ("Investment purchases", "PaymentsToAcquireOtherInvestments"),
    "iprd": ("Purchased in-process R&D", "PaymentsToAcquireInProcessResearchAndDevelopment"),
    "acquisitions": ("Acquisitions, net of cash acquired", "OtherPaymentsToAcquireBusinesses"),
    "other_investing": ("Other investing cash used", "PaymentsForProceedsFromOtherInvestingActivities"),
    "investing_total": ("Reported net investing cash flow", "NetCashProvidedByUsedInInvestingActivities"),
    "dividends": ("Cash dividends", "PaymentsOfDividends"),
    "short_debt": ("Short-term borrowings, net", "ProceedsFromRepaymentsOfShortTermDebt"),
    "long_proceeds": ("Long-term borrowing proceeds, net", "ProceedsFromIssuanceOfLongTermDebt"),
    "long_repayments": ("Long-term debt repaid", "RepaymentsOfLongTermDebt"),
    "buybacks": ("Share repurchases", "PaymentsForRepurchaseOfCommonStock"),
    "other_financing": ("Other financing cash flow", "ProceedsFromPaymentsForOtherFinancingActivities"),
    "financing_total": ("Reported net financing cash flow", "NetCashProvidedByUsedInFinancingActivities"),
    "fx": ("Exchange-rate effect on cash", "EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
    "change": ("Reported cash increase", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect"),
}
NOTE_MEMBERS = [("2026", "2026"), ("2027", "2027"), ("2028", "2028"),
                ("2029", "2029"), ("2030", "2030"), ("2031–2040", "20312040"),
                ("2041–2050", "20412050"), ("2051–2060", "20512060"), ("2061–2070", "20612070")]
# These are reviewed prose, not inline facts or unconditional payment forecasts. The source
# hashes bind them to the documents actually read; a different document requires a new review.
DISCLOSURES = [
    ("unused_june", "Unused committed facilities", 10_100_000_000, END, "Reported unused commitment",
     "quarter", "MD&A p. 31", "Of this, $10B supports commercial paper. Not cash or verified drawable credit; do not add CP capacity again. Agreement conditions and facility-by-facility June composition are Unavailable."),
    ("cp_support", "Facilities supporting commercial paper", 10_000_000_000, END, "Subset of unused facilities",
     "quarter", "MD&A p. 31", "Included in the $10.1B; not another source of funds."),
    ("atai", "Pending AtaiBeckley acquisition", 2_800_000_000, "Disclosed August 5, 2026", "Approximate conditional closing payment",
     "quarter", "MD&A p. 31", "Payable at closing, subject to conditions. Disclosed after quarter end; closing date, completion and funding allocation are not established here."),
    ("unpaid_kelonia", "Unpaid Kelonia cash consideration", 208_000_000, END, "Unpaid acquisition consideration",
     "quarter", "Note 4 p. 13", "Payment date Unavailable. Separate from cash already paid and from contingent-consideration fair value."),
    ("unpaid_centessa", "Unpaid Centessa cash consideration", 88_000_000, END, "Unpaid acquisition consideration",
     "quarter", "Note 4 p. 13", "Payment date Unavailable. Do not add to paid acquisition cash or contingent-consideration fair value."),
    ("july_paid", "July infectious-disease acquisitions: cash paid", 2_000_000_000, "July 2026", "Approximate subsequent cash use",
     "quarter", "MD&A p. 31; Note 4 pp. 13–14", "Already paid after June. Other July cash flows are unknown; June cash less this payment is not a current cash balance."),
    ("july_ceiling", "July acquisitions: aggregate consideration up to", 3_900_000_000, "July 2026", "Conditional aggregate ceiling",
     "quarter", "Note 4 pp. 13–14", "Includes upfront cash and potential clinical, regulatory and commercial milestones. Includes the approximately $2B paid; do not add the two amounts or infer a precise remaining cash bill."),
    ("vc", "Unfunded venture fund commitments", 806_000_000, END, "Approximate investment commitment",
     "quarter", "MD&A p. 31", "Expected to be paid over up to ten years. Individual capital-call dates are Unavailable."),
    ("manufacturing", "Development-medicine supply arrangements: up to", 10_000_000_000, ANNUAL, "Approximate conditional purchase shortfall ceiling",
     "annual", "MD&A p. 51", "Payments if specified purchases are not met under executed manufacturing and supply agreements; durations generally up to eight years. Not an unconditional $10B bill. Updated June ceiling, annual payments and overlap with other spending are Unavailable."),
    ("indiana", "Additional Indiana manufacturing investment", 4_500_000_000, "Announced August 5, 2026", "Announced investment commitment",
     "release", "Highlights; Other announcements", "Release says committed an additional $4.5B. Contractual payment schedule, spending to date and overlap with capex or supply commitments are not established by this release. Not added to debt or the $10B ceiling."),
]


def build(annual: Path, quarter: Path, *, text_checked=False) -> dict:
    """Read exact periods and named dimensions. Only a source-hash audit enables prose amounts."""
    result = {"ticker": "LLY", "period_end": END, "accession": SOURCES["quarter"]["accession"],
              "checked_as_of": "2026-10-15", "sources": SOURCES, "inputs": {}, "cash": None,
              "cash_detail": "", "notes_schedule": None, "notes_detail": "", "disclosures": [],
              "coverage": None, "coverage_detail": "Future dated principal, operating cash generation, "
              "acquisition payment dates and drawable facilities are not established. Historical flows are not future funding."}
    documents = {"annual": Path(annual), "quarter": Path(quarter)}
    contexts = {k: fx._contexts(ET.parse(p).getroot()) for k, p in documents.items()}

    def read(key, label, tag, source="quarter", instant=None, dimensions=(), location="Cash flows p. 8"):
        meta = SOURCES[source]
        f = (fx.read_instant(documents[source], meta["accession"], tag, instant, dimensions=dimensions)
             if instant else fx.read_duration(documents[source], meta["accession"], tag, START, END, dimensions=dimensions))
        if f["value"] is not None and (contexts[source][f["context_id"]]["entity_identifier"] or "").lstrip("0") != "59478":
            f.update(value=None, detail="The selected entity is not Lilly.")
        f.update(label=label, period_start=None if instant else START, period_end=instant or END,
                 source_kind="Inline XBRL", location=location, **meta)
        result["inputs"][key] = f
        return f["value"]

    for key, (label, tag) in FLOWS.items():
        read(key, label, "us-gaap:" + tag)
    for key, date in [("opening", ANNUAL), ("closing", END)]:
        read(key, key.title() + " cash and equivalents", "us-gaap:CashAndCashEquivalentsAtCarryingValue",
             instant=date, location="Balance sheet p. 7; cash flows p. 8")
    read("current_debt", "Current borrowing", "us-gaap:DebtCurrent", instant=END, location="Balance sheet p. 7")
    read("noncurrent_debt", "Noncurrent borrowing", "us-gaap:LongTermDebtNoncurrent", instant=END, location="Balance sheet p. 7")
    level3 = [("us-gaap:FairValueByFairValueHierarchyLevelAxis", "us-gaap:FairValueInputsLevel3Member")]
    for key, suffix in [("contingent_current", "Current"), ("contingent_noncurrent", "Noncurrent")]:
        read(key, "Contingent consideration fair value: " + suffix.lower(),
             "us-gaap:BusinessCombinationContingentConsiderationLiability" + suffix,
             instant=END, dimensions=level3, location="Note 8 p. 17")
    for label, member in NOTE_MEMBERS:
        read("notes_" + member, "Notes due " + label, "us-gaap:DebtInstrumentCarryingAmount", "annual", ANNUAL,
             [("us-gaap:DebtInstrumentAxis", "lly:NotesDue" + member + "Member")], "Note 11 p. 76")
    for key, label, tag in [("adjustment", "Other long-term debt and adjustments (source magnitude)", "OtherLongTermDebt"),
                            ("annual_cp", "Commercial paper", "CommercialPaper"),
                            ("annual_total", "Reported total debt", "DebtLongtermAndShorttermCombinedAmount"),
                            ("annual_unused", "Unused facilities at December 31", "LineOfCreditFacilityRemainingBorrowingCapacity")]:
        read(key, label, "us-gaap:" + tag, "annual", ANNUAL, location="Note 11 p. 76")
    for key, member, label in [("facility_2026", "2026", "364-day facility expires August 2026"),
                                ("facility_2029", "December2029", "Facility expires December 2029")]:
        read(key, label, "us-gaap:LineOfCreditFacilityMaximumBorrowingCapacity", "annual", ANNUAL,
             [("us-gaap:DebtInstrumentRedemptionPeriodAxis", "lly:MaturityDate" + member + "Member")], "Note 11 p. 76; MD&A p. 51")
    v = {k: f["value"] for k, f in result["inputs"].items()}
    required = [*FLOWS, "opening", "closing"]
    if any(v[k] is None for k in required):
        result["cash_detail"] = "Missing cash reconciliation input: " + ", ".join(k for k in required if v[k] is None)
    else:
        investing = -sum(v[k] for k in ["capex", "investments", "iprd", "acquisitions", "other_investing"])
        financing = v["short_debt"] + v["long_proceeds"] - v["long_repayments"] - v["dividends"] - v["buybacks"] + v["other_financing"]
        if (investing != v["investing_total"] or financing != v["financing_total"] or
                v["ocf"] + investing + financing + v["fx"] != v["change"] or
                v["opening"] + v["change"] != v["closing"]):
            result["cash_detail"] = "Cash-flow subtotals or opening-to-closing cash do not reconcile."
        else:
            result["cash"] = {"ocf_less_capex": v["ocf"] - v["capex"],
                              "acquisitions_iprd": v["acquisitions"] + v["iprd"],
                              "payouts": v["dividends"] + v["buybacks"],
                              "net_borrowing": v["short_debt"] + v["long_proceeds"] - v["long_repayments"],
                              "other": -v["investments"] - v["other_investing"] + v["other_financing"] + v["fx"]}
    notes = [v["notes_" + member] for _, member in NOTE_MEMBERS]
    controls = [v[k] for k in ["adjustment", "annual_cp", "annual_total"]]
    if any(x is None or x < 0 for x in notes + controls):
        result["notes_detail"] = "A due-year carrying amount or reconciliation input is missing or negative."
    elif sum(notes) - v["adjustment"] + v["annual_cp"] != v["annual_total"]:
        result["notes_detail"] = "Due-year notes less the printed negative adjustment plus commercial paper do not reconcile."
    else:
        result["notes_schedule"] = {"total_notes": sum(notes), "adjustment_coefficient": -1,
                                    "total_debt": v["annual_total"], "basis": "Historical carrying amounts, not principal cash payments"}
    if text_checked:
        for key, label, value, date, kind, source, location, detail in DISCLOSURES:
            f = dict(key=key, label=label, value=value, period_end=date, period_start=None,
                     kind=kind, source_kind="Reviewed filing text", tag=None, context_id=None,
                     unit="USD", scale=None, decimals=None, dimensions=[], location=location, detail=detail,
                     **SOURCES[source])
            result["disclosures"].append(f)
    return result


def audit_sources(folder: Path) -> bool:
    """No unreviewed replacement document may inherit the manually checked prose findings."""
    return all((folder / s["document"]).is_file() and
               hashlib.sha256((folder / s["document"]).read_bytes()).hexdigest() == s["sha256"]
               for s in SOURCES.values())


def load():
    return json.loads(SAMPLE.read_text())


def for_snapshot(snapshot):
    if snapshot["ticker"] != "LLY":
        return None
    review = load()
    m = snapshot["metrics"]
    if (m["cash"]["accession"] != review["accession"] or m["cash"]["period_end"] != END or
            m["cash"]["value"] != review["inputs"]["closing"]["value"] or
            m["gross_debt"]["value"] != sum(review["inputs"][k]["value"] for k in ["current_debt", "noncurrent_debt"])):
        return None
    return review
