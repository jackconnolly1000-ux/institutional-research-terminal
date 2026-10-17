"""Make every source URL in the three company workbooks a native, clickable hyperlink.

The workbook builders' spreadsheet runtime can't author hyperlink actions, so URLs were full, copyable text
(known problem 9). This edits only worksheet XML and worksheet relationship parts inside each saved .xlsx:
each cell whose text is an https URL (or "Source: https://…") gets a hyperlink to exactly that URL, and the two
guide sentences that told readers to copy URLs are updated. Cell values and styles are unchanged; links keep the
existing text style because blue text means a reported input in these workbooks. It refuses a workbook that
doesn't match its manifest, then records the new bytes. No network, no AI calls.

Run from app/:  .venv/Scripts/python tests/offline/add_workbook_hyperlinks.py
"""
import hashlib
import html
import json
import re
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "samples"
STEMS = ("lly_liquidity", "oracle_liquidity", "vistra_liquidity")
LINK = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CELL = re.compile(r'<x:c r="([A-Z]+\d+)"[^>]*t="str"><x:v>((?:Source: )?https://[^<]+)</x:v></x:c>')
GUIDE = {"Copy a full URL into a browser to open the source.": "Select a source URL to open it in a browser.",
         "URLs remain full, copyable source text. Native hyperlink actions are not authored by this spreadsheet runtime.":
             "Source URLs are full text and open as links when selected."}


def link_sheet(xml, rels, sheet_name):
    """Return (xml, rels, count) with a hyperlink for each URL cell; rels is the sheet's relationships XML or None."""
    found = [(ref, html.unescape(text).removeprefix("Source: ")) for ref, text in CELL.findall(xml)]
    if not found:
        return xml, rels, 0
    if "<x:hyperlinks" in xml:
        raise SystemExit(f"{sheet_name} already has hyperlinks")
    rels = rels or ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>')
    links, entries = [], []
    for k, (ref, url) in enumerate(found, 1):
        rid = f"rIdSource{k}"
        if f'Id="{rid}"' in rels:
            raise SystemExit(f"{sheet_name}: relationship id {rid} already used")
        entries.append(f'<Relationship Id="{rid}" Type="{LINK}" Target={quoteattr(url)} TargetMode="External"/>')
        links.append(f'<x:hyperlink ref="{ref}" r:id="{rid}"/>')
    block = f'<x:hyperlinks xmlns:r="{REL_NS}">' + "".join(links) + "</x:hyperlinks>"
    if xml.count("<x:pageMargins") != 1:
        raise SystemExit(f"{sheet_name}: expected one pageMargins element to place hyperlinks before")
    xml = xml.replace("<x:pageMargins", block + "<x:pageMargins", 1)   # schema order: after mergeCells, before pageMargins
    rels = rels.replace("</Relationships>", "".join(entries) + "</Relationships>", 1)
    return xml, rels, len(found)


def patch(stem):
    path, manifest_path = SAMPLES / f"{stem}.xlsx", SAMPLES / f"{stem}.manifest.json"
    content, manifest = path.read_bytes(), json.loads(manifest_path.read_text())
    if hashlib.sha256(content).hexdigest() != manifest["workbook_sha256"]:
        raise SystemExit(f"{stem}: workbook doesn't match its manifest; refusing to edit it")
    src = zipfile.ZipFile(BytesIO(content))
    names = src.namelist()
    replaced, total, guide_hits = {}, 0, dict.fromkeys(GUIDE, 0)
    for name in names:
        if not re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name):
            continue
        xml = src.read(name).decode("utf-8")
        for old, new in GUIDE.items():
            guide_hits[old] += xml.count(escape(old))
            xml = xml.replace(escape(old), escape(new))
        rels_name = name.replace("worksheets/", "worksheets/_rels/") + ".rels"
        rels = src.read(rels_name).decode("utf-8-sig") if rels_name in names else None
        xml, rels, count = link_sheet(xml, rels, name)
        total += count
        replaced[name] = xml
        if count:
            replaced[rels_name] = rels
    if any(hits != 1 for hits in guide_hits.values()):
        raise SystemExit(f"{stem}: guide sentences not found exactly once: {guide_hits}")
    out = BytesIO()
    with zipfile.ZipFile(out, "w") as dst:
        for info in src.infolist():
            data = replaced.get(info.filename)
            dst.writestr(info, data.encode("utf-8") if data is not None else src.read(info.filename))
        for name, data in replaced.items():   # relationship parts that didn't exist before
            if name not in names:
                dst.writestr(zipfile.ZipInfo(name, date_time=(2026, 10, 17, 0, 0, 0)), data.encode("utf-8"),
                             compress_type=zipfile.ZIP_DEFLATED)
    new = out.getvalue()
    path.write_bytes(new)
    manifest["workbook_sha256"] = hashlib.sha256(new).hexdigest()
    manifest_path.write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))   # LF, as git stores it
    print(f"{stem}: {total} source links;", manifest["workbook_sha256"][:12])


if __name__ == "__main__":
    for stem in STEMS:
        patch(stem)
