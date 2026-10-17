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
    out = ('<p class="lr-meta"><span class="ol-key out" aria-hidden="true"></span>Uses cash, left of zero · '
           '<span class="ol-key in" aria-hidden="true"></span>adds cash or a positive result, right of zero</p><div class="lr-chart">')
    for name, value in rows:
        width = abs(value) / maximum * 100 if value is not None else 0
        bar = f'<span class="lr-bar{" in" if value and value > 0 else ""}" style="width:{width:.4f}%"></span>' if value else ''
        out += (f'<div class="lr-bar-row"><span>{esc(name)}</span><div class="lr-track" aria-hidden="true">'
                f'<div class="lr-half">{bar if value is not None and value < 0 else ""}</div>'
                f'<div class="lr-half">{bar if value is not None and value > 0 else ""}</div></div>'
                f'<span class="lr-bar-value">{esc(money(value))}</span></div>')
    return out + '</div>'


def render_flow(snapshot, money):
    model = build(snapshot)
    return (_bars(model["flow"], money) + '<p class="lr-meta">FCF = OCF − capital spending. The FCF bar is the result, not another cash flow to add. Capital spending is shown as a use.</p>')


def render_balances(snapshot, money):
    """One panel per balance, both dates in each, on one shared scale so cash and borrowing compare honestly.

    All values are balances (never negative here), so bars start at zero on the left; the old diverging
    layout left half the width empty. Identity color (theme.SERIES_CASH / SERIES_BORROWING) plus each panel's
    title means color never carries the meaning alone."""
    from datetime import date
    from ui import esc
    model = build(snapshot)
    day = lambda iso: (lambda d: f"{d:%b} {d.day}, {d:%Y}")(date.fromisoformat(iso))
    dates = [d for d, _ in model["points"]]
    known = [v for _, values in model["points"] for v in values if v is not None]
    maximum = max(known, default=1) or 1
    kinds = {"Cash and equivalents": "cash", "Baseline borrowing": "borrowing"}
    out = (f'<section class="lr-obligations lr-balancechart"><h3>{esc(model["title"])}</h3>'
           f'<p class="lr-meta">Balances at {esc(day(dates[0]))} (latest annual) and {esc(day(dates[1]))} (latest '
           'quarter) · ' + ('USD billions' if all(v >= 1e9 for v in known) else 'USD, in B or M') + (' · one scale for both panels' if len(model["series"]) == 2 else '')
           + '</p><div class="lr-bal-grid">')
    for k, name in enumerate(model["series"]):
        values = [v[k] for _, v in model["points"]]
        out += (f'<div class="lr-bal-panel" role="figure" aria-label="{esc(name)} at both dates">'
                f'<h4><span class="lr-swatch lr-{kinds[name]}" aria-hidden="true"></span>{esc(name)}</h4>')
        for when, value in zip(dates, values):
            width = 0 if value is None else max(value / maximum * 100, 0.5)
            shown = "Unavailable" if value is None else money(value)
            out += (f'<div class="lr-bal-row"><span class="lr-bal-date">{esc(day(when))}</span>'
                    f'<div class="lr-bal-track" title="{esc(name)}, {esc(day(when))}: {esc(shown)}">'
                    + (f'<span class="lr-bal-bar lr-{kinds[name]}" style="width:{width:.4f}%"></span>' if value is not None else '')
                    + f'</div><strong class="lr-bal-value">{esc(shown)}</strong></div>')
        if None not in values:
            change = values[1] - values[0]
            sign = "+" if change > 0 else "−" if change < 0 else ""
            out += f'<p class="lr-meta">Change since {esc(day(dates[0]))}: {sign}{esc(money(abs(change)) if change else "$0")}</p>'
        out += '</div>'
    out += f'</div><p class="lr-meta">{esc(model["note"])}</p>'
    out += '<p class="lr-meta">' + ' · '.join(f'<a href="{esc(url)}">{"Annual" if i == 0 else "Latest"} source filing</a>' for i, url in enumerate(model["sources"])) + '</p></section>'
    return out
