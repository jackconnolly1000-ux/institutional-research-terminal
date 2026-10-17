"""Two source-backed chart questions; unknown history is omitted, never plotted as zero."""
import hashlib
from pathlib import Path
import company_history


def fingerprint():
    return {"code": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "history": company_history.fingerprint()}


def build(snapshot):
    h = company_history.build(snapshot)
    r = {x["key"]: x for x in h["rows"]}
    flow = [("Operating cash flow", r["operating_cash_flow"]["value"]),
            ("Capital spending", -r["capital_spending"]["value"] if r["capital_spending"]["value"] is not None else None),
            ("Free cash flow", r["free_cash_flow"]["value"])]
    series = ["Cash and equivalents"]
    if r["gross_debt"]["annual_value"] is not None:
        series.append("Baseline borrowing")
    points = [(h["annual_end"], [r["cash"]["annual_value"]] + ([r["gross_debt"]["annual_value"]] if len(series) == 2 else [])),
              (h["period_end"], [r["cash"]["value"]] + ([r["gross_debt"]["value"]] if len(series) == 2 else []))]
    return {"flow": flow, "points": points, "series": series, "period_start": h["period_start"], "period_end": h["period_end"],
            "title": "How did borrowing and cash change?" if len(series) == 2 else "How did cash change?",
            "note": "Baseline borrowing excludes leases; cash excludes restricted cash and investments. These balances do not establish repayment coverage." if len(series) == 2 else
            "Older borrowing is Unavailable, so this chart compares cash only. No zero borrowing value or debt trend is inferred. Cash excludes restricted cash and investments.",
            "sources": [h["annual_source"], h["current_source"]]}


def _bars(rows, money):
    from ui import esc
    maximum = max((abs(v) for _, v in rows if v is not None), default=1) or 1
    out = '<p class="lr-meta">Uses left of zero · 0 · positive values right of zero</p><div class="lr-chart">'
    for name, value in rows:
        width = abs(value) / maximum * 100 if value is not None else 0
        bar = f'<span class="lr-bar" style="width:{width:.4f}%"></span>' if value else ''
        out += (f'<div class="lr-bar-row"><span>{esc(name)}</span><div class="lr-track" aria-hidden="true">'
                f'<div class="lr-half">{bar if value is not None and value < 0 else ""}</div>'
                f'<div class="lr-half">{bar if value is not None and value > 0 else ""}</div></div>'
                f'<span class="lr-bar-value">{esc(money(value))}</span></div>')
    return out + '</div>'


def render_flow(snapshot, money):
    model = build(snapshot)
    return (_bars(model["flow"], money) + '<p class="lr-meta">FCF = OCF − capital spending. The FCF bar is the result, not another cash flow to add. Capital spending is shown as a use.</p>')


def render_balances(snapshot, money):
    from ui import esc
    model = build(snapshot)
    rows = [(f"{name} · {date}", value) for date, values in model["points"] for name, value in zip(model["series"], values)]
    out = f'<section class="lr-obligations lr-balancechart"><h3>{esc(model["title"])}</h3><p class="lr-meta">USD billions · balance-sheet dates shown with each bar</p>'
    out += _bars(rows, money) + f'<p class="lr-meta">{esc(model["note"])}</p>'
    out += '<p class="lr-meta">' + ' · '.join(f'<a href="{esc(url)}">{"Annual" if i == 0 else "Latest"} source filing</a>' for i, url in enumerate(model["sources"])) + '</p></section>'
    return out
