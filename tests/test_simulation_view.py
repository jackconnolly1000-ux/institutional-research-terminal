"""The Oracle stress scenario in the app: Oracle only, labelled, editable, and recorded in its own workbook."""
import os
import unittest
from io import BytesIO
from unittest import mock

from openpyxl import load_workbook
from streamlit.runtime.memory_media_file_storage import MemoryMediaFileStorage
from streamlit.testing.v1 import AppTest

import liquidity_simulation as ls
import simulation_view as sv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVED = {}
REAL_STORE = MemoryMediaFileStorage.load_and_get_id


def record(storage, data, mimetype, kind, filename=None):
    file_id = REAL_STORE(storage, data, mimetype, kind, filename)
    SERVED[file_id] = data
    return file_id


class ScenarioPanel(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(MemoryMediaFileStorage, "load_and_get_id", record)
        p.start()
        self.addCleanup(p.stop)
        self.app = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=90)
        self.app.run()

    def pick(self, ticker):
        self.app.segmented_control[0].set_value(ticker).run()
        self.assertFalse(self.app.exception, [e.value for e in self.app.exception])

    def labels(self):
        return [e.proto.label for e in self.app.expander]

    def test_only_oracle_has_the_scenario(self):
        self.pick("ORCL")
        self.assertIn("Stress scenario (illustrative) · Sep 2026–Aug 2027", self.labels())
        text = "\n".join(m.value for m in self.app.markdown)
        self.assertIn(ls.LABEL, text)
        self.assertEqual(len(self.app.dataframe), 2)
        self.assertEqual(len(self.app.dataframe[0].value), 4)
        self.assertEqual(list(self.app.dataframe[1].value["Correlation setting"]), list(ls.COMPARE_CORRELATIONS))
        for ticker in ("LLY", "VST"):
            self.pick(ticker)
            self.assertFalse(any(label.startswith("Stress scenario") for label in self.labels()))

    def test_an_invalid_range_runs_nothing(self):
        self.pick("ORCL")
        next(n for n in self.app.number_input if n.key == "sim_ocf_low").set_value(60.0).run()
        self.assertTrue(any("low ≤ most likely ≤ high" in w.value for w in self.app.warning))
        self.assertEqual(len(self.app.dataframe), 0)

    def test_the_download_records_inputs_seed_and_results(self):
        self.pick("ORCL")
        button = next(b for b in self.app.get("download_button") if b.proto.label == "Download this scenario (Excel)")
        wb = load_workbook(BytesIO(SERVED[button.proto.url.rsplit("/", 1)[-1].split(".")[0]]))
        self.assertEqual(wb.sheetnames, ["Scenario", "Results", "Correlation"])
        self.assertEqual([wb["Correlation"].cell(r, 2).value for r in (2, 3, 4)], list(ls.COMPARE_CORRELATIONS))
        self.assertEqual(wb["Scenario"]["A2"].value, ls.LABEL)
        self.assertIn("Seed 2026, 10,000 trials", wb["Scenario"]["A3"].value)
        self.assertEqual(wb["Results"].max_row, 5)
        expected = ls.simulate(ls.oracle_inputs(), ls.oracle_decisions()[0], 10_000, 2026)
        self.assertAlmostEqual(wb["Results"]["E2"].value, expected["mean"], delta=1)
        self.assertAlmostEqual(wb["Results"]["J2"].value, expected["probability_shortfall"])

    def test_the_correlation_setting_reaches_every_result_and_the_download(self):
        self.pick("ORCL")
        self.app.slider(key="sim_rho").set_value(0.5).run()
        self.assertFalse(self.app.exception)
        button = next(b for b in self.app.get("download_button") if b.proto.label == "Download this scenario (Excel)")
        wb = load_workbook(BytesIO(SERVED[button.proto.url.rsplit("/", 1)[-1].split(".")[0]]))
        self.assertEqual(wb["Scenario"]["B12"].value, 0.5)
        from dataclasses import replace
        tied = replace(ls.oracle_inputs(), correlation=0.5)
        expected = ls.simulate(tied, ls.oracle_decisions()[0], 10_000, 2026)
        self.assertAlmostEqual(wb["Results"]["E2"].value, expected["mean"], delta=1)
        self.assertAlmostEqual(wb["Results"]["F2"].value, expected["sd"], delta=1)


class ScenarioWorkbook(unittest.TestCase):
    def test_workbook_is_arial_10_with_numbers_as_numbers(self):
        i, decisions = ls.oracle_inputs(), ls.oracle_decisions()
        results = [(ls.simulate(i, d, 1_000, 1), d) for d in decisions]
        wb = load_workbook(BytesIO(sv.workbook(i, results, 1_000, 1)))
        cell = wb["Results"]["E2"]
        self.assertIsInstance(cell.value, float)
        self.assertEqual((cell.font.name, cell.font.sz), ("Arial", 10.0))
        self.assertIn("Not modelled", wb["Scenario"]["A14"].value)
        self.assertEqual(wb["Scenario"]["B12"].number_format, "+0.0;-0.0;0.0")   # a ratio, not $ millions
        self.assertNotIn("Correlation", wb.sheetnames)                            # only when a comparison is passed


if __name__ == "__main__":
    unittest.main()
