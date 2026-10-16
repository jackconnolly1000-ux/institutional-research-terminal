"""Dated interpretations of exact checked evidence, shared by the app and exports.

The prose is reviewed against these frozen sources. Changed evidence requires a new
review rather than silently retaining a conclusion about different facts.
"""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

FOLDER = Path(__file__).parent / "samples"
CHECKED = {
    "liquidity_pilots.json": "7277641a931df81119db973b3340eb3e31249453c4fa706efcd4c3f333241760",
    "lly_liquidity.json": "542757d63352a595c467c4105e10ac6dfa5139bd6562c043d2881e352aa0808b",
    "lly_financing.json": "d13be6bc052357ce2745b83131784d2c52c95ab1addcef36fa81c7965ed9425e",
    "lly_interest.json": "9a82bb4336cf164825a2502de10a0cdc038b139ec505485ea914d6c1e038a614",
    "oracle_liquidity.json": "ecc763f0701f9d97568adf4396792427d309812d1c8b3ca480fc3aa1da6c9200",
    "oracle_financing.json": "d913c737cfa41886784dd008c92f5c30d5cbb59969f238ed2d6eae8d7ef113ad",
    "oracle_revolver.json": "c1fc2b38a04f92187fa676581ac3e8eb07f4a9edc85a1bf58389beabab808103",
    "oracle_interest.json": "0aa090b90a9f7207b693697be60f215bb6c4e5177fa3423a3d5e6e56d3ac6cec",
    "vistra_liquidity.json": "8f4bdb5f276cb38b2929c998565168869f02b0ce2d6b84e7c285e9002ea0affd",
    "vistra_interest.json": "6a18cf366130ac1aeaf1edccb748b96a1abc3361864651a13b99504d2defa2d4",
}
FILES = {
    "LLY": ["liquidity_pilots.json", "lly_liquidity.json", "lly_financing.json", "lly_interest.json"],
    "ORCL": ["liquidity_pilots.json", "oracle_liquidity.json", "oracle_financing.json", "oracle_revolver.json", "oracle_interest.json"],
    "VST": ["liquidity_pilots.json", "vistra_liquidity.json", "vistra_interest.json"],
}
COMPARISON = ("Coverage bases differ: Lilly derives operating income and its interim capitalization basis is unstated. "
              "Oracle uses reported operating income and a reported interest line with unresolved composition/capitalization. "
              "Vistra uses reported operating income and a separate interest component before the capitalized-interest deduction. "
              "The periods also differ. These historical accrual ratios do not rank funding strength, measure covenant headroom or prove future repayment capacity.")


def source(label, accession, document, cik, location):
    return {"label": label, "accession": accession, "location": location,
            "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{document}"}


LQ = source("10-Q filed Aug 5, 2026", "0000059478-26-000081", "lly-20260630.htm", 59478, "pp. 7–8, 12–14, 17, 23, 31")
LK = source("10-K filed Feb 12, 2026", "0000059478-26-000013", "lly-20251231.htm", 59478, "pp. 51, 57, 76–77")
LE = source("Earnings exhibit filed Aug 5, 2026", "0000059478-26-000077", "q226lillysalesandearningsp.htm", 59478, "Other announcements")
OQ = source("10-Q filed Sep 11, 2026", "0001193125-26-389274", "orcl-20260831.htm", 1341439, "pp. 1–2, 5–7, 12–14, 32–35")
OK = source("10-K filed Jun 22, 2026", "0001193125-26-277521", "orcl-20260531.htm", 1341439, "pp. 50, 65, 83–85, 88")
OA = source("Credit agreement filed Mar 11, 2026", "0001193125-26-101045", "orcl-ex10_17.htm", 1341439, "§§2.01, 2.21, 4.02, 6.02(c)")
VQ = source("10-Q filed Aug 10, 2026", "0001692819-26-000019", "vistra-20260630.htm", 1692819, "pp. 1–5, 15, 20–28, 39, 67–70")
VK = source("10-K filed Feb 27, 2026", "0001692819-26-000006", "vistra-20251231.htm", 1692819, "pp. 79, 113–121, 159–160")
VA = source("Credit amendment filed Jun 30, 2026", "0001140361-26-026944", "ef20077059_ex10-1.htm", 1692819, "Annex B §§7.1–7.2, 9.13, 10.9")
VN = source("Issuance 8-K filed Sep 24, 2026", "0001140361-26-037577", "ef20082680_8k.htm", 1692819, "Items 1.01, 8.01; Ex. 4.2")

CONCLUSIONS = {
    "LLY": {
        "conclusion": "Acquisition and manufacturing spending compete with repayment resources. H1 cash generation after cash PP&E was less than acquisition/IPR&D cash plus shareholder payouts. Incomplete payment dates and unverified post-expiry credit prevent a future funding-surplus conclusion.",
        "rows": [
            ("Near-term obligations", "At June 30, 2026, current borrowing was $7.050B, a carrying classification without a complete dated principal schedule. Unpaid acquisition cash was $296M with dates unstated. Approximately $2.8B for pending AtaiBeckley was conditional on closing, disclosed August 5.", [LQ]),
            ("Resources and access", "$8.950B cash at June 30 excludes restricted cash. H1 2026 OCF less cash PP&E was $10.764B, already reflected in cash. June unused commitments of $10.1B are not verified drawable funds. The $6B facility's August 2026 expiry has no checked renewal.", [LQ, LK]),
            ("Competing cash uses", "H1 2026 acquisitions/IPR&D used $13.291B and dividends/buybacks $7.051B, while net borrowing contributed $12.602B. July acquisitions used approximately $2B. August's $4.5B Indiana announcement has no cash schedule. Subsequent uses do not establish an updated cash balance.", [LQ, LE]),
            ("Decisive unknowns", "Future funding coverage: Unavailable. Needed: remaining principal dates, current drawable credit and acquisition/manufacturing payment timing. The December 2025 supply/manufacturing ceiling of up to approximately $10B is conditional over generally up to eight years. Its overlap with later investment announcements is unresolved.", [LQ, LK, LE]),
        ],
        "coverage_basis": "TTM Jul 2025–Jun 2026: derived operating income $33.633B / reported interest $1.079B. Annual interest is net of capitalization; the interim basis and capitalized amount are unstated. No capitalization adjustment or earnings addback is made.",
        "coverage_sources": [LQ, LK], "coverage_formula": "='Debt and liquidity'!B50",
    },
    "ORCL": {
        "conclusion": "Equity proceeds and specified customer prepayments contributed to funding a quarter in which capex exceeded operating cash flow. The dated cash balance does not establish coverage of future debt and infrastructure payments.",
        "rows": [
            ("Near-term obligations", "At August 31, 2026, current borrowing was $7.625B, not a principal payment calendar. September 2026–May 2027 disclosed payments are $3.219B operating leases, $620M finance leases and $5.449B purchase/other obligations. They remain separate because overlap is unresolved.", [OQ]),
            ("Resources and access", "$36.369B cash at August 31 excludes $2.565B restricted cash. The $10B revolver was undrawn at May 31. August/later drawings and drawable capacity are Unavailable. Draw conditions apply. The fully used $20B gross ATM equity program provides no remaining capacity.", [OQ, OK, OA]),
            ("Competing cash uses", "Jun–Aug 2026 OCF $23.103B included $11.363B specified customer prepayments. Cash capex was $28.499B and net ATM proceeds $19.909B. OCF less specified prepayments and capex was negative $16.759B. This historical exclusion is not recurring OCF or a forecast.", [OQ]),
            ("Decisive unknowns", "Future funding coverage: Unavailable. Needed: remaining debt principal dates, current drawable credit, future cash generation and commitment overlap. The $288B leases not yet commenced have no annual payment schedule. Historical equity/prepayment inflows are already in cash and cannot be added again.", [OQ, OK, OA]),
        ],
        "coverage_basis": "TTM Sep 2025–Aug 2026: reported operating income $23.057B / reported interest $5.104B. Borrowing-only composition and capitalization basis are Unavailable. Separately disclosed $357M finance-lease interest is not added or subtracted without a reconciliation.",
        "coverage_sources": [OQ, OK], "coverage_formula": "='Cash analysis'!B49",
    },
    "VST": {
        "conclusion": "Selected late-2026 payments require attention to facility conditions and where funds sit. June reported liquidity cannot be treated as current cash available to Parent, and historical earnings coverage does not resolve those access constraints.",
        "rows": [
            ("Near-term obligations", "June 30 disclosures identify $261M Pulaski bridge principal due Dec 3, 2026, $297M construction balance with December conversion conditions, $500M notes due Dec 30 and $631M Nuveen principal/interest due Dec 31. Vistra guarantees the bridge. This is not a complete debt-service schedule. A further $800M notes mature Jan 30, 2027.", [VQ]),
            ("Resources and access", "June 30 cash was $435M, excluding $46M restricted cash. Reported liquidity $6.295B also included $4.408B revolver and $1.452B commodity-linked availability at that date. Revolver LCs already reduce capacity. Current drawable capacity and Parent-accessible cash are Unavailable. Project debt and collateral constrain transfers.", [VQ, VK, VA]),
            ("Competing cash uses", "H1 2026 OCF less capex/nuclear fuel/LTSA prepayments was $650M, against $959M buybacks/dividends. Approximately $2.3B Cogentrix cash consideration was expected at a conditional late-2026 closing. Helix's initial $500M remained callable at June 30. The additional up-to-$500M was conditional or elective.", [VQ]),
            ("Decisive unknowns", "Future funding coverage: Unavailable. Needed: current borrowing base, draw-condition compliance, Parent transfers and closing/call timing. Helix funded-to-date and completed preferred redemptions are unresolved. Later issuance proceeds are not added to June liquidity. Project debt is already included in baseline borrowing.", [VQ, VK, VA, VN]),
        ],
        "coverage_basis": "TTM Jul 2025–Jun 2026: reported operating income $3.563B / separate interest component $1.117B, before the capitalized-interest deduction. The swap/extinguishment/Other bridge reconciles. Receivables/Nuveen allocation and all-in financing-cost coverage remain Unavailable.",
        "coverage_sources": [VQ, VK], "coverage_formula": "='Cash review'!B79",
    },
}


def fingerprint():
    """Workbook manifests bind both the selected evidence and this interpretation."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def load(ticker, folder=None):
    folder = Path(folder) if folder is not None else FOLDER
    if ticker not in FILES:
        return None
    try:
        for name in FILES[ticker]:
            if hashlib.sha256((folder / name).read_bytes()).hexdigest() != CHECKED[name]:
                return None
        snapshot = next(s for s in json.loads((folder / "liquidity_pilots.json").read_text())["snapshots"] if s["ticker"] == ticker)
        stem = {"LLY": "lly", "ORCL": "oracle", "VST": "vistra"}[ticker]
        interest = json.loads((folder / f"{stem}_interest.json").read_text())
        out = deepcopy(CONCLUSIONS[ticker])
        out.update(ticker=ticker, company=snapshot["company_name"], period_end=snapshot["metrics"]["cash"]["period_end"],
                   reviewed="2026-10-16", status="Checked", coverage=interest["calculation"]["value"],
                   comparison=COMPARISON, snapshot=snapshot, evidence_files=FILES[ticker])
        return out
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        return None


def for_snapshot(snapshot):
    review = load(snapshot.get("ticker"))
    return review if review and review["snapshot"] == snapshot else None


def render(snapshot):
    from html import escape
    review = for_snapshot(snapshot)
    if review is None:
        return '<section class="lr-funding"><h3>Funding conclusion</h3><p>Unavailable: the saved evidence does not match this reviewed conclusion.</p></section>'
    out = ('<section class="lr-funding"><h3>Funding conclusion</h3>'
           f'<p class="lr-meta">Interpretation checked {review["reviewed"]} · balance sheet {review["period_end"]} · dates below remain historical</p>'
           f'<p class="lr-answer">{escape(review["conclusion"])}</p>')
    for label, text, sources in review["rows"]:
        out += f'<div class="lr-funding-row"><h4>{escape(label)}</h4><div><p>{escape(text)}</p>'
        out += '<div class="lr-meta">' + ' · '.join(f'<a href="{escape(s["url"])}" target="_blank" rel="noopener noreferrer">{escape(s["label"])} {escape(s["location"])}</a>' for s in sources) + '</div></div></div>'
    out += (f'<details><summary>Historical coverage basis: {review["coverage"]:.2f}x</summary>'
            f'<p>{escape(review["coverage_basis"])}</p><p class="lr-meta">{escape(COMPARISON)}</p></details></section>')
    return out.replace("$", "&#36;")
