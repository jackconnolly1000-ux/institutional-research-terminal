"""Display the reported-line ratio without implying contractual borrowing coverage."""
import oracle_interest as oi
from ui import esc


def render(snapshot, money):
    if snapshot.get("ticker") != "ORCL":
        return ""
    out = '<section class="lr-maturity"><h3>How did Oracle’s operating earnings cover reported interest?</h3>'
    r = oi.for_snapshot(snapshot)
    if r is None:
        return out + '<p>Unavailable: the checked Oracle interest review does not match this snapshot.</p></section>'
    c = r["calculation"]
    out += '<p class="lr-meta">TTM September 1, 2025–August 31, 2026 · reported operating income / reported Interest expense</p>'
    if c["value"] is None:
        out += '<p>Reported-line coverage Unavailable: ' + esc(c["detail"]) + '</p>'
    else:
        out += f'<div class="lr-stat-value">{c["value"]:.2f}x</div>'
        out += '<p>TTM reported operating income of ' + esc(money(c["operating_income"], 3))
        out += ' divided by ' + esc(money(c["interest"], 3)) + ' reported interest expense. Historical earnings coverage does not show cash available for future repayments.</p>'
    out += '<div class="ol-table-wrap"><table class="ol-table"><thead><tr><th>Build, USD millions</th><th>FY2026</th><th>+ Q1 FY2027</th><th>− Q1 FY2026</th><th>TTM</th></tr></thead><tbody>'
    for key, label in [("operating_income", "Reported operating income"), ("interest", "Reported Interest expense")]:
        out += '<tr><td>' + label + '</td>'
        for value in [*(c["periods"][p][key] for p in ["fy", "current", "prior"]), c[key]]:
            out += '<td>' + (f'{value/1e6:,.0f}' if value is not None else 'Unavailable') + '</td>'
        out += '</tr>'
    out += '</tbody></table></div><p><strong>Capitalized-interest basis:</strong> ' + esc(r["basis"]) + '</p>'
    out += '<p><strong>Composition:</strong> ' + esc(r["composition"]) + '</p>'
    out += '<p class="lr-meta">' + esc(r["limitations"]) + '</p>'
    out += '<details><summary>Interest composition, unavailable measures and filing evidence</summary>'
    lease = c["lease_interest"]
    if lease is not None:
        out += '<p>The lease notes separately report interest of 279M + 126M − 48M = ' + f'{lease/1e6:,.0f}'
        out += 'M TTM. This amount is not added to or subtracted from the denominator because overlap with the reported interest line is not established.</p>'
    for gap in r["unavailable"].values():
        out += '<p class="lr-meta">Unavailable: ' + esc(gap["detail"]) + '</p>'
    for source, role, loc in [("annual", "fy", "Operations p. 65; MD&A p. 50; revenue policy p. 71; prepayments p. 73; leases p. 88"),
                              ("quarter", "current", "Operations p. 2; prepayments p. 7; leases p. 12; MD&A p. 32")]:
        f = r["inputs"][role + "_interest"]
        out += '<p class="lr-meta"><a href="' + esc(f["source_url"]) + '" target="_blank" rel="noopener noreferrer">'
        out += esc(f["form"] + ' · ' + loc) + '</a> · ' + esc(f["accession"]) + '</p>'
    out += '<p class="lr-meta">The Oracle Excel Data sheet retains exact periods, contexts, tags, units and source fingerprints. The calculation is separate from the revolver’s 3.0x contract covenant.</p></details></section>'
    return out.replace("$", "&#36;")
