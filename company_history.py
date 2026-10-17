"""Two dated observations within each pilot, without filling unsupported older debt."""
import hashlib
import importlib
import json
from pathlib import Path

import ratio_review

SAMPLE = Path(__file__).parent / "samples/company_history.json"
CHECKED_SHA256 = "69082f1c56993e848a3e358f280224f536303b9199f4ec0f57fd944a00b9184c"


def fingerprint():
    return {"code": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "facts": hashlib.sha256(SAMPLE.read_bytes()).hexdigest(), "ratios": ratio_review.fingerprint()}


def build(snapshot):
    current = ratio_review.build(snapshot)
    if hashlib.sha256(SAMPLE.read_bytes()).hexdigest() != CHECKED_SHA256:
        raise ValueError("History source facts changed and require review")
    prior = json.loads(SAMPLE.read_text())[snapshot["ticker"]]
    facts = prior["facts"]
    if any(f["value"] is None or f["unit"] != "USD" or f["period_end"] != prior["annual_end"]
           or f["accession"] != prior["accession"] or f.get("dimensions") for f in facts):
        raise ValueError("History needs one checked annual USD balance sheet")
    if facts[2]["value"] <= 0 or any(f["value"] < 0 for f in facts[3:]):
        raise ValueError("History balance-sheet denominator or borrowing needs review")
    cash, assets, liabilities = [f["value"] for f in facts[:3]]
    debt = sum(f["value"] for f in facts[3:]) if len(facts) > 3 else None
    m = snapshot["metrics"]
    ocf, capex = (m[k]["inputs"][0] for k in ("operating_cash_flow", "capital_spending"))
    if any((f["period_start"], f["period_end"], f["accession"], f["unit"]) !=
           (prior["annual_start"], prior["annual_end"], prior["accession"], "USD") for f in (ocf, capex)):
        raise ValueError("Annual flow source period differs from the history date")
    interest = importlib.import_module(ratio_review.INTEREST_MODULES[snapshot["ticker"]]).load()
    annual_interest = interest["calculation"]["periods"]["fy"] if interest else None
    op = annual_interest["operating_income"] if annual_interest else None
    expense = annual_interest["interest"] if annual_interest else None
    aocf, acapex = ocf["value"], capex["value"]
    fcf = aocf - acapex if aocf is not None and acapex is not None else None
    values = [cash, debt, debt - cash if debt is not None else None, assets / liabilities, aocf, acapex,
              fcf, aocf / debt if aocf is not None and debt and debt > 0 else None,
              fcf / debt if fcf is not None and debt and debt > 0 else None,
              op / expense if op is not None and expense is not None and expense > 0 else None]
    rows = [{**r, "annual_value": value, "annual_detail": prior["debt_detail"] if value is None and
             r["key"] in {"gross_debt", "net_debt", "ocf_to_debt", "fcf_to_debt"} else
             "Checked annual interest or cash-flow input is missing." if value is None else ""}
            for r, value in zip(current["rows"], values)]
    return {**current, "rows": rows, "annual_start": prior["annual_start"], "annual_end": prior["annual_end"],
            "annual_facts": facts, "annual_flows": [ocf, capex],
            "annual_interest_inputs": {k: v for k, v in interest["inputs"].items() if k.startswith("fy_")} if interest else {},
            "annual_operating_income": op, "annual_interest": expense,
            "annual_source": facts[0]["source_url"], "current_source": snapshot["source_url"],
            "note": "Balance-sheet figures compare the stated dates. Flows and interest coverage compare a fiscal year with a later TTM: both span twelve months and overlap. No interim annualization, independent-period growth rate or future repayment coverage is inferred."}


def render(snapshot, money):
    from ui import esc
    model = build(snapshot)
    out = '<section class="lr-obligations lr-history"><h3>What changed since the fiscal year end?</h3>'
    out += f'<p class="lr-meta">{esc(model["note"])}</p><div class="lr-history-scroll"><table><thead><tr><th>Measure</th>'
    out += f'<th>As of / FY ended {esc(model["annual_end"])}</th><th>As of / TTM ended {esc(model["period_end"])}</th></tr></thead><tbody>'
    for row in model["rows"]:
        def show(value):
            return "Unavailable" if value is None else f'{value:.2f}x' if row["unit"] == "ratio" else f'{value:.1%}' if row["unit"] == "fraction" else money(value)
        out += f'<tr><td>{esc(row["label"])}</td><td>{esc(show(row["annual_value"]))}</td><td>{esc(show(row["value"]))}</td></tr>'
    out += '</tbody></table></div>'
    out += f'<p class="lr-meta">Fiscal year {esc(model["annual_start"])} to {esc(model["annual_end"])}. Later TTM {esc(model["period_start"])} to {esc(model["period_end"])}. Borrowing excludes leases; net debt excludes restricted cash and investments. Capital-spending and interest bases retain the company-specific limits above.</p>'
    for detail in dict.fromkeys(r["annual_detail"] for r in model["rows"] if r["annual_detail"]):
        out += f'<p class="lr-meta">{esc(detail)}</p>'
    out += f'<p class="lr-meta"><a href="{esc(model["annual_source"])}">Annual source filing</a> · <a href="{esc(model["current_source"])}">Latest source filing</a></p></section>'
    return out
