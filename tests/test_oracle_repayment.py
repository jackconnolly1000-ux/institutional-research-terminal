"""Dated obligation/resource matching must not turn historical evidence into future coverage."""
import json
import unittest
from copy import deepcopy

import oracle_financing as financing
import oracle_liquidity as liquidity
import oracle_repayment as repayment


class OracleRepayment(unittest.TestCase):
    def setUp(self):
        self.review=json.loads(liquidity.SAMPLE.read_text())
        self.annual=json.loads(financing.SAMPLE.read_text())

    def test_each_checked_payment_retains_amount_date_basis_and_source(self):
        got=repayment.build(self.review,self.annual)
        self.assertEqual(got["status"],"Checked")
        self.assertEqual(len(got["obligations"]),21)
        for obligation in got["obligations"]:
            fact=self.review["inputs"][obligation["key"]]
            self.assertEqual(obligation["value"],fact["value"])
            self.assertEqual(obligation["accession"],fact["accession"])
            self.assertEqual(obligation["source_url"],fact["source_url"])
        self.assertEqual(got["obligations"][0]["due_start"],"2026-09-01")
        self.assertEqual(got["obligations"][0]["due_end"],"2027-05-31")
        self.assertIsNone(got["obligations"][-1]["due_end"])

    def test_historical_cash_and_inflows_never_become_allocations_or_coverage(self):
        got=repayment.build(self.review,self.annual)
        self.assertEqual([r["value"] for r in got["resources"]],
                         [36369e6,2565e6,23103e6,11363e6,19909e6,10000e6])
        for obligation in got["obligations"]:
            self.assertIsNone(obligation["funding_available"])
            self.assertIsNone(obligation["coverage"])
            self.assertIn("not established",obligation["coverage_detail"])
        self.assertNotIn("total_available",got)
        self.assertIn("not added",got["conclusion"])

    def test_facility_expiry_changes_the_candidate_resource_explanation(self):
        got=repayment.build(self.review,self.annual)
        first,crossing,after=got["obligations"][0],got["obligations"][12],got["obligations"][15]
        self.assertIn("conditional revolver",first["candidate_resources"])
        self.assertIn("expires within",crossing["candidate_resources"])
        self.assertIn("expires before",after["candidate_resources"])
        self.assertIn("final payment date",got["obligations"][-1]["coverage_detail"])

    def test_unreconciled_payment_is_missing_and_does_not_poison_other_schedules(self):
        self.review["schedules"]["finance"].update(status="Unavailable",detail="Reported total did not reconcile.")
        got=repayment.build(self.review,self.annual)
        self.assertIsNotNone(got["obligations"][0]["value"])
        self.assertIsNone(got["obligations"][1]["value"])
        self.assertIn("did not reconcile",got["obligations"][1]["coverage_detail"])

    def test_unchecked_review_is_refused_and_old_debt_is_not_rolled_forward(self):
        for key,value in [("accession","other"),("period_end","2026-09-30"),("status","Unavailable")]:
            changed=deepcopy(self.review);changed[key]=value
            got=repayment.build(changed,self.annual)
            self.assertEqual(got["status"],"Unavailable")
            self.assertEqual(got["obligations"],[])
        got=repayment.build(self.review,self.annual)
        self.assertEqual([r["value"] for r in got["historical_debt"]],[r["value"] for r in self.annual["buckets"]])
        self.assertIsNone(got["gaps"][0]["value"])
        changed=deepcopy(self.annual);changed["accession"]="other"
        self.assertEqual(repayment.build(self.review,changed)["historical_debt"],[])


if __name__=="__main__":unittest.main()
