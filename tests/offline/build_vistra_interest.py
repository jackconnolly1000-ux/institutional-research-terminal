"""Freeze the reviewed Vistra interest bridge without network or AI calls."""
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import vistra_interest as vi

raw = ROOT.parent / "data/raw/sec/VST"
for name, digest in {**{s["document"]:s["sha256"] for s in vi.SOURCES.values()}, **vi.TAXONOMY}.items():
    if hashlib.sha256((raw / name).read_bytes()).hexdigest() != digest:
        raise SystemExit("Source changed; review periods, definitions and sign conventions before rebuilding")
r = vi.build(*(raw / vi.SOURCES[k]["document"] for k in ["annual", "quarter", "prior_original"]))
if r["calculation"]["value"] is None or vi.fingerprint(r["inputs"]) != vi.CHECKED_INPUTS_SHA256:
    raise SystemExit("Extracted inputs differ from the checked evidence")
vi.SAMPLE.write_text(json.dumps(r, indent=2) + "\n")
print(json.dumps(r["calculation"], indent=2))
