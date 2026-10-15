"""Financial questions first; filing mechanics remain available in the evidence disclosure.

The notes are selected, manually checked disclosures, not an exhaustive obligations list. Each belongs to the
pilot's specified 10-Q and remains separate from borrowing and ratios (docs/pilot_evidence_*.md).
"""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from ui import esc

NOTES = {
    "LLY": [
        {"name": "Pending AtaiBeckley acquisition", "amount": "Approximately $2.8B",
         "date": "2026-06-30", "kind": "Future commitment", "location": "10-Q MD&A, p. 31",
         "detail": "Potential payment at closing, subject to closing conditions. Not recognized as borrowing."},
        {"name": "Venture fund commitments", "amount": "Approximately $806M",
         "date": "2026-06-30", "kind": "Unfunded commitment", "location": "10-Q MD&A, p. 31; Note 8",
         "detail": "Expected to be paid over up to ten years. Not recognized as borrowing."},
    ],
    "ORCL": [
        {"name": "Leases not yet commenced", "amount": "$288B",
         "date": "2026-08-31", "kind": "Future commitment", "location": "10-Q Note 6, p. 13",
         "detail": "Substantially all data centers; expected to commence in fiscal 2027–2029 with 15–19 year terms. Not on the balance sheet or in the lease maturities table."},
        {"name": "Operating lease liabilities", "amount": "$34.621B",
         "date": "2026-08-31", "kind": "Recognized liability", "location": "10-Q Note 6, p. 12",
         "detail": "Recognized leases, separate from borrowing and from leases not yet commenced."},
        {"name": "Finance lease liabilities", "amount": "$9.185B",
         "date": "2026-08-31", "kind": "Recognized liability", "location": "10-Q Note 6, p. 12",
         "detail": "Shown separately under this review's borrowing definition; excluded from baseline gross debt."},
        {"name": "Purchase and other obligations", "amount": "$34.150B",
         "date": "2026-08-31", "kind": "Unrecorded commitment", "location": "10-Q Note 6, p. 13",
         "detail": "Primarily cloud infrastructure components and data center power. Overlap with other commitments is not established; no combined total is presented."},
    ],
    "VST": [
        {"name": "Nuveen final payment", "amount": "$631M due Dec 31, 2026",
         "date": "2026-06-30", "kind": "Recognized purchase obligation", "location": "10-Q Note 12, p. 28",
         "detail": "Principal and interest on the minority-interest purchase. The current balance-sheet obligation is $613M. Both describe the same obligation; neither is added to baseline borrowing."},
        {"name": "Helix initial commitment", "amount": "$500M",
         "date": "2026-06-30", "kind": "Callable investment commitment", "location": "10-Q MD&A, p. 69; Note 7, p. 15",
         "detail": "Remains callable by the fund's general partner, who determines timing and amount. Amount funded to date is not separately disclosed."},
        {"name": "Helix additional commitment", "amount": "Up to $500M",
         "date": "2026-06-30", "kind": "Conditional investment commitment", "location": "10-Q MD&A, p. 69; Note 7, p. 15",
         "detail": "The specified milestones had not occurred at June 30. Vistra may also elect to fund it regardless of those milestones."},
    ],
}

LIMITS = {
    "LLY": "Lease liabilities at June 30 are Unavailable. Selection of major commitments is not complete; contingencies, tax, collaboration and investment notes need further review. Later financing findings are not loaded in this saved view.",
    "ORCL": "Commercial paper is not separately disclosed in this 10-Q. The capex-financing balance and the later status of the 10-K's $3.3B lessor guarantee remain unresolved. Later financing findings are not loaded in this saved view.",
    "VST": "June 30 lease liabilities are Unavailable. Derivatives, litigation and the remaining retirement-obligation detail need further review. Credit-support overlaps are unresolved; the selected notes below are not a complete obligations list.",
}

CSS = """<style>
.lr-review {max-width:1180px; margin:8px auto 0; color:var(--text); font-variant-numeric:tabular-nums;}
.lr-review * {box-sizing:border-box;}
.lr-review h2 {font-size:1.5rem;line-height:1.3;letter-spacing:-.02em;padding:0;margin:4px 0 7px;color:var(--text-strong);}
.lr-review h3 {font-size:1.05rem;line-height:1.4;margin:0 0 7px;padding:0;color:var(--text-strong);}
.lr-review p {font-size:.9rem;line-height:1.55;margin:8px 0;}
.lr-review .lr-meta {font-size:.78rem;color:var(--text-muted);line-height:1.5;}
.lr-lead {border-bottom:1px solid var(--border);padding:0 0 18px;}
.lr-lead .lr-answer {font-size:1.12rem;max-width:850px;color:var(--text-strong);margin-top:12px;}
.lr-summary {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;padding:18px 0;border-bottom:1px solid var(--border);}
.lr-stat-label {font-size:.8rem;color:var(--text-muted);}
.lr-stat-value {font-size:1.5rem;font-weight:650;line-height:1.5;color:var(--text-strong);}
.lr-stat-detail {font-size:.75rem;color:var(--text-muted);}
.lr-grid {display:grid;grid-template-columns:1.15fr 1fr;gap:30px;margin:24px 0;}
.lr-section {min-width:0;}
.lr-chart {margin:18px 0;}
.lr-bar-row {display:grid;grid-template-columns:115px minmax(40px,1fr) 85px;gap:12px;align-items:center;margin:12px 0;font-size:.8rem;}
.lr-bar-value {text-align:right;color:var(--text-strong);white-space:nowrap;}
.lr-track {display:grid;grid-template-columns:1fr 1fr;height:19px;}
.lr-half {display:flex;align-items:center;min-width:0;}
.lr-half:first-child {justify-content:flex-end;border-right:1px solid var(--border-strong);}
.lr-bar {display:block;height:12px;background:var(--text-muted);min-width:1px;}
.lr-row {display:flex;justify-content:space-between;gap:16px;border-bottom:1px solid var(--border);padding:10px 0;font-size:.85rem;}
.lr-row span {max-width:75%;}
.lr-row strong {white-space:nowrap;font-weight:600;}
.lr-ratios {display:grid;grid-template-columns:1fr 1fr;gap:18px;border-top:1px solid var(--border);padding-top:14px;margin-top:20px;}
.lr-ratios strong {display:block;font-size:1.2rem;color:var(--text-strong);}
.lr-obligations {border-top:1px solid var(--border);padding:22px 0 8px;}
.lr-obligation {display:grid;grid-template-columns:minmax(160px,1fr) minmax(0,2fr);gap:24px;border-bottom:1px solid var(--border);padding:14px 0;}
.lr-obligation p {margin:0 0 5px;}
.lr-obligation strong {color:var(--text-strong);}
.lr-limits {padding:15px 0 4px;}
.lr-review a {color:var(--link);}
.lr-review + .irt-evidence {max-width:1180px;margin:12px auto;}
@media(max-width:760px) {.lr-grid {grid-template-columns:1fr;gap:24px;} .lr-summary {grid-template-columns:repeat(2,minmax(0,1fr));} .lr-obligation {grid-template-columns:1fr;gap:4px;} .lr-review h2 {font-size:1.3rem;} .lr-bar-row {grid-template-columns:96px minmax(30px,1fr) 75px;gap:7px;} .lr-stat-value {font-size:1.3rem;}}
</style>"""


def money(value, digits=2):
    if value is None:
        return "Unavailable"
    magnitude = Decimal(str(abs(value)))
    if 0 < magnitude < 1_000_000_000:
        millions = (magnitude / 1_000_000).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return f"{'−' if value < 0 else ''}${millions:,.0f}M"
    billions = (magnitude / 1_000_000_000).quantize(Decimal(10) ** -digits, rounding=ROUND_HALF_UP)
    return f"{'−' if value < 0 else ''}${billions:,.{digits}f}B"


def pct(metric):
    return "Unavailable" if metric["value"] is None else f"{metric['value']:.1%}"


def headline(snapshot):
    m = snapshot["metrics"]
    fcf = m["free_cash_flow"]["value"]
    if fcf is None:
        return "Cash generation could not be established from the checked inputs."
    if fcf < 0:
        return f"Reported capital spending exceeded operating cash flow by {money(-fcf)}."
    if fcf == 0:
        return "Operating cash flow equalled reported capital spending."
    return f"Operating cash flow exceeded reported capital spending by {money(fcf)}."


def render(snapshot):
    """Deterministic, source-linked explanations; no ratings or implied repayment assumptions."""
    m = snapshot["metrics"]
    end = date.fromisoformat(m["cash"]["period_end"]).strftime("%b %d, %Y")
    source = snapshot["source_url"]
    output = CSS + '<section class="lr-review">'
    output += f'<header class="lr-lead"><div class="lr-meta">{esc(snapshot["ticker"])} · Debt and liquidity review</div>'
    output += f'<h2>{esc(snapshot["company_name"])}</h2><div class="lr-meta">Balance sheet: {esc(end)} · '
    output += f'<a href="{esc(source)}" target="_blank" rel="noopener noreferrer">Source 10-Q</a> · Saved review, Oct 14, 2026</div>'
    output += f'<p class="lr-answer">{esc(headline(snapshot))}</p>'
    output += '<p class="lr-meta">Cash flows cover the trailing twelve months to this balance-sheet date. Borrowing is at carrying amount and excludes leases. Figures are rounded; evidence retains exact inputs.</p></header>'
    output += '<div class="lr-summary">'
    for label, value, detail in (
        ("Cash and equivalents", money(m["cash"]["value"]), "Excludes restricted cash"),
        ("Baseline gross debt", money(m["gross_debt"]["value"]), "Borrowing, excluding leases"),
        ("Net debt", money(m["net_debt"]["value"]), "Gross debt less cash"),
        ("Current ratio", f'{m["current_ratio"]["value"]:.2f}x' if m["current_ratio"]["value"] is not None else "Unavailable", "Current assets / liabilities"),
    ):
        output += f'<div><div class="lr-stat-label">{esc(label)}</div><div class="lr-stat-value">{esc(value)}</div><div class="lr-stat-detail">{esc(detail)}</div></div>'
    output += '</div><div class="lr-grid"><section class="lr-section"><h3>What remained after capital spending?</h3>'
    output += f'<div class="lr-meta">TTM ended {esc(end)} · USD billions · 10-K and 10-Q cash-flow statements</div>'
    bars = [("Operating cash flow", m["operating_cash_flow"]["value"]),
            ("Capital spending", -m["capital_spending"]["value"] if m["capital_spending"]["value"] is not None else None),
            ("Free cash flow", m["free_cash_flow"]["value"])]
    maximum = max((abs(v) for _, v in bars if v is not None), default=1) or 1
    output += '<div class="lr-chart">'
    for name, value in bars:
        width = abs(value) / maximum * 100 if value is not None else 0
        bar = f'<span class="lr-bar" style="width:{width:.4f}%"></span>' if value else ''
        output += (f'<div class="lr-bar-row"><span>{esc(name)}</span><div class="lr-track" aria-hidden="true">'
                   f'<div class="lr-half">{bar if value is not None and value < 0 else ""}</div>'
                   f'<div class="lr-half">{bar if value is not None and value > 0 else ""}</div></div>'
                   f'<span class="lr-bar-value">{esc(money(value))}</span></div>')
    output += '</div>'
    output += f'<p class="lr-meta">{esc(m["free_cash_flow"]["notes"][0])}</p>'
    output += '<div class="lr-ratios">'
    for key, label in (("ocf_to_debt", "TTM operating cash flow / debt"), ("fcf_to_debt", "TTM free cash flow / debt")):
        output += f'<div><span class="lr-stat-label">{esc(label)}</span><strong>{esc(pct(m[key]))}</strong></div>'
    output += '</div><p class="lr-meta">Historical flows relative to period-end borrowing; these percentages are not repayment forecasts. FCF excludes acquisitions, dividends and other cash uses.</p></section>'
    output += '<section class="lr-section"><h3>What makes up the borrowing?</h3>'
    output += f'<div class="lr-meta">At {esc(end)} · amounts in B or M · same 10-Q as the balance sheet</div>'
    for fact in m["gross_debt"]["inputs"]:
        label = fact["label"].replace("Long-term debt, less amounts due currently", "Long-term debt, noncurrent")
        value = money(fact["value"], 3)
        if fact["value"] == 0:
            value = "$0 · reported"
        output += f'<div class="lr-row"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>'
    assets = m["current_ratio"]["inputs"]["current_assets"]
    liabilities = m["current_ratio"]["inputs"]["current_liabilities"]
    if assets["value"] is not None and liabilities["value"] is not None:
        gap = assets["value"] - liabilities["value"]
        direction = "exceeded" if gap >= 0 else "were below"
        output += (f'<p>Current assets of {esc(money(assets["value"]))} {direction} current liabilities of '
                   f'{esc(money(liabilities["value"]))} by {esc(money(abs(gap)))}.</p>')
    output += '<p class="lr-meta">Current assets include items other than cash. This comparison does not establish whether specific payments can be met; a maturity schedule and financing terms are still needed.</p></section></div>'
    output += '<section class="lr-obligations"><h3>What sits outside baseline borrowing?</h3><p class="lr-meta">Selected disclosures, each shown separately. Commitments are not all payable now and are not added to debt or to each other.</p>'
    for item in NOTES[snapshot["ticker"]]:
        output += (f'<article class="lr-obligation"><div><p><strong>{esc(item["name"])}</strong></p>'
                   f'<p>{esc(item["amount"])}</p><div class="lr-meta">As of {esc(item["date"])} · {esc(item["kind"])}</div></div>'
                   f'<div><p>{esc(item["detail"])}</p><a class="lr-meta" href="{esc(source)}" target="_blank" rel="noopener noreferrer">{esc(item["location"])}</a></div></article>')
    output += '</section><section class="lr-limits"><h3>What remains unresolved?</h3>'
    output += f'<p class="lr-meta">{esc(LIMITS[snapshot["ticker"]])} Interest coverage and a full debt maturity review are not included.</p></section></section>'
    return output
