"""Correct one stale About-sheet sentence in the saved combined workbook and rebind its manifest.

The combined export (samples/liquidity_pilots.xlsx) was built on Oct 15, before Oracle's August 31 principal
calendar was checked (Oct 17). Its About sheet, B7, said the August schedule was Unavailable. Only that cell's
text changes; every other byte of every part is copied unchanged, and the manifest's workbook fingerprint is rebound.
Run from app/: .venv\\Scripts\\python tests/offline/patch_combined_principal_note.py
"""
import hashlib
import json
import sys
import zipfile
from io import BytesIO
from pathlib import Path

SAMPLES = Path(__file__).resolve().parents[2] / "samples"
WORKBOOK = SAMPLES / "liquidity_pilots.xlsx"
MANIFEST = SAMPLES / "liquidity_pilots.manifest.json"
SHEET = "xl/worksheets/sheet3.xml"   # About
OLD = "August schedule and revolver availability are Unavailable."
NEW = ("August 31 note and term-loan principal is dated in the individual Oracle workbook (Payment dates); "
       "commercial paper and current revolver availability are Unavailable.")


def main() -> None:
    src = zipfile.ZipFile(BytesIO(WORKBOOK.read_bytes()))
    about = src.read(SHEET).decode("utf-8")
    if NEW in about:
        print("Already patched.")
        return
    if about.count(OLD) != 1:
        sys.exit("Expected exactly one stale sentence in the About sheet; nothing written.")
    out = BytesIO()
    with zipfile.ZipFile(out, "w") as dst:
        for info in src.infolist():
            data = about.replace(OLD, NEW).encode("utf-8") if info.filename == SHEET else src.read(info.filename)
            dst.writestr(info, data)
    content = out.getvalue()
    WORKBOOK.write_bytes(content)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["workbook_sha256"] = hashlib.sha256(content).hexdigest()
    MANIFEST.write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))   # LF bytes
    print(f"Patched B7; workbook_sha256 {manifest['workbook_sha256']}")


if __name__ == "__main__":
    main()
