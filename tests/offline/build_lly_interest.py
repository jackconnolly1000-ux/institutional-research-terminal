"""Freeze the checked Lilly interest review; no retrieval or paid calls."""
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import lly_interest as li
import lly_liquidity as ll

raw = ROOT.parent / "data/raw/sec/LLY"
for role in ["annual", "quarter"]:
    source = ll.SOURCES[role]
    if hashlib.sha256((raw / source["document"]).read_bytes()).hexdigest() != source["sha256"]:
        raise SystemExit("Changed source needs renewed table and capitalization-basis review.")
r = li.build(raw / ll.SOURCES["annual"]["document"], raw / ll.SOURCES["quarter"]["document"])
if r["calculation"]["value"] is None:
    raise SystemExit(r["calculation"]["detail"])
if hashlib.sha256(json.dumps(r["inputs"], sort_keys=True, separators=(",", ":")).encode()).hexdigest() != li.CHECKED_INPUTS_SHA256:
    raise SystemExit("Extracted inputs differ from the checked values; review before freezing.")
li.SAMPLE.write_text(json.dumps(r, indent=2) + "\n")
print(json.dumps(r["calculation"], indent=2))
