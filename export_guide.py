"""Contents and reading rules for the three checked individual exports."""
import hashlib
from pathlib import Path

COMMON = [
    ("Funding conclusion", "Start here: obligations, accessible resources, competing uses and decisive unknowns."),
    ("Borrowing and leases", "Borrowing components, dated lease liabilities and uncommenced commitments, separately."),
    ("Debt and liquidity", "Latest checked ratios, formulas, periods and company-specific limits."),
    ("History", "Annual versus latest dated balances; overlapping FY and TTM flows. Unavailable is not zero."),
    ("Core charts", "What remained after capital spending, and how checked cash/borrowing balances changed."),
]
DETAILS = {
    "LLY": [("Repayment review", "H1 cash uses, conditional commitments, credit evidence and selected May issuance maturities.")],
    "ORCL": [("Repayment review", "Dated obligations, possible funding and unresolved availability."),
             ("Cash analysis", "Quarter cash bridge, customer prepayments, equity proceeds and historical interest build."),
             ("Payment dates", "Contract schedules on their own dates and bases; no combined obligations total.")],
    "VST": [("Cash review", "Cash uses and interest/swaps/extinguishment/capitalization reconciliation."),
            ("Payment dates", "Selected Nuveen, Helix and project payments; conditional or unknown dates stay explicit."),
            ("Financing capacity", "Resource access, letters of credit, facility conditions and Parent restrictions.")],
}
TAIL = [("Data", "Reported inputs with filing dates, accessions, tags, contexts and source URLs; separate evidence blocks."),
        ("About", "Definitions, source scope, missing values, colors and methodology references.")]
CAPTION = "Individual workbook: funding conclusion, borrowing and leases, reconciled ratios, dated history, charts, company detail and source evidence. Figures are historical; editing inputs does not update the checked narrative."
COMBINED_CAPTION = "The optional combined workbook contains the original core metric summary, source inputs and About sheet only. Company dates, fiscal periods and definitions differ; this is not a peer ranking. Use each company's primary download for its full review, history, charts and limitations."


def contents(ticker):
    return COMMON + DETAILS[ticker] + TAIL


def fingerprint():
    root = Path(__file__).parent
    return {"code": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "layout": hashlib.sha256((root / "tests/offline/export_guide.mjs").read_bytes()).hexdigest()}
