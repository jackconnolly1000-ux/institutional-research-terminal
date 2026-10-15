"""Rebuild the saved Oracle cash analysis, without network or AI calls."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import oracle_liquidity as ol

review = ol.build(ROOT / "tests/fixtures/ORCL_2026Q1_liquidity.htm")
if review["status"] != "Checked" or any(s["status"] != "Checked" for s in review["schedules"].values()):
    raise ValueError(review["detail"] or review["schedules"])
ol.SAMPLE.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
print("Built", ol.SAMPLE.name, review["cash"])
