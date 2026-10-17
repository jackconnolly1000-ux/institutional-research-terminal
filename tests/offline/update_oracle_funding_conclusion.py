"""Write Oracle's re-reviewed funding conclusion into the saved Oracle workbook and rebind all three manifests.

Like add_oracle_principal_block.py, this edits worksheet XML inside the saved .xlsx because the usual builder
(build_oracle_liquidity.mjs) needs the Codex artifact runtime. Only the Funding conclusion, Data and About sheets
change: Funding conclusion A3 and B6–B10 take the text and date from funding_conclusions.load("ORCL"); Data's
"Funding conclusion evidence" block (rows 90–100, referenced by no formula) is rewritten from the same sources;
About B2 states the new review date. Lilly and Vistra workbooks are not edited; their manifests are rebound to
the new interpretation fingerprint because the interpretation file is shared. No network, no AI calls.

Run from app/:  .venv/Scripts/python tests/offline/update_oracle_funding_conclusion.py
"""
import hashlib
import json
import re
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import funding_conclusions as fc  # noqa: E402

SAMPLES = ROOT / "samples"
WORKBOOK = SAMPLES / "oracle_liquidity.xlsx"
BEFORE = "12a4075fe96684f42946e464495b5c2ab729681091c988ffeb31a74ca325add6"   # with the principal calendar block
FUNDING, DATA, ABOUT = "xl/worksheets/sheet1.xml", "xl/worksheets/sheet9.xml", "xl/worksheets/sheet10.xml"
BLOCK = range(90, 101)        # free through row 101; the reported-input table starts at row 102
MIDDLE, LAST = ("25", "205", "205", "16", "208"), ("26", "206", "206", "18", "209")   # existing block styles


def set_text(xml, ref, new):
    """Replace one string cell's text, keeping its style."""
    m = re.search(rf'<x:c r="{ref}" s="(\d+)" t="str"><x:v>.*?</x:v></x:c>', xml, re.S)
    if m is None:
        raise SystemExit(f"{ref} is not a string cell as expected")
    return xml[:m.start()] + f'<x:c r="{ref}" s="{m.group(1)}" t="str"><x:v>{escape(new)}</x:v></x:c>' + xml[m.end():]


def evidence_rows(review):
    rows = [(label, s) for label, _, sources in review["rows"] for s in sources]
    rows += [("Historical coverage", s) for s in review["coverage_sources"]]
    if len(rows) > len(BLOCK):
        raise SystemExit("The funding evidence no longer fits above the reported-input table")
    out = ""
    for k, (label, s) in enumerate(rows):
        r = BLOCK.start + k
        st = LAST if k == len(rows) - 1 else MIDDLE
        cells = [("A", st[0], label), ("B", st[1], s["label"]), ("C", st[2], s["accession"]),
                 ("D", st[3], s["location"]), ("M", st[4], s["url"])]
        out += (f'<x:row r="{r}" ht="72" customHeight="1">'
                + "".join(f'<x:c r="{c}{r}" s="{style}" t="str"><x:v>{escape(v)}</x:v></x:c>' for c, style, v in cells)
                + "</x:row>")
    return out


def main():
    content = WORKBOOK.read_bytes()
    if hashlib.sha256(content).hexdigest() != BEFORE:
        raise SystemExit("The saved Oracle workbook is not the reviewed calendar version; refusing to edit it.")
    review = fc.load("ORCL")
    if review is None:
        raise SystemExit("Oracle's funding conclusion does not load against its checked evidence.")
    src = zipfile.ZipFile(BytesIO(content))

    funding = src.read(FUNDING).decode("utf-8")
    funding = set_text(funding, "A3", f"Balance sheet {review['period_end']}. Interpretation checked {review['reviewed']}. "
                                      "Source dates remain historical.")
    funding = set_text(funding, "B6", review["conclusion"])
    for row, (_, text, _) in enumerate(review["rows"], 7):
        funding = set_text(funding, f"B{row}", text)
    # Existing row heights (55 and 76 points) already fit the longer text; Excel's AutoFit needs 51 for both.

    data = src.read(DATA).decode("utf-8")
    start = data.index(f'<x:row r="{BLOCK.start}"')
    end = data.index('<x:row r="102"')
    if any(f'<x:row r="{r}"' in data[start:end] for r in (100, 101)):
        raise SystemExit("Rows 100–101 are no longer free")
    data = data[:start] + evidence_rows(review) + data[end:]

    about = src.read(ABOUT).decode("utf-8")
    about = set_text(about, "B2", "Cash review checked October 15, 2026; interest and index consistency checked October 16; "
                                  "funding interpretation re-checked October 17 against the August 31 principal calendar. "
                                  "Cash flows remain June 1–August 31, 2026. Not live data or investment advice.")

    out = BytesIO()
    with zipfile.ZipFile(out, "w") as dst:
        for info in src.infolist():
            data_bytes = {FUNDING: funding, DATA: data, ABOUT: about}.get(info.filename)
            dst.writestr(info, data_bytes.encode("utf-8") if data_bytes is not None else src.read(info.filename))
    new = out.getvalue()
    WORKBOOK.write_bytes(new)
    for stem in ("lly_liquidity", "oracle_liquidity", "vistra_liquidity"):
        path = SAMPLES / f"{stem}.manifest.json"
        manifest = json.loads(path.read_text())
        manifest["funding_sha256"] = fc.fingerprint()
        if stem == "oracle_liquidity":
            manifest["workbook_sha256"] = hashlib.sha256(new).hexdigest()
        path.write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))   # LF, as git stores it
    print("Oracle funding conclusion written;", WORKBOOK.name, hashlib.sha256(new).hexdigest()[:12],
          "; three manifests rebound to", fc.fingerprint()[:12])


if __name__ == "__main__":
    main()
