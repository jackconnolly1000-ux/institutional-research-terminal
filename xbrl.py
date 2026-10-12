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
TAGS = [*REVENUE_TAGS, GROSS_PROFIT, OPERATING_INCOME, OPERATING_CASH_FLOW, CAPEX]

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
    """Keep only the six tags, in dollars, from 10-K and 10-Q filings (and amendments). A full file is 3 to 8 MB;
    this is what the app caches per company, and what the test fixtures hold. since drops periods ending earlier."""
    gaap = facts.get("facts", {}).get("us-gaap", {})
    kept = {}
    for tag in TAGS:
        rows = [r for r in gaap.get(tag, {}).get("units", {}).get("USD", [])
                if r.get("form") in PERIODIC_FORMS and r.get("start") and (since is None or r["end"] >= since)]
        if rows:
            kept[tag] = {"units": {"USD": rows}}
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


def _anchor(filings: dict) -> tuple[str, str]:
    """(period end, form) of the latest original 10-K or 10-Q. Amendments are left out here so a late 10-K/A
    doesn't pull TTM back a year; their values still count when periods are deduplicated."""
    originals = [(f["filed"], acc, f) for acc, f in filings.items() if f["form"] in ("10-K", "10-Q")]
    if not originals:
        raise XbrlError("no 10-K or 10-Q figures in SEC company facts")
    f = max(originals)[2]
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
