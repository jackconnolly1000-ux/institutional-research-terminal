"""A dated Oracle funding explanation; no ratings or inferred repayment forecast."""
from ui import esc
import oracle_liquidity as ol
import oracle_financing as of

CSS = """
.ol-bridge {margin:22px 0 12px;}
.ol-step,.ol-axis {display:grid;grid-template-columns:220px minmax(80px,1fr) 100px;gap:16px;align-items:center;margin:16px 0;font-size:.85rem;}
.ol-axis {font-size:.75rem;color:var(--text-muted);margin:0 0 12px;}
.ol-axis-scale {display:flex;justify-content:space-between;}
.ol-track {display:grid;grid-template-columns:1fr 1fr;height:20px;}
.ol-side {display:flex;align-items:center;min-width:0;}
.ol-side:first-child {justify-content:flex-end;border-right:1px solid var(--border-strong);}
.ol-fill {display:block;height:14px;background:var(--text-muted);min-width:1px;}
.ol-step strong {text-align:right;white-space:nowrap;font-weight:600;}
.ol-balances {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border:1px solid var(--border);margin:18px 0;}
.ol-balances > div {padding:14px 16px;}
.ol-balances > div + div {border-left:1px solid var(--border);}
.ol-balances span {display:block;font-size:.78rem;color:var(--text-muted);}
.ol-balances strong {font-size:1.3rem;color:var(--text-strong);font-weight:600;}
.ol-table-wrap {overflow-x:auto;margin:12px 0;}
.ol-table {width:100%;border-collapse:collapse;font-size:.8rem;}
.ol-table th,.ol-table td {padding:10px 8px;border-bottom:1px solid var(--border);text-align:right;vertical-align:top;}
.ol-table th:first-child,.ol-table td:first-child {text-align:left;}
.ol-table th {font-weight:600;}
.ol-resource {display:grid;grid-template-columns:220px 110px minmax(0,1fr);gap:16px;padding:14px 0;border-bottom:1px solid var(--border);}
.ol-resource strong {text-align:right;white-space:nowrap;}
.ol-resource p {margin:0;}
.ol-repayments {margin:18px 0;}
.ol-repayments details {padding:12px 0;border-bottom:1px solid var(--border);}
.ol-repayments summary {font-weight:600;cursor:pointer;}
.ol-obligation {display:flex;justify-content:space-between;gap:16px;margin:14px 0 4px;}
.ol-obligation strong {white-space:nowrap;}
@media(max-width:760px) {.ol-resource {display:flex;flex-wrap:wrap;gap:8px 12px;} .ol-resource > div {flex:1;min-width:0;} .ol-resource p {flex-basis:100%;width:100%;} .ol-repayments {overflow-wrap:anywhere;}}
@media(max-width:760px) {.ol-step {display:flex;flex-wrap:wrap;justify-content:space-between;gap:7px 12px;font-size:.82rem;margin:18px 0;} .ol-step > span {flex:1;max-width:calc(100% - 100px);} .ol-step strong {order:1;width:90px;} .ol-step .ol-track {order:2;flex-basis:100%;width:100%;} .ol-axis {display:block;} .ol-axis > span {display:none;} .ol-balances {grid-template-columns:1fr;} .ol-balances > div {display:flex;justify-content:space-between;gap:10px;align-items:center;padding:10px 12px;} .ol-balances > div + div {border-left:0;border-top:1px solid var(--border);} .ol-balances strong {font-size:1.15rem;white-space:nowrap;} .ol-table th,.ol-table td {padding:9px 5px;font-size:.72rem;}}
"""


def render(snapshot, money):
    review = ol.for_snapshot(snapshot)
    if review is None:
        return ""
    out = '<section class="lr-maturity"><h3>What funded Oracle’s cash balance?</h3>'
    if review["status"] != "Checked":
        return out + f'<p>Unavailable: {esc(review["detail"])}</p></section>'
    inputs, c = review["inputs"], review["cash"]
    v = {k: f["value"] for k, f in inputs.items()}
    amount = lambda x: esc(money(x, 3))
    source = (f'<a href="{esc(review["source_url"])}" target="_blank" rel="noopener noreferrer">'
              '10-Q cash flows, p. 5; cash note, p. 6</a>')
    out += f'<p class="lr-meta">June 1–August 31, 2026 · USD billions · {source} · checked Oct 15, 2026</p>'
    out += (f'<p>Operating cash flow of {amount(v["ocf"])} was below cash capital spending of '
            f'{amount(v["capex"])}. Net equity proceeds of {amount(v["equity"])} helped fund the quarter’s '
            'cash uses. Those proceeds are already included in August cash.</p>')
    out += '<div class="ol-balances">'
    for label, value in (("May 31 cash including restricted", v["opening_total"]),
                         ("Quarter change", v["change"]),
                         ("August 31 cash including restricted", v["closing_total"])):
        out += f'<div><span>{esc(label)}</span><strong>{amount(value)}</strong></div>'
    out += '</div><p><strong>What added to or used cash during the quarter?</strong></p>'
    steps = [("OCF excluding specified prepayments", c["ocf_less_prepay"]),
             ("Specified customer prepayments", v["prepay"]),
             ("Equity proceeds, net", v["equity"]),
             ("Cash capital spending", -v["capex"]),
             ("Debt repayments", -v["debt_repayments"]),
             ("Other cash flows, net", c["other_net"])]
    # Every bar shares zero. Balance totals sit outside the changes so they cannot be added twice.
    maximum = 30_000_000_000
    out += ('<div class="ol-bridge" role="figure" aria-label="Quarter cash contributions: uses left, sources right">'
            '<div class="ol-axis"><span>Quarter cash contribution</span><div class="ol-axis-scale">'
            '<span>−$30B · cash used</span><span>0</span><span>cash added · +$30B</span></div><span>USD</span></div>')
    for label, value in steps:
        bar = f'<span class="ol-fill" style="width:{abs(value)/maximum*100:.4f}%"></span>'
        shown = ("+" if value > 0 else "") + money(value, 3)
        out += (f'<div class="ol-step"><span>{esc(label)}</span><div class="ol-track" aria-hidden="true">'
                f'<div class="ol-side">{bar if value < 0 else ""}</div>'
                f'<div class="ol-side">{bar if value > 0 else ""}</div></div><strong>{esc(shown)}</strong></div>')
    out += ('</div><p class="lr-meta">The six signed contributions sum to the quarter’s cash increase. '
            'The first two together equal reported OCF. Prepayments are separated once. '
            'Other cash flows include dividends, investments and other financing. All rows cover June–August 2026.</p>')
    out += (f'<p>Closing cash including restricted cash was {amount(v["closing_total"])}. Excluding '
            f'{amount(c["restricted_at_end"])} restricted cash leaves {amount(v["closing_cash"])} cash and equivalents '
            'on the balance sheet. That exclusion is not another cash outflow.</p>')
    out += '<div class="lr-grid"><div><h3>How much came from customer prepayments?</h3>'
    share = f'{c["prepay_share_ocf"]:.1%}' if c["prepay_share_ocf"] is not None else "Unavailable"
    out += (f'<p>The specified prepayment contribution was {amount(v["prepay"])} ({share} of reported OCF). '
            f'Subtracting it leaves {amount(c["ocf_less_prepay"])} OCF and '
            f'{amount(c["fcf_less_prepay"])} after cash capital spending, compared with '
            f'{amount(c["fcf"])} reported OCF less cash capital spending.</p>'
            '<p class="lr-meta">The remainder includes working-capital changes and other cash items. Its recurrence '
            'has not been established. Prepayments fund future performance obligations and are not debt proceeds '
            'or cash free of future service costs. See 10-Q Note 1, pp. 6–7.</p></div><div>')
    out += '<h3>Historical funding exclusions</h3>'
    out += (f'<p>The reported cash increase, including restricted cash, was {amount(v["change"])}. '
            f'Subtracting ATM equity proceeds gives {amount(c["change_without_equity"])}. '
            f'Subtracting both ATM proceeds and the specified prepayment contribution gives '
            f'{amount(c["change_without_equity_and_prepay"])}.</p>'
            '<p class="lr-meta">These calculations hold all other reported flows fixed. They do not model changes '
            'in spending, borrowing, customer behavior or restricted cash. They are not forecasts, cash runway '
            'estimates or proof that funding would have been unavailable.</p></div></div>')
    out += '<details><summary>Cash sources and uses behind the chart</summary><div class="ol-table-wrap"><table class="ol-table">'
    out += '<thead><tr><th>Quarter cash-flow line</th><th>USD (B or M)</th></tr></thead><tbody>'
    signs = {"capex": -1, "investment_purchases": -1, "dividends": -1, "cp": -1, "debt_repayments": -1}
    for key in ol.FLOWS:
        if key in {"investing", "financing", "change", "unpaid_capex"}:
            continue
        label = inputs[key]["label"] + (" (inside OCF)" if key == "prepay" else "")
        out += f'<tr><td>{esc(label)}</td><td>{amount(v[key]*signs.get(key,1))}</td></tr>'
    out += ('</tbody></table></div><p class="lr-meta">The $4.202B grouped debt-repayment line is used once. '
            'The cash-flow commercial-paper line is a reported zero, while MD&A describes about $1.1B CP '
            'repayment within its repayment discussion. Classification remains unresolved; another $1.1B is '
            'not deducted. Interest and operating-lease payments already reflected in OCF are not deducted again.</p>')
    out += (f'<p class="lr-meta">Unpaid capex disclosed separately: {amount(v["unpaid_capex"])}. '
            'It is noncash in this quarter and is not added to cash capex. Its payment dates and overlap with '
            'purchase commitments are Unavailable.</p></details>')
    out += '<h3>What payments are actually dated?</h3>'
    out += (f'<p class="lr-meta">At August 31, 2026 · USD, amounts in B or M · '
            f'<a href="{esc(of.QUARTER_SOURCE)}" target="_blank" rel="noopener noreferrer">10-Q Note 6, pp. 12–13</a>. '
            'Lease amounts are undiscounted payments including interest. Purchase obligations remain separate.</p>')
    schedules = review["schedules"]
    out += '<div class="ol-table-wrap"><table class="ol-table"><thead><tr><th>Due period</th><th>Operating leases</th><th>Finance leases</th><th>Purchase and other</th></tr></thead><tbody>'
    for i, (label, _, _) in enumerate(ol.DUE):
        out += f'<tr><td>{esc(label)}</td>'
        for key in ol.SCHEDULES:
            value = schedules[key]["rows"][i]["value"] if schedules[key]["status"] == "Checked" else None
            out += f'<td>{amount(value)}</td>'
        out += '</tr>'
    out += '</tbody></table></div>'
    for key, schedule in schedules.items():
        if schedule["status"] != "Checked":
            out += f'<p>{esc(key.title())} schedule Unavailable: {esc(schedule["detail"])}</p>'
    out += (f'<p>The first row covers September 1, 2026–May 31, 2027. Another '
            f'{amount(v["not_commenced"])} of operating leases had not commenced. Commencement is expected '
            'in fiscal 2027–2029 with 15–19 year terms; this does not establish annual cash payments. '
            'Their payment timing is Unavailable, and they are not in the table.</p>'
            '<p class="lr-meta">No combined total of leases, purchase obligations, unpaid capex and borrowing is '
            'presented. Disclosed overlap and payment timing are insufficient. The historical May debt '
            'schedule below has not been used as an August payment schedule.</p>')
    out += '<h3>How much financing capacity is established?</h3>'
    out += revolver_html(snapshot, money)
    out += ('<p>The $20B gross ATM program was fully utilized in the quarter; it is not unused '
            'financing capacity. <a href="' + esc(of.QUARTER_SOURCE) +
            '" target="_blank" rel="noopener noreferrer">10-Q Note 7, pp. 13–14</a>.</p>')
    out += ('<p><strong>Repayment assessment:</strong> the quarter relied on identified customer prepayments '
            'and equity funding while capital spending exceeded OCF. A future repayment surplus or shortfall '
            'is Unavailable: remaining debt principal at August 31, current drawable credit and future '
            'operating cash generation have not been established. The two later saved 8-Ks checked below '
            'do not establish additional corporate borrowing.</p>')
    out += repayment_html(snapshot, money) + '</section>'
    # Streamlit's Markdown math parser otherwise consumes prose between currency signs.
    return out.replace("$", "&#36;")


def revolver_html(snapshot, money):
    import oracle_revolver
    audit = oracle_revolver.for_snapshot(snapshot)
    if not audit or audit["status"] != "Checked":
        return '<p>Revolver audit Unavailable: the checked saved evidence is required.</p>'
    out = '<p>' + esc(audit["conclusion"]) + '</p>'
    for row in audit["dates"]:
        source = audit["sources"][row["source"]]
        out += '<details><summary>' + esc(row["date"]) + ' · drawable capacity Unavailable</summary>'
        for key, label in [("commitment", "Committed amount"), ("drawn", "Outstanding advances"),
                           ("undrawn", "Undrawn commitment")]:
            out += (f'<div class="ol-obligation"><span>{label}</span>'
                    f'<strong>{esc(money(row[key],3))}</strong></div>')
        out += ('<p class="lr-meta">' + esc(row["detail"]) + ' ' + esc(row["compliance"]) +
                ' ' + esc(row["drawable_detail"]) + ' <a href="' + esc(source["source_url"]) +
                '" target="_blank" rel="noopener noreferrer">' + esc(source["form"] + ', filed ' +
                source["filed"] + ', ' + row["location"]) + '</a>.</p></details>')
    out += '<details><summary>Letters of credit, increase option and draw conditions</summary>'
    for term in audit["terms"]:
        out += ('<p class="lr-meta"><strong>' + esc(term["label"]) + ':</strong> ' +
                esc(term["detail"]) + ' <a href="' + esc(audit["sources"][term["source"]]["source_url"]) +
                '" target="_blank" rel="noopener noreferrer">' + esc(term["location"]) + '</a>.</p>')
    out += '</details><details><summary>Later saved filings and audit scope</summary>'
    for event in audit["later"]:
        out += '<p class="lr-meta"><strong>' + esc(event["date"]) + ':</strong> ' + esc(event["detail"])
        for key in event["sources"]:
            source = audit["sources"][key]
            out += ' <a href="' + esc(source["source_url"]) + '" target="_blank" rel="noopener noreferrer">' + esc(source["form"]) + '</a>'
        out += '.</p>'
    out += '<p class="lr-meta">' + esc(audit["scope"]) + '</p>'
    out += ('<p class="lr-meta"><a href="' + esc(audit["inventory"]["source_url"]) +
            '" target="_blank" rel="noopener noreferrer">SEC financing index through ' +
            esc(audit["inventory"]["through"]) + '</a> · index check ' + esc(audit["inventory"]["checked"]) +
            '. Indexing identifies candidate filings; the two document reviews establish their findings.</p>')
    return out + '</details>'


def repayment_html(snapshot, money):
    import oracle_repayment
    review = oracle_repayment.for_snapshot(snapshot)
    if not review or review["status"] != "Checked":
        return '<p>Repayment funding review Unavailable: the checked Oracle inputs are required.</p>'
    out = '<h3>Which resources could fund the dated payments?</h3>'
    out += '<p>Resources below retain their dates. They are not a combined available-liquidity total.</p>'
    for resource in review["resources"]:
        dates = resource["period_end"] if resource["period_start"] == resource["period_end"] else resource["period_start"] + ' to ' + resource["period_end"]
        out += (f'<div class="ol-resource"><div>{esc(resource["label"])}'
                f'<div class="lr-meta">{esc(dates)}</div></div><strong>{esc(money(resource["value"],3))}</strong>'
                f'<p class="lr-meta">{esc(resource["detail"])} '
                f'<a href="{esc(resource["source_url"])}" target="_blank" rel="noopener noreferrer">Source</a></p></div>')
    out += '<div class="ol-repayments">'
    for index, (label, start, end) in enumerate(ol.DUE):
        rows = review["obligations"][index*3:index*3+3]
        out += f'<details{" open" if index == 0 else ""}><summary>{esc(label)} · funding coverage Unavailable</summary>'
        out += f'<p class="lr-meta">{esc(start)} to {esc(end or "final date Unavailable")}. Lease payments include interest.</p>'
        for row in rows:
            out += (f'<div class="ol-obligation"><span>{esc(row["label"])}</span>'
                    f'<strong>{esc(money(row["value"],3))}</strong></div>'
                    f'<p class="lr-meta">{esc(row["competing_uses"])}</p>')
        out += (f'<p><strong>Potential funding:</strong> {esc(rows[0]["candidate_resources"])}</p>'
                f'<p class="lr-meta"><strong>Coverage Unavailable:</strong> {esc(rows[0]["coverage_detail"])}</p></details>')
    out += '</div><p>' + esc(review["conclusion"]) + '</p>'
    out += '<details><summary>Undated obligations and missing debt dates</summary>'
    for gap in review["gaps"]:
        out += f'<p><strong>{esc(gap["label"])}</strong>'
        if gap["value"] is not None:
            out += ' · ' + esc(money(gap["value"],3))
        out += '<br>' + esc(gap["detail"]) + '</p>'
    return out + '</details>'
