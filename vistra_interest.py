"""Vistra's reconciled interest component; raw XBRL signs remain intact."""
import hashlib
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

import filing_xbrl as fx
from reviewed_financing import BASE

SAMPLE = Path(__file__).parent / "samples/vistra_interest.json"
CHECKED_INPUTS_SHA256 = "1eb610315c9b7d6d721ef404d38777feaa211df47d3eb1b346003b5445170bbd"
START, END = "2025-07-01", "2026-06-30"
SOURCES = {
    "annual": dict(document="vistra-20251231.htm", accession="0001692819-26-000006", form="10-K", filed="2026-02-27",
                   sha256="42e6a0ba0c833ede7d9d452b9f1ea68fbc4cb52035129ab5d5e02916e02822d4", operations="Operations p. 79", note="Interest table p. 121"),
    "quarter": dict(document="vistra-20260630.htm", accession="0001692819-26-000019", form="10-Q", filed="2026-08-10",
                    sha256="c6d9f5b5d8348c2060282019841c8bec09662fefd3b78f6fefd3add3ed985875", operations="Operations p. 1", note="Debt Note 12 p. 28"),
    "prior_original": dict(document="vistra-20250630.htm", accession="0001692819-25-000085", form="10-Q", filed="2025-08-08",
                           sha256="4234cc94ced57c42cf07c4a35295b480a87033491e96881774eee658f1dc75ea", operations="Operations p. 1", note="Debt Note 9 p. 30"),
}
for s in SOURCES.values():
    s["source_url"] = BASE + s["accession"].replace("-", "") + "/" + s["document"]
TAXONOMY = {
    "vistra-20260630.xsd": "c07fac7f1b1449b593e9d59eea88861f95c687dbe1cb24655d1da7623e4c9490",
    "vistra-20260630_lab.xml": "497c98ab20dd76a3f64bb1f745a603086369c104dab3c6ffd284e41baea2285f",
}
PERIODS = [("fy", "annual", "2025-01-01", "2025-12-31", 1),
           ("current", "quarter", "2026-01-01", END, 1),
           ("prior", "quarter", "2025-01-01", "2025-06-30", -1),
           ("prior_original", "prior_original", "2025-01-01", "2025-06-30", 0)]
TAGS = {"operating_income": "us-gaap:OperatingIncomeLoss",
        "interest": "vistra:PostEmergenceInterestPaidAndAccrued",
        "swaps": "vistra:UnrealizedGainLossOnInterestRateSwapDerivatives",
        "amortization": "us-gaap:AmortizationOfDebtDiscountPremium",
        "extinguishment": "us-gaap:GainsLossesOnExtinguishmentOfDebt",
        "capitalized": "us-gaap:InterestCostsCapitalizedAdjustment",
        "other": "us-gaap:InterestExpenseOther",
        "total": "us-gaap:InterestExpenseNonoperating"}
# These multipliers reconstruct the printed expense table; they never alter source facts.
EFFECTS = {"interest": 1, "swaps": -1, "amortization": 1,
           "extinguishment": -1, "capitalized": -1, "other": 1}
BASIS = ("The reported Interest expense component is before the separately displayed capitalized-interest "
         "deduction and before interest income. TTM capitalized interest is 151M (125 + 82 − 56), shown "
         "only in the reconciliation. The coverage denominator stays 1,117M as reported; capitalized "
         "interest is not added to or subtracted from it again.")
COMPOSITION = ("The denominator excludes the separately reported unrealized swap mark-to-market effects, "
               "debt-cost amortization, extinguishment effects and Other. The mixed total is 1,132M TTM; "
               "it is not the selected interest component. Receivables-facility and Nuveen interest may "
               "sit in the component or Other; the checked filings do not establish the allocation. "
               "Other's detailed composition is Unavailable.")
LIMITS = ("Historical accrual earnings coverage, not cash interest coverage, future repayment coverage, "
          "covenant headroom or drawable capacity. The numerator is reported consolidated operating income "
          "without adjusted earnings addbacks; it retains reported operating and commodity-hedge effects. "
          "The interest component is not a fully verified allocation of all borrowing and Nuveen costs. "
          "Cash swap settlements and a fully reconciled all-in financing-cost measure remain Unavailable.")
GAPS = {
    "receivables_allocation": "The receivables facility records interest, but its allocation between the component and Other is not stated.",
    "nuveen_allocation": "Nuveen carries interest; whether it is in the component or Other is not established.",
    "other_composition": "Other is reported, but its detailed components are not disclosed in the checked table.",
    "cash_swap_settlements": "Unrealized mark-to-market changes do not identify cash swap interest settlements or their allocation.",
    "all_in_borrowing_cost": "Cannot reconstruct a fully allocated borrowing/financing-cost denominator from this table.",
    "covenant_headroom": "This operating-income/component ratio is not a contract-defined covenant calculation.",
    "drawable_credit": "Historical earnings coverage does not establish draw conditions or transferable cash.",
}


def calculate(inputs):
    out = dict(periods={}, ttm={}, value=None, detail="", prior_agrees=False)
    reasons = []
    for role, source, start, end, coefficient in PERIODS:
        p = dict(coefficient=coefficient, effects={}, calculated_total=None, difference=None)
        out["periods"][role] = p
        for key, tag in TAGS.items():
            f = inputs.get(role + "_" + key, {});value = f.get("value")
            valid = (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and
                     f.get("tag") == tag and f.get("unit") == fx.USD and f.get("dimensions") == [] and
                     str(f.get("entity_identifier") or "").lstrip("0") == "1692819" and
                     (f.get("period_start"), f.get("period_end")) == (start, end) and
                     f.get("accession") == SOURCES[source]["accession"] and
                     f.get("source_sha256") == SOURCES[source]["sha256"])
            if valid and key in {"interest", "capitalized"} and value < 0:
                valid = False
            p[key] = value if valid else None
            if not valid:
                reasons.append(role + " " + key + ": missing or incompatible checked fact; " + f.get("detail", ""))
        for key, sign in EFFECTS.items():
            p["effects"][key] = p[key] * sign if p[key] is not None else None
        if all(v is not None for v in p["effects"].values()):
            p["calculated_total"] = sum(p["effects"].values())
            if p["total"] is not None:
                p["difference"] = p["calculated_total"] - p["total"]
                if p["difference"] != 0:
                    reasons.append(role + " interest components do not reconcile to the reported mixed total.")
    for key in TAGS:
        periods = [out["periods"][p] for p in ["fy", "current", "prior"]]
        out["ttm"][key] = sum(p["coefficient"] * p[key] for p in periods) if all(p[key] is not None for p in periods) else None
    prior, original = out["periods"]["prior"], out["periods"]["prior_original"]
    out["prior_agrees"] = all(prior[k] is not None and prior[k] == original[k] for k in TAGS)
    if not out["prior_agrees"]:
        reasons.append("The current filing's H1 2025 comparatives do not all match the checked original H1 2025 filing.")
    denominator = out["ttm"]["interest"]
    if denominator is not None and denominator <= 0:
        reasons.append("TTM interest component is zero or negative; coverage is Unavailable.")
    if (denominator is not None and denominator > 0 and out["ttm"]["operating_income"] is not None and
            out["prior_agrees"] and all(p["difference"] == 0 for p in out["periods"].values())):
        out["value"] = out["ttm"]["operating_income"] / denominator
    out["detail"] = "; ".join(reasons)
    return out


def build(annual, quarter, prior_original):
    docs = dict(annual=annual, quarter=quarter, prior_original=prior_original);inputs = {}
    for role, source, start, end, coefficient in PERIODS:
        meta = SOURCES[source]
        for key, tag in TAGS.items():
            try:
                f = fx.read_duration(docs[source], meta["accession"], tag, start, end)
            except (OSError, ET.ParseError) as e:
                f = dict(value=None, tag=tag, detail="Source could not be read: " + type(e).__name__)
            f.update(label=role + " " + key, period_start=start, period_end=end,
                     document=meta["document"], accession=meta["accession"], form=meta["form"], filed=meta["filed"],
                     source_url=meta["source_url"], source_sha256=meta["sha256"],
                     location=meta["operations"] if key == "operating_income" else meta["note"],
                     selection_rule="Exact tag, duration, USD, Vistra CIK and no dimensions; agreeing duplicates only")
            inputs[role + "_" + key] = f
    return dict(ticker="VST", checked_as_of="2026-10-16", period_start=START, period_end=END,
                inputs=inputs, calculation=calculate(inputs), basis=BASIS, composition=COMPOSITION, limitations=LIMITS,
                unavailable={k:dict(value=None, status="Unavailable", detail=v) for k, v in GAPS.items()}, tag=None,
                formula="TTM reported operating income / TTM reported interest component before capitalized interest",
                ttm_formula="FY2025 + H1 2026 - H1 2025", schema_sources=TAXONOMY)


def fingerprint(inputs):
    return hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load():
    try:
        r = json.loads(SAMPLE.read_text())
        if (fingerprint(r["inputs"]) == CHECKED_INPUTS_SHA256 and r["basis"] == BASIS and r["composition"] == COMPOSITION and
                r["limitations"] == LIMITS and r["schema_sources"] == TAXONOMY and
                r["unavailable"] == {k:dict(value=None, status="Unavailable", detail=v) for k, v in GAPS.items()} and
                (r["period_start"], r["period_end"]) == (START, END) and r["calculation"] == calculate(r["inputs"])):
            return r
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def for_snapshot(snapshot):
    a = snapshot.get("metrics", {}).get("cash", {})
    if snapshot.get("ticker") == "VST" and (a.get("period_end"), a.get("accession")) == (END, SOURCES["quarter"]["accession"]):
        return load()
    return None
