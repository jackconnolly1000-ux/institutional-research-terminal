"""Reconcile the frozen pilot metrics and describe their shared app/export basis."""
import hashlib
import importlib
import math
from datetime import date, timedelta
from pathlib import Path

import cash_generation
import liquidity_pilot

ROOT = Path(__file__).parent
ORDER = ("cash", "gross_debt", "net_debt", "current_ratio", "operating_cash_flow",
         "capital_spending", "free_cash_flow", "ocf_to_debt", "fcf_to_debt")
INTEREST_MODULES = {"LLY": "lly_interest", "ORCL": "oracle_interest", "VST": "vistra_interest"}
COVERAGE_CELLS = {"LLY": "='Debt and liquidity'!B50", "ORCL": "='Cash analysis'!B49",
                  "VST": "='Cash review'!B79"}


def fingerprint():
    """Bind exports to the ratio rules and all saved inputs used by this presentation."""
    files = ["ratio_review.py", "liquidity_pilot.py", "cash_generation.py",
             "samples/liquidity_pilots.json", *[f"samples/{m}.json" for m in INTEREST_MODULES.values()]]
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}


def _equal(actual, expected, label):
    if actual is None and expected is None:
        return
    if actual is None or expected is None or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12):
        raise ValueError(f"{label} does not reconcile to its inputs")


def build(snapshot):
    """Refuse incompatible periods and stale derived results, retaining supported missing values."""
    ticker, m = snapshot["ticker"], snapshot["metrics"]
    spec = cash_generation.SOURCES[ticker]
    end, accession = spec["quarter"][4], spec["quarter"][0]
    start = m["operating_cash_flow"]["period_start"]
    debt, cash, current = m["gross_debt"], m["cash"], m["current_ratio"]
    instant_inputs = [cash, *debt["inputs"], *current["inputs"].values()]
    if any(f["period_end"] != end or f["accession"] != accession or f["unit"] != "USD"
           for f in instant_inputs if f["value"] is not None):
        raise ValueError("Balance-sheet ratio inputs must share the checked date, accession and USD unit")
    components = [f["value"] for f in debt["inputs"]]
    if any(v is not None and v < 0 for v in components):
        raise ValueError("Negative borrowing components need a new presentation review")
    _equal(debt["value"], None if None in components else sum(components), "Baseline debt")
    _equal(m["net_debt"]["value"], liquidity_pilot.net_debt(cash, debt)["value"], "Net debt")
    assets, liabilities = (current["inputs"][key]["value"] for key in ("current_assets", "current_liabilities"))
    _equal(current["value"], assets / liabilities if assets is not None and liabilities is not None
           and liabilities > 0 else None, "Current ratio")
    expected_start = (date.fromisoformat(spec["prior"][1]) + timedelta(days=1)).isoformat()
    for key in ("operating_cash_flow", "capital_spending"):
        flow = m[key]
        if (flow["period_start"], flow["period_end"], flow["unit"]) != (expected_start, end, "USD"):
            raise ValueError("Flow ratios require the checked trailing twelve months in USD")
        expected = [(spec["annual"][0], *spec["annual"][3:5], 1),
                    (accession, *spec["quarter"][3:5], 1), (accession, *spec["prior"], -1)]
        actual = [(f["accession"], f["period_start"], f["period_end"], f["coefficient"])
                  for f in flow["inputs"]]
        tag = cash_generation.OCF if key == "operating_cash_flow" else spec["capex_tag"]
        if actual != expected or any(f["unit"] != "USD" or f["tag"] != tag for f in flow["inputs"]):
            raise ValueError("Flow build must use the checked FY + current YTD - prior YTD facts")
        values = [f["value"] for f in flow["inputs"]]
        _equal(flow["value"], None if None in values else values[0] + values[1] - values[2], key)
    ocf, capex = m["operating_cash_flow"]["value"], m["capital_spending"]["value"]
    _equal(m["free_cash_flow"]["value"], ocf - capex if ocf is not None and capex is not None else None, "FCF")
    for key, flow in (("ocf_to_debt", "operating_cash_flow"), ("fcf_to_debt", "free_cash_flow")):
        _equal(m[key]["value"], liquidity_pilot.flow_to_debt(m[flow], debt)["value"], key)
        if m[key]["inputs"] != {"flow": m[flow], "debt": debt}:
            raise ValueError("Flow-ratio provenance differs from its displayed inputs")
    if (m["net_debt"]["inputs"] != {"baseline_gross_debt": debt, "cash": cash}
            or m["free_cash_flow"]["inputs"] != {"operating_cash_flow": m["operating_cash_flow"],
                                                 "capital_spending": m["capital_spending"]}):
        raise ValueError("Derived metric provenance differs from its displayed inputs")
    # Derived values also carry periods and units; checking only their leaves hides stale labels.
    for key in ORDER:
        metric = m[key]
        unit = "ratio" if key == "current_ratio" else "fraction" if key.endswith("to_debt") else "USD"
        if (metric["period_end"] != end or metric["unit"] != unit
                or (metric.get("tag") is not None and key != "cash")):
            raise ValueError("Derived metric period, unit or tag is inconsistent")
        if key in ORDER[4:] and metric.get("period_start") != start:
            raise ValueError("Cash-flow and flow-ratio periods differ")
    flow_basis = spec["basis"]
    notes = {
        "cash": "Cash and cash equivalents excluding restricted cash. Investments are not substituted.",
        "gross_debt": "Carrying amount of borrowing. Operating/finance leases and commitments are excluded. "
                      + " ".join(debt.get("caveats", [])),
        "net_debt": "Baseline borrowing less cash excluding restricted cash. Same date and filing. Negative net debt is retained.",
        "current_ratio": "Total current assets / total current liabilities from one balance sheet. Liabilities include more than borrowing; assets include more than cash.",
        "operating_cash_flow": ("Reported historical OCF; recurrence is not established. "
                                + (flow_basis if ticker == "ORCL" else "Uses FY + current YTD - prior YTD.")),
        "capital_spending": flow_basis if ticker != "ORCL" else "Cash capital expenditures. Capex-financing cash flows are not added.",
        "free_cash_flow": "OCF less reported capital spending. Uses the spending basis above; excludes acquisitions, dividends and other cash uses.",
        "ocf_to_debt": "Historical TTM OCF / period-end baseline borrowing, not average debt or repayment coverage. The reported OCF basis above is retained.",
        "fcf_to_debt": "Historical TTM FCF / period-end baseline borrowing. Uses the spending basis above; not repayment coverage.",
    }
    rows = [{"key": key, "label": m[key]["label"], "value": m[key]["value"], "unit": m[key]["unit"],
             "period_start": m[key].get("period_start"), "period_end": end,
             "formula": m[key].get("formula", "Reported cash and cash equivalents"),
             "detail": m[key].get("detail", ""), "basis": notes[key]} for key in ORDER]
    interest = importlib.import_module(INTEREST_MODULES[ticker]).load()
    if interest is not None and (interest["period_start"], interest["period_end"]) != (start, end):
        raise ValueError("Interest coverage and cash-flow TTM periods differ")
    rows.append({"key": "interest_coverage", "label": "Historical interest coverage", "unit": "ratio",
                 "value": interest["calculation"]["value"] if interest else None,
                 "period_start": start, "period_end": end, "formula": "TTM operating income / TTM reported interest",
                 "basis": interest["basis"] if interest else "Unavailable: checked interest review could not be loaded.",
                 "detail": interest["limitations"] if interest else "Checked interest inputs are missing or stale."})
    return {"ticker": ticker, "company": snapshot["company_name"], "period_start": start, "period_end": end,
            "rows": rows, "coverage_cell": COVERAGE_CELLS[ticker]}


def display(row):
    if row["value"] is None:
        return "Unavailable"
    if row["unit"] == "fraction":
        return f'{row["value"]:.1%}'
    if row["unit"] == "ratio":
        return f'{row["value"]:.2f}x'
    return f'{row["value"]:,.0f} USD'
