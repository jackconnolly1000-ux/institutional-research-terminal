"""Rebuild the frozen pilot with the production selectors; no network or Claude calls."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import liquidity_pilot  # noqa: E402
import cash_generation  # noqa: E402

fixtures = ROOT / "tests" / "fixtures"
snapshots = []
for ticker, company in liquidity_pilot.PILOTS.items():
    facts = json.loads((fixtures / f"{ticker}_companyfacts.json").read_text())
    docs = {company["accession"]: fixtures / "VST_2026Q2_ixbrl.htm"} if ticker == "VST" else None
    flows = {cash_generation.SOURCES[ticker][role][0]: fixtures / f"{ticker}_{role}_cashflow.htm"
             for role in ("annual", "quarter")}
    snapshot = liquidity_pilot.build_snapshot(facts, ticker, docs, flows)
    snapshots.append(snapshot)
liquidity_pilot.SAMPLE.write_text(json.dumps({"checked_as_of": liquidity_pilot.FILED_BY,
                                             "snapshots": snapshots}, indent=2) + "\n", encoding="utf-8")
print("Built", liquidity_pilot.SAMPLE.name)
