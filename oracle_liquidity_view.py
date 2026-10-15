"""A dated Oracle funding explanation; no ratings or inferred repayment forecast."""
from ui import esc
import oracle_liquidity as ol
import oracle_financing as of

CSS = """
.ol-bridge {margin:18px 0 10px;}
.ol-step {display:grid;grid-template-columns:170px minmax(50px,1fr) 95px;gap:12px;align-items:center;margin:14px 0;font-size:.82rem;}
.ol-track {height:16px;position:relative;border-left:1px solid var(--border-strong);border-right:1px solid var(--border);}
.ol-float {position:absolute;top:2px;height:12px;background:var(--text-muted);min-width:1px;}
.ol-total {background:var(--text-strong);}
.ol-step strong {text-align:right;white-space:nowrap;font-weight:600;}
.ol-table-wrap {overflow-x:auto;margin:12px 0;}
.ol-table {width:100%;border-collapse:collapse;font-size:.8rem;}
.ol-table th,.ol-table td {padding:10px 8px;border-bottom:1px solid var(--border);text-align:right;vertical-align:top;}
.ol-table th:first-child,.ol-table td:first-child {text-align:left;}
.ol-table th {font-weight:600;}
@media(max-width:760px) {.ol-step {grid-template-columns:125px minmax(40px,1fr) 83px;gap:7px;font-size:.75rem;} .ol-table th,.ol-table td {padding:9px 5px;font-size:.72rem;}}
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
    steps = [("Opening cash, May 31", v["opening_total"], True),
             ("OCF less identified prepayments", c["ocf_less_prepay"], False),
             ("Customer prepayments", v["prepay"], False),
             ("Equity proceeds, net", v["equity"], False),
             ("Cash capital spending", -v["capex"], False),
             ("Debt repayments", -v["debt_repayments"], False),
             ("Other cash flows, net", c["other_net"], False),
             ("Closing cash, August 31", v["closing_total"], True)]
    positions, previous = [], 0
    for label, value, total in steps:
        start, end = (0, value) if total else (previous, previous + value)
        positions.append((label, value, total, start, end))
        previous = end
    maximum = max(max(start, end) for _, _, _, start, end in positions) or 1
    out += '<div class="ol-bridge" role="figure" aria-label="Quarter cash reconciliation including restricted cash">'
    for label, value, total, start, end in positions:
        shown = ("+" if value > 0 and not total else "") + money(value, 3)
        out += (f'<div class="ol-step"><span>{esc(label)}</span><div class="ol-track" aria-hidden="true">'
                f'<span class="ol-float {"ol-total" if total else ""}" '
                f'style="left:{min(start,end)/maximum*100:.4f}%;width:{abs(end-start)/maximum*100:.4f}%" '
                f'title="Cash after this row: {amount(end)}"></span></div><strong>{esc(shown)}</strong></div>')
    out += ('</div><p class="lr-meta">Floating bars start where the previous row ended. Opening and closing '
            'totals include restricted cash. Prepayments are separated from OCF once, not added to reported OCF.</p>')
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
    out += ('<p>The March 6 agreement establishes a $10B revolver, originally maturing March 6, 2031. '
            'The May 31 10-K reports zero drawn and covenant compliance then. August drawable capacity and '
            'covenant headroom are <strong>Unavailable</strong>. The $20B gross ATM program was fully utilized '
            'in the quarter; it is not unused financing capacity.</p>')
    out += ('<details><summary>Draw conditions and covenant definition</summary><p class="lr-meta">'
            'Draws require accurate representations and no default. Commitments can change or terminate, '
            'and extensions require lender consent and conditions. Contract EBITDA has specified addbacks '
            'and exclusions. Net cash interest includes finance-lease interest and specified swap costs, '
            'less cash interest income. A generic operating-income/interest ratio does not establish compliance. '
            f'<a href="{esc(ol.CREDIT_URL)}" target="_blank" rel="noopener noreferrer">March 6 credit agreement, '
            '§§1.01, 2.01, 2.06, 4.02, 6.02(c)</a>. The covenant minimum is 3.0x under the contract definitions. '
            'Commercial-paper program capacity is not added to revolver capacity. '
            f'<a href="{esc(of.QUARTER_SOURCE)}" target="_blank" rel="noopener noreferrer">ATM use: 10-Q Note 7, pp. 13–14</a>.</p></details>')
    out += ('<p><strong>Repayment assessment:</strong> the quarter relied on identified customer prepayments '
            'and equity funding while capital spending exceeded OCF. A future repayment surplus or shortfall '
            'is Unavailable: remaining debt principal at August 31, current drawable credit and future '
            'operating cash generation have not been established. The two later saved 8-Ks checked below '
            'do not establish additional corporate borrowing.</p></section>')
    # Streamlit's Markdown math parser otherwise consumes prose between currency signs.
    return out.replace("$", "&#36;")
