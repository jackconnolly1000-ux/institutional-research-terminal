"""Keep the six reviewed cash-flow statements' real facts, contexts and units, unchanged.

Run from the repository after saving the source documents under ../data/raw/sec/<ticker>/.
These small fixtures retain all occurrences, including other periods and dimensions, so the reader must select.
"""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import cash_generation as cg  # noqa: E402
import filing_xbrl as fx  # noqa: E402

XHTML = "http://www.w3.org/1999/xhtml"
for prefix, uri in {"": XHTML, **fx.NS}.items():
    ET.register_namespace(prefix, uri)
for ticker, spec in cg.SOURCES.items():
    for role in ("annual", "quarter"):
        filename = spec[role][1]
        root = ET.parse(ROOT.parent / "data/raw/sec" / ticker / filename).getroot()
        facts = [e for e in root.iter(f"{{{fx.IX}}}nonFraction")
                 if e.get("name") in {cg.OCF, spec["capex_tag"]}]
        contexts = {e.get("contextRef") for e in facts}
        units = {e.get("unitRef") for e in facts}
        html = ET.Element(f"{{{XHTML}}}html")
        body = ET.SubElement(html, f"{{{XHTML}}}body")
        resources = ET.SubElement(ET.SubElement(body, f"{{{fx.IX}}}header"), f"{{{fx.IX}}}resources")
        resources.extend(e for e in root.iter(f"{{{fx.XBRLI}}}context") if e.get("id") in contexts)
        resources.extend(e for e in root.iter(f"{{{fx.XBRLI}}}unit") if e.get("id") in units)
        for fact in facts:
            fact.tail = None
            ET.SubElement(body, f"{{{XHTML}}}p").append(fact)
        output = Path(__file__).parent / f"{ticker}_{role}_cashflow.htm"
        ET.ElementTree(html).write(output, encoding="utf-8", xml_declaration=True)
        print(output.name, len(facts), "facts")
