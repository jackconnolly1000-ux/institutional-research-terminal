"""The four validation checks from VSB 2008 Module 2 (logic, boundary, distribution, stability), plus inputs."""
import json
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

import liquidity_simulation as ls

B = 1_000_000_000
M = 1_000_000


def fixed(value):
    return ls.Triangular(value, value, value)


class Inputs(unittest.TestCase):
    def test_fixed_inputs_trace_to_the_checked_evidence(self):
        i = ls.oracle_inputs()
        self.assertEqual(i.starting_cash, 36_369 * M)            # 10-Q cash and equivalents, Aug 31, 2026
        self.assertEqual(i.principal_due, 7_317 * M)             # principal calendar, Sep 2026–Aug 2027
        self.assertEqual((i.ocf_ex_prepayments.low, i.ocf_ex_prepayments.mode, i.ocf_ex_prepayments.high),
                         (31_977 * M, 35_577 * M, 46_960 * M))
        self.assertEqual((i.prepayments.low, i.prepayments.high), (0, 11_363 * M))
        self.assertEqual((i.commercial_paper_due.low, i.commercial_paper_due.high), (287 * M, 387 * M))
        names = [d.name for d in ls.oracle_decisions()]
        self.assertEqual(len(names), 4)
        self.assertEqual({d.capex for d in ls.oracle_decisions()}, {75_660 * M, 55_663 * M})
        self.assertEqual({d.dividends for d in ls.oracle_decisions()}, {6_260 * M})

    def test_missing_evidence_refuses_to_run(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("liquidity_pilots.json", "oracle_liquidity.json"):
                shutil.copy(ls.SAMPLES / name, Path(d) / name)
            self.assertIsNone(ls.oracle_inputs(d))   # no principal calendar in this folder
            self.assertIsNone(ls.run(d))

    def test_every_result_carries_the_scenario_label(self):
        for r in ls.run(trials=500)["results"]:
            self.assertEqual(r["label"], ls.LABEL)
            self.assertIn("not a forecast", r["label"])


class Exclusions(unittest.TestCase):
    """Audit (Oct 17): a cash use is left out only when a filing shows it is inside a modelled line; the rest are
    measured separately and never folded into the base result."""

    def test_every_exclusion_cites_its_overlap(self):
        for name, status, proof in ls.EXCLUDED:
            self.assertIn(status, ("Inside OCF", "Not in starting cash"), name)
            self.assertTrue(("10-K" in proof or "10-Q" in proof or "ASC" in proof), name)
        self.assertNotIn("Finance-lease principal", [e[0] for e in ls.EXCLUDED])

    def test_uses_outside_the_model_trace_to_the_evidence(self):
        uses = {u.name: u for u in ls.oracle_uses_outside_model()}
        self.assertEqual(uses["Finance-lease principal"].amount, 620 * M)          # 10-Q Note 6, Sep–May
        self.assertIn("financing cash flow", uses["Finance-lease principal"].why_outside)
        self.assertEqual(uses["Short-term financing related to capex"].amount, (1_422 + 3_345 - 830) * M)
        self.assertEqual(uses["Purchase and other obligations"].amount, 5_449 * M)  # 10-Q Note 6, Sep–May
        self.assertIn("not established", uses["Purchase and other obligations"].why_outside)

    def test_an_added_use_lowers_every_trial_by_exactly_its_amount(self):
        i, d = ls.oracle_inputs(), ls.oracle_decisions()[0]
        base = ls.simulate(i, d, 5_000)["ending_cash"]
        added = ls.simulate(replace(i, added_uses=2 * B), d, 5_000)["ending_cash"]
        self.assertTrue(np.allclose(base - added, 2 * B))

    def test_effects_start_from_the_unchanged_base(self):
        i, d, uses = ls.oracle_inputs(), ls.oracle_decisions()[2], ls.oracle_uses_outside_model()
        rows = ls.outside_use_effects(i, uses, d, 5_000)
        self.assertEqual(rows[0]["scenario"], "Base model")
        self.assertEqual(rows[0]["share_below_zero"], ls.simulate(i, d, 5_000)["share_below_zero"])
        self.assertAlmostEqual(rows[-1]["added_uses"], sum(u.amount for u in uses))
        shares = [r["share_below_zero"] for r in rows]
        self.assertEqual(shares[-1], max(shares))                    # more uses never improve ending cash

    def test_results_are_shares_of_trials_and_state_the_timing_limit(self):
        r = ls.simulate(ls.oracle_inputs(), ls.oracle_decisions()[0], 100)
        self.assertFalse([k for k in r if "probability" in k])
        self.assertIn("each payment date", ls.TIMING_LIMIT)
        for t in (ls.oracle_inputs().ocf_ex_prepayments, ls.oracle_inputs().prepayments):
            self.assertTrue(t.basis.startswith("Assumed"))


class Logic(unittest.TestCase):
    """Check 1: with every input fixed, the simulation equals a hand calculation."""

    def test_fixed_inputs_match_hand_calculation(self):
        i = replace(ls.oracle_inputs(), ocf_ex_prepayments=fixed(40 * B), prepayments=fixed(2 * B),
                    commercial_paper_due=fixed(0.3 * B))
        d = ls.Decision("test", capex=60 * B, dividends=6 * B, revolver=False)
        hand = 36.369 * B + 40 * B + 2 * B - 60 * B - 6 * B - 7.317 * B - 0.3 * B
        r = ls.simulate(i, d, trials=100)
        self.assertAlmostEqual(r["mean"], hand, delta=1)
        self.assertEqual(r["sd"], 0)
        self.assertEqual(r["share_below_zero"], 0.0 if hand >= 0 else 1.0)


class Boundary(unittest.TestCase):
    """Check 2: extreme inputs and decisions behave as the logic says."""

    def setUp(self):
        self.i = ls.oracle_inputs()

    def test_revolver_covers_a_gap_up_to_its_commitment_and_no_more(self):
        i = replace(self.i, ocf_ex_prepayments=fixed(0), prepayments=fixed(0), commercial_paper_due=fixed(0))
        small = ls.Decision("gap 5B", capex=36.369 * B - 7.317 * B + 5 * B, dividends=0, revolver=True)
        self.assertAlmostEqual(ls.simulate(i, small, 10)["mean"], 0, delta=1)
        large = ls.Decision("gap 15B", capex=36.369 * B - 7.317 * B + 15 * B, dividends=0, revolver=True)
        self.assertAlmostEqual(ls.simulate(i, large, 10)["mean"], -5 * B, delta=1)

    def test_zero_capex_and_dividends_never_falls_short(self):
        d = ls.Decision("no spending", capex=0, dividends=0, revolver=False)
        self.assertEqual(ls.simulate(self.i, d, 5_000)["share_below_zero"], 0.0)

    def test_worst_and_best_corners_bound_every_trial(self):
        d = ls.oracle_decisions()[0]
        worst = ls.ending_cash(self.i, d, self.i.ocf_ex_prepayments.low, 0, self.i.commercial_paper_due.high)[1]
        best = ls.ending_cash(self.i, d, self.i.ocf_ex_prepayments.high, self.i.prepayments.high,
                              self.i.commercial_paper_due.low)[1]
        cash = ls.simulate(self.i, d, 20_000)["ending_cash"]
        self.assertGreaterEqual(cash.min(), worst - 1)
        self.assertLessEqual(cash.max(), best + 1)

    def test_a_reversed_triangle_is_rejected(self):
        with self.assertRaises(ValueError):
            ls.Triangular(3, 1, 2)


class Distribution(unittest.TestCase):
    """Check 3: sampled inputs match their stated range, mode and mean."""

    def test_samples_match_the_triangle(self):
        t = ls.oracle_inputs().ocf_ex_prepayments
        x = t.draw(np.random.default_rng(7), 200_000)
        self.assertGreaterEqual(x.min(), t.low)
        self.assertLessEqual(x.max(), t.high)
        self.assertAlmostEqual(x.mean(), t.mean, delta=0.01 * t.mean)
        counts, edges = np.histogram(x, bins=40)
        peak = (edges[counts.argmax()] + edges[counts.argmax() + 1]) / 2
        self.assertLess(abs(peak - t.mode), (t.high - t.low) / 20)


class Correlation(unittest.TestCase):
    """Correlation changes how OCF and prepayments move together, not each one's own triangle (class rule)."""

    def setUp(self):
        self.i = ls.oracle_inputs()

    def test_inverse_cdf_hits_the_corners_and_the_mode(self):
        t = ls.Triangular(10, 20, 40)
        self.assertEqual(list(t.quantile([0, 1 / 3, 1])), [10, 20, 40])   # a third of the area lies left of 20
        self.assertEqual(list(ls.Triangular(0, 0, 9).quantile([0, 1])), [0, 9])
        self.assertEqual(list(fixed(5).quantile([0.2, 0.9])), [5, 5])

    def test_correlated_draws_keep_each_triangle(self):
        u1, u2 = ls.correlated_uniforms(np.random.default_rng(3), 200_000, 0.6)
        for t, u in ((self.i.ocf_ex_prepayments, u1), (self.i.prepayments, u2)):
            x = t.quantile(u)
            self.assertGreaterEqual(x.min(), t.low)
            self.assertLessEqual(x.max(), t.high)
            self.assertAlmostEqual(x.mean(), t.mean, delta=0.01 * t.high)
        x, y = self.i.ocf_ex_prepayments.quantile(u1), self.i.prepayments.quantile(u2)
        self.assertAlmostEqual(np.corrcoef(x, y)[0, 1], 0.6, delta=0.05)

    def test_correlation_moves_spread_not_mean(self):
        d = ls.oracle_decisions()[0]                     # no revolver, so ending cash is linear in the inputs
        low, zero, high = ls.compare_correlations(self.i, d, 50_000)
        self.assertAlmostEqual(low["mean"], zero["mean"], delta=0.05 * B)
        self.assertAlmostEqual(high["mean"], zero["mean"], delta=0.05 * B)
        self.assertLess(low["sd"], zero["sd"])
        self.assertLess(zero["sd"], high["sd"])
        self.assertAlmostEqual(zero["realized_correlation"], 0, delta=0.02)

    def test_correlation_must_be_inside_minus_one_to_one(self):
        for rho in (1.0, -1.0, 1.5):
            with self.assertRaises(ValueError):
                ls.simulate(replace(self.i, correlation=rho), ls.oracle_decisions()[0], 10)


class Stability(unittest.TestCase):
    """Check 4: more trials settle the estimates; the same seed reproduces exactly."""

    def test_more_trials_agree_and_seeds_reproduce(self):
        i, d = ls.oracle_inputs(), ls.oracle_decisions()[1]
        small, large = ls.simulate(i, d, 10_000, seed=1), ls.simulate(i, d, 50_000, seed=2)
        self.assertAlmostEqual(small["mean"], large["mean"], delta=0.15 * B)
        self.assertAlmostEqual(small["share_below_zero"], large["share_below_zero"], delta=0.02)
        again = ls.simulate(i, d, 10_000, seed=1)
        self.assertTrue(np.array_equal(small["ending_cash"], again["ending_cash"]))
        tied = replace(i, correlation=0.5)
        self.assertTrue(np.array_equal(ls.simulate(tied, d, 5_000, seed=4)["ending_cash"],
                                       ls.simulate(tied, d, 5_000, seed=4)["ending_cash"]))


if __name__ == "__main__":
    unittest.main()
