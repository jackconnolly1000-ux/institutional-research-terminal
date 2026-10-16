"""A selected interest component and an independently reconciled mixed total."""
import vistra_interest as vi
from ui import esc


def render(snapshot, money):
    if snapshot.get("ticker") != "VST":
        return ""
    out = '<section class="lr-maturity"><h3>How did Vistra’s operating earnings cover reported interest?</h3>'
    r = vi.for_snapshot(snapshot)
    if r is None:
        return out + '<p>Unavailable: the checked Vistra interest review does not match this snapshot.</p></section>'
    c = r["calculation"];t = c["ttm"]
    out += '<p class="lr-meta">TTM July 1, 2025–June 30, 2026 · operating income / reported interest component before capitalized interest</p>'
    if c["value"] is None:
        out += '<p>Interest coverage Unavailable: ' + esc(c["detail"]) + '</p>'
    else:
        out += f'<div class="lr-stat-value">{c["value"]:.2f}x</div>'
        out += '<p>TTM reported operating income of ' + esc(money(t["operating_income"], 3))
        out += ' divided by ' + esc(money(t["interest"], 3)) + ' of the separately reported Interest expense component. The mixed interest-and-related-charges total is not the denominator.</p>'

    def table(rows):
        text = '<div class="ol-table-wrap"><table class="ol-table"><thead><tr><th>USD millions</th><th>FY2025</th><th>+ H1 2026</th><th>− H1 2025</th><th>TTM</th></tr></thead><tbody>'
        for label, values in rows:
            text += '<tr><td>' + esc(label) + '</td>'
            for v in values:
                text += '<td>' + ('Unavailable' if v is None else f'({abs(v)/1e6:,.0f})' if v < 0 else f'{v/1e6:,.0f}') + '</td>'
            text += '</tr>'
        return text + '</tbody></table></div>'

    roles = ["fy", "current", "prior"]
    out += table([(label, [*(c["periods"][p][key] for p in roles), t[key]]) for key, label in
                  [("operating_income", "Reported operating income"), ("interest", "Selected interest component")]])
    out += '<p><strong>Capitalized-interest basis:</strong> ' + esc(r["basis"]) + '</p>'
    out += '<p><strong>Composition:</strong> ' + esc(r["composition"]) + '</p>'
    out += '<p class="lr-meta">' + esc(r["limitations"]) + '</p>'
    out += '<details><summary>Interest reconciliation, signs and filing evidence</summary>'
    rows = []
    for key, label in [("interest", "Interest component"), ("swaps", "Unrealized swap (gain) loss"),
                       ("amortization", "Debt-cost amortization"), ("extinguishment", "Extinguishment (gain) loss"),
                       ("capitalized", "Less capitalized interest"), ("other", "Other")]:
        rows.append((label, [*(c["periods"][p]["effects"][key] for p in roles),
                             None if t[key] is None else t[key] * vi.EFFECTS[key]]))
    for key, label in [("calculated_total", "Reconstructed mixed total"), ("total", "Reported mixed total"), ("difference", "Reconciliation difference")]:
        values = [c["periods"][p][key] for p in roles]
        rows.append((label, [*values, sum(v*s for v, s in zip(values, [1, 1, -1])) if all(v is not None for v in values) else None]))
    out += table(rows)
    out += '<p>Parentheses mean a reduction in expense. Raw swap and extinguishment facts use a gain-positive sign; this table reverses those signs to match the printed expense rows. Capitalized interest is a separate deduction in the mixed total, not a second adjustment to the selected denominator.</p>'
    out += '<p>The original H1 2025 filing independently agrees with all eight comparative facts. Three-month facts and parent/segment facts are not substituted. The extension schema identifies the interest component as a monetary duration with a debit balance and label Interest expense; its documentation does not resolve the receivables/Nuveen allocation.</p>'
    for g in r["unavailable"].values():
        out += '<p class="lr-meta">Unavailable: ' + esc(g["detail"]) + '</p>'
    for source, role in [("annual", "fy"), ("quarter", "current"), ("prior_original", "prior_original")]:
        f = r["inputs"][role + "_interest"]
        out += '<p class="lr-meta"><a href="' + esc(f["source_url"]) + '" target="_blank" rel="noopener noreferrer">'
        out += esc(f["form"] + ' · ' + f["location"]) + '</a> · ' + esc(f["accession"]) + '</p>'
    out += '<p class="lr-meta">The Vistra Excel Data sheet preserves exact periods, tags, contexts, dimensions, source fingerprints and raw signs. Its Cash review shows the expense-sign reconciliation.</p></details></section>'
    return out.replace("$", "&#36;")
