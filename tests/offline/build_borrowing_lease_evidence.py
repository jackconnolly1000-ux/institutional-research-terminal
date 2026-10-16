"""Reproduce only the lease facts checked in the pilot evidence. No network."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from filing_xbrl import read_instant

RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "data/raw/sec"
snapshots = json.loads((ROOT / "samples/liquidity_pilots.json").read_text())["snapshots"]
SOURCES = {
    "LLY": ("lly-20251231.htm", "0000059478-26-000013", "2025-12-31", "2026-02-12", "10-K Note 10, p. 76", 59478,
            [222, 1140, None, None, None, None]),
    "ORCL": ("orcl-20260831.htm", "0001193125-26-389274", "2026-08-31", "2026-09-11", "10-Q Note 6, pp. 12–13", 1341439,
             [4027, 30594, 34621, 749, 8436, 9185]),
    "VST": ("vistra-20251231.htm", "0001692819-26-000006", "2025-12-31", "2026-02-27", "10-K lease note, pp. 122–123", 1692819,
            [13, 92, 105, 4, 218, 222]),
}
TAGS = ["OperatingLeaseLiabilityCurrent", "OperatingLeaseLiabilityNoncurrent", "OperatingLeaseLiability",
        "FinanceLeaseLiabilityCurrent", "FinanceLeaseLiabilityNoncurrent", "FinanceLeaseLiability"]
out = {"checked_as_of": "2026-10-16", "companies": {}}
for snapshot in snapshots:
    ticker = snapshot["ticker"]
    name, acc, end, filed, location, cik, values = SOURCES[ticker]
    path = RAW / ticker / name
    facts = {}
    for tag, expected in zip(TAGS, values):
        if expected is None:
            continue
        fact = read_instant(path, acc, "us-gaap:" + tag, end)
        assert fact["value"] == expected * 1_000_000, (ticker, tag, fact)
        facts[tag] = {**fact, "label": tag, "period_end": end, "filed": filed,
                      "form": "10-Q" if ticker == "ORCL" else "10-K", "location": location,
                      "source_url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{name}",
                      "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    if ticker == "ORCL":
        fact = read_instant(path, acc, "orcl:LesseeOperatingLeaseLeaseNotYetCommencedLeaseCommitments", end)
        assert fact["value"] == 288_000_000_000
        facts["not_commenced"] = {**facts["OperatingLeaseLiability"], **fact,
                                  "label": "Leases not yet commenced", "location": "10-Q Note 6, p. 13"}
    out["companies"][ticker] = {"anchor_accession": snapshot["metrics"]["cash"]["accession"],
        "anchor_date": snapshot["metrics"]["cash"]["period_end"], "facts": facts}
(ROOT / "samples/borrowing_leases.json").write_text(json.dumps(out, indent=2) + "\n")
print("Checked lease facts rebuilt for", ", ".join(out["companies"]))
