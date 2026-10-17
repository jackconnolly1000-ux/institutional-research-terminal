"""Release 2, step 1: an illustrative liquidity stress simulation for Oracle (VSB 2008 Module 2 Monte Carlo).

Question: if Oracle's operating cash flow over the next twelve months (Sep 1, 2026–Aug 31, 2027) varied within
a stated range, how often would its checked August 31 cash, plus that cash flow, fall short of the cash uses the
evidence dates, and by how much?

This is a SCENARIO FROM STATED ASSUMPTIONS, NOT A FORECAST OR FUNDING CONCLUSION. The checked reviews keep future
funding coverage Unavailable; nothing here changes them.

Model (uncertain inputs -> business logic -> outputs, as in class):
    ending cash = starting cash + OCF excluding prepayments + prepayments
                  - capital spending - dividends - dated debt principal - commercial paper due
                  (+ revolver draw, a hypothetical, capped at the $10B commitment)
Fixed inputs come from the saved, checked JSON and keep their sources. Uncertain inputs are triangular. Capex
and dividends are decisions the user sets, not uncertainties. Lease payments are NOT subtracted: operating lease
payments are already inside OCF, finance-lease interest is too and its principal split is not disclosed, and
purchase obligations overlap capex. Subtracting them as well would count the same cash twice.
No Streamlit, no network. Seeded, so the same inputs and seed give identical output.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SAMPLES = Path(__file__).parent / "samples"
HORIZON = ("2026-09-01", "2027-08-31")
LABEL = "Illustrative scenario from stated assumptions, not a forecast or funding conclusion."
DEFAULT_TRIALS = 10_000
DEFAULT_SEED = 2026
B = 1_000_000_000


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
            "Low: fiscal 2026 OCF. Most likely: TTM OCF less the specified prepayments. High: Jun–Aug 2026 OCF "
            "excluding prepayments, times four (one quarter annualized, so an optimistic upper bound)."),
        prepayments=Triangular(0, 0, q["prepay"]["value"],
            "Between none (Q1 FY2026 had none) and one more quarter like Jun–Aug 2026. Recurrence isn't established."),
        commercial_paper_due=Triangular(cp_low, (cp_low + cp_high) / 2, cp_high,
            "The August 31 balance is Unavailable; this is the range implied by rounded 10-Q figures. "
            "Commercial paper is short-term, so the balance is treated as due within the year."),
        sources={
            "starting_cash": "10-Q balance sheet, Aug 31, 2026 (cash and equivalents, excludes restricted cash)",
            "principal_due": "Oracle principal calendar: notes and term loan due Sep 2026–Aug 2027 (oracle_principal.json)",
            "revolver_commitment": "Revolving credit agreement, $10B commitment; drawable amount Unavailable (hypothetical only)",
            "ocf": "10-K FY2026 and 10-Q Q1 FY2027 cash-flow statements (liquidity_pilots.json, oracle_liquidity.json)",
        })


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
              - inputs.principal_due - commercial_paper)
    if not decision.revolver:
        return before, before
    draw = np.minimum(np.maximum(-before, 0), inputs.revolver_commitment)
    return before, before + draw


def simulate(inputs: Inputs, decision: Decision, trials: int = DEFAULT_TRIALS, seed: int = DEFAULT_SEED) -> dict:
    """Seeded trials for one decision. Draw order is fixed, so each seed is reproducible."""
    if trials < 1:
        raise ValueError("trials must be positive")
    rng = np.random.default_rng(seed)
    ocf = inputs.ocf_ex_prepayments.draw(rng, trials)
    pre = inputs.prepayments.draw(rng, trials)
    cp = inputs.commercial_paper_due.draw(rng, trials)
    before, after = ending_cash(inputs, decision, ocf, pre, cp)
    short = after < 0
    return {
        "decision": decision.name, "trials": trials, "seed": seed, "label": LABEL,
        "mean": float(after.mean()), "sd": float(after.std(ddof=1)) if trials > 1 else 0.0,
        "p10": float(np.percentile(after, 10)), "p50": float(np.percentile(after, 50)),
        "p90": float(np.percentile(after, 90)),
        "probability_shortfall": float(short.mean()),
        "mean_shortfall": float(-after[short].mean()) if short.any() else 0.0,
        "probability_revolver_used": float((after > before).mean()) if decision.revolver else 0.0,
        "ending_cash": after,
    }


def run(folder: Path | None = None, trials: int = DEFAULT_TRIALS, seed: int = DEFAULT_SEED) -> dict | None:
    """All four default scenarios, or None when the checked evidence doesn't load."""
    inputs = oracle_inputs(folder)
    if inputs is None:
        return None
    return {"inputs": inputs, "horizon": HORIZON, "label": LABEL,
            "results": [simulate(inputs, d, trials, seed) for d in oracle_decisions(folder)]}
