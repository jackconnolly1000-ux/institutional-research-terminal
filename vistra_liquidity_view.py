"""A dated repayment timeline and financing constraints for the checked Vistra filing."""
from html import escape as esc
import vistra_liquidity as vl
from vistra_liquidity_sources import Q, K

CSS = """
.vl-section {border-top:1px solid var(--border);padding:24px 0;}
.vl-facts {display:grid;grid-template-columns:1fr 1fr;gap:24px;margin:16px 0;}
.vl-table-wrap {overflow-x:auto;margin:16px 0;}
.vl-table {width:100%;border-collapse:collapse;font-size:.82rem;line-height:1.5;}
.vl-table th,.vl-table td {text-align:left;vertical-align:top;padding:10px 12px 10px 0;border-bottom:1px solid var(--border);}
.vl-table th {font-weight:600;color:var(--text-muted);}
.vl-table .vl-number {text-align:right;white-space:nowrap;}
.vl-timeline {margin:18px 0;}
.vl-payment {display:grid;grid-template-columns:105px 180px minmax(30px,1fr) 85px;gap:12px;align-items:center;padding:13px 0;border-bottom:1px solid var(--border);font-size:.82rem;}
.vl-payment .vl-date {color:var(--text-muted);}
.vl-payment-track {height:13px;background:var(--surface-raised);}
.vl-payment-bar {display:block;height:13px;background:var(--text-muted);}
.vl-section summary {cursor:pointer;font-size:.85rem;padding:8px 0;}
.vl-resource {display:grid;grid-template-columns:210px 100px minmax(0,1fr);gap:16px;padding:13px 0;border-bottom:1px solid var(--border);font-size:.84rem;line-height:1.55;}
.vl-resource p {margin:0;}
.vl-term {padding:10px 0;border-bottom:1px solid var(--border);}
@media(max-width:760px) {.vl-facts {grid-template-columns:1fr;gap:8px;} .vl-payment {grid-template-columns:95px 1fr 75px;gap:8px;} .vl-payment-track {grid-column:2;grid-row:2;} .vl-payment strong {grid-column:3;grid-row:1;} .vl-resource {display:block;} .vl-resource > strong {display:block;text-align:left;margin:4px 0;} .vl-resource p {margin-top:6px;} }
"""


def render(snapshot, money):
    review=vl.for_snapshot(snapshot)
    if review is None: return ''
    out='<section class="vl-section"><h3>How does Vistra fund its repayments?</h3>'
    if review['status']!='Checked':
        return out+'<p>Unavailable: '+esc(review['detail'])+'</p></section>'
    f=review['inputs']; v=lambda k:f[k]['value']
    amount=lambda x:'$0' if x==0 else money(x,3)
    c=review['cash']
    out+=(f'<p class="lr-meta">Cash flows: Jan 1–Jun 30, 2026 · balance sheet and capacity: Jun 30, 2026 · '
          f'<a href="{Q}" target="_blank" rel="noopener noreferrer">10-Q filed Aug 10, pp. 2, 4–5, 20–28 and 68–69</a>'
          ' · review checked Oct 15, 2026</p>')
    out+=(f'<p>First-half operating cash flow less capital spending was <strong>{amount(c["fcf"])}</strong>. '
          f'Buybacks and common/preferred dividends used <strong>{amount(c["distributions"])}</strong>, '
          f'exceeding that amount by {amount(c["distributions"]-c["fcf"])} before the other cash flows below.</p>')
    out+='<div class="vl-facts"><div><table class="vl-table"><thead><tr><th>Jan–Jun cash flow</th><th class="vl-number">USD (B or M)</th></tr></thead><tbody>'
    for name,value in [('Operating cash flow',v('ocf')),('Capital spending',-v('capex')),
                       ('After capital spending',c['fcf']),('Buybacks and dividends',-c['distributions']),
                       ('Net debt cash flow',c['net_debt_cash']),('Other investing',c['other_investing']),
                       ('Fees, withholding, Nuveen principal and other financing',-v('fees')-v('withholding')-v('nuveen_principal_paid')+v('other_financing')),
                       ('Change including restricted cash',v('change'))]:
        out+=f'<tr><td>{esc(name)}</td><td class="vl-number">{esc(amount(value))}</td></tr>'
    out+='</tbody></table></div><div>'
    out+=(f'<p>Cash including restricted balances fell from {amount(v("opening_total"))} to {amount(v("closing_total"))}. '
          f'The ending total includes {amount(c["restricted"])} restricted cash '
          f'({amount(v("restricted_current"))} current and {amount(v("restricted_noncurrent"))} noncurrent), '
          f'leaving {amount(v("cash"))} cash and equivalents on the balance sheet.</p>')
    out+=(f'<p>Debt issuance cash proceeds of {amount(v("debt_issued"))} supported refinancing during the half. '
          'They are financing inflows, separate from operating cash generation. The net debt cash-flow row also includes revolver, commodity-linked and receivables activity.</p>')
    out+='<p class="lr-meta">Capital spending includes nuclear fuel and LTSA prepayments. OCF includes working capital and commodity margin movements. Cash flows are seasonal and tend to be weighted toward the second half; no recurring run rate or forecast is inferred.</p></div></div>'
    out+='<details><summary>Cash-flow inputs and reconciliation</summary>'
    for k in [*vl.INVESTING,*vl.FINANCING]:
        out+=f'<div class="lr-row"><span>{esc(f[k]["label"])}</span><strong>{esc(amount(v(k)*vl.FLOWS[k][2]))}</strong></div>'
    out+='<p class="lr-meta">Trust-security sales and purchases are retained as separate reported flows, not treated as gross cash available for corporate debt. Nuveen principal paid was $19M in financing. The additional $19M interest described in Note 12 is not deducted again from OCF.</p></details>'
    out+='<h3 style="margin-top:24px">Which payments have disclosed dates?</h3>'
    out+='<p class="lr-meta">Selected June 30 balances and payment terms · USD millions · 10-Q Note 12 pp. 21–28. Bars compare the listed amounts; they do not show a complete repayment schedule.</p><div class="vl-timeline">'
    maximum=max((p['value'] for p in review['payments'] if p['value'] is not None),default=1) or 1
    dates=['Dec 3, 2026','Dec 2026','Dec 30, 2026','Dec 31, 2026','Jan 30, 2027','Jul 31, 2027']
    for p,day in zip(review['payments'],dates):
        width=p['value']/maximum*100 if p['value'] is not None else 0
        out+=(f'<div class="vl-payment"><span class="vl-date">{day}</span><span>{esc(p["label"])}</span>'
              f'<div class="vl-payment-track" aria-hidden="true"><span class="vl-payment-bar" style="width:{width:.4f}%"></span></div>'
              f'<strong class="lr-bar-value">{("$"+format(p["value"]/1_000_000,",.0f")+"M") if p["value"] is not None else "Unavailable"}</strong></div>')
    out+='</div><p>Pulaski’s construction loan may convert to a term loan only after commercial operation and other conditions. Its $297M is not assumed to be refinanced. Vistra guarantees the $261M bridge repayment.</p>'
    out+='<p>Nuveen’s $631M includes principal and interest. Its $613M carrying liability describes the same obligation. The senior-note amounts are principal only; coupon interest is additional.</p>'
    out+='<details><summary>Other commitments and the historical annual schedule</summary>'
    for k,text in [('cogentrix','expected cash consideration at Cogentrix closing, anticipated in late 2026 subject to conditions and adjustments; exact payment date and completion Unavailable'),
                   ('helix_initial','initial Helix commitment remains callable at June 30; call dates and amount funded to date Unavailable'),
                   ('helix_additional','additional Helix commitment; milestones had not occurred at June 30 and Vistra may elect to invest regardless')]:
        out+=f'<p><strong>{esc(amount(v(k)))}</strong> {text}.</p>'
    out+='<p class="lr-meta">Cogentrix also contemplates debt assumption and shares; those are not added to its expected cash payment. Helix is not assigned an invented payment date.</p>'
    if review['annual']:
        out+=f'<p><a href="{K}" target="_blank" rel="noopener noreferrer">10-K annual schedule at Dec 31, 2025</a>: '
        out+='; '.join(f'{2026+i if i<5 else "thereafter"}: {esc(amount(v("annual_"+str(i))))}' for i in range(6))+'.</p>'
        out+=f'<p class="lr-meta">{esc(review["annual"]["detail"])} Principal {amount(review["annual"]["principal"])} less {amount(v("annual_costs"))} costs reconciles to {amount(v("annual_carrying"))} carrying debt at December 31.</p>'
    else: out+='<p>Annual maturity reconciliation: Unavailable.</p>'
    out+='</details><h3 style="margin-top:24px">Which resources can support those obligations?</h3>'
    if review['capacity']:
        out+=f'<p>Reported June 30 liquidity was <strong>{amount(review["capacity"]["reported_liquidity"])}</strong>: '
        out+=f'{amount(v("cash"))} cash, {amount(v("revolver_available"))} revolver availability and {amount(v("commodity_available"))} commodity-linked availability. These figures are not cash all held at Parent or capacity verified for a later draw.</p>'
    else: out+='<p>Facility-capacity reconciliation: Unavailable.</p>'
    out+='<div class="lr-meta">Amounts below are reported available capacity at June 30, 2026. Current drawable amounts are Unavailable.</div>'
    out+='<p>Vistra Operations’ cash and permitted corporate borrowing are potential sources for its notes and acquisitions. Nuveen and Helix funding depends on cash reaching the obligated entity; transferable amounts are Unavailable. Project cash flows service project debt, with Vistra’s bridge guarantee providing separate recourse.</p>'
    for r in review['resources']:
        out+=(f'<div class="vl-resource"><div><strong>{esc(r["label"])}</strong><br><span class="lr-meta">{esc(r["borrower"])}</span></div>'
              f'<strong class="lr-bar-value">{esc(amount(r["available"]))}</strong><p>{esc(r["detail"])}</p></div>')
    out+='<p>Revolver availability already deducts $1.092B of letters of credit from the $5.5B limit. Commodity-linked availability is $1.452B against a $1.75B limit because its borrowing base is lower. Neither limit is unused cash.</p>'
    out+='<details><summary>Contract conditions, project recourse and collateral</summary>'
    for t in review['terms']:
        out+=f'<div class="vl-term"><p><strong>{esc(t["name"])}</strong></p><p>{esc(t["detail"])}</p><a class="lr-meta" href="{esc(t["source_url"])}" target="_blank" rel="noopener noreferrer">{esc(t["location"])} · filed {esc(t["filed"])}</a></div>'
    if review['debt']:
        out+='<p>Project debt of $1.633B is already inside $19.764B long-term principal and the $19.895B baseline carrying borrowing total. It is not added again.</p>'
    for note in review['limits'][3:6]: out+=f'<p class="lr-meta">{esc(note)}</p>'
    out+='</details><h3 style="margin-top:24px">What changed after June 30?</h3>'
    for e in review['events']:
        if e['accession'] not in ['0001140361-26-028619','0001140361-26-037577','0001140361-26-038468']: continue
        out+=(f'<article class="lr-event"><div class="lr-meta">Event {esc(e["event_date"])}<br>Filed {esc(e["filed"])}</div>'
              f'<div><p><strong>{esc(e["kind"])}</strong></p><p>{esc(e["finding"])}</p>'
              f'<a class="lr-meta" href="{esc(e["source_url"])}" target="_blank" rel="noopener noreferrer">8-K · {esc(e["accession"])}</a></div></article>')
    out+='<p>The final prospectus estimated $1.48B net proceeds and intended possible preferred-stock redemption. Actual net cash retained and completed redemptions are Unavailable. No September proceeds are added to June cash.</p>'
    out+=f'<p class="lr-meta">{esc(review["inventory"]["detail"])}</p>'
    out+='<h3 style="margin-top:24px">Repayment assessment</h3><p>The checked first half produced $650M after reported capital spending, while buybacks and dividends used $959M. Facility access, collateral needs, the pending acquisition and dated repayments must therefore be assessed together. These historical figures do not establish a future funding surplus or shortfall.</p>'
    out+='<p class="lr-meta">Unavailable: current drawable credit, covenant headroom, Parent-accessible cash, Helix call dates, project conversion completion, remaining full June debt-service schedule and future cash generation. No combined obligations total or cash runway is presented.</p></section>'
    return out.replace('$','&#36;')
