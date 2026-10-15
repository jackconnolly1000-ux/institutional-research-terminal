"""Keep all occurrences of the checked Oracle tags, with their real contexts and units."""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import filing_xbrl as fx
import oracle_liquidity as ol

XHTML = "http://www.w3.org/1999/xhtml"
for prefix, uri in {"": XHTML, **fx.NS}.items():
    ET.register_namespace(prefix, uri)
root = ET.parse(ROOT.parent / "data/raw/sec/ORCL/orcl-20260831.htm").getroot()
tags = {row[1] for row in ol.FLOWS.values()} | {row[1] for row in ol.INSTANTS.values()}
tags |= {"us-gaap:" + t for rows in ol.SCHEDULES.values() for t in rows}
tags |= {"us-gaap:" + t for t in ol.CONTROLS.values()}
facts = [e for e in root.iter(f"{{{fx.IX}}}nonFraction") if e.get("name") in tags]
contexts, units = {e.get("contextRef") for e in facts}, {e.get("unitRef") for e in facts}
html = ET.Element(f"{{{XHTML}}}html")
body = ET.SubElement(html, f"{{{XHTML}}}body")
resources = ET.SubElement(ET.SubElement(body, f"{{{fx.IX}}}header"), f"{{{fx.IX}}}resources")
resources.extend(e for e in root.iter(f"{{{fx.XBRLI}}}context") if e.get("id") in contexts)
resources.extend(e for e in root.iter(f"{{{fx.XBRLI}}}unit") if e.get("id") in units)
for fact in facts:
    fact.tail = None
    ET.SubElement(body, f"{{{XHTML}}}p").append(fact)
output = Path(__file__).parent / "ORCL_2026Q1_liquidity.htm"
ET.ElementTree(html).write(output, encoding="utf-8", xml_declaration=True)
print(output.name, len(facts), "facts")
