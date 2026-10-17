"""Release 2, step 1: an illustrative liquidity stress simulation for Oracle (VSB 2008 Module 2 Monte Carlo).

Question: if Oracle's operating cash flow over the next twelve months (Sep 1, 2026–Aug 31, 2027) varied within
an assumed range, in what share of simulated trials would its checked August 31 cash, plus that cash flow, end the
window below the cash uses the model subtracts, and by how much?

This is a SCENARIO FROM STATED ASSUMPTIONS, NOT A FORECAST OR FUNDING CONCLUSION. A share of trials is a property of
the assumptions, not a probability of default or of a funding gap. The checked reviews keep future funding coverage
Unavailable; nothing here changes them.

Model (uncertain inputs -> business logic -> outputs, as in class):
    ending cash = starting cash + OCF excluding prepayments + prepayments
                  - capital spending - dividends - dated debt principal - commercial paper due - added uses
                  (+ revolver draw, a hypothetical, capped at the $10B commitment)
Filing facts: starting cash and dated note/term-loan principal (oracle_principal.json). Assumptions: every triangle.
Its corners are anchored to checked historical figures, but history doesn't establish future bounds or that any
value is most likely. Capex and dividends are decisions. OCF and prepayments can be correlated (default 0).

Only end-of-window cash is tested: cash could fall below zero on a payment date inside the window while ending cash
is positive. Uses left out are in EXCLUDED (overlap shown by a filing) and oracle_uses_outside_model() (not
shown to overlap; their effect is measured by added_uses, never folded into the base result).
No Streamlit, no network. Seeded, so the same inputs and seed give identical output.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np

SAMPLES = Path(__file__).parent / "samples"
HORIZON = ("2026-09-01", "2027-08-31")
LABEL = "Illustrative scenario from stated assumptions, not a forecast or funding conclusion."
DEFAULT_TRIALS = 10_000
DEFAULT_SEED = 2026
B = 1_000_000_000
COMPARE_CORRELATIONS = (-0.5, 0.0, 0.5)
CORRELATION_BASIS = ("No filing establishes how OCF excluding prepayments and customer prepayments move together, so "
                     "the default is 0 (independent). Positive: strong cloud demand could raise both. Negative: "
                     "prepaid cash is not collected again later. The setting is the correlation of the normal scores "
                     "behind each draw; the realized correlation of the dollar draws is reported beside it.")
TIMING_LIMIT = ("Ending cash is measured once, on August 31, 2027. The model does not test cash on each payment date: "
                "a maturity early in the window could exceed cash on hand even when ending cash is positive, and the "
                "timing of OCF, capex and dividends within the year is not modelled.")
TRIANGLE_BASIS = ("Assumed distribution. The corners are anchored to checked historical figures; history does not "
                  "establish that future values stay inside them or that the middle value is most likely.")
TEN_K = "10-K fiscal 2026, accession 0001193125-26-277521"
TEN_Q = "10-Q Q1 fiscal 2027, accession 0001193125-26-389274"
# Cash uses left out because a filing shows they are already inside a modelled line. Counting them again would
# subtract the same cash twice.
EXCLUDED = [
    ("Operating lease payments", "Inside OCF",
     f"Oracle's policy: operating lease cash flows are operating cash flows ({TEN_K}, Note 1)."),
    ("Finance-lease interest", "Inside OCF",
     f"Oracle's policy: the interest component of finance-lease payments is an operating cash flow ({TEN_K}, Note 1)."),
    ("Interest on borrowing and income taxes", "Inside OCF",
     "US GAAP classifies cash interest and income taxes as operating cash flows (ASC 230). Historical OCF reflects "
     "historical interest, not interest on debt raised since."),
    ("Restricted cash ($2.565B at Aug 31, 2026)", "Not in starting cash",
     f"Starting cash excludes it ({TEN_Q}, balance sheet and cash reconciliation). Excluding it is a balance choice, "
     "not a cash use."),
]
_PHI = np.vectorize(lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2))), otypes=[float])


@dataclass(frozen=True)
class Triangular:
    """Minimum, most likely, maximum (USD). A zero-width triangle is a fixed value."""
    low: float
    mode: float
    high: float
    basis: str = ""

    def __post_init__(self):
        if not self.low <= self.mode <= self.high:
            raise ValueError(f"Triangle must satisfy low <= mode <= high, got {self.low}, {self.mode}, {self.high}")

    @property
    def mean(self) -> float:
        return (self.low + self.mode + self.high) / 3

    def draw(self, rng: np.random.Generator, n: int) -> np.ndarray:
        if self.low == self.high:
            return np.full(n, float(self.low))
        return rng.triangular(self.low, self.mode, self.high, n)

    def quantile(self, u) -> np.ndarray:
        """Inverse CDF: the value with a share u of the triangle below it. Turns uniforms into triangular draws."""
        u = np.asarray(u, dtype=float)
        a, c, b = self.low, self.mode, self.high
        if a == b:
            return np.full(u.shape, float(a))
        split = (c - a) / (b - a)    # share of the area left of the mode
        left = a + np.sqrt(u * (b - a) * (c - a))
        right = b - np.sqrt((1 - u) * (b - a) * (b - c))
        return np.where(u < split, left, right)


def correlated_uniforms(rng: np.random.Generator, n: int, rho: float) -> tuple[np.ndarray, np.ndarray]:
    """Two uniform series whose normal scores have correlation rho (a Gaussian copula).

    Each series stays uniform, so each input keeps its own triangle; only how they move together changes, as in
    class. The second score is rho * z1 + sqrt(1 - rho^2) * z2. With the same seed, every rho reuses the same z1 and
    z2, so differences between correlation settings come from the correlation, not from new random numbers.
    """
    if not -1 < rho < 1:
        raise ValueError(f"Correlation must be between -1 and 1 (exclusive), got {rho}")
    z1, z2 = rng.standard_normal((2, n))
    return _PHI(z1), _PHI(rho * z1 + math.sqrt(1 - rho * rho) * z2)


@dataclass(frozen=True)
class Decision:
    """What the user chooses: capex, dividends and whether the revolver is assumed usable."""
    name: str
    capex: float
    dividends: float
    revolver: bool


@dataclass
class Inputs:
    starting_cash: float
    principal_due: float
    revolver_commitment: float
    ocf_ex_prepayments: Triangular
    prepayments: Triangular
    commercial_paper_due: Triangular
    sources: dict = field(default_factory=dict)
    correlation: float = 0.0      # OCF excluding prepayments vs prepayments, normal-score correlation
    added_uses: float = 0.0       # a fixed extra use, for measuring uses outside the base model; 0 in the base


@dataclass(frozen=True)
class OutsideUse:
    """A cash use the base model leaves out without a filing showing it overlaps a modelled line."""
    name: str
    amount: float          # the stated amount used to measure its effect (USD)
    amount_basis: str      # what that amount is and why it may over- or understate the use
    why_outside: str       # why it is not in the base model
    source: str


def oracle_inputs(folder: Path | None = None) -> Inputs | None:
    """Fixed inputs and default ranges from the saved checked evidence; None if any of it doesn't load."""
    import oracle_principal
    folder = Path(folder) if folder else SAMPLES
    try:
        snap = next(s for s in json.loads((folder / "liquidity_pilots.json").read_text(encoding="utf-8"))["snapshots"]
                    if s["ticker"] == "ORCL")
        quarter = json.loads((folder / "oracle_liquidity.json").read_text(encoding="utf-8"))
        calendar = oracle_principal.load(folder)
        if calendar is None or quarter.get("status") != "Checked":
            return None
        q, ocf = quarter["inputs"], snap["metrics"]["operating_cash_flow"]
        fiscal_year = next(f["value"] for f in ocf["inputs"] if f["role"] == "Fiscal year")
        ttm = ocf["value"]
        rec = calendar["reconciliation"]
        cp_low, cp_high = rec["commercial_paper_range"]
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        return None
    ttm_ex = ttm - q["prepay"]["value"]
    quarter_ex = (q["ocf"]["value"] - q["prepay"]["value"]) * 4
    return Inputs(
        starting_cash=q["closing_cash"]["value"],
        principal_due=calendar["next_twelve_months"]["principal"],
        revolver_commitment=10 * B,
        ocf_ex_prepayments=Triangular(fiscal_year, ttm_ex, quarter_ex,
            "Assumed. Low set at fiscal 2026 OCF; most likely set at TTM OCF less the specified prepayments; high set "
            "at Jun–Aug 2026 OCF excluding prepayments times four (one quarter annualized). These are checked "
            "historical figures; they do not establish future bounds or that the TTM figure is most likely."),
        prepayments=Triangular(0, 0, q["prepay"]["value"],
            "Assumed. From none (Q1 FY2026 had none) to one more quarter like Jun–Aug 2026, most likely none. "
            "Recurrence isn't established."),
        commercial_paper_due=Triangular(cp_low, (cp_low + cp_high) / 2, cp_high,
            "The August 31 balance is Unavailable; the low and high are the range implied by rounded 10-Q figures "
            "(derived). The midpoint as most likely, and repayment within the year, are assumptions."),
        sources={
            "starting_cash": "10-Q balance sheet, Aug 31, 2026 (cash and equivalents, excludes restricted cash)",
            "principal_due": "Oracle principal calendar: notes and term loan due Sep 2026–Aug 2027 (oracle_principal.json)",
            "revolver_commitment": "Revolving credit agreement, $10B commitment; drawable amount Unavailable (hypothetical only)",
            "ocf": "10-K FY2026 and 10-Q Q1 FY2027 cash-flow statements (liquidity_pilots.json, oracle_liquidity.json)",
        })


def oracle_uses_outside_model(folder: Path | None = None) -> list[OutsideUse] | None:
    """Uses not shown to overlap a modelled line, each with the stated amount its effect is measured at."""
    folder = Path(folder) if folder else SAMPLES
    try:
        q = json.loads((folder / "oracle_liquidity.json").read_text(encoding="utf-8"))["inputs"]
        finance, purchase = q["finance_0"]["value"], q["purchase_0"]["value"]
        capex_financing_quarter = q["capex_financing"]["value"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    # Net proceeds by year from the 10-K cash-flow statement (p. 68; pilot_evidence_oracle.md); fiscal 2024 was nil.
    capex_financing = 1_422_000_000 + 3_345_000_000 + capex_financing_quarter
    return [
        OutsideUse("Finance-lease principal", finance,
                   "$0.620B of finance-lease payments due Sep 2026–May 2027 (undiscounted). It includes interest that "
                   "is already in OCF, so it overstates principal for those nine months; Jun–Aug 2027 is Unavailable.",
                   "Oracle classifies the principal component as a financing cash flow, so it is not inside OCF or "
                   "capex. The principal amount for the window is not disclosed.",
                   f"{TEN_Q}, Note 6 p. 12; {TEN_K}, Note 1"),
        OutsideUse("Short-term financing related to capex", capex_financing,
                   "Cumulative net proceeds: $1.422B (fiscal 2025) + $3.345B (fiscal 2026) − $0.830B (Jun–Aug 2026) = "
                   "$3.937B. An indicator only: the balance, terms and due dates are not disclosed.",
                   "A separate financing line, so its repayment is not in cash capex or OCF. Whether it would be "
                   "repaid or rolled within the window is not stated.",
                   f"{TEN_K} p. 68; {TEN_Q} p. 5"),
        OutsideUse("Purchase and other obligations", purchase,
                   "$5.449B due Sep 2026–May 2027. Jun–Aug 2027 is part of fiscal 2028's $6.176B and is Unavailable.",
                   "Primarily cloud-infrastructure components (likely capex when paid) and data-center power (likely "
                   "inside OCF). The filing does not split them, so overlap with the capex decision and OCF is "
                   "possible but not established.",
                   f"{TEN_Q}, Note 6 p. 13"),
    ]


# Omissions with no amount that can be measured; stated, not simulated.
UNQUANTIFIED = [
    ("Leases not yet commenced ($288B)", "Payments would enter OCF after commencement (fiscal 2027–2029) and are not "
     "in the historical OCF the triangle is anchored to. Annual amounts are Unavailable. Direction: lowers cash."),
    ("Lessor-borrowing guarantee (up to $3.3B)", "Disclosed at May 31, 2026 for a borrowing maturing September 2026; "
     "its status at August 31 is not stated. Contingent, not modelled."),
    ("Other financing activities, net", "$0.242B outflow in Jun–Aug 2026 with no stated composition; it may include "
     "the finance-lease principal above. Not modelled."),
    ("June–August 2027 lease and purchase payments", "Fall in fiscal 2028 buckets that are not split by month. "
     "Unavailable."),
    ("Share repurchases and acquisitions", "None in Jun–Aug 2026; not modelled. They would be decisions."),
]


def outside_use_effects(inputs: Inputs, uses: list[OutsideUse], decision: Decision,
                        trials: int = DEFAULT_TRIALS, seed: int = DEFAULT_SEED) -> list[dict]:
    """The base result, then each outside use subtracted alone, then all together. Same seed throughout, so the
    differences come from the added use, not new random numbers."""
    rows = [("Base model", 0.0)] + [(u.name, u.amount) for u in uses] + [("All three together", sum(u.amount for u in uses))]
    return [{"scenario": name, "added_uses": amount,
             **simulate(replace(inputs, added_uses=amount), decision, trials, seed)} for name, amount in rows]


def oracle_decisions(folder: Path | None = None) -> list[Decision]:
    """The two capex levels the evidence supports, each with and without the hypothetical revolver."""
    folder = Path(folder) if folder else SAMPLES
    snap = next(s for s in json.loads((folder / "liquidity_pilots.json").read_text(encoding="utf-8"))["snapshots"]
                if s["ticker"] == "ORCL")
    quarter = json.loads((folder / "oracle_liquidity.json").read_text(encoding="utf-8"))["inputs"]
    capex = snap["metrics"]["capital_spending"]
    ttm = capex["value"]
    fiscal_year = next(f["value"] for f in capex["inputs"] if f["role"] == "Fiscal year")
    dividends = quarter["dividends"]["value"] * 4
    return [Decision(f"Capex at {label}{', revolver assumed usable' if rev else ''}", amount, dividends, rev)
            for label, amount in (("the TTM rate", ttm), ("the fiscal 2026 level", fiscal_year))
            for rev in (False, True)]


def ending_cash(inputs: Inputs, decision: Decision, ocf, prepayments, commercial_paper):
    """The business logic, for scalars or arrays: cash before and after any revolver draw."""
    before = (inputs.starting_cash + ocf + prepayments - decision.capex - decision.dividends
              - inputs.principal_due - commercial_paper - inputs.added_uses)
    if not decision.revolver:
        return before, before
    draw = np.minimum(np.maximum(-before, 0), inputs.revolver_commitment)
    return before, before + draw


def simulate(inputs: Inputs, decision: Decision, trials: int = DEFAULT_TRIALS, seed: int = DEFAULT_SEED) -> dict:
    """Seeded trials for one decision. Draw order is fixed, so each seed is reproducible."""
    if trials < 1:
        raise ValueError("trials must be positive")
    rng = np.random.default_rng(seed)
    u_ocf, u_pre = correlated_uniforms(rng, trials, inputs.correlation)
    ocf = inputs.ocf_ex_prepayments.quantile(u_ocf)
    pre = inputs.prepayments.quantile(u_pre)
    cp = inputs.commercial_paper_due.draw(rng, trials)
    before, after = ending_cash(inputs, decision, ocf, pre, cp)
    short = after < 0
    varies = trials > 1 and ocf.std() > 0 and pre.std() > 0
    return {
        "decision": decision.name, "trials": trials, "seed": seed, "label": LABEL,
        "correlation": inputs.correlation,
        "realized_correlation": float(np.corrcoef(ocf, pre)[0, 1]) if varies else None,
        "mean": float(after.mean()), "sd": float(after.std(ddof=1)) if trials > 1 else 0.0,
        "p10": float(np.percentile(after, 10)), "p50": float(np.percentile(after, 50)),
        "p90": float(np.percentile(after, 90)),
        # Shares of simulated trials under the stated assumptions; not probabilities of default or of a funding gap.
        "share_below_zero": float(short.mean()),
        "mean_shortfall": float(-after[short].mean()) if short.any() else 0.0,
        "share_revolver_used": float((after > before).mean()) if decision.revolver else 0.0,
        "ending_cash": after,
    }


def compare_correlations(inputs: Inputs, decision: Decision, trials: int = DEFAULT_TRIALS,
                         seed: int = DEFAULT_SEED, rhos=COMPARE_CORRELATIONS) -> list[dict]:
    """One decision at several correlations, same seed: the class check that correlation moves spread, not mean."""
    return [simulate(replace(inputs, correlation=rho), decision, trials, seed) for rho in rhos]


def run(folder: Path | None = None, trials: int = DEFAULT_TRIALS, seed: int = DEFAULT_SEED) -> dict | None:
    """All four default scenarios, or None when the checked evidence doesn't load."""
    inputs = oracle_inputs(folder)
    if inputs is None:
        return None
    return {"inputs": inputs, "horizon": HORIZON, "label": LABEL,
            "results": [simulate(inputs, d, trials, seed) for d in oracle_decisions(folder)]}
