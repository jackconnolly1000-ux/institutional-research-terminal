"""Retain real interest and operating facts, including parent/segment facts to be refused."""
import hashlib
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import vistra_interest as vi
import filing_xbrl as fx

for prefix, uri in {"": "http://www.w3.org/1999/xhtml", **fx.NS}.items():
    ET.register_namespace(prefix, uri)
for source, name in [("annual", "VST_2025_interest.htm"), ("quarter", "VST_2026H1_interest.htm"),
                     ("prior_original", "VST_2025H1_interest.htm")]:
    meta = vi.SOURCES[source];p = ROOT.parent / "data/raw/sec/VST" / meta["document"]
    if hashlib.sha256(p.read_bytes()).hexdigest() != meta["sha256"]:
        raise SystemExit("Changed source requires review")
    root = ET.parse(p).getroot()
    facts = [f for f in root.iter(f"{{{fx.IX}}}nonFraction") if f.get("name") in vi.TAGS.values()]
    contexts, units = {f.get("contextRef") for f in facts}, {f.get("unitRef") for f in facts}
    out = ET.Element("html");res = ET.SubElement(out, "resources")
    res.extend(c for c in root.iter(f"{{{fx.XBRLI}}}context") if c.get("id") in contexts)
    res.extend(u for u in root.iter(f"{{{fx.XBRLI}}}unit") if u.get("id") in units)
    for f in facts:
        f.tail = None;ET.SubElement(out, "p").append(f)
    ET.ElementTree(out).write(Path(__file__).parent / name, encoding="utf-8", xml_declaration=True)
    print(name, len(facts), "real facts")
