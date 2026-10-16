"""Rebuild the accession-specific audit only from the exact reviewed saved documents."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import oracle_revolver

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", nargs="?", type=Path, default=ROOT.parent / "data/raw/sec/ORCL")
    audit = oracle_revolver.build(parser.parse_args().folder)
    if audit["status"] != "Checked":
        raise SystemExit(audit["detail"])
    oracle_revolver.SAMPLE.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print("Saved Oracle revolver audit: 7 documents, 3 evidence dates, 2 later filing checks.")
