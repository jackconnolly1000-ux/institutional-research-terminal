"""Rebuild the saved maturity schedule from real filing facts without network access."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import oracle_financing as of  # noqa: E402

snapshot = of.build(ROOT / "tests/fixtures/ORCL_2026_maturities.htm",
                    ROOT / "tests/fixtures/ORCL_2026Q1_financing.htm")
if snapshot["status"] != "Checked":
    raise ValueError(snapshot["detail"])
of.SAMPLE.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
print("Built", of.SAMPLE.name)
