"""Check saved annual balance sheets against selectors before freezing history inputs."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import cash_generation as cg
import filing_xbrl as fx
import xbrl

EXPECTED = {"LLY": [7268, 55629, 35228, 1635, 40868],
            "ORCL": [31289, 46567, 41764, 7199, 122342], "VST": [785, 9179, 11814]}
LOCATIONS = {"LLY": "10-K balance sheet p. 56; cash flows p. 58",
             "ORCL": "10-K balance sheet p. 64; cash/restricted cash policy p. 70",
             "VST": "10-K balance sheet p. 80; cash/restricted cash reconciliation"}
out = {}
for ticker, values in EXPECTED.items():
    acc, document, filed, start, end = cg.SOURCES[ticker]["annual"]
    path = ROOT.parent / "data/raw/sec" / ticker / document
    tree = fx.ET.parse(path)
    facts = json.loads((ROOT / f"tests/fixtures/{ticker}_companyfacts.json").read_text())
    cash = xbrl.cash_and_equivalents(facts, filed_by=filed)
    ratio = xbrl.current_ratio(facts, filed_by=filed)
    debt = xbrl.baseline_gross_debt(facts, ticker, filed_by=filed)
    selected = [cash, ratio["inputs"]["current_assets"], ratio["inputs"]["current_liabilities"]]
    if ticker != "VST":
        selected += debt["inputs"]
    checked = []
    for f, expected in zip(selected, values):
        raw = fx.read_instant(path, acc, f["tag"], end)
        assert raw["value"] == f["value"] == expected * 1e6, (ticker, f["tag"], raw)
        context = tree.find(f".//{{{fx.XBRLI}}}context[@id='{raw['context_id']}']")
        entity = context.find(f"{{{fx.XBRLI}}}entity/{{{fx.XBRLI}}}identifier").text
        assert entity.lstrip("0") == str(cg.SOURCES[ticker]["cik"])
        checked.append({**f, **raw, "unit": "USD", "period_end": end, "source_url":
            f"https://www.sec.gov/Archives/edgar/data/{cg.SOURCES[ticker]['cik']}/{acc.replace('-', '')}/{document}",
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "location": LOCATIONS[ticker]})
    out[ticker] = {"annual_start": start, "annual_end": end, "accession": acc, "facts": checked,
                   "debt_detail": debt["detail"] if ticker == "VST" else ""}
(ROOT / "samples/company_history.json").write_text(json.dumps(out, indent=2) + "\n")
print("Annual instant facts checked for LLY, ORCL and VST")
