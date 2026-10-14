"""Tests for filing_xbrl.py on saved filing data: tests/fixtures/VST_2026Q2_ixbrl.htm, a trimmed copy of Vistra's
Jun 30, 2026 10-Q inline XBRL (accession 0001692819-26-000019) built by tests/fixtures/make_filing_fixture.py.
Expected values were read from the printed filing (balance sheet p. 2, Note 12 p. 27; docs/pilot_evidence_vistra.md).
No network calls."""
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import filing_xbrl as fx  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "VST_2026Q2_ixbrl.htm"
FULL = Path(__file__).resolve().parents[2] / "data" / "raw" / "sec" / "VST" / "vistra-20260630.htm"
ACCESSION = "0001692819-26-000019"
AR = "vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed"
M = 1_000_000


class VistraFiling(unittest.TestCase):
    def read(self, tag, instant, document=FIXTURE):
        return fx.read_instant(document, ACCESSION, tag, instant)

    def test_accounts_receivable_financing_jun_30_2026(self):
        r = self.read(AR, "2026-06-30")
        self.assertEqual((r["value"], r["context_id"], r["dimensions"], r["unit"], r["scale"], r["decimals"]),
                         (300 * M, "c-8", [], "iso4217:USD", 6, "-6"))
        self.assertEqual((r["tag"], r["period"], r["document"], r["accession"], r["note"]),
                         (AR, "2026-06-30", FIXTURE.name, ACCESSION, None))
        self.assertEqual(r["facts_found"], 2)   # balance sheet and Note 12 table, both c-8, both 300

    def test_dimensioned_note_12_fact_is_not_selected(self):
        # The Note 12 text fact (c-722) is also 300 at Jun 30 but carries DebtInstrumentAxis; it is present in the
        # data and ignored, so the result comes only from the undimensioned c-8
        root = ET.parse(FIXTURE).getroot()
        c722 = [f for f in root.iter(f"{{{fx.IX}}}nonFraction") if f.get("name") == AR and f.get("contextRef") == "c-722"]
        self.assertEqual(len(c722), 1)
        self.assertEqual(self.read(AR, "2026-06-30")["context_id"], "c-8")

    def test_dec_31_2025_comparative(self):
        r = self.read(AR, "2025-12-31")
        self.assertEqual((r["value"], r["context_id"]), (1_225 * M, "c-9"))

    def test_fixed_zero_is_a_reported_zero(self):
        r = self.read("us-gaap:ShortTermBorrowings", "2026-06-30")
        self.assertEqual((r["value"], r["note"]), (0, None))
        self.assertEqual(self.read("us-gaap:ShortTermBorrowings", "2025-12-31")["value"], 1_800 * M)

    def test_standard_tag_matches_the_balance_sheet(self):
        self.assertEqual(self.read("us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent", "2026-06-30")["value"],
                         1_876 * M)

    def test_wrong_date_is_unavailable(self):
        r = self.read(AR, "2026-03-31")
        self.assertEqual((r["value"], r["note"]), (None, fx.UNAVAILABLE))
        self.assertIn("instants at other dates (2025-12-31, 2026-06-30)", r["detail"])

    def test_duration_facts_are_not_instants(self):
        r = self.read("vistra:ProceedsFromRepaymentsOfAccountsReceivableFinancing", "2026-06-30")
        self.assertIsNone(r["value"])
        self.assertIn("duration fact(s), not instants", r["detail"])

    def test_another_tag_is_never_substituted(self):
        r = self.read("us-gaap:AccountsReceivableSecuritization", "2026-06-30")
        self.assertIsNone(r["value"])
        self.assertIn("no us-gaap:AccountsReceivableSecuritization fact", r["detail"])
        # The same local name under another prefix is a different tag
        self.assertIsNone(self.read("us-gaap:AccountsReceivableSecuritizationProgramAmountsBorrowed", "2026-06-30")["value"])

    @unittest.skipUnless(FULL.exists(), "full 10-Q not saved on this machine (data/raw/sec/VST)")
    def test_full_document_gives_the_same_result(self):
        r = self.read(AR, "2026-06-30", document=FULL)
        self.assertEqual((r["value"], r["context_id"], r["document"]), (300 * M, "c-8", "vistra-20260630.htm"))


HEAD = """<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
 xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:xbrldi="http://xbrl.org/2006/xbrldi"><body>
<ix:header><ix:resources>
<xbrli:context id="i"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">1</xbrli:identifier></xbrli:entity>
 <xbrli:period><xbrli:instant>2026-06-30</xbrli:instant></xbrli:period></xbrli:context>
<xbrli:context id="i2"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">1</xbrli:identifier></xbrli:entity>
 <xbrli:period><xbrli:instant>2026-06-30</xbrli:instant></xbrli:period></xbrli:context>
<xbrli:context id="d"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">1</xbrli:identifier>
 <xbrli:segment><xbrldi:explicitMember dimension="us-gaap:DebtInstrumentAxis">x:PartMember</xbrldi:explicitMember></xbrli:segment>
 </xbrli:entity><xbrli:period><xbrli:instant>2026-06-30</xbrli:instant></xbrli:period></xbrli:context>
<xbrli:unit id="usd"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
<xbrli:unit id="eur"><xbrli:measure>iso4217:EUR</xbrli:measure></xbrli:unit>
</ix:resources></ix:header>
"""


def fact(text, context="i", unit="usd", scale="6", **attrs):
    extra = "".join(f' {k}="{v}"' for k, v in attrs.items())
    return (f'<p><ix:nonFraction name="x:Borrowed" contextRef="{context}" unitRef="{unit}" scale="{scale}" '
            f'decimals="-6"{extra}>{text}</ix:nonFraction></p>')


class Rules(unittest.TestCase):
    def read(self, *facts):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.htm"
            path.write_text(HEAD + "".join(facts) + "</body></html>", encoding="utf-8")
            return fx.read_instant(path, "a-1", "x:Borrowed", "2026-06-30")

    def test_scale_and_comma(self):
        self.assertEqual(self.read(fact("1,234.5"))["value"], 1_234_500_000)

    def test_sign_attribute_makes_the_value_negative(self):
        self.assertEqual(self.read(fact("40", sign="-"))["value"], -40 * M)

    def test_conflicting_facts_are_unavailable(self):
        r = self.read(fact("300"), fact("310"))
        self.assertIsNone(r["value"])
        self.assertIn("conflicting x:Borrowed facts", r["detail"])

    def test_agreeing_duplicates_are_one_value(self):
        r = self.read(fact("300"), fact("300"))
        self.assertEqual((r["value"], r["facts_found"]), (300 * M, 2))

    def test_wrong_unit_is_unavailable(self):
        r = self.read(fact("300", unit="eur"))
        self.assertIsNone(r["value"])
        self.assertIn("units other than iso4217:USD at 2026-06-30 (iso4217:EUR)", r["detail"])

    def test_only_a_dimensioned_fact_is_unavailable(self):
        r = self.read(fact("300", context="d"))
        self.assertIsNone(r["value"])
        self.assertIn("only dimensioned contexts at 2026-06-30 (d)", r["detail"])

    def test_two_undimensioned_contexts_are_not_chosen_between(self):
        r = self.read(fact("300", context="i"), fact("300", context="i2"))
        self.assertIsNone(r["value"])
        self.assertIn("more than one undimensioned context (i, i2)", r["detail"])

    def test_undefined_context_is_unavailable(self):
        r = self.read(fact("300", context="nope"))
        self.assertIn("context 'nope', which the document does not define", r["detail"])

    def test_unknown_display_format_is_unavailable(self):
        r = self.read(fact("three hundred", format="ixt:num-word-en"))
        self.assertIn("display format 'ixt:num-word-en' is not one this reader handles", r["detail"])

    def test_text_that_is_not_a_number_is_unavailable(self):
        r = self.read(fact("(300)"))
        self.assertIn("is not a plain number", r["detail"])

    def test_fixed_zero_ignores_the_dash(self):
        self.assertEqual(self.read(fact("—", format="ixt:fixed-zero"))["value"], 0)


if __name__ == "__main__":
    unittest.main()
