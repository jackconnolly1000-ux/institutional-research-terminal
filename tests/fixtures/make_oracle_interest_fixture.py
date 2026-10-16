"""Keep all real facts for the selected tags, including segment facts that must be refused."""
import hashlib
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import oracle_interest as oi
import filing_xbrl as fx

for prefix, uri in {"": "http://www.w3.org/1999/xhtml", **fx.NS}.items():
    ET.register_namespace(prefix, uri)
for source, output in [("annual", "ORCL_2026_interest.htm"), ("quarter", "ORCL_2027Q1_interest.htm")]:
    meta = oi.SOURCES[source]
    path = ROOT.parent / "data/raw/sec/ORCL" / meta["document"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta["sha256"]:
        raise SystemExit("Changed source needs renewed review")
    root = ET.parse(path).getroot()
    facts = [f for f in root.iter(f"{{{fx.IX}}}nonFraction") if f.get("name") in oi.TAGS.values()]
    contexts, units = {f.get("contextRef") for f in facts}, {f.get("unitRef") for f in facts}
    copy = ET.Element("html");resources = ET.SubElement(copy, "resources")
    resources.extend(c for c in root.iter(f"{{{fx.XBRLI}}}context") if c.get("id") in contexts)
    resources.extend(c for c in root.iter(f"{{{fx.XBRLI}}}unit") if c.get("id") in units)
    for f in facts:
        f.tail = None;ET.SubElement(copy, "p").append(f)
    ET.ElementTree(copy).write(Path(__file__).parent / output, encoding="utf-8", xml_declaration=True)
    print(output, len(facts), "real facts")
