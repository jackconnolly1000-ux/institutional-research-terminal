"""Accession-specific review of Oracle's saved revolver evidence, with no network calls.

Contract headroom is distinct from an amount demonstrated to pass every draw condition.
The reviewed document hashes prevent a changed local source from silently inheriting this audit.
"""
import hashlib
import json
from pathlib import Path

import oracle_financing as financing

SAMPLE = Path(__file__).parent / "samples/oracle_revolver.json"
CHECKED = "2026-10-15"
SCOPE = ("Seven saved documents: the May 31 10-K, August 31 10-Q, March 6 credit agreement, "
         "and the September 10 and September 14 8-Ks with their exhibits. "
         "The latest saved filing is September 14, 2026. This is not a complete later-filing inventory.")

# Each finding belongs to these exact saved documents, not to a company or form in general.
_SOURCES = [
    ("annual", "orcl-20260531.htm", "10-K", "2026-06-22", financing.ACCESSION, "2026-05-31",
     "61a353e222f961e516bb3e8eed024a5245cfadbf30e3cc16a4a520129f1bdf63"),
    ("quarter", "orcl-20260831.htm", "10-Q", "2026-09-11", financing.QUARTER_ACCESSION, "2026-08-31",
     "051dd4893fa497f36d99c8a355cbc90107f56e1a628c78e38c76e7dca0d4a6fd"),
    ("agreement", "orcl-ex10_17.htm", "10-Q Ex. 10.17", "2026-03-11", "0001193125-26-101045", "2026-03-06",
     "df6152c36ea03e85eeef7153f4a9778cf170bfefd2ffd682c80aa401711478a0"),
    ("earnings", "8k-000119312526387905-orcl-20260910.htm", "8-K", "2026-09-10", "0001193125-26-387905", "2026-09-10",
     "159c0926d92ff240406168337f5361dd67b314a0c465306dcae903aa67107d5c"),
    ("earnings_exhibit", "8k-000119312526387905-orcl-ex99_1.htm", "8-K Ex. 99.1", "2026-09-10", "0001193125-26-387905", "2026-09-10",
     "805d1f0650b1498f845c40fd18d7ed2da0db5035165fe6086b35eb856c177eed"),
    ("plan", "8k-000119312526389753-d20034d8k.htm", "8-K", "2026-09-14", "0001193125-26-389753", "2026-09-12",
     "d3c88d191e5e9ad5a1e62298e67e10d5f1e3b419dda8e4647a8bca0cd8afefb1"),
    ("plan_exhibit", "8k-000119312526389753-d20034dex991.htm", "8-K Ex. 99.1", "2026-09-14", "0001193125-26-389753", "2026-09-12",
     "d934b837abf4c1f17b79c765e48365d76a89f73ee66b6023c14de722b3f8d0b3"),
]


def _review() -> dict:
    sources = {}
    for key, name, form, filed, accession, period, digest in _SOURCES:
        document = name.split("-", 2)[2] if name.startswith("8k-") else name
        sources[key] = dict(document=document, form=form, filed=filed, accession=accession,
                            period=period, sha256=digest,
                            source_url=financing.BASE + accession.replace("-", "") + "/" + document)
    dates = [
        dict(date="2026-03-06", source="agreement", location="Title; §§1.01, 2.01, 2.04–2.06",
             commitment=10_000_000_000, drawn=None,
             compliance="Unavailable: no borrowing-date compliance evidence in the agreement.",
             detail="Original contractual commitment. The agreement does not establish actual borrowings on this date."),
        dict(date="2026-05-31", source="annual", location="Note 6, pp. 84–85",
             commitment=10_000_000_000, drawn=0,
             compliance="Reported compliant with debt-related covenants at May 31. Ratio and headroom not disclosed.",
             detail="The 10-K confirms the $10B facility and zero outstanding borrowing. Undrawn commitment is arithmetic, not a verified draw authorization."),
        dict(date="2026-08-31", source="quarter", location="Note 5 p. 11; MD&A liquidity pp. 33–35",
             commitment=None, drawn=None,
             compliance="Unavailable: no updated revolver compliance statement or contract ratio in this 10-Q.",
             detail="The 10-Q does not update the revolver commitment or borrowing balance. Other borrowing and repayment lines cannot identify revolver use."),
    ]
    for row in dates:
        row["undrawn"] = (row["commitment"] - row["drawn"]
                          if row["commitment"] is not None and row["drawn"] is not None else None)
        row["drawable"] = None
        row["drawable_detail"] = ("Unavailable: public evidence does not establish all conditions for a specific borrowing."
                                  if row["undrawn"] is not None else
                                  "Unavailable: same-date commitment, outstanding advances and draw conditions are not established.")
    terms = [
        ("Replacement of the old facility", "10-K Note 6, p. 85",
         "The old $6B revolver was terminated on March 6, 2026 when the new $10B facility was entered. They are not two concurrent commitments."),
        ("Exposure and letters of credit", "§1.01 Revolving Credit Exposure; §2.01",
         "Exposure is defined as outstanding advances. No letter-of-credit issuance subfacility or LC deduction is specified in these operative provisions. Generic Debt and interest definitions mention LCs; they do not create a facility LC sublimit. Company-wide LC usage is Unavailable, not assumed zero."),
        ("Reductions and termination", "§§2.04, 7.01",
         "Oracle may reduce unused commitments on at least three business days' notice. Partial reductions are at least $10M, then $1M increments, and cannot leave commitments below outstanding exposure. Terminated commitments cannot be reinstated. Default provisions can accelerate advances and terminate commitments. No later reduction amount is established by the saved filings."),
        ("Conditional increase ceiling", "§2.05, especially (d)",
         "The agreement permits aggregate commitments up to $12B, subject to conditions and willing existing or additional lenders. This is an option ceiling, not a $12B commitment or $2B of available funding. No exercised increase is established by the saved filings."),
        ("Borrowing procedure and conditions", "§§2.02, 4.02",
         "Notice is due by 11 a.m. New York time three business days before a Term SOFR borrowing, or on the borrowing day for Base Rate. Specified representations must hold, subject to the agreement's exceptions and materiality terms, before and after the borrowing and use of proceeds. No Default or Event of Default may be continuing or result. Public filings do not supply a borrowing-specific confirmation."),
        ("Covenant and evidence needed", "§§1.01, 6.01(f)(iii), 6.02(c)",
         "The contract ratio must be at least 3.0x at fiscal quarter-end. It uses four-quarter contract EBITDA and net cash interest, with specified adjustments and acquisition rules. EBITDA includes specified cash and noncash addbacks. Cash interest includes finance-lease interest and net swap costs, excludes LC fees, and is reduced by cash interest income. The agreement requires a no-default certificate with financial reports; no such separate certificate is in the saved set. Generic operating-income coverage cannot establish covenant headroom."),
        ("Permitted uses", "§§2.21, 6.01(g)",
         "Working capital and other general corporate purposes, subject to Regulation U/X and sanctions, anti-corruption, anti-bribery and anti-money-laundering restrictions. No allocation to a particular repayment is established."),
        ("Expiration and extensions", "§§1.01, 2.06, 2.07",
         "Original maturity is March 6, 2031, subject to earlier termination. Up to two 365-day extensions may be requested. Each lender elects independently; extending and replacement commitments must exceed 50% of the prior total, and extension conditions apply. Non-extending lenders keep their dates. No exercised extension is established by the saved filings."),
    ]
    later = [
        dict(date="2026-09-10", sources=["earnings", "earnings_exhibit"],
             detail="Results, the already completed equity sale and dividends. No updated revolver balance, increase, reduction, extension or drawable amount established."),
        dict(date="2026-09-14", sources=["plan", "plan_exhibit"],
             detail="Filed September 14 for the September 12 insider trading-plan cancellation. No corporate revolver update established."),
    ]
    return dict(status="Checked", ticker="ORCL", anchor=financing.ANCHOR,
                checked_as_of=CHECKED, scope=SCOPE, sources=sources, dates=dates,
                terms=[dict(label=a, location=b, detail=c, source="annual" if a == "Replacement of the old facility" else "agreement") for a, b, c in terms],
                later=later, increase_ceiling=12_000_000_000, original_maturity="2031-03-06",
                conclusion="May 31 undrawn commitment is $10B. Actual drawable capacity is Unavailable at every reviewed date. No saved later disclosure establishes a new amount. Commercial-paper program size is not added to revolver capacity or automatically deducted from it.")


def build(folder: Path) -> dict:
    """Publish the hand-reviewed findings only for the exact seven documents read in this audit."""
    for _, name, *_, digest in _SOURCES:
        try:
            if hashlib.sha256((folder / name).read_bytes()).hexdigest() != digest:
                return dict(status="Unavailable", detail=f"Saved source changed and needs review: {name}.")
        except OSError:
            return dict(status="Unavailable", detail=f"Saved source missing: {name}.")
    return _review()


def load() -> dict:
    """Do not let an edited or stale saved audit inherit the checked registry's interpretation."""
    try:
        saved = json.loads(SAMPLE.read_text())
        if saved == _review():
            return saved
    except (OSError, ValueError):
        pass
    return dict(status="Unavailable", detail="The saved Oracle revolver audit is missing or does not match the checked review.")


def for_snapshot(snapshot: dict) -> dict | None:
    if snapshot.get("ticker") != "ORCL":
        return None
    anchor = snapshot.get("metrics", {}).get("cash", {})
    if anchor.get("accession") != financing.QUARTER_ACCESSION or anchor.get("period_end") != financing.ANCHOR:
        return dict(status="Unavailable", detail="This revolver audit covers only the checked August 31 Oracle snapshot.")
    return load()
