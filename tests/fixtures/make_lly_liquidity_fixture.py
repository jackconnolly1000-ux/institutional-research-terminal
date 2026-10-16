"""Retain real Lilly liquidity facts, including all competing dates and dimensions."""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import filing_xbrl as fx
import lly_liquidity as ll

raw = ROOT.parent / "data/raw/sec/LLY"
if not ll.audit_sources(raw):
    raise SystemExit("Saved source hashes differ from the reviewed documents; review required.")
XHTML = "http://www.w3.org/1999/xhtml"
for prefix, uri in {"": XHTML, **fx.NS}.items():
    ET.register_namespace(prefix, uri)
tags = {"us-gaap:" + v[1] for v in ll.FLOWS.values()} | {
    "us-gaap:" + t for t in ["CashAndCashEquivalentsAtCarryingValue", "DebtCurrent", "LongTermDebtNoncurrent",
    "BusinessCombinationContingentConsiderationLiabilityCurrent", "BusinessCombinationContingentConsiderationLiabilityNoncurrent",
    "DebtInstrumentCarryingAmount", "OtherLongTermDebt", "CommercialPaper", "DebtLongtermAndShorttermCombinedAmount",
    "LineOfCreditFacilityRemainingBorrowingCapacity", "LineOfCreditFacilityMaximumBorrowingCapacity"]}
for source, name in [("annual", "LLY_2025_liquidity.htm"), ("quarter", "LLY_2026H1_liquidity.htm")]:
    root = ET.parse(raw / ll.SOURCES[source]["document"]).getroot()
    facts = [e for e in root.iter(f"{{{fx.IX}}}nonFraction") if e.get("name") in tags]
    contexts, units = {e.get("contextRef") for e in facts}, {e.get("unitRef") for e in facts}
    html = ET.Element(f"{{{XHTML}}}html")
    body = ET.SubElement(html, f"{{{XHTML}}}body")
    resources = ET.SubElement(ET.SubElement(body, f"{{{fx.IX}}}header"), f"{{{fx.IX}}}resources")
    resources.extend(e for e in root.iter(f"{{{fx.XBRLI}}}context") if e.get("id") in contexts)
    resources.extend(e for e in root.iter(f"{{{fx.XBRLI}}}unit") if e.get("id") in units)
    for f in facts:
        f.tail = None
        ET.SubElement(body, f"{{{XHTML}}}p").append(f)
    ET.ElementTree(html).write(Path(__file__).parent / name, encoding="utf-8", xml_declaration=True)
    print(name, len(facts), "facts")
