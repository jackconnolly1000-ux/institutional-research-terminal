"""Preserve the real per-instrument borrowing facts from the saved Oracle 10-K and 10-Q, unchanged.

Reads the two full filings outside the repository (data/raw/sec/ORCL) and keeps only the facts
oracle_principal.py reads, with their contexts and units, so the calendar tests run offline.
"""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import filing_xbrl as fx  # noqa: E402

XHTML = "http://www.w3.org/1999/xhtml"
for prefix, uri in {"": XHTML, **fx.NS}.items():
    ET.register_namespace(prefix, uri)
RAW = ROOT.parent / "data/raw/sec/ORCL"
KEEP = {
    "orcl-20260531.htm": ("ORCL_2026_principal.htm", {
        "us-gaap:DebtInstrumentCarryingAmount", "us-gaap:DebtInstrumentFaceAmount",
        "us-gaap:DebtInstrumentMaturityDate", "us-gaap:DebtInstrumentInterestRateStatedPercentage",
        "us-gaap:DebtLongtermAndShorttermCombinedAmount",
        "us-gaap:DebtInstrumentUnamortizedDiscountPremiumAndDebtIssuanceCostsNet"}),
    "orcl-20260831.htm": ("ORCL_2027Q1_principal.htm", {
        "us-gaap:DebtInstrumentCarryingAmount", "us-gaap:NotesPayableCurrent", "us-gaap:LongTermNotesAndLoans",
        "us-gaap:RepaymentsOfDebt", "us-gaap:RepaymentsOfCommercialPaper"}),
}
for source, (target, tags) in KEEP.items():
    root = ET.parse(RAW / source).getroot()
    facts = [e for e in root.iter() if e.tag in (f"{{{fx.IX}}}nonFraction", f"{{{fx.IX}}}nonNumeric")
             and e.get("name") in tags]
    contexts, units = {e.get("contextRef") for e in facts}, {e.get("unitRef") for e in facts if e.get("unitRef")}
    html = ET.Element(f"{{{XHTML}}}html")
    body = ET.SubElement(html, f"{{{XHTML}}}body")
    resources = ET.SubElement(ET.SubElement(body, f"{{{fx.IX}}}header"), f"{{{fx.IX}}}resources")
    resources.extend(e for e in root.iter(f"{{{fx.XBRLI}}}context") if e.get("id") in contexts)
    resources.extend(e for e in root.iter(f"{{{fx.XBRLI}}}unit") if e.get("id") in units)
    for fact in facts:
        fact.tail = None
        ET.SubElement(body, f"{{{XHTML}}}p").append(fact)
    ET.ElementTree(html).write(Path(__file__).parent / target, encoding="utf-8", xml_declaration=True)
    print(target, len(facts), "facts")
