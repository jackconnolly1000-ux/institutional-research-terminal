"""Oracle's historical reported-line coverage, distinct from its credit covenant."""
import hashlib
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

import filing_xbrl as fx
import oracle_financing as financing

SAMPLE = Path(__file__).parent / "samples/oracle_interest.json"
CHECKED_INPUTS_SHA256 = "ede5de268f49b89123c69435ddb21055563d55f0dba9e5498e6e402bfda11c18"
START, END = "2025-09-01", "2026-08-31"
SOURCES = {
    "annual": dict(document="orcl-20260531.htm", accession=financing.ACCESSION,
                   form="10-K", filed="2026-06-22",
                   source_url=financing.SOURCE,
                   sha256="61a353e222f961e516bb3e8eed024a5245cfadbf30e3cc16a4a520129f1bdf63"),
    "quarter": dict(document="orcl-20260831.htm", accession=financing.QUARTER_ACCESSION,
                    form="10-Q", filed="2026-09-11",
                    source_url=financing.QUARTER_SOURCE,
                    sha256="051dd4893fa497f36d99c8a355cbc90107f56e1a628c78e38c76e7dca0d4a6fd"),
}
PERIODS = [("fy", "annual", "2025-06-01", "2026-05-31", 1),
           ("current", "quarter", "2026-06-01", END, 1),
           ("prior", "quarter", "2025-06-01", "2025-08-31", -1)]
TAGS = {"operating_income": "us-gaap:OperatingIncomeLoss",
        "interest": "us-gaap:InterestExpense",
        "lease_interest": "us-gaap:FinanceLeaseInterestExpense"}
BASIS = ("Reported interest expense before any interest-income offset. The saved 10-K and 10-Q "
         "do not state its capitalized-interest basis. Capitalized interest and total interest incurred "
         "are Unavailable; neither is assumed zero or added to or subtracted from expense.")
COMPOSITION = ("MD&A attributes the increase primarily to higher average borrowings, but does not "
               "provide a complete interest-line reconciliation. Finance-lease interest is separately "
               "disclosed; whether it is already inside the selected line is Unavailable, so it is not added. "
               "The annual revenue policy discusses contract-financing interest in non-operating income "
               "(expenses), net. The customer-prepayment notes call related interest immaterial, not zero; "
               "no exact amount or reconciliation to the selected line is established.")
LIMITS = ("Historical accrual earnings coverage, not cash interest coverage or a repayment forecast. "
          "Borrowing-only interest coverage is Unavailable because the reported line's full composition "
          "is not established. The revolver uses contract-defined Consolidated EBITDA / Consolidated "
          "Net Interest Expense, including specified adjustments; this ratio does not establish covenant "
          "headroom, current compliance or drawable credit. No adjusted earnings addbacks are made.")
GAPS = {
    "capitalized_interest": "The checked filings do not state the amount capitalized or the expense line's capitalization basis.",
    "interest_incurred": "Cannot reconstruct total interest incurred without the capitalized amount and basis.",
    "borrowing_only_coverage": "The reported Interest expense line is not reconciled by component.",
    "finance_lease_overlap": "Whether lease-note interest is already in Interest expense is not established.",
    "customer_financing_interest": "Described as immaterial; no exact amount or selected-line reconciliation is established.",
    "covenant_headroom": "Contract-defined EBITDA and net-interest adjustments have not been fully reconciled.",
    "drawable_credit": "Historical reported-line coverage does not establish borrowing-date draw conditions.",
}


def calculate(inputs):
    """Reject mismatched periods and segments; preserve independently supported components."""
    out = dict(periods={}, operating_income=None, interest=None, lease_interest=None, value=None, detail="")
    reasons = []
    for role, source, start, end, coefficient in PERIODS:
        period = dict(coefficient=coefficient, period_start=start, period_end=end)
        out["periods"][role] = period
        for key, tag in TAGS.items():
            f = inputs.get(role + "_" + key, {})
            value = f.get("value")
            valid = (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and
                     f.get("tag") == tag and f.get("unit") == fx.USD and f.get("dimensions") == [] and
                     str(f.get("entity_identifier") or "").lstrip("0") == "1341439" and
                     (f.get("period_start"), f.get("period_end")) == (start, end) and
                     f.get("accession") == SOURCES[source]["accession"] and
                     f.get("source_sha256") == SOURCES[source]["sha256"])
            if key != "operating_income" and valid and value < 0:
                valid = False
            period[key] = value if valid else None
            if not valid:
                reasons.append(role + " " + key + ": missing or incompatible checked fact; " + f.get("detail", ""))
    for key in TAGS:
        if all(p[key] is not None for p in out["periods"].values()):
            out[key] = sum(p["coefficient"] * p[key] for p in out["periods"].values())
    if out["interest"] is not None and out["interest"] <= 0:
        reasons.append("TTM reported interest is zero or negative; coverage is Unavailable.")
    if out["operating_income"] is not None and out["interest"] is not None and out["interest"] > 0:
        out["value"] = out["operating_income"] / out["interest"]
    out["detail"] = "; ".join(reasons)
    return out


def build(annual, quarter):
    inputs = {}
    for role, source, start, end, coefficient in PERIODS:
        meta = SOURCES[source]
        for key, tag in TAGS.items():
            try:
                f = fx.read_duration(annual if source == "annual" else quarter, meta["accession"], tag, start, end)
            except (OSError, ET.ParseError) as e:
                f = dict(value=None, tag=tag, detail="Source could not be read: " + type(e).__name__)
            f.update(label=role + " " + key, period_start=start, period_end=end,
                     document=meta["document"], accession=meta["accession"], form=meta["form"], filed=meta["filed"],
                     source_url=meta["source_url"], source_sha256=meta["sha256"],
                     location=("Leases Note 9 p. 88" if source == "annual" else "Leases Note 6 p. 12") if key == "lease_interest" else
                     ("Operations p. 65; MD&A p. 50" if source == "annual" else "Operations p. 2; MD&A p. 32"),
                     selection_rule="Exact tag, duration, USD, Oracle CIK and no dimensions; agreeing duplicates only")
            inputs[role + "_" + key] = f
    return dict(ticker="ORCL", checked_as_of="2026-10-16", period_start=START, period_end=END,
                inputs=inputs, calculation=calculate(inputs), basis=BASIS, composition=COMPOSITION,
                limitations=LIMITS, unavailable={k:dict(value=None, status="Unavailable", detail=v) for k, v in GAPS.items()},
                tag=None, formula="TTM reported operating income / TTM reported Interest expense",
                ttm_formula="FY2026 + Q1 FY2027 - Q1 FY2026")


def fingerprint(inputs):
    return hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load():
    try:
        r = json.loads(SAMPLE.read_text())
        if (fingerprint(r["inputs"]) == CHECKED_INPUTS_SHA256 and r["basis"] == BASIS and
                r["composition"] == COMPOSITION and r["limitations"] == LIMITS and
                r["unavailable"] == {k:dict(value=None, status="Unavailable", detail=v) for k, v in GAPS.items()} and
                (r["period_start"], r["period_end"]) == (START, END) and r["calculation"] == calculate(r["inputs"])):
            return r
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def for_snapshot(snapshot):
    anchor = snapshot.get("metrics", {}).get("cash", {})
    if snapshot.get("ticker") == "ORCL" and (anchor.get("period_end"), anchor.get("accession")) == (END, financing.QUARTER_ACCESSION):
        return load()
    return None
