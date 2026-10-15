"""Cash flows reconcile to independently read tables, using the production duration reader."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import cash_generation as cg  # noqa: E402
import filing_xbrl as fx  # noqa: E402
import xbrl  # noqa: E402
from test_filing_xbrl import HEAD, fact  # noqa: E402

M = 1_000_000


class PilotCashFlows(unittest.TestCase):
    def test_each_role_and_total_matches_the_printed_statements(self):
        expected = {"LLY": ((16813, 16023, 4753), (7841, 5259, 3207), (28083, 9893, 18190)),
                    "ORCL": ((31977, 23103, 8140), (55663, 28499, 8502), (46940, 75660, -28720)),
                    "VST": ((4070, 2222, 1171), (2752, 1572, 1458), (5121, 2866, 2255))}
        for ticker, (ocf, capex, totals) in expected.items():
            spec = cg.SOURCES[ticker]
            docs = {spec[role][0]: ROOT / f"tests/fixtures/{ticker}_{role}_cashflow.htm"
                    for role in ("annual", "quarter")}
            result = cg.build(ticker, docs)
            self.assertEqual(tuple(f["value"] / M for f in result["operating_cash_flow"]["inputs"]), ocf)
            self.assertEqual(tuple(f["value"] / M for f in result["capital_spending"]["inputs"]), capex)
            self.assertEqual(tuple(v["value"] / M for v in result.values()), totals)
            for key in ("operating_cash_flow", "capital_spending"):
                metric = result[key]
                self.assertIsNone(metric["tag"])
                self.assertEqual([i["coefficient"] for i in metric["inputs"]], [1, 1, -1])
                for f in metric["inputs"]:
                    self.assertEqual(f["dimensions"], [])
                    self.assertTrue(f["context_id"] and f["scale"] == 6)
                    self.assertIn(f["accession"].replace("-", ""), f["source_url"])
            # Keep this comparison separate from the checked expectations above: it checks the existing engine.
            if ticker != "LLY":
                facts = json.loads((ROOT / f"tests/fixtures/{ticker}_companyfacts.json").read_text())
                self.assertEqual(result["free_cash_flow"]["value"],
                                 xbrl.ttm_metrics(facts, "2026-10-14")["metrics"]["free_cash_flow"]["value"])

    def test_missing_filing_is_unavailable_never_zero(self):
        result = cg.build("LLY", {})
        self.assertTrue(all(m["value"] is None for m in result.values()))
        self.assertTrue(result["operating_cash_flow"]["inputs"])
        self.assertIn("not supplied", result["operating_cash_flow"]["detail"])

    def test_document_without_the_exact_tag_does_not_substitute(self):
        spec = cg.SOURCES["LLY"]
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "without-capex.htm"
            content = (ROOT / "tests/fixtures/LLY_quarter_cashflow.htm").read_text()
            empty.write_text(content.replace(spec["capex_tag"], "us-gaap:AnotherTag"))
            result = cg.build("LLY", {spec["annual"][0]: ROOT / "tests/fixtures/LLY_annual_cashflow.htm",
                                      spec["quarter"][0]: empty})
        self.assertEqual(result["operating_cash_flow"]["value"], 28083 * M)
        self.assertIsNone(result["capital_spending"]["value"])
        self.assertIsNone(result["free_cash_flow"]["value"])

    def test_wrong_company_document_is_refused(self):
        spec = cg.SOURCES["LLY"]
        with tempfile.TemporaryDirectory() as tmp:
            wrong = Path(tmp) / "another-company.htm"
            wrong.write_text((ROOT / "tests/fixtures/LLY_quarter_cashflow.htm").read_text().replace("0000059478", "0000000001"))
            result = cg.build("LLY", {spec["annual"][0]: ROOT / "tests/fixtures/LLY_annual_cashflow.htm",
                                      spec["quarter"][0]: wrong})
        self.assertIsNone(result["operating_cash_flow"]["value"])
        self.assertIn("entity does not match", result["operating_cash_flow"]["detail"])

    def test_full_documents_match_trimmed_facts_when_available(self):
        # Full documents stay outside git; the committed fixtures make every calculation reproducible elsewhere.
        raw = ROOT.parent / "data/raw/sec"
        if not all((raw / ticker / spec[role][1]).exists()
                   for ticker, spec in cg.SOURCES.items() for role in ("annual", "quarter")):
            self.skipTest("six full cash-flow source documents are not saved on this machine")
        for ticker, spec in cg.SOURCES.items():
            full = cg.build(ticker, {spec[r][0]: raw / ticker / spec[r][1] for r in ("annual", "quarter")})
            trimmed = cg.build(ticker, {spec[r][0]: ROOT / f"tests/fixtures/{ticker}_{r}_cashflow.htm"
                                       for r in ("annual", "quarter")})
            for key in full:
                self.assertEqual(full[key]["value"], trimmed[key]["value"])
                if key != "free_cash_flow":
                    self.assertEqual([f["context_id"] for f in full[key]["inputs"]],
                                     [f["context_id"] for f in trimmed[key]["inputs"]])


class DurationRules(unittest.TestCase):
    def read(self, body, header=None):
        header = header or HEAD.replace("<xbrli:instant>2026-06-30</xbrli:instant>",
                                        "<xbrli:startDate>2026-01-01</xbrli:startDate><xbrli:endDate>2026-06-30</xbrli:endDate>")
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "flow.htm"
            doc.write_text(header + body + "</body></html>")
            return fx.read_duration(doc, "test", "x:Borrowed", "2026-01-01", "2026-06-30")

    def test_duration_preserves_dates_scale_sign_and_negative_flows(self):
        result = self.read(fact("1,234", sign="-"))
        self.assertEqual((result["value"], result["start"], result["end"]),
                         (-1234 * M, "2026-01-01", "2026-06-30"))

    def test_same_end_with_wrong_start_is_rejected(self):
        header = HEAD.replace("<xbrli:instant>2026-06-30</xbrli:instant>",
                              "<xbrli:startDate>2026-04-01</xbrli:startDate><xbrli:endDate>2026-06-30</xbrli:endDate>")
        self.assertIsNone(self.read(fact("20"), header)["value"])

    def test_instants_dimensions_and_wrong_units_are_rejected(self):
        for body, head in ((fact("20"), HEAD), (fact("20", context="d"), None),
                           (fact("20", unit="eur"), None)):
            self.assertIsNone(self.read(body, head)["value"])

    def test_conflicts_and_ambiguous_contexts_are_rejected(self):
        self.assertIsNone(self.read(fact("20") + fact("21"))["value"])
        self.assertIsNone(self.read(fact("20") + fact("20", context="i2"))["value"])
        self.assertEqual(self.read(fact("20") + fact("20"))["value"], 20 * M)


if __name__ == "__main__":
    unittest.main()
