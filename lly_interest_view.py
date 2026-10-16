"""A historical, explicitly derived earnings-coverage calculation."""
import lly_interest as li
from ui import esc


def render(snapshot, money):
    if snapshot.get("ticker") != "LLY":
        return ""
    r = li.for_snapshot(snapshot)
    out = '<section class="lr-maturity"><h3>How did operating earnings cover reported interest?</h3>'
    if r is None:
        return out + '<p>Unavailable: the checked Lilly interest review does not match this snapshot.</p></section>'
    c = r["calculation"]
    out += '<p class="lr-meta">TTM July 1, 2025–June 30, 2026 · derived operating income / reported interest expense on borrowings</p>'
    if c["value"] is None:
        out += '<p>Interest coverage Unavailable: ' + esc(c["detail"]) + '</p>'
    else:
        out += (f'<div class="lr-stat-value">{c["value"]:.2f}x</div>'
                f'<p>Derived TTM operating income of {esc(money(c["operating_income"],3))} divided by '
                f'{esc(money(c["interest"],3))} reported interest expense. This measures historical earnings coverage; '
                'it does not show cash available for future repayments.</p>')
    out += '<div class="ol-table-wrap"><table class="ol-table"><thead><tr><th>Build, USD millions</th><th>FY2025</th><th>+ H1 2026</th><th>− H1 2025</th><th>TTM</th></tr></thead><tbody>'
    for field, label in [("operating_income", "Derived operating income"), ("interest", "Reported interest expense")]:
        out += '<tr><td>' + label + '</td>'
        for role in ["fy", "current", "prior"]:
            value = c["periods"].get(role, {}).get(field)
            out += '<td>' + (f'{value/1_000_000:,.0f}' if value is not None else 'Unavailable') + '</td>'
        value = c[field]
        out += '<td>' + (f'{value/1_000_000:,.0f}' if value is not None else 'Unavailable') + '</td></tr>'
    out += '</tbody></table></div><p><strong>Capitalized-interest basis:</strong> ' + esc(r["basis"]) + '</p>'
    out += '<p class="lr-meta">' + esc(r["limitations"]) + '</p>'
    out += '<details><summary>Operating-income derivation, segment rule and filing evidence</summary>'
    out += '<p>Lilly does not present an operating-income subtotal in these statements. The numerator is derived as '
    out += esc(r["operating_formula"]) + '. Each period reconciles independently to pretax income minus the XBRL nonoperating income (expense) fact. '
    out += 'That fact is positive income and negative expense, opposite the printed Other—net expense-row convention.</p>'
    out += '<p>Quarterly interest uses only the checked single-segment axis/member. Extra or missing dimensions are rejected. '
    out += 'Annual interest is undimensioned. The six-month facts, 677 and 493, are used; the three-month 345 and 249 are not added. '
    out += 'Rounded MD&A IPR&amp;D repeats are excluded by selecting the consolidated operations table, retaining its exact tagged amounts.</p>'
    for source, ops, interest in [("annual", "Operations p. 57", "Borrowings Note 11 p. 77"),
                                  ("quarter", "Operations p. 5", "Segment Note 11 p. 23")]:
        f = r["inputs"][("fy" if source == "annual" else "current") + "_interest"]
        out += '<p class="lr-meta"><a href="' + esc(f["source_url"]) + '" target="_blank" rel="noopener noreferrer">'
        out += esc(f["form"] + ' · ' + ops + '; ' + interest) + '</a> · ' + esc(f["accession"]) + '</p>'
    out += '<p class="lr-meta">The Lilly Excel Data sheet retains every value, tag, exact duration, context, dimension, scale, decimals and source-selection rule.</p></details></section>'
    return out.replace("$", "&#36;")
