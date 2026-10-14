"""Manual filing findings are joined only to the exact filings checked."""

import sys
import html
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import reviewed_financing  # noqa: E402
import filing_review  # noqa: E402
import sec_data  # noqa: E402


def inventory(*accessions, since="2026-06-30", through="2026-10-14", status="indexed"):
    rows = []
    for acc in accessions:
        checked = reviewed_financing.VST.get(acc)
        rows.append({"accession": acc, "form": checked["form"] if checked else "8-K",
                     "filed": checked["filed"] if checked else "2026-10-08",
                     "period": checked["period"] if checked else "2026-10-07",
                     "items": "1.01,9.01", "url": "https://www.sec.gov/test-index.htm",
                     "review": "Not checked"})
    return {"since": since, "through": through, "status": status, "notes": [], "filings": rows}


class ReviewedFinancing(unittest.TestCase):
    def test_checked_vistra_sources_and_no_double_counting(self):
        accessions = tuple(reviewed_financing.VST)
        original = inventory(*accessions, "unknown")
        got = reviewed_financing.annotate(original, "VST")
        self.assertEqual(original["filings"][0]["review"], "Not checked")
        self.assertEqual(sum(r["review"].startswith("Checked ") for r in got["filings"]), 10)
        self.assertEqual(got["filings"][-1]["review"], "Not checked")
        issued = next(r for r in got["filings"] if r["accession"].endswith("037577"))
        self.assertIn("completed $1.5 billion", issued["finding"])
        self.assertIn("New debt issued", issued["kind"])
        for r in got["filings"]:
            if r is not issued and r["review"].startswith("Checked "):
                self.assertNotIn("New debt issued", r["kind"])
        rendered = filing_review.render(got)
        self.assertIn("10 indexed document(s) manually checked", rendered)
        self.assertIn("1 indexed document(s) Not checked", rendered)
        self.assertIn("review coverage is incomplete", rendered)
        self.assertIn("$1.5 billion", html.unescape(rendered))
        self.assertIn("Source document", rendered)
        self.assertIn("Repurchase amendment, Ex. 10.1", rendered)

    def test_complete_index_distinguishes_one_issuance_from_offering_documents(self):
        got = reviewed_financing.annotate(inventory(*reviewed_financing.VST), "VST")
        rendered = filing_review.render(got)
        self.assertIn("All indexed candidates for these dates were checked", rendered)
        self.assertEqual(sum(r["kind"].startswith("New debt issued") for r in got["filings"]), 1)
        self.assertEqual(sum(r["kind"].startswith("Not a financing") for r in got["filings"]), 1)

    def test_live_inventory_shape_joins_ten_checked_filings(self):
        rows = sorted(reviewed_financing.VST.items(), key=lambda pair: pair[1]["filed"], reverse=True)
        columns = {"form": [], "filingDate": [], "reportDate": [], "accessionNumber": [],
                   "primaryDocument": [], "items": []}
        for acc, checked in rows:
            columns["form"].append(checked["form"])
            columns["filingDate"].append(checked["filed"])
            columns["reportDate"].append(checked["period"])
            columns["accessionNumber"].append(acc)
            columns["primaryDocument"].append(checked["source_url"].rsplit("/", 1)[-1])
            columns["items"].append("1.01,9.01" if checked["form"] == "8-K" else "")
        subs = {"filings": {"recent": columns, "files": []}}
        indexed = sec_data.filing_review_inventory(subs, "1692819", "2026-06-30", "2026-10-14",
                                                   lambda _: self.fail("No older page expected"))
        got = reviewed_financing.annotate(indexed, "VST")
        self.assertEqual(got["status"], "indexed")
        self.assertEqual(len(got["filings"]), 10)
        self.assertTrue(all(f["review"] == "Checked 2026-10-14" for f in got["filings"]))

    def test_filing_metadata_mismatch_cannot_claim_review(self):
        acc = "0001140361-26-037577"
        for key, wrong in (("form", "8-K/A"), ("filed", "2026-09-25"),
                           ("period", "2026-09-23")):
            with self.subTest(key=key):
                data = inventory(acc)
                data["filings"][0][key] = wrong
                self.assertEqual(reviewed_financing.annotate(data, "VST")["filings"][0]["review"], "Not checked")

    def test_no_future_review_or_other_anchor_or_company(self):
        acc = "0001140361-26-028619"
        for data, ticker in ((inventory(acc, through="2026-09-30"), "VST"),
                             (inventory(acc, since="2026-03-31"), "VST"),
                             (inventory(acc), "LLY")):
            self.assertEqual(reviewed_financing.annotate(data, ticker)["filings"][0]["review"], "Not checked")

    def test_incomplete_index_remains_incomplete_and_unknown_is_unreviewed(self):
        data = inventory("0001140361-26-028619", "unknown", status="incomplete")
        got = reviewed_financing.annotate(data, "VST")
        self.assertEqual(got["status"], "incomplete")
        self.assertIn("Filing index incomplete", filing_review.render(got))
        self.assertEqual(got["filings"][1]["review"], "Not checked")


if __name__ == "__main__":
    unittest.main()
