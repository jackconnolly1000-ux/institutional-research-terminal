"""Commitment arithmetic must never become verified drawable cash or carry forward across dates."""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import oracle_revolver as revolver

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT.parent / "data/raw/sec/ORCL"


class OracleRevolver(unittest.TestCase):
    def test_undrawn_is_derived_only_at_the_supported_date(self):
        audit = revolver.load()
        self.assertEqual(audit["status"], "Checked")
        march, may, august = audit["dates"]
        self.assertEqual(march["commitment"], 10e9)
        self.assertIsNone(march["drawn"])
        self.assertIsNone(march["undrawn"])
        self.assertEqual(may["commitment"] - may["drawn"], may["undrawn"])
        self.assertEqual(may["undrawn"], 10e9)
        self.assertIn("Reported compliant", may["compliance"])
        for key in ("commitment", "drawn", "undrawn", "drawable"):
            self.assertIsNone(august[key])
        for row in audit["dates"]:
            self.assertIsNone(row["drawable"])
            self.assertIn("Unavailable", row["drawable_detail"])

    def test_option_and_lc_findings_are_not_cash_or_an_assumed_deduction(self):
        audit = revolver.load()
        terms = {t["label"]: t for t in audit["terms"]}
        self.assertEqual(audit["increase_ceiling"], 12e9)
        self.assertIn("not a $12B commitment", terms["Conditional increase ceiling"]["detail"])
        self.assertIn("not assumed zero", terms["Exposure and letters of credit"]["detail"])
        self.assertIn("outstanding advances", terms["Exposure and letters of credit"]["detail"])
        self.assertEqual(audit["original_maturity"], "2031-03-06")
        self.assertIn("Non-extending lenders keep their dates", terms["Expiration and extensions"]["detail"])
        self.assertIn("three business days", terms["Reductions and termination"]["detail"])
        self.assertIn("3.0x", terms["Covenant and evidence needed"]["detail"])
        self.assertIn("Regulation U/X", terms["Permitted uses"]["detail"])
        self.assertIn("not two concurrent", terms["Replacement of the old facility"]["detail"])

    def test_later_filings_do_not_carry_forward_may_balances(self):
        audit = revolver.load()
        self.assertEqual([e["date"] for e in audit["later"]], ["2026-09-10", "2026-09-14"])
        for event in audit["later"]:
            self.assertNotIn("drawable", event)
            for key in event["sources"]:
                self.assertIn(audit["sources"][key]["form"], ["8-K", "8-K Ex. 99.1"])
        self.assertIn("not a complete review of all liability", audit["scope"])
        self.assertEqual(audit['inventory']['through'],'2026-10-15')
        snapshot = json.loads((ROOT / "samples/liquidity_pilots.json").read_text())["snapshots"][1]
        self.assertEqual(revolver.for_snapshot(snapshot), audit)
        snapshot["metrics"]["cash"]["period_end"] = "2026-11-30"
        self.assertEqual(revolver.for_snapshot(snapshot)["status"], "Unavailable")
        snapshot["ticker"] = "VST"
        self.assertIsNone(revolver.for_snapshot(snapshot))

    def test_changed_or_missing_saved_audit_is_unavailable(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "changed.json"
            with patch.object(revolver, "SAMPLE", path):
                self.assertEqual(revolver.load()["status"], "Unavailable")
                audit = revolver._review()
                audit["dates"][2]["drawable"] = 10e9
                path.write_text(json.dumps(audit))
                self.assertEqual(revolver.load()["status"], "Unavailable")

    def test_index_candidates_use_actual_rows_and_exact_dates(self):
        data=json.loads((ROOT/'tests/fixtures/ORCL_20261015_submissions.json').read_text())
        self.assertEqual(revolver.index_candidates(data),revolver.expected_candidates())
        self.assertEqual(len(revolver.index_candidates(data)),2)
        changed=deepcopy(data);recent=changed['filings']['recent']
        i=next(i for i,f in enumerate(recent['form']) if f=='DEF 14A')
        recent['form'][i]='8-K'
        self.assertNotEqual(revolver.index_candidates(changed),revolver.expected_candidates())
        recent['filingDate'][i]='2026-10-16'
        self.assertEqual(revolver.index_candidates(changed),revolver.expected_candidates())
        changed['cik']=59478
        self.assertIsNone(revolver.index_candidates(changed))

    def test_missing_history_is_not_a_complete_inventory(self):
        data=json.loads((ROOT/'tests/fixtures/ORCL_20261015_submissions.json').read_text())
        recent=data['filings']['recent'];keep=[i for i,d in enumerate(recent['filingDate']) if d>'2026-08-31']
        data['filings']['recent']={k:[v[i] for i in keep] for k,v in recent.items()}
        self.assertIsNone(revolver.index_candidates(data))

    @unittest.skipUnless((RAW / "orcl-ex10_17.htm").exists(), "Saved credit agreement not present")
    def test_exact_source_set_reproduces_audit_and_changed_source_is_refused(self):
        self.assertEqual(revolver.build(RAW), revolver.load())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = revolver._SOURCES[0][1]
            (root / first).write_bytes((RAW / first).read_bytes() + b"changed")
            self.assertIn("changed", revolver.build(root)["detail"])
            (root / first).unlink()
            self.assertIn("missing", revolver.build(root)["detail"])


if __name__ == "__main__":
    unittest.main()
