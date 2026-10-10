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

SUPPLY = "The Company depends on a small number of suppliers for key components, and a disruption could reduce net sales."
TARIFF = "International trade issues, including tariffs and counter tariffs, could raise the cost of materials we buy."
OLD_LEGAL = "We are a defendant in litigation with a federal agency regarding our money transfer services."
CUR_TEXT = f"{SUPPLY} {TARIFF}"
PRIOR_TEXT = f"The Company depends on suppliers for key components. {OLD_LEGAL}"


def meta(sid, form="10-K", filed="2026-02-26"):
    return {"form": form, "filed": filed, "period": "2025-12-31", "accession": f"acc-{sid}", "url": f"https://sec/{sid}",
            "index_url": "", "label": f"{form} for the period ended 2025-12-31, filed {filed}"}


def sources(prior=True, eight_k=True, quarterly=False):
    """Hand-built sources shaped like build_sources output, with a code comparison when there is a prior 10-K."""
    cur = Source("R_CUR", "Risk factors, latest annual report", "found", meta("R_CUR"), text=CUR_TEXT)
    out = [cur]
    if prior:
        pri = Source("R_PRIOR", "Risk factors, prior annual report", "found", meta("R_PRIOR", filed="2025-02-27"), text=PRIOR_TEXT)
        cur.compared = pri.compared = True
        out += [pri, Source("R_CMP", "Risk factors: changes since the prior 10-K", "found", meta("R_CUR"),
                            text=f"[P1] CHANGED (edited): {SUPPLY}\n[P2] NEW (no close match in the prior 10-K): {TARIFF}\n"
                                 f"[R1] REMOVED (in the prior 10-K, no counterpart now): {OLD_LEGAL}",
                            extra={"labels": {"P1": ("CHANGED", "edited"), "P2": ("NEW", ""), "R1": ("REMOVED", "")},
                                   "counts": {"CHANGED (edited)": 1, "NEW": 1, "REMOVED": 1}, "unchanged": [],
                                   "removed": [OLD_LEGAL], "prior_label": meta("R_PRIOR", filed="2025-02-27")["label"],
                                   "prior_url": "https://sec/R_PRIOR"})]
    else:
        out.append(Source("", "Risk factors, prior annual report", "missing", note="Only one 10-K."))
    if quarterly:
        out.append(Source("QU1", "Risk factor updates, quarterly report", "found", meta("QU1", "10-Q", "2026-05-01"),
                          text="Demand for our products may change quickly with economic conditions and customer budgets."))
    out.append(Source("MDA", "Management's discussion and analysis", "found", meta("MDA", "10-Q", "2026-08-01"),
                      text="Net sales increased 8% to $5.2 billion in the quarter, driven by services."))
    if eight_k:
        out.append(Source("K8_1", "Current report (8-K)", "found", meta("K8_1", "8-K", "2026-09-18"),
                          text="On September 18, 2026 the Board appointed a new Chief Financial Officer effective October 1."))
    for s in out:
        s.sent_text = s.text if s.sendable else ""
    return out


def finding(**kw):
    base = {"headline": "Supplier concentration remains a stated risk", "summary": "s", "implication": "i",
            "detail": "d", "category": "COSTS_SUPPLY_CHAIN", "impact": "MEDIUM", "impact_basis": "b",
            "source_id": "R_CMP", "paragraph_id": "P1", "quote": "depends on a small number of suppliers for key components"}
    return base | kw


def answer(**kw):
    base = {"catalysts": [finding(source_id="MDA", paragraph_id="", quote="Net sales increased 8% to $5.2 billion")],
            "risks": [finding()],
            "other_risks": [finding(source_id="MDA", paragraph_id="", quote="Net sales increased 8% to $5.2 billion in the quarter")],
            "events": [{"source_id": "K8_1", "category": "LEADERSHIP", "headline": "New CFO appointed",
                        "summary": "s", "quote": "the Board appointed a new Chief Financial Officer"}],
            "questions": [{"question": "How is supplier risk being reduced?", "source_id": "R_CMP"}]}
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
    def test_available_with_counts_and_both_periods(self):
        c = analysis.comparison_status(sources())
        self.assertEqual(c["status"], "available")
        self.assertIn("filed 2025-02-27", c["prior"])
        self.assertEqual(c["counts"]["NEW"], 1)

    def test_missing_prior(self):
        c = analysis.comparison_status(sources(prior=False))
        self.assertEqual(c["status"], "missing")
        self.assertIn("Only one 10-K", c["reason"])

    def test_failed_prior_download_is_failed_not_missing(self):
        srcs = sources(prior=False)
        srcs[1] = Source("R_PRIOR", "Risk factors, prior annual report", "failed", meta("R_PRIOR"), note="Download failed")
        self.assertEqual(analysis.comparison_status(srcs)["status"], "failed")


class BuildSources(unittest.TestCase):
    PARA = "The Company depends on a small number of suppliers for key components and could lose sales. "

    def test_statuses_and_code_comparison(self):
        k = Filing("10-K", "2026-02-26", "2025-12-31", "a-1", "k.htm", "1")
        k_old = Filing("10-K", "2025-02-27", "2024-12-31", "a-2", "k0.htm", "1")
        e = Filing("8-K", "2026-09-18", "", "a-3", "e.htm", "1", "5.02")
        sel = select_filings([e, k, k_old], date(2026, 10, 10))
        risk = lambda body: f"Item 1A. Risk Factors\n{body}\nItem 1B. Unresolved Staff Comments None."
        mda = ("Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations\n"
               + "Net sales increased 8% to $5.2 billion during the year on higher services revenue. " * 5 + "\nItem 7A. Market Risk None.")
        cur = risk(self.PARA * 3 + "\n" + TARIFF + " " + TARIFF)
        prior = risk(self.PARA * 3 + "\n" + OLD_LEGAL + " " + OLD_LEGAL)
        srcs = analysis.build_sources(sel, {"a-1": cur + "\n" + mda, "a-2": prior, "a-3": "8-K text"})
        by = {(s.id or s.role): s for s in srcs}
        self.assertTrue(by["R_CUR"].compared and not by["R_CUR"].sendable)
        self.assertIn("R_CMP", by)
        self.assertEqual(by["R_CMP"].extra["counts"], {"UNCHANGED": 1, "NEW": 1, "REMOVED": 1})
        self.assertNotIn(self.PARA.strip(), by["R_CMP"].text)          # unchanged paragraphs aren't sent
        self.assertEqual(by["Risk factor updates, quarterly report"].status, "not_applicable")

    def test_failed_prior_means_no_comparison(self):
        k = Filing("10-K", "2026-02-26", "2025-12-31", "a-1", "k.htm", "1")
        k_old = Filing("10-K", "2025-02-27", "2024-12-31", "a-2", "k0.htm", "1")
        sel = select_filings([k, k_old], date(2026, 10, 10))
        srcs = analysis.build_sources(sel, {"a-1": f"Item 1A. Risk Factors\n{self.PARA * 4}\nItem 1B. None.", "a-2": RuntimeError("timeout")})
        by = {s.id: s for s in srcs if s.id}
        self.assertEqual(by["R_PRIOR"].status, "failed")
        self.assertNotIn("R_CMP", by)
        self.assertTrue(by["R_CUR"].sendable)                          # sent directly instead


class Budget(unittest.TestCase):
    @staticmethod
    def counter(prompt, tool):  # stand-in for the token-counting endpoint: 4 characters per token
        return (len(prompt) + len(str(tool))) // 4

    def test_fits_without_trimming(self):
        srcs = sources()
        r = fit_to_budget("AAPL", "Apple", srcs, self.counter)
        self.assertEqual(sum(s.coverage()["omitted_chars"] for s in srcs), 0)
        self.assertLessEqual(r["input_tokens"], analysis.REQUEST_TOKEN_BUDGET - analysis.MAX_OUTPUT_TOKENS)

    def test_comparison_kept_first_and_cut_only_between_entries(self):
        srcs = sources()
        cmp_ = next(s for s in srcs if s.id == "R_CMP")
        cmp_.text = "\n".join(f"[P{i}] CHANGED (edited): Paragraph {i} about supplier costs and demand. " * 3 for i in range(1, 4000))
        next(s for s in srcs if s.id == "MDA").text = "Net sales sentence. " * 30000
        budget = 40_000
        r = fit_to_budget("AAPL", "Apple", srcs, self.counter, budget=budget)
        self.assertLessEqual(r["input_tokens"], budget - analysis.MAX_OUTPUT_TOKENS)
        self.assertTrue(cmp_.sent_text.endswith("demand. "))           # whole entries only
        cov = {s.id: s.coverage() for s in srcs if s.id}
        self.assertGreater(cov["R_CMP"]["sent_chars"], cov["MDA"]["sent_chars"])
        self.assertIn("rest was omitted", r["prompt"])

    def test_water_fill(self):
        self.assertEqual(analysis.water_fill({"a": 10, "b": 100, "c": 100}, 110), {"a": 10, "b": 50, "c": 50})


class ResponseChecks(unittest.TestCase):
    def test_complete_with_trend_from_code(self):
        r = check_response("tool_use", answer(), sources())
        self.assertEqual({k: v["status"] for k, v in r["sections"].items()},
                         {"catalysts": "complete", "risks": "complete", "other_risks": "complete", "events": "complete", "questions": "complete"})
        self.assertTrue(is_cacheable(r))
        risk = r["sections"]["risks"]["items"][0]
        self.assertEqual((risk["trend"], risk["trend_reason"]), ("CHANGED", "edited"))
        self.assertEqual(risk["excerpt"]["status"], "matched")         # checked against the current 10-K section

    def test_model_trend_is_ignored(self):
        r = check_response("tool_use", answer(risks=[finding(paragraph_id="P2", quote="including tariffs and counter tariffs, could raise the cost", trend="UNCHANGED")]), sources())
        self.assertEqual(r["sections"]["risks"]["items"][0]["trend"], "NEW")

    def test_removed_paragraph_quotes_the_prior_10k(self):
        r = check_response("tool_use", answer(risks=[finding(paragraph_id="R1", quote="defendant in litigation with a federal agency")]), sources())
        risk = r["sections"]["risks"]["items"][0]
        self.assertEqual((risk["trend"], risk["excerpt"]["status"]), ("REMOVED", "matched"))
        self.assertIn("filed 2025-02-27", risk["source"]["label"])

    def test_risks_must_cite_risk_factor_sources(self):
        r = check_response("tool_use", answer(risks=[finding(source_id="MDA", paragraph_id="", quote="Net sales increased 8% to $5.2 billion"),
                                                     finding(paragraph_id="P99")]), sources())
        self.assertEqual([d["reason"] for d in r["sections"]["risks"]["dropped"]],
                         ["risk cites MDA, which is not a risk-factor source", "unknown paragraph 'P99' in R_CMP"])
        self.assertFalse(is_cacheable(r))

    def test_quarterly_and_no_comparison_trends(self):
        r = check_response("tool_use", answer(risks=[finding(source_id="QU1", paragraph_id="", quote="Demand for our products may change quickly with economic conditions")]),
                           sources(quarterly=True))
        self.assertEqual(r["sections"]["risks"]["items"][0]["trend"], "QUARTERLY_UPDATE")
        r = check_response("tool_use", answer(risks=[finding(source_id="R_CUR", paragraph_id="")]), sources(prior=False))
        self.assertEqual(r["sections"]["risks"]["items"][0]["trend"], "NOT_COMPARED")

    def test_cut_off_answer_is_never_empty_or_cacheable(self):
        r = check_response("max_tokens", {"catalysts": [finding(source_id="MDA", paragraph_id="", quote="Net sales increased 8% to $5.2 billion")]}, sources())
        self.assertEqual(r["response_status"], "incomplete")
        self.assertEqual(r["sections"]["catalysts"]["status"], "partial")
        self.assertEqual(r["sections"]["events"]["status"], "missing")      # not "no events found"
        self.assertFalse(is_cacheable(r))

    def test_genuinely_empty_and_no_input(self):
        self.assertEqual(check_response("tool_use", answer(events=[]), sources())["sections"]["events"]["status"], "empty")
        self.assertEqual(check_response("tool_use", answer(events=[]), sources(eight_k=False))["sections"]["events"]["status"], "no_input")

    def test_invalid_items_are_dropped_with_reasons(self):
        r = check_response("tool_use", answer(catalysts=[finding(source_id="MDA", impact="SEVERE"), finding(source_id="X9")]), sources())
        self.assertEqual([d["reason"] for d in r["sections"]["catalysts"]["dropped"]], ["unknown impact 'SEVERE'", "unknown source 'X9'"])
        self.assertEqual(r["sections"]["catalysts"]["status"], "invalid")

    def test_quote_from_another_source(self):
        r = check_response("tool_use", answer(catalysts=[finding(source_id="K8_1", paragraph_id="", quote="Net sales increased 8% to $5.2 billion")]), sources())
        ex = r["sections"]["catalysts"]["items"][0]["excerpt"]
        self.assertEqual((ex["status"], ex["found_in"]), ("not_matched", ["MDA"]))

    def test_no_material_changes_source_is_rejected(self):
        srcs = sources(quarterly=True)
        srcs[[s.id for s in srcs].index("QU1")].status = "no_material_changes"
        r = check_response("tool_use", answer(risks=[finding(source_id="QU1", paragraph_id="", quote="Demand for our products may change quickly")]), srcs)
        self.assertIn("reports no material changes", r["sections"]["risks"]["dropped"][0]["reason"])

    def test_other_risks_cite_management_discussion_only(self):
        r = check_response("tool_use", answer(other_risks=[finding(source_id="K8_1", paragraph_id="", quote="the Board appointed a new Chief Financial Officer")]), sources())
        self.assertIn("management's discussion (MDA) only", r["sections"]["other_risks"]["dropped"][0]["reason"])
        r = check_response("tool_use", answer(), sources())
        other = r["sections"]["other_risks"]["items"][0]
        self.assertNotIn("trend", other)                                 # not compared to last year

    def test_figures_must_appear_in_the_cited_source(self):
        ok = finding(source_id="MDA", paragraph_id="", quote="Net sales increased 8% to $5.2 billion",
                     summary="Net sales rose 8% to $5,200 million.")             # same figures, other format
        bad = finding(source_id="MDA", paragraph_id="", quote="Net sales increased 8% to $5.2 billion",
                      summary="Operating income fell to $14.7 million, a 7.3% margin.")
        r = check_response("tool_use", answer(catalysts=[ok, bad]), sources())
        items = r["sections"]["catalysts"]["items"]
        self.assertEqual(items[0]["unsupported_figures"], [])
        self.assertEqual(items[1]["unsupported_figures"], ["$14.7 million", "7.3%"])   # flagged, not rejected
        self.assertEqual(r["sections"]["catalysts"]["status"], "complete")

    def test_figures_from_a_second_cited_source(self):
        two = finding(source_id="MDA", paragraph_id="", quote="Net sales increased 8% to $5.2 billion",
                      summary="Net sales rose 8% to $5.2 billion; a new CFO starts October 1.", other_source_ids=["K8_1"],
                      detail="Sales of $5.2 billion; the 8-K names 2026 as the start year.")
        item = check_response("tool_use", answer(catalysts=[two]), sources())["sections"]["catalysts"]["items"][0]
        self.assertEqual(item["unsupported_figures"], [])
        self.assertEqual([o["id"] for o in item["other_sources"]], ["K8_1"])
        bad = check_response("tool_use", answer(catalysts=[finding(source_id="MDA", other_source_ids=["X1"])]), sources())
        self.assertIn("other_source_ids", bad["sections"]["catalysts"]["dropped"][0]["reason"])

    def test_refusal_and_no_output(self):
        self.assertEqual(check_response("refusal", None, sources())["response_status"], "refused")
        self.assertEqual(check_response("end_turn", None, sources())["response_status"], "no_output")


class Wording(unittest.TestCase):
    def test_banned_words_flagged_financial_leverage_allowed(self):
        self.assertEqual(analysis.wording_flags({"summary": "Revenue surged and margins soared."}), ["summary: surged", "summary: soared"])
        self.assertEqual(analysis.wording_flags({"detail": "a 3.50x leverage covenant", "implication": "debt capacity and leverage ratio"}), [])
        self.assertEqual(analysis.wording_flags({"headline": "The company will leverage AI"}), ["headline: leverage"])
        self.assertEqual(analysis.wording_flags({"detail": "unlimited amounts if leverage stays below 2.00x"}), [])
        self.assertEqual(analysis.wording_flags({"question": "Are any units at elevated risk of impairment?"}), [])
        self.assertEqual(analysis.wording_flags({"headline": "Plans to elevate the brand"}), ["headline: elevate"])

    def test_new_risk_claim_flagged(self):
        flags = analysis.wording_flags({"headline": "New risk disclosed on contract termination"})
        self.assertEqual(len(flags), 1)
        self.assertIn("no close match", flags[0])

    def test_figure_formats_are_normalized(self):
        fig = lambda t: [(k, round(v, 4)) for k, v, _, _ in analysis._figures(t)]
        self.assertEqual(fig("$14.7M"), fig("14.7 million"))
        self.assertEqual(fig("15%"), fig("15.0 percent"))
        self.assertEqual(fig("On June 30, 2026, in Q3 2026, Item 1A of Form 10-K listed 3 segments"), [])
        self.assertEqual(fig("approved in November 2025 and November 12, 2025"), [])
        self.assertEqual(analysis.unsupported_figures({"summary": "$109.4 billion"}, ["Net sales 109,430 (in millions)"]), [])


if __name__ == "__main__":
    unittest.main()
