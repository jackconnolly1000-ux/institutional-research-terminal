"""Build tests/fixtures/VST_2026Q2_ixbrl.htm: a trimmed copy of Vistra's Jun 30, 2026 10-Q inline XBRL.

The full document (3.8 MB, saved outside the repo) is too large to commit. This keeps, unchanged, every ix:nonFraction
fact for the tags below (attributes and displayed text as filed) plus the contexts and units they refer to, so
filing_xbrl.py is tested on real filing data. Download the 10-Q into Stock Project/data/raw/sec/VST/, then from app/:
    .venv/bin/python tests/fixtures/make_filing_fixture.py        (Windows: .venv\\Scripts\\python)
"""
import xml.etree.ElementTree as ET
from pathlib import Path

APP = Path(__file__).resolve().parents[2]
SOURCE = APP.parent / "data" / "raw" / "sec" / "VST" / "vistra-20260630.htm"   # accession 0001692819-26-000019
OUT = Path(__file__).parent / "VST_2026Q2_ixbrl.htm"
TAGS = {
    "vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed",   # balance sheet (c-8) and Note 12 (c-722)
    "vistra:ProceedsFromRepaymentsOfAccountsReceivableFinancing",      # durations only, for the rejection test
    "us-gaap:ShortTermBorrowings",                                     # printed "—", ixt:fixed-zero
    "us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent",
    "us-gaap:LongTermDebtAndCapitalLeaseObligations",
}
XHTML, IX, XBRLI = "http://www.w3.org/1999/xhtml", "http://www.xbrl.org/2013/inlineXBRL", "http://www.xbrl.org/2003/instance"

# Keep the filer's prefixes when writing
for prefix, uri in {"": XHTML, "ix": IX, "xbrli": XBRLI, "xbrldi": "http://xbrl.org/2006/xbrldi",
                    "ixt": "http://www.xbrl.org/inlineXBRL/transformation/2020-02-12",
                    "iso4217": "http://www.xbrl.org/2003/iso4217"}.items():
    ET.register_namespace(prefix, uri)

root = ET.parse(SOURCE).getroot()
facts = [f for f in root.iter(f"{{{IX}}}nonFraction") if f.get("name") in TAGS]
context_ids = {f.get("contextRef") for f in facts}
unit_ids = {f.get("unitRef") for f in facts}

html = ET.Element(f"{{{XHTML}}}html")
body = ET.SubElement(html, f"{{{XHTML}}}body")
hidden = ET.SubElement(body, f"{{{XHTML}}}div", {"style": "display:none"})
resources = ET.SubElement(ET.SubElement(hidden, f"{{{IX}}}header"), f"{{{IX}}}resources")
resources.extend(c for c in root.iter(f"{{{XBRLI}}}context") if c.get("id") in context_ids)
resources.extend(u for u in root.iter(f"{{{XBRLI}}}unit") if u.get("id") in unit_ids)
for f in facts:
    f.tail = None
    ET.SubElement(body, f"{{{XHTML}}}p").append(f)
ET.ElementTree(html).write(OUT, encoding="utf-8", xml_declaration=True)
print(f"{OUT.name}: {len(facts)} facts, {len(context_ids)} contexts, {OUT.stat().st_size:,} bytes")
