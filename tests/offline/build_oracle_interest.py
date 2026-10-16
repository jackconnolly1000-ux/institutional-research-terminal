"""Freeze the reviewed Oracle coverage facts without network or AI calls."""
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import oracle_interest as oi

raw = ROOT.parent / "data/raw/sec/ORCL"
for s in oi.SOURCES.values():
    if hashlib.sha256((raw / s["document"]).read_bytes()).hexdigest() != s["sha256"]:
        raise SystemExit("Source changed; review composition and capitalization before rebuilding")
r = oi.build(*(raw / oi.SOURCES[k]["document"] for k in ["annual", "quarter"]))
if r["calculation"]["value"] is None or oi.fingerprint(r["inputs"]) != oi.CHECKED_INPUTS_SHA256:
    raise SystemExit("Extracted inputs differ from checked evidence")
oi.SAMPLE.write_text(json.dumps(r, indent=2) + "\n")
print(json.dumps(r["calculation"], indent=2))
