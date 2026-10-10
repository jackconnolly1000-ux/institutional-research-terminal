"""Tests for analysis.py: sources, comparison status, token budget, response checks, excerpt matching. No network.

Run from app/:  .venv/bin/python -m unittest discover -s tests -p "test_*.py"
"""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analysis  # noqa: E402
from analysis import Source, check_response, fit_to_budget, is_cacheable, match_excerpt  # noqa: E402
from sec_data import Filing, select_filings  # noqa: E402

RISK_TEXT = ("Item 1A. Risk Factors The Company depends on a small number of suppliers for key components. "
             "A disruption could reduce net sales. " * 40 + "Item 1B. Unresolved Staff Comments None.")
MDA_TEXT = ("Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations "
            "Net sales increased 8% to $5.2 billion. " * 40 + "Item 7A. Market Risk None.")


def meta(sid, form="10-K", filed="2026-02-26"):
    return {"form": form, "filed": filed, "period": "2025-12-31", "accession": f"acc-{sid}", "url": f"https://sec/{sid}",
            "index_url": "", "label": f"{form} for the period ended 2025-12-31, filed {filed}"}


def sources(prior=True, eight_k=True):
    out = [Source("R_CUR", "Risk factors, latest annual report", "found", meta("R_CUR"),
                  text="The Company depends on a small number of suppliers for key components. A disruption could reduce net sales.")]
    out.append(Source("R_PRIOR", "Risk factors, prior annual report", "found", meta("R_PRIOR", filed="2025-02-27"),
                      text="The Company depends on suppliers.") if prior else
               Source("", "Risk factors, prior annual report", "missing", note="Only one 10-K."))
    out.append(Source("MDA", "Management's discussion and analysis", "found", meta("MDA", "10-Q", "2026-08-01"),
                      text="Net sales increased 8% to $5.2 billion in the quarter, driven by services."))
    if eight_k:
        out.append(Source("K8_1", "Current report (8-K)", "found", meta("K8_1", "8-K", "2026-09-18"),
                          text="On September 18, 2026 the Board appointed a new Chief Financial Officer effective October 1."))
    for s in out:
        s.sent_text = s.text
    return out


def finding(**kw):
    base = {"headline": "Supplier concentration remains a stated risk", "summary": "s", "implication": "i",
            "detail": "d", "category": "COSTS_SUPPLY_CHAIN", "impact": "MEDIUM", "impact_basis": "b",
            "source_id": "R_CUR", "quote": "depends on a small number of suppliers for key components", "trend": "UNCHANGED"}
    return base | kw


def answer(**kw):
    base = {"catalysts": [finding(source_id="MDA", quote="Net sales increased 8% to $5.2 billion")],
            "risks": [finding()],
            "events": [{"source_id": "K8_1", "category": "LEADERSHIP", "headline": "New CFO appointed",
                        "summary": "s", "quote": "the Board appointed a new Chief Financial Officer"}],
            "questions": [{"question": "How is supplier risk being reduced?", "source_id": "R_CUR"}]}
    return base | kw


class Excerpts(unittest.TestCase):
    SRC = "The Company’s gross margin was 47.6% — up from 46.3% — driven by mix. Costs  rose in Q2."

    def test_exact_and_normalized(self):
        self.assertEqual(match_excerpt("The Company's gross margin was 47.6% - up from 46.3%", self.SRC)["status"], "matched")

    def test_fragments_must_be_in_order(self):
        self.assertEqual(match_excerpt("gross margin was 47.6% ... costs rose in Q2", self.SRC)["status"], "matched")
        self.assertEqual(match_excerpt("costs rose in Q2 ... gross margin was 47.6%", self.SRC)["status"], "not_matched")

    def test_changed_word_does_not_match(self):
        self.assertEqual(match_excerpt("The Company's gross margin was also 47.6%", self.SRC)["status"], "not_matched")

    def test_too_short_and_empty(self):
        self.assertEqual(match_excerpt("gross margin", self.SRC)["status"], "too_short")
        self.assertEqual(match_excerpt("", self.SRC)["status"], "no_quote")


class Comparison(unittest.TestCase):
    def test_available_with_both_periods(self):
        c = analysis.comparison_status(sources())
        self.assertEqual(c["status"], "available")
        self.assertIn("filed 2025-02-27", c["prior"])

    def test_missing_prior(self):
        c = analysis.comparison_status(sources(prior=False))
        self.assertEqual(c["status"], "missing")
        self.assertIn("Only one 10-K", c["reason"])

    def test_failed_prior_download_is_failed_not_missing(self):
        srcs = sources()
        srcs[1] = Source("R_PRIOR", "Risk factors, prior annual report", "failed", meta("R_PRIOR"), note="Download failed")
        self.assertEqual(analysis.comparison_status(srcs)["status"], "failed")


class BuildSources(unittest.TestCase):
    def test_statuses_for_failed_missing_and_not_applicable(self):
        k = Filing("10-K", "2026-02-26", "2025-12-31", "a-1", "k.htm", "1")
        k_old = Filing("10-K", "2025-02-27", "2024-12-31", "a-2", "k0.htm", "1")
        e = Filing("8-K", "2026-09-18", "", "a-3", "e.htm", "1", "5.02")
        sel = select_filings([e, k, k_old], date(2026, 10, 10))
        srcs = analysis.build_sources(sel, {"a-1": RISK_TEXT + " " + MDA_TEXT, "a-2": RuntimeError("timeout"), "a-3": "8-K text"})
        by_role = {(s.id or s.role): s.status for s in srcs}
        self.assertEqual(by_role["R_CUR"], "found")
        self.assertEqual(by_role["R_PRIOR"], "failed")
        self.assertEqual(by_role["Risk factor updates, quarterly report"], "not_applicable")
        self.assertEqual(by_role["MDA"], "found")
        self.assertEqual(by_role["K8_1"], "found")


class Budget(unittest.TestCase):
    @staticmethod
    def counter(prompt, tool):  # stand-in for the token-counting endpoint: 4 characters per token
        return (len(prompt) + len(str(tool))) // 4

    def test_fits_without_trimming(self):
        srcs = sources()
        for s in srcs:
            s.sent_text = ""
        r = fit_to_budget("AAPL", "Apple", srcs, self.counter)
        self.assertEqual(sum(s.coverage()["omitted_chars"] for s in srcs), 0)
        self.assertLessEqual(r["input_tokens"], analysis.REQUEST_TOKEN_BUDGET - analysis.MAX_OUTPUT_TOKENS)

    def test_trims_largest_sources_and_reports_omissions(self):
        srcs = sources()
        srcs[0].text = "Risk sentence about suppliers. " * 20000   # about 600K characters
        budget = 30_000
        r = fit_to_budget("AAPL", "Apple", srcs, self.counter, budget=budget)
        self.assertLessEqual(r["input_tokens"], budget - analysis.MAX_OUTPUT_TOKENS)
        cov = {s.id: s.coverage() for s in srcs if s.id}
        self.assertGreater(cov["R_CUR"]["omitted_chars"], 0)
        self.assertEqual(cov["MDA"]["omitted_chars"], 0)      # small sources are sent whole
        self.assertIn("omitted to fit the request budget", r["prompt"])

    def test_water_fill(self):
        self.assertEqual(analysis.water_fill({"a": 10, "b": 100, "c": 100}, 110), {"a": 10, "b": 50, "c": 50})


class ResponseChecks(unittest.TestCase):
    def test_complete(self):
        r = check_response("tool_use", answer(), sources())
        self.assertEqual(r["response_status"], "complete")
        self.assertEqual({k: v["status"] for k, v in r["sections"].items()},
                         {"catalysts": "complete", "risks": "complete", "events": "complete", "questions": "complete"})
        self.assertTrue(is_cacheable(r))
        risk = r["sections"]["risks"]["items"][0]
        self.assertEqual(risk["excerpt"]["status"], "matched")
        self.assertEqual(risk["source"]["filed"], "2026-02-26")

    def test_cut_off_answer_is_never_empty_or_cacheable(self):
        r = check_response("max_tokens", {"catalysts": [finding(source_id="MDA", quote="Net sales increased 8% to $5.2 billion")]}, sources())
        self.assertEqual(r["response_status"], "incomplete")
        self.assertEqual(r["sections"]["catalysts"]["status"], "partial")
        self.assertEqual(r["sections"]["events"]["status"], "missing")      # not "no events found"
        self.assertFalse(is_cacheable(r))

    def test_genuinely_empty_is_empty(self):
        r = check_response("tool_use", answer(events=[]), sources())
        self.assertEqual(r["sections"]["events"]["status"], "empty")
        self.assertTrue(is_cacheable(r))

    def test_no_8k_input_is_no_input(self):
        r = check_response("tool_use", answer(events=[]), sources(eight_k=False))
        self.assertEqual(r["sections"]["events"]["status"], "no_input")

    def test_invalid_items_are_dropped_with_reasons(self):
        r = check_response("tool_use", answer(risks=[finding(impact="SEVERE"), finding(source_id="X9")]), sources())
        self.assertEqual(r["sections"]["risks"]["status"], "invalid")
        self.assertEqual([d["reason"] for d in r["sections"]["risks"]["dropped"]],
                         ["unknown impact 'SEVERE'", "unknown source 'X9'"])
        self.assertFalse(is_cacheable(r))

    def test_trend_without_comparison_becomes_not_compared(self):
        r = check_response("tool_use", answer(risks=[finding(trend="STABLE")]), sources(prior=False))
        risk = r["sections"]["risks"]["items"][0]
        self.assertEqual(risk["trend"], "NOT_COMPARED")
        self.assertIn("NOT_COMPARED", risk["trend_note"])

    def test_new_needs_the_whole_prior_section(self):
        srcs = sources()
        srcs[1].sent_text = srcs[1].text[:10]          # prior 10-K only partly sent
        r = check_response("tool_use", answer(risks=[finding(trend="NEW"), finding(trend="ESCALATED")]), srcs)
        new, esc = r["sections"]["risks"]["items"]
        self.assertEqual(new["trend"], "NOT_COMPARED")
        self.assertIn("absence can't be confirmed", new["trend_note"])
        self.assertEqual((esc["trend"], esc.get("trend_partial")), ("ESCALATED", True))

    def test_trend_only_for_annual_source(self):
        r = check_response("tool_use", answer(risks=[finding(source_id="MDA", quote="Net sales increased 8% to $5.2 billion", trend="NEW")]), sources())
        self.assertEqual(r["sections"]["risks"]["items"][0]["trend"], "NOT_COMPARED")

    def test_quote_from_another_source(self):
        r = check_response("tool_use", answer(risks=[finding(source_id="MDA")]), sources())
        ex = r["sections"]["risks"]["items"][0]["excerpt"]
        self.assertEqual((ex["status"], ex["found_in"]), ("not_matched", ["R_CUR"]))

    def test_refusal_and_no_output(self):
        self.assertEqual(check_response("refusal", None, sources())["response_status"], "refused")
        self.assertEqual(check_response("end_turn", None, sources())["response_status"], "no_output")


if __name__ == "__main__":
    unittest.main()
