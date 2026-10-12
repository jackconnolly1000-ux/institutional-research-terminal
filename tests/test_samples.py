"""Checks on the committed saved sample in samples/: the files are complete and frozen at one date. No network.

Run from app/:  .venv/bin/python -m unittest discover -s tests -p "test_*.py"
"""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

import pandas as pd

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


class SavedSample(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((SAMPLES / "manifest.json").read_text(encoding="utf-8"))

    def test_manifest(self):
        self.assertEqual(self.manifest["tickers"], ["AAPL", "STRL"])
        self.assertEqual(self.manifest["label"], "Saved sample. Analysis run Oct 10, 2026. "
                                                 "Price history through the Oct 9 close, retrieved Oct 11.")

    def test_profiles_are_complete(self):
        for t in self.manifest["tickers"]:
            with self.subTest(t):
                p = json.loads((SAMPLES / f"{t}.json").read_text(encoding="utf-8"))
                self.assertEqual({"ticker", "company_name", "industry", "financials", "evidence", "analysis", "event_markers"} - set(p), set())
                self.assertEqual(p["analysis"]["response_status"], "complete")
                self.assertEqual(p["financials"]["status"], "ok")
                self.assertNotIn("questions", p["analysis"]["sections"])

    def test_prices_end_at_the_oct_9_close_and_match_the_tile(self):
        for t in self.manifest["tickers"]:
            with self.subTest(t):
                hist = pd.read_csv(SAMPLES / f"{t}_prices.csv", index_col=0, parse_dates=True)
                self.assertEqual(f"{hist.index[-1]:%Y-%m-%d}", self.manifest["prices_through"])
                tile = json.loads((SAMPLES / f"{t}.json").read_text(encoding="utf-8"))["financials"]["metrics"]["price"]["value"]
                self.assertAlmostEqual(tile, hist["Close"].iloc[-1], places=2)

    def test_every_file_the_app_loads_is_tracked_by_git(self):
        # A .gitignore rule (*.csv) once kept the price files out of a commit; the offline checks still passed
        # because the files were on disk, but the deployed sample would have had no charts.
        if shutil.which("git") is None:
            self.skipTest("git isn't installed, so tracked files can't be checked")
        files = ["manifest.json"] + [f"{t}{end}" for t in self.manifest["tickers"] for end in (".json", "_prices.csv")]
        for name in files:
            with self.subTest(name):
                result = subprocess.run(["git", "ls-files", "--error-unmatch", name], cwd=SAMPLES,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, f"samples/{name} is not tracked by git: {result.stderr.strip()}")


if __name__ == "__main__":
    unittest.main()
