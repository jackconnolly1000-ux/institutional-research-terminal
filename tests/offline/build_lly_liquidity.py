"""Rebuild Lilly's review only after verifying all saved source documents."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import lly_liquidity as ll

raw = ROOT.parent / "data/raw/sec/LLY"
if not ll.audit_sources(raw):
    raise SystemExit("Source documents changed or are missing; manually review before rebuilding.")
review = ll.build(raw / ll.SOURCES["annual"]["document"], raw / ll.SOURCES["quarter"]["document"], text_checked=True)
if review["cash"] is None or review["notes_schedule"] is None:
    raise SystemExit(json.dumps({k: review[k] for k in ["cash_detail", "notes_detail"]}))
ll.SAMPLE.write_text(json.dumps(review, indent=2) + "\n")
print(json.dumps({"cash": review["cash"], "notes": review["notes_schedule"]}, indent=2))
