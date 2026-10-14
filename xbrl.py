"""Trailing-twelve-month (TTM) figures from SEC XBRL company facts (data.sec.gov/api/xbrl/companyfacts).

No Streamlit and no network calls here. app.py downloads the JSON (with caching) and passes it in,
so tests call these exact functions on saved company facts.

Why this exists: Yahoo doesn't say what period its margins and free cash flow cover. Company facts are the numbers
companies tag in their own 10-K and 10-Q filings, each with a start date, end date, form and accession number,
so every figure here can name its period and the filings it came from.

Method (decided Oct 11, 2026):
- TTM ends at the period of the latest 10-K or 10-Q. If that's a 10-K, TTM is that fiscal year.
  If it's a 10-Q, TTM = latest fiscal year + current year to date - prior year to date.
- When the same period was reported more than once (a 10-Q repeats last year's figures as comparatives,
  and a restatement changes them), the most recently filed value is used.
- A tag with no value for a needed period is "Not reported in SEC data". Nothing falls back to an older
  period, another tag (except revenue's second tag below) or Yahoo.

Cash and the current-ratio inputs (decided Oct 14, 2026; docs/debt_liquidity_plan.md) are balance-sheet amounts, so they
follow a stricter rule than the TTM figures: they come from the anchor filing itself (see _instant_fact), and the two
current-ratio inputs must come from one filing (see current_ratio).
"""
from __future__ import annotations

from datetime import date, timedelta

URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SOURCE = "SEC XBRL company facts (data.sec.gov)"
NOT_REPORTED = "Not reported in SEC data"

REVENUE_TAGS = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"]   # first one with a full TTM wins
GROSS_PROFIT = "GrossProfit"
OPERATING_INCOME = "OperatingIncomeLoss"
OPERATING_CASH_FLOW = "NetCashProvidedByUsedInOperatingActivities"
CAPEX = "PaymentsToAcquirePropertyPlantAndEquipment"
TAGS = [*REVENUE_TAGS, GROSS_PROFIT, OPERATING_INCOME, OPERATING_CASH_FLOW, CAPEX]   # flows over a period
# Balance-sheet values at one date ("instants", no start date). Confirmed for LLY, ORCL and VST to exclude restricted
# cash; for other filers the plan's open item 1 applies.
CASH = "CashAndCashEquivalentsAtCarryingValue"
CURRENT_ASSETS = "AssetsCurrent"
CURRENT_LIABILITIES = "LiabilitiesCurrent"
DEBT_CURRENT = "DebtCurrent"
LONG_TERM_DEBT_NONCURRENT = "LongTermDebtNoncurrent"
DEBT_TOTAL = "DebtLongtermAndShorttermCombinedAmount"
NOTES_PAYABLE_CURRENT = "NotesPayableCurrent"
LONG_TERM_NOTES_AND_LOANS = "LongTermNotesAndLoans"
INSTANT_TAGS = [CASH, CURRENT_ASSETS, CURRENT_LIABILITIES, DEBT_CURRENT, LONG_TERM_DEBT_NONCURRENT, DEBT_TOTAL,
                NOTES_PAYABLE_CURRENT, LONG_TERM_NOTES_AND_LOANS]

# Borrowing presentations verified per company from its filings (docs/pilot_evidence_*.md). Debt tags are not
# universal (plan, source rules), so a company without an entry gets Unavailable, never a guessed set of tags.
# components: (tag, noun, label) added together; total_check: a filer total that must equal their sum when the
# same filing reports it at the same date; not_added and caveats are stated with the result.
BORROWING_PRESENTATIONS = {
    "LLY": {
        "name": "balance sheet: short-term borrowings and current maturities of long-term debt, plus long-term debt",
        "components": [(DEBT_CURRENT, "short-term borrowings and current maturities",
                        "Short-term borrowings and current maturities of long-term debt"),
                       (LONG_TERM_DEBT_NONCURRENT, "long-term debt", "Long-term debt")],
        "total_check": DEBT_TOTAL,
        # The Note 8 fair-value table (CommercialPaper + LongTermDebt carrying amounts) presents the same debt;
        # adding it would double count
        "not_added": "Note 8 fair-value table (commercial paper and long-term debt carrying amounts), which presents "
                     "the same debt",
        "evidence": "docs/pilot_evidence_lly.md",
        "caveats": [],
    },
    "ORCL": {
        "name": "balance sheet: notes payable and other borrowings, current plus non-current",
        "components": [(NOTES_PAYABLE_CURRENT, "notes payable and other borrowings, current",
                        "Notes payable and other borrowings, current"),
                       (LONG_TERM_NOTES_AND_LOANS, "notes payable and other borrowings, non-current",
                        "Notes payable and other borrowings, non-current")],
        # The 10-K's Note 6 total; a 10-Q does not report it
        "total_check": DEBT_TOTAL,
        "not_added": "the rounded fair-value disclosure of senior notes and other long-term borrowings (a narrower "
                     "subset of the same debt), operating and finance lease liabilities, and cash-flow amounts for "
                     "short-term financing related to capital expenditures",
        "evidence": "docs/pilot_evidence_oracle.md",
        # Stated with every Oracle result so the total is not read as more than it is
        "caveats": ["The split of this total by instrument (senior notes, term loans, commercial paper) is itemized "
                    "only in the 10-K's Note 6; a 10-Q's commercial paper balance is Unavailable and is not inferred "
                    "from this total.",
                    "Short-term financing related to capital expenditures has no disclosed balance (Unavailable); "
                    "its cash-flow amounts are not added to debt."],
    },
}
UNAVAILABLE = "Unavailable"

PERIODIC_FORMS = {"10-K", "10-Q", "10-K/A", "10-Q/A"}
# Fiscal years are 52 or 53 weeks for many filers (Apple: 364 or 371 days), so "a year" is a range
YEAR_DAYS = range(350, 381)
SLACK = timedelta(days=7)

METRICS = {   # key: label, unit
    "revenue": ("Revenue", "USD"),
    "gross_margin": ("Gross margin", "fraction"),
    "operating_margin": ("Operating margin", "fraction"),
    "free_cash_flow": ("Free cash flow", "USD"),
}


class XbrlError(Exception):
    """No usable company facts. Raised (not returned) so st.cache_data never stores it."""


def companyfacts_url(cik: str) -> str:
    return URL.format(cik=str(cik).zfill(10))


def trim(facts: dict, since: str | None = None) -> dict:
    """Keep only the tags read here, from 10-K and 10-Q filings (and amendments): the six period tags in dollars,
    and the balance-sheet tags in every unit, so a fact in another currency can be reported rather than silently missing.
    A full file is 3 to 8 MB; this is what the app caches per company, and what the test fixtures hold.
    since drops periods ending earlier."""
    gaap = facts.get("facts", {}).get("us-gaap", {})
    kept = {}
    for tag in TAGS:
        rows = [r for r in gaap.get(tag, {}).get("units", {}).get("USD", [])
                if r.get("form") in PERIODIC_FORMS and r.get("start") and (since is None or r["end"] >= since)]
        if rows:
            kept[tag] = {"units": {"USD": rows}}
    for tag in INSTANT_TAGS:
        units = {}
        for unit, all_rows in gaap.get(tag, {}).get("units", {}).items():
            rows = [r for r in all_rows
                    if r.get("form") in PERIODIC_FORMS and not r.get("start") and (since is None or r["end"] >= since)]
            if rows:
                units[unit] = rows
        if units:
            kept[tag] = {"units": units}
    return {"cik": facts.get("cik"), "entityName": facts.get("entityName"), "facts": {"us-gaap": kept}}


def _days(start: str, end: str) -> int:
    return (date.fromisoformat(end) - date.fromisoformat(start)).days


def _latest_values(rows: list[dict], filed_by: str | None) -> dict:
    """{(start, end): the most recently filed record}. Ties on the filing date go to the later accession number."""
    out = {}
    for r in rows:
        if r.get("form") not in PERIODIC_FORMS or not r.get("start") or (filed_by and r["filed"] > filed_by):
            continue
        key = (r["start"], r["end"])
        if key not in out or (r["filed"], r["accn"]) > (out[key]["filed"], out[key]["accn"]):
            out[key] = r
    return out


def _filings(gaap: dict, filed_by: str | None) -> dict:
    """{accession: {form, period, filed}}. A filing's period is the latest end date among its facts:
    comparatives in it end earlier, its own period ends last."""
    out = {}
    for tag in TAGS:
        for r in gaap.get(tag, {}).get("units", {}).get("USD", []):
            if r.get("form") not in PERIODIC_FORMS or (filed_by and r["filed"] > filed_by):
                continue
            f = out.setdefault(r["accn"], {"form": r["form"], "period": r["end"], "filed": r["filed"]})
            f["period"] = max(f["period"], r["end"])
    return out


def _anchor_filing(filings: dict) -> tuple[str, dict]:
    """(accession, {form, period, filed}) of the latest original 10-K or 10-Q. Amendments are left out here so a
    late 10-K/A doesn't pull TTM back a year; their values still count when periods are deduplicated."""
    originals = [(f["filed"], acc, f) for acc, f in filings.items() if f["form"] in ("10-K", "10-Q")]
    if not originals:
        raise XbrlError("no 10-K or 10-Q figures in SEC company facts")
    _, acc, f = max(originals)
    return acc, f


def _anchor(filings: dict) -> tuple[str, str]:
    """(period end, form) of the latest original 10-K or 10-Q."""
    f = _anchor_filing(filings)[1]
    return f["period"], f["form"]


def _fmt(d: str) -> str:
    x = date.fromisoformat(d)
    return f"{x:%b} {x.day}, {x.year}"


def _ttm_for_tag(values: dict, end: str, basis: str) -> tuple[list[dict] | None, str]:
    """The records that make one tag's TTM ending at end, each with its role, or (None, why not)."""
    fiscal_years = [r for r in values.values() if _days(r["start"], r["end"]) in YEAR_DAYS]
    if basis == "10-K":
        fy = next((r for r in fiscal_years if r["end"] == end), None)
        return ([{**fy, "role": "fiscal year"}], "") if fy else (None, f"no value for the fiscal year ended {_fmt(end)}")
    ytd = max((r for r in values.values() if r["end"] == end and _days(r["start"], r["end"]) < YEAR_DAYS.start),
              key=lambda r: _days(r["start"], r["end"]), default=None)
    if ytd is None:
        return None, f"no year to date value ending {_fmt(end)}"
    ytd_start = date.fromisoformat(ytd["start"])
    fy = next((r for r in fiscal_years
               if ytd_start - SLACK <= date.fromisoformat(r["end"]) < ytd_start), None)
    if fy is None:
        return None, f"no value for the fiscal year before {_fmt(ytd['start'])}"
    year_ago = date.fromisoformat(end) - timedelta(days=364)
    prior = next((r for r in values.values() if r["start"] == fy["start"] and r is not fy
                  and abs(date.fromisoformat(r["end"]) - year_ago) <= SLACK), None)
    if prior is None:
        return None, "no prior year to date value"
    return [{**fy, "role": "fiscal year"}, {**ytd, "role": "current year to date"},
            {**prior, "role": "prior year to date"}], ""


def _total(parts: list[dict]) -> float:
    return sum(-p["val"] if p["role"] == "prior year to date" else p["val"] for p in parts)


def ttm_metrics(facts: dict, filed_by: str | None = None) -> dict:
    """Four TTM metrics from company facts (full or trimmed). filed_by (YYYY-MM-DD) ignores anything filed later,
    to reproduce what the data said on that day (tests and the saved sample use it).

    Returns {"source", "period_end", "basis" (10-K or 10-Q), "metrics": {key: metric}}. Each metric has
    label, unit, value (None when not reported), period_end, tags, components (each value used, with its role,
    period and filing), filings (form, period, filed, accession; oldest first), note (NOT_REPORTED or None) and
    detail (why it's not reported)."""
    gaap = facts.get("facts", {}).get("us-gaap", {})
    filings = _filings(gaap, filed_by)
    end, basis = _anchor(filings)

    def parts(tag):
        rows = gaap.get(tag, {}).get("units", {}).get("USD", [])
        if not rows:
            return None, f"no {tag} tag"
        got, why = _ttm_for_tag(_latest_values(rows, filed_by), end, basis)
        return ([{**p, "tag": tag} for p in got], "") if got else (None, f"{tag}: {why}")

    def metric(key, tagged_parts, value_from):
        label, unit = METRICS[key]
        missing = [why for _, (p, why) in tagged_parts if p is None]
        used = [x for _, (p, _) in tagged_parts if p for x in p]
        value = None if missing else value_from({tag: _total(p) for tag, (p, _) in tagged_parts})
        if value is None and not missing:
            missing = ["revenue is zero"]
        if value is None:
            used = []
        accs = sorted({p["accn"] for p in used}, key=lambda a: (filings[a]["filed"], a))
        return {"label": label, "unit": unit, "value": value, "period_end": end,
                "tags": [tag for tag, _ in tagged_parts] if value is not None else [],
                "components": [{"tag": p["tag"], "role": p["role"], "start": p["start"], "end": p["end"], "value": p["val"],
                                "form": p["form"], "filed": p["filed"], "accession": p["accn"]} for p in used],
                "filings": [{"form": filings[a]["form"], "period": filings[a]["period"], "filed": filings[a]["filed"],
                             "accession": a} for a in accs],
                "note": None if value is not None else NOT_REPORTED,
                "detail": "; ".join(missing)}

    tried = [(tag, parts(tag)) for tag in REVENUE_TAGS]
    revenue = next((t for t in tried if t[1][0]), (REVENUE_TAGS[0], (None, "; ".join(why for _, (_, why) in tried))))
    ratio = lambda num: lambda t: (t[num] / t[revenue[0]]) if t[revenue[0]] else None

    metrics = {
        "revenue": metric("revenue", [revenue], lambda t: t[revenue[0]]),
        "gross_margin": metric("gross_margin", [(GROSS_PROFIT, parts(GROSS_PROFIT)), revenue], ratio(GROSS_PROFIT)),
        "operating_margin": metric("operating_margin", [(OPERATING_INCOME, parts(OPERATING_INCOME)), revenue],
                                   ratio(OPERATING_INCOME)),
        "free_cash_flow": metric("free_cash_flow", [(OPERATING_CASH_FLOW, parts(OPERATING_CASH_FLOW)), (CAPEX, parts(CAPEX))],
                                 lambda t: t[OPERATING_CASH_FLOW] - t[CAPEX]),
    }
    return {"source": SOURCE, "period_end": end, "basis": basis, "metrics": metrics}


RULE_ANCHOR = ("USD instant at the balance-sheet date, from the latest original 10-K or 10-Q itself")
RULE_AMENDED = ("USD instant at the balance-sheet date, from the latest amendment to that same period, "
                "which replaces the original filing's value")


def cash_and_equivalents(facts: dict, filed_by: str | None = None) -> dict:
    """Cash and cash equivalents at the balance-sheet date of the latest original 10-K or 10-Q (the same anchor
    the TTM figures use). filed_by works as in ttm_metrics. Selection rules: see _instant_fact."""
    gaap = facts.get("facts", {}).get("us-gaap", {})
    return _instant_fact(gaap, CASH, "cash", "Cash and cash equivalents", filed_by)


def _instant_fact(gaap: dict, tag: str, noun: str, label: str, filed_by: str | None) -> dict:
    """One balance-sheet value at the balance-sheet date of the latest original 10-K or 10-Q.

    Why stricter than the TTM rule: a balance-sheet value belongs to one filing and one date. So
    - only a USD instant dated exactly at the balance-sheet date counts, and it must come from the anchor filing;
      another filing's value is never substituted for a missing one;
    - an amendment (10-K/A, 10-Q/A) replaces the value, and the result says so, only when its filing's fiscal year
      and period (fy, fp) match the anchor filing's; otherwise it is flagged and not used. An amendment with
      conflicting values at the date makes the result Unavailable;
    - any other filing that reports the same date with a different value (a later comparative) is flagged in
      notes and not used, because a changed comparative may be a restatement that needs reading.

    Returns label, unit, value (None when unavailable), period_end, tag, form, filed, accession, selection_rule,
    notes (list of strings), note (None or UNAVAILABLE) and detail (why unavailable)."""
    anchor_acc, anchor = _anchor_filing(_filings(gaap, filed_by))
    end = anchor["period"]
    result = {"source": SOURCE, "label": label, "unit": "USD", "value": None,
              "period_end": end, "tag": f"us-gaap:{tag}", "form": None, "filed": None, "accession": None,
              "selection_rule": None, "notes": [], "note": UNAVAILABLE, "detail": ""}

    def unavailable(why):
        return {**result, "detail": why}

    units = gaap.get(tag, {}).get("units", {})
    if not units:
        return unavailable(f"no {tag} tag")
    visible = lambda rows: [r for r in rows if r.get("form") in PERIODIC_FORMS and not r.get("start")
                            and (not filed_by or r["filed"] <= filed_by)]
    usd = visible(units.get("USD", []))
    at_end = [r for r in usd if r["end"] == end]
    own = [r for r in at_end if r["accn"] == anchor_acc]
    anchor_name = f"the latest periodic filing ({anchor['form']}, accession {anchor_acc})"

    if not own:
        if any(r["accn"] == anchor_acc and r["end"] != end for r in usd):
            dates = sorted({r["end"] for r in usd if r["accn"] == anchor_acc})
            return unavailable(f"{anchor_name} reports {noun} only at {', '.join(_fmt(d) for d in dates)}, "
                               f"not at its balance-sheet date {_fmt(end)}")
        other_units = sorted(u for u, rows in units.items() if u != "USD"
                             and any(r["accn"] == anchor_acc and r["end"] == end for r in visible(rows)))
        if other_units:
            return unavailable(f"{anchor_name} reports {noun} at {_fmt(end)} only in {', '.join(other_units)}, not USD")
        if at_end:
            return unavailable(f"{anchor_name} reports no {noun} at {_fmt(end)}; other filings that do are not "
                               f"substituted ({', '.join(sorted({r['accn'] for r in at_end}))})")
        return unavailable(f"{anchor_name} reports no {noun} at {_fmt(end)}")
    if len({r["val"] for r in own}) > 1:
        return unavailable(f"{anchor_name} reports more than one {noun} value at {_fmt(end)}")

    chosen, rule, notes = own[0], RULE_ANCHOR, []
    # An amendment amends the anchor's report only if the filing says it covers the same fiscal period. Each
    # companyfacts row carries its filing's fiscal year and period (fy, fp, from the filing's cover data), so the
    # anchor's and the amendment's must match. The latest date in an amendment's facts is not used for this: an
    # amendment to a later report can carry only an earlier comparative.
    report = lambda acc: {(r.get("fy"), r.get("fp")) for r in usd if r["accn"] == acc}
    anchor_report = report(anchor_acc)
    later_amendments = sorted({r["accn"]: r for r in at_end if r["form"].endswith("/A")
                               and (r["filed"], r["accn"]) > (chosen["filed"], chosen["accn"])}.values(),
                              key=lambda r: (r["filed"], r["accn"]))
    same_period = [r for r in later_amendments
                   if len(anchor_report) == 1 and None not in next(iter(anchor_report))
                   and report(r["accn"]) == anchor_report]
    for r in later_amendments:
        if r not in same_period:
            notes.append(f"Not used: {r['form']} filed {r['filed']} (accession {r['accn']}) reports "
                         f"{r['val']:,} USD for {_fmt(end)}, but it could not be established that it amends the "
                         f"{anchor['form']} for this period")
    if same_period:
        amended = same_period[-1]
        if len({r["val"] for r in at_end if r["accn"] == amended["accn"]}) > 1:
            return unavailable(f"the amendment {amended['form']} filed {amended['filed']} (accession "
                               f"{amended['accn']}) reports more than one {noun} value at {_fmt(end)}")
        if amended["val"] != chosen["val"]:
            notes.append(f"Amended: {amended['form']} filed {amended['filed']} (accession {amended['accn']}) "
                         f"reports {amended['val']:,} USD, replacing {chosen['val']:,} USD in {chosen['form']} "
                         f"(accession {chosen['accn']})")
            chosen, rule = amended, RULE_AMENDED
        else:
            notes.append(f"{amended['form']} filed {amended['filed']} (accession {amended['accn']}) "
                         f"reports the same value")
    # Only the latest same-period amendment is used; an earlier one that differs is flagged like any other filing.
    # Amendments whose period could not be established were flagged above.
    used = ({r["accn"] for r in own} | {r["accn"] for r in later_amendments if r not in same_period}
            | ({same_period[-1]["accn"]} if same_period else set()))
    for r in sorted((r for r in at_end if r["accn"] not in used), key=lambda r: (r["filed"], r["accn"])):
        if r["val"] != chosen["val"]:
            notes.append(f"Not used: {r['form']} filed {r['filed']} (accession {r['accn']}) reports "
                         f"{r['val']:,} USD for {_fmt(end)}; possible revision, check that filing")

    return {**result, "value": chosen["val"], "form": chosen["form"], "filed": chosen["filed"],
            "accession": chosen["accn"], "selection_rule": rule, "notes": notes, "note": None}


def current_ratio(facts: dict, filed_by: str | None = None) -> dict:
    """Current ratio = current assets / current liabilities at the balance-sheet date of the latest original 10-K
    or 10-Q. filed_by works as in ttm_metrics. The ratio is derived: it has no XBRL tag; its inputs carry theirs.

    Each input is selected by _instant_fact (anchor filing's own USD instant at that exact date, amendments only
    when they amend the same fiscal period). Both inputs share the anchor's date by construction, and they must also
    come from one filing, because a ratio of an amended numerator over an unamended denominator mixes two versions
    of the balance sheet. So when one input was replaced by an amendment, the other is taken from that same
    amendment if it reports it; if it doesn't, no ratio is calculated.

    Returns label, unit ("ratio"), value (None when unavailable), period_end, formula, tag (None),
    inputs {"current_assets", "current_liabilities"} (each as _instant_fact returns it), notes, note and detail."""
    gaap = facts.get("facts", {}).get("us-gaap", {})
    assets = _instant_fact(gaap, CURRENT_ASSETS, "current assets", "Current assets", filed_by)
    liabilities = _instant_fact(gaap, CURRENT_LIABILITIES, "current liabilities", "Current liabilities", filed_by)
    result = {"source": SOURCE, "label": "Current ratio", "unit": "ratio", "value": None,
              "period_end": assets["period_end"], "formula": f"{CURRENT_ASSETS} / {CURRENT_LIABILITIES}",
              "tag": None, "inputs": {"current_assets": assets, "current_liabilities": liabilities},
              "notes": [], "note": UNAVAILABLE, "detail": ""}

    def unavailable(why):
        return {**result, "inputs": {"current_assets": assets, "current_liabilities": liabilities}, "detail": why}

    missing = [f"{x['label'].lower()}: {x['detail']}" for x in (assets, liabilities) if x["value"] is None]
    if missing:
        return unavailable("; ".join(missing))

    paired, why = _one_filing(gaap, [assets, liabilities], "current-ratio", filed_by)
    if paired is None:
        return unavailable(why)
    assets, liabilities = paired
    if liabilities["value"] <= 0:
        return unavailable(f"current liabilities are {liabilities['value']:,} USD; a ratio with a zero or negative "
                           f"denominator is not meaningful")
    return {**result, "inputs": {"current_assets": assets, "current_liabilities": liabilities},
            "value": assets["value"] / liabilities["value"], "note": None}


def _one_filing(gaap: dict, inputs: list[dict], purpose: str, filed_by: str | None) -> tuple[list[dict] | None, str]:
    """Make inputs selected by _instant_fact come from one filing version, or say why they can't.

    They already share the anchor's date. When an amendment replaced some of them, the others are taken from that
    same (newest) amendment, but only if it reports them once at that date and their rows carry the anchor filing's
    single, complete fiscal year and period (the _instant_fact rule). Otherwise nothing is combined.
    Returns (inputs, "") or (None, reason)."""
    newer = max(inputs, key=lambda x: (x["filed"], x["accession"]))
    anchor_acc = _anchor_filing(_filings(gaap, filed_by))[0]
    out = []
    for older in inputs:
        if older["accession"] == newer["accession"]:
            out.append(older)
            continue
        older_tag = older["tag"].split(":")[-1]
        usd = [r for r in gaap.get(older_tag, {}).get("units", {}).get("USD", [])
               if r.get("form") in PERIODIC_FORMS and not r.get("start") and (not filed_by or r["filed"] <= filed_by)]
        rows = [r for r in usd if r["accn"] == newer["accession"] and r["end"] == newer["period_end"]]
        report = lambda acc: {(r.get("fy"), r.get("fp")) for r in usd if r["accn"] == acc}
        anchor_report = report(anchor_acc)
        source = f"{newer['label'].lower()} comes from {newer['form']} (accession {newer['accession']})"
        if rows and not (len(anchor_report) == 1 and None not in next(iter(anchor_report))
                         and report(newer["accession"]) == anchor_report):
            return None, (f"{source}, but it could not be established that its {older['label'].lower()} figure "
                          f"covers the anchor's fiscal period; inputs from different filings are not combined")
        if len({r["val"] for r in rows}) != 1:
            how = "does not report" if not rows else "reports more than one value for"
            return None, (f"{source}, which {how} {older['label'].lower()} at {_fmt(newer['period_end'])}; "
                          f"inputs from different filings are not combined")
        every = "both" if len(inputs) == 2 else "all"
        out.append({**older, "value": rows[0]["val"], "form": newer["form"], "filed": newer["filed"],
                    "accession": newer["accession"], "selection_rule": RULE_AMENDED,
                    "notes": older["notes"] + [f"Taken from {newer['form']} (accession {newer['accession']}) so "
                                               f"{every} {purpose} inputs come from one filing"]})
    return out, ""


def baseline_gross_debt(facts: dict, ticker: str, filed_by: str | None = None) -> dict:
    """Baseline gross debt (plan definition: reported carrying amounts of interest-bearing borrowing, excluding
    leases) at the balance-sheet date of the latest original 10-K or 10-Q, from the company's verified
    presentation in BORROWING_PRESENTATIONS. filed_by works as in ttm_metrics. The total is derived: it has no
    XBRL tag; each component carries its own.

    Each component is selected by _instant_fact (anchor filing's own USD instant at that exact date) and all must
    come from one filing version (_one_filing). Before adding, overlap is checked: when that filing also reports the
    filer's own total at the same date, the components must sum to it exactly; a difference means overlap or a
    missing component, so nothing is calculated. A negative component is refused.

    Returns label, unit, value (None when unavailable), period_end, formula, tag (None), presentation, inputs
    (list, each as _instant_fact returns it), not_added, evidence, caveats, notes, note and detail."""
    gaap = facts.get("facts", {}).get("us-gaap", {})
    presentation = BORROWING_PRESENTATIONS.get(ticker)
    end = _anchor_filing(_filings(gaap, filed_by))[1]["period"]
    result = {"source": SOURCE, "label": "Baseline gross debt", "unit": "USD", "value": None, "period_end": end,
              "formula": None, "tag": None, "presentation": None, "inputs": [], "not_added": None,
              "evidence": None, "caveats": [], "notes": [], "note": UNAVAILABLE, "detail": ""}
    if presentation is None:
        return {**result, "detail": f"no verified borrowing presentation for {ticker}; debt components are chosen "
                                    f"per company from its filings, not guessed"}
    components = presentation["components"]
    inputs = [_instant_fact(gaap, tag, noun, label, filed_by) for tag, noun, label in components]
    result.update(formula=" + ".join(tag for tag, _, _ in components), presentation=presentation["name"],
                  inputs=inputs, not_added=presentation["not_added"], evidence=presentation["evidence"],
                  caveats=presentation["caveats"])

    def unavailable(why):
        return {**result, "inputs": inputs, "detail": why}

    missing = [f"{x['label'].lower()}: {x['detail']}" for x in inputs if x["value"] is None]
    if missing:
        return unavailable("; ".join(missing))
    paired, why = _one_filing(gaap, inputs, "gross-debt", filed_by)
    if paired is None:
        return unavailable(why)
    inputs = paired
    negative = [x for x in inputs if x["value"] < 0]
    if negative:
        return unavailable("; ".join(f"{x['label'].lower()} is {x['value']:,} USD; a borrowing balance cannot be "
                                     f"negative, so the components are not added" for x in negative))
    total = sum(x["value"] for x in inputs)

    notes = []
    check = presentation.get("total_check")
    if check:
        acc = inputs[0]["accession"]
        rows = [r for r in gaap.get(check, {}).get("units", {}).get("USD", [])
                if r["accn"] == acc and r["end"] == end and not r.get("start")
                and (not filed_by or r["filed"] <= filed_by)]
        reported = {r["val"] for r in rows}
        if len(reported) > 1:
            return unavailable(f"the filing (accession {acc}) reports more than one {check} total at {_fmt(end)}")
        if reported:
            filer_total = reported.pop()
            if filer_total != total:
                return unavailable(f"the components sum to {total:,} USD but the same filing (accession {acc}) "
                                   f"reports a total ({check}) of {filer_total:,} USD at {_fmt(end)}; that points "
                                   f"to overlap or a missing component, so nothing is calculated")
            notes.append(f"Matches the filing's own total ({check}) of {filer_total:,} USD")
    return {**result, "inputs": inputs, "value": total, "notes": notes, "note": None}
