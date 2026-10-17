"""Apply Artifact Tool-authored column separators without round-tripping native workbook features.

Only border/style references change in existing company files. Original formulas, caches, chart parts,
relationships and hyperlinks remain intact. Run organize_exports.mjs first; pass its output directory.
"""
import copy
import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ET.register_namespace("x", NS)


def apply(stem, folder):
    path = ROOT / "samples" / (stem + "_liquidity.xlsx")
    src = zipfile.ZipFile(path)
    authored = zipfile.ZipFile(folder / (stem + "-layout.xlsx"))
    old = ET.fromstring(src.read("xl/styles.xml")); new = ET.fromstring(authored.read("xl/styles.xml"))
    borders, xfs = old.find(f"{{{NS}}}borders"), old.find(f"{{{NS}}}cellXfs")
    new_borders, new_xfs = new.find(f"{{{NS}}}borders"), new.find(f"{{{NS}}}cellXfs")
    mapped = {}; replaced = {}
    for name in src.namelist():
        if not name.startswith("xl/worksheets/sheet") or not name.endswith(".xml"):
            continue
        root = ET.fromstring(src.read(name))
        layout = {c.attrib["r"]: c for c in ET.fromstring(authored.read(name)).findall(f".//{{{NS}}}c")}
        for c in root.findall(f".//{{{NS}}}sheetData/{{{NS}}}row/{{{NS}}}c"):
            ref = c.attrib["r"]
            if ref not in layout:
                continue
            key = int(c.get("s", "0")), int(layout[ref].get("s", "0"))
            if key not in mapped:
                xf = copy.deepcopy(xfs[key[0]])
                border = copy.deepcopy(borders[int(xf.get("borderId", "0"))])
                overlay = new_borders[int(new_xfs[key[1]].get("borderId", "0"))]
                for side in ("left", "right"):
                    edge = overlay.find(f"{{{NS}}}{side}")
                    if edge is not None and edge.get("style"):
                        prev = border.find(f"{{{NS}}}{side}")
                        if prev is not None:
                            border.remove(prev)
                        border.append(copy.deepcopy(edge))
                order = {name: i for i, name in enumerate(("start", "end", "left", "right", "top", "bottom", "diagonal", "vertical", "horizontal"))}
                border[:] = sorted(border, key=lambda e: order.get(e.tag.rsplit("}", 1)[-1], 99))
                borders.append(border); xf.set("borderId", str(len(borders) - 1)); xf.set("applyBorder", "1")
                mapped[key] = len(xfs); xfs.append(xf)
            c.set("s", str(mapped[key]))
        replaced[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    borders.set("count", str(len(borders))); xfs.set("count", str(len(xfs)))
    replaced["xl/styles.xml"] = ET.tostring(old, encoding="utf-8", xml_declaration=True)
    output = BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as dest:
        for info in src.infolist():
            dest.writestr(info, replaced.get(info.filename, src.read(info.filename)))
    path.write_bytes(output.getvalue())
    manifest = path.with_suffix(".manifest.json")
    m = json.loads(manifest.read_text()); m["workbook_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest.write_bytes((json.dumps(m, indent=2) + "\n").encode())


def main(folder):
    for stem in ("lly", "oracle", "vistra"):
        apply(stem, folder)
    path = ROOT / "samples/liquidity_pilots.xlsx"
    path.write_bytes((folder / "combined.xlsx").read_bytes())
    from add_workbook_hyperlinks import link_sheet
    src = zipfile.ZipFile(path); replaced = {}
    for name in src.namelist():
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
            xml, rels, count = link_sheet(src.read(name).decode(), None, name)
            replaced[name] = xml.encode()
            if count:
                replaced[name.replace("worksheets/", "worksheets/_rels/") + ".rels"] = rels.encode()
    content = BytesIO()
    with zipfile.ZipFile(content, "w", zipfile.ZIP_DEFLATED) as dest:
        for info in src.infolist():
            dest.writestr(info, replaced.get(info.filename, src.read(info.filename)))
        for name in replaced.keys() - set(src.namelist()):
            dest.writestr(name, replaced[name])
    path.write_bytes(content.getvalue())
    p = path.with_suffix(".manifest.json"); m = json.loads(p.read_text())
    m["workbook_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    p.write_bytes((json.dumps(m, indent=2) + "\n").encode())
    import export_guide
    for stem in ("lly", "oracle", "vistra"):
        p = ROOT / "samples" / (stem + "_liquidity.manifest.json")
        m = json.loads(p.read_text()); m["guide_sha256"] = export_guide.fingerprint()
        p.write_bytes((json.dumps(m, indent=2) + "\n").encode())


if __name__ == "__main__":
    main(Path(sys.argv[1]))
