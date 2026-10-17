"""Rebuild samples/oracle_principal.json from the two full saved Oracle filings. No network, no AI calls.

Run from app/:  .venv/Scripts/python tests/offline/build_oracle_principal.py
The saved filings live outside the repository in ../data/raw/sec/ORCL. The build refuses to write a
calendar whose checks do not all agree, and records each source document's SHA-256.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import oracle_principal as op  # noqa: E402

RAW = ROOT.parent / "data/raw/sec/ORCL"
annual, quarter = RAW / op.ANNUAL["document"], RAW / op.QUARTERLY["document"]
review = op.build(annual, quarter)
if review["status"] != "Checked":
    raise SystemExit("Calendar checks did not all agree: " + review.get("detail", json.dumps(review["checks"])[:2000]))
review["source_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (annual, quarter)}
# LF explicitly: git stores LF (.gitattributes), and the workbook manifest fingerprints these exact bytes
op.SAMPLE.write_bytes((json.dumps(review, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print(op.SAMPLE.name, len(review["instruments"]), "instruments,", len(review["checks"]), "checks agree")
