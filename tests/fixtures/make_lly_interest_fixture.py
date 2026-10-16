"""Preserve the real operations table and all competing interest facts and contexts."""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import filing_xbrl as fx
import lly_interest as li
import lly_liquidity as ll

raw = ROOT.parent / "data/raw/sec/LLY"
if not ll.audit_sources(raw):
    raise SystemExit("Changed source documents need review.")
for prefix, uri in {"": "http://www.w3.org/1999/xhtml", **fx.NS}.items():
    ET.register_namespace(prefix, uri)
for role, output in [("annual", "LLY_2025_interest.htm"), ("quarter", "LLY_2026H1_interest.htm")]:
    root = ET.parse(raw / ll.SOURCES[role]["document"]).getroot()
    table = li.statement_table(root)
    if table is None:
        raise SystemExit("Unique operations table missing")
    interest = [f for f in root.iter(f"{{{fx.IX}}}nonFraction") if f.get("name") == li.INTEREST]
    # Keep rounded MD&A IPR&D facts too: the test must demonstrate table selection,
    # rather than pass because ambiguous facts were stripped from its fixture.
    inside = set(table.iter(f"{{{fx.IX}}}nonFraction"))
    outside = [f for f in root.iter(f"{{{fx.IX}}}nonFraction") if f not in inside and
               f.get("name") == "us-gaap:" + li.TAGS["iprd"]]
    facts = [*inside, *interest, *outside]
    contexts, units = {f.get("contextRef") for f in facts}, {f.get("unitRef") for f in facts}
    html = ET.Element("html");res = ET.SubElement(html, "resources")
    res.extend(c for c in root.iter(f"{{{fx.XBRLI}}}context") if c.get("id") in contexts)
    res.extend(u for u in root.iter(f"{{{fx.XBRLI}}}unit") if u.get("id") in units)
    html.append(table)
    for f in [*interest, *outside]:
        f.tail = None;ET.SubElement(html, "p").append(f)
    ET.ElementTree(html).write(Path(__file__).parent / output, encoding="utf-8", xml_declaration=True)
    print(output, len(facts), "facts")
