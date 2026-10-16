"""The whole app in Streamlit's AppTest: the saved debt and liquidity reviews are the default page and need no
secrets or network; general filing research sits behind a secondary button and keeps the archived example.

Every socket connection fails during these tests, so a live SEC, Yahoo or Anthropic request would raise.
"""
import hashlib
import html
import json
import os
import socket
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

from openpyxl import load_workbook
import streamlit
from streamlit.runtime.memory_media_file_storage import MemoryMediaFileStorage
from streamlit.testing.v1 import AppTest

import liquidity_pilot

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"
RESEARCH = "General filing research — experimental"
ARCHIVED = "View archived example (AAPL, STRL · Oct 10, 2026)"
WORKBOOKS = {"LLY": "lly_liquidity", "ORCL": "oracle_liquidity", "VST": "vistra_liquidity"}


REAL_CONNECT = socket.socket.connect


def refuse_connection(sock, address, *args, **kwargs):
    """Loopback stays open: on Windows, asyncio builds its internal socket pair through 127.0.0.1."""
    if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1", "localhost"):
        return REAL_CONNECT(sock, address, *args, **kwargs)
    raise AssertionError(f"A network connection was attempted: {address}")


def refuse_create(address, *args, **kwargs):
    raise AssertionError(f"A network connection was attempted: {address}")


def page_text(app) -> str:
    return html.unescape("\n".join(m.value for m in app.markdown))


SERVED = {}   # media file id -> the bytes a download button would serve
REAL_STORE = MemoryMediaFileStorage.load_and_get_id


def record_download(storage, data, mimetype, kind, filename=None):
    file_id = REAL_STORE(storage, data, mimetype, kind, filename)
    SERVED[file_id] = data
    return file_id


def download_bytes(button) -> bytes:
    """AppTest discards its media store after each run, so the bytes are recorded as they are stored."""
    return SERVED[button.proto.url.rsplit("/", 1)[-1].split(".")[0]]


class NoSecretsFile:
    """Behaves like st.secrets on a deployment with no secrets file: every read raises."""
    def get(self, *args, **kwargs):
        raise FileNotFoundError("No secrets files found")

    __getitem__ = __contains__ = get


class AppPages(unittest.TestCase):
    def setUp(self):
        # No secrets and no SEC contact, even if this machine has them, and no network at all.
        patches = [mock.patch.dict(os.environ, {}, clear=False),
                   mock.patch.object(socket.socket, "connect", refuse_connection),
                   mock.patch.object(socket, "create_connection", refuse_create),
                   mock.patch.object(streamlit, "secrets", NoSecretsFile()),
                   mock.patch.object(MemoryMediaFileStorage, "load_and_get_id", record_download)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        os.environ.pop("SEC_CONTACT_EMAIL", None)
        self.app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)

    def run_clean(self):
        self.app.run()
        self.assertFalse(self.app.exception, [e.value for e in self.app.exception])
        self.assertFalse(self.app.error, [e.value for e in self.app.error])
        return self.app

    def click(self, label):
        next(b for b in self.app.button if b.label == label).click()
        return self.run_clean()

    def labels(self, kind):
        return [w.proto.label for w in self.app.get(kind)]

    def test_default_page_opens_lilly_without_secrets_or_network(self):
        app = self.run_clean()
        text = page_text(app)
        self.assertIn("Debt &amp; Liquidity Research Terminal", "\n".join(m.value for m in app.markdown))
        self.assertEqual(app.segmented_control[0].value, "LLY")
        self.assertEqual(app.segmented_control[0].options, ["Eli Lilly (LLY)", "Oracle (ORCL)", "Vistra (VST)"])
        self.assertIn("Eli Lilly and Company", text)
        self.assertIn("54.91B", text)
        self.assertIn("Funding conclusion for LLY", text)
        # No Run analysis action and no enclosing review expander on the default page
        self.assertNotIn("Run analysis", [b.label for b in app.button])
        self.assertEqual([e.proto.label for e in app.expander], ["Optional combined export"])
        self.assertIn(RESEARCH, [b.label for b in app.button])
        self.assertIn("Download LLY review and evidence", self.labels("download_button"))

    def test_selector_opens_each_checked_review(self):
        app = self.run_clean()
        expected = {"ORCL": ("Oracle Corporation", "125.34B", "Download ORCL review and evidence"),
                    "VST": ("Vistra Corp.", "19.90B", "Download VST review and evidence")}
        for ticker, (name, debt, button) in expected.items():
            app.segmented_control[0].set_value(ticker)
            self.run_clean()
            text = page_text(app)
            self.assertIn(name, text)
            self.assertIn(debt, text)
            self.assertIn(f"Funding conclusion for {ticker}", text)
            self.assertIn(button, self.labels("download_button"))
            self.assertNotIn("Eli Lilly and Company", text)   # only the selected review is built
        self.assertIn("Financing changes after June 30", page_text(app))

    def test_review_downloads_are_the_checked_workbooks(self):
        app = self.run_clean()
        for ticker, stem in WORKBOOKS.items():
            app.segmented_control[0].set_value(ticker)
            self.run_clean()
            button = next(b for b in app.get("download_button") if b.proto.label.startswith(f"Download {ticker}"))
            content = download_bytes(button)
            self.assertEqual(content, (SAMPLES / f"{stem}.xlsx").read_bytes())
            manifest = json.loads((SAMPLES / f"{stem}.manifest.json").read_text())
            self.assertEqual(hashlib.sha256(content).hexdigest(), manifest["workbook_sha256"])
        combined = next(b for b in app.get("download_button") if "all three" in b.proto.label)
        manifest = json.loads((SAMPLES / "liquidity_pilots.manifest.json").read_text())
        self.assertEqual(hashlib.sha256(download_bytes(combined)).hexdigest(), manifest["workbook_sha256"])

    def test_research_is_secondary_and_works_without_secrets(self):
        self.run_clean()
        app = self.click(RESEARCH)
        self.assertIn(RESEARCH, page_text(app))
        self.assertFalse(app.segmented_control)
        run = next(b for b in app.button if b.label == "Run analysis")
        self.assertTrue(run.proto.disabled)
        self.assertIn("ANTHROPIC_API_KEY is not set", page_text(app))
        self.assertIn("SEC_CONTACT_EMAIL is not set", page_text(app))
        self.assertEqual(app.multiselect[0].value, ["AAPL"])

    def test_archived_example_and_selections_survive_navigation(self):
        app = self.run_clean()
        app.segmented_control[0].set_value("ORCL")
        self.run_clean()
        self.click(RESEARCH)
        app.multiselect[0].set_value(["AAPL", "STRL"])
        self.run_clean()
        app = self.click(ARCHIVED)
        text = page_text(app)
        self.assertIn("Archived filing-research example (AAPL, STRL). Analysis run Oct 10, 2026", text)
        self.assertEqual([t.label for t in app.tabs], ["AAPL", "STRL"])
        workbook = load_workbook(BytesIO(download_bytes(app.get("download_button")[0])))
        self.assertEqual(workbook.sheetnames, ["Market data", "Findings", "8-K events", "Evidence", "Filing review"])
        self.assertIn("AAPL", [c.value for c in workbook["Findings"]["A"]])

        app = self.click("Debt and liquidity reviews")
        self.assertEqual(app.segmented_control[0].value, "ORCL")   # company kept
        self.assertIn("Oracle Corporation", page_text(app))
        app = self.click(RESEARCH)
        self.assertEqual(app.multiselect[0].value, ["AAPL", "STRL"])   # tickers kept
        self.assertIn("Archived filing-research example", page_text(app))   # results kept
        self.assertEqual([t.label for t in app.tabs], ["AAPL", "STRL"])

    def test_stale_company_selection_falls_back_to_first_review(self):
        self.app.session_state["review_company"] = "AAPL"
        app = self.run_clean()
        self.assertEqual(app.segmented_control[0].value, "LLY")
        self.assertIn("Eli Lilly and Company", page_text(app))

    def test_missing_saved_reviews_show_a_stated_gap(self):
        with mock.patch.object(liquidity_pilot, "SAMPLE", ROOT / "samples" / "missing.json"):
            app = self.run_clean()
        self.assertIn("Saved reviews unavailable", page_text(app))
        self.assertFalse(app.get("download_button"))
        self.assertIn(RESEARCH, [b.label for b in app.button])   # the other tool is still reachable

    def test_changed_saved_review_refuses_its_workbook(self):
        with tempfile.TemporaryDirectory() as folder:
            stale = Path(folder) / "liquidity_pilots.json"
            saved = json.loads((SAMPLES / "liquidity_pilots.json").read_text())
            saved["snapshots"][0]["checked_as_of"] = "2026-10-01"
            stale.write_text(json.dumps(saved))
            with mock.patch.object(liquidity_pilot, "SAMPLE", stale):
                app = self.run_clean()
        self.assertIn("Lilly review workbook Unavailable", "\n".join(c.value for c in app.caption))
        self.assertIn("Combined workbook Unavailable", "\n".join(c.value for c in app.caption))
        self.assertFalse(app.get("download_button"))

    def test_malformed_saved_review_is_not_rendered(self):
        with tempfile.TemporaryDirectory() as folder:
            broken = Path(folder) / "liquidity_pilots.json"
            saved = json.loads((SAMPLES / "liquidity_pilots.json").read_text())
            del saved["snapshots"][0]["metrics"]["cash"]
            broken.write_text(json.dumps(saved))
            with mock.patch.object(liquidity_pilot, "SAMPLE", broken):
                app = self.run_clean()
        self.assertIn("LLY review unavailable", page_text(app))
        self.assertFalse([b for b in app.get("download_button") if "LLY" in b.proto.label])


if __name__ == "__main__":
    unittest.main()
