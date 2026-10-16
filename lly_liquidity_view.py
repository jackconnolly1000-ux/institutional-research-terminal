"""Lilly funding review from one shared, dated evidence model; no network or AI."""
import lly_liquidity as ll
from ui import esc


def render(snapshot, money):
    if snapshot["ticker"] != "LLY":
        return ""
    r = ll.for_snapshot(snapshot)
    if r is None:
        return '<section class="lr-maturity"><h3>Lilly repayment review</h3><p>Unavailable: the saved review does not match this balance sheet.</p></section>'
    f = r["inputs"]
    amount = lambda v: esc(money(v, 3))
    source = lambda key, location: ('<a href="' + esc(r["sources"][key]["source_url"]) +
                                   '" target="_blank" rel="noopener noreferrer">' + esc(location) + '</a>')
    out = '<section class="lr-maturity"><h3>What funded Lilly’s cash balance?</h3>'
    out += '<p class="lr-meta">January–June 2026 · USD billions · ' + source("quarter", "10-Q cash flows p. 8") + ' · reviewed October 15, 2026</p>'
    c = r["cash"]
    if c is None:
        out += '<p>Cash reconciliation Unavailable: ' + esc(r["cash_detail"]) + '</p>'
    else:
        out += (f'<p>Operating cash flow less cash PP&amp;E spending was {amount(c["ocf_less_capex"])}. '
                f'Cash acquisitions and purchased in-process R&amp;D used {amount(c["acquisitions_iprd"])}; '
                f'dividends and buybacks used another {amount(c["payouts"])}. Net borrowing contributed '
                f'{amount(c["net_borrowing"])}. Cash growth therefore does not establish a future repayment surplus.</p>')
        out += '<div class="ol-balances">'
        for label, key in [("December 31 cash", "opening"), ("Half-year increase", "change"), ("June 30 cash", "closing")]:
            out += f'<div><span>{label}</span><strong>{amount(f[key]["value"])}</strong></div>'
        out += '</div><p><strong>Which half-year flows added to or used cash?</strong></p>'
        steps = [("Operating cash flow", f["ocf"]["value"]), ("Cash PP&E spending", -f["capex"]["value"]),
                 ("Acquisitions and purchased IPR&D", -c["acquisitions_iprd"]),
                 ("Dividends and buybacks", -c["payouts"]), ("Net borrowing", c["net_borrowing"]), ("Other cash flows, net", c["other"])]
        out += ('<div class="ol-bridge" role="figure" aria-label="Lilly half-year cash changes, uses left and sources right">'
                '<div class="ol-axis"><span>January–June 2026</span><div class="ol-axis-scale">'
                '<span>−$20B · used</span><span>0</span><span>added · +$20B</span></div><span>USD</span></div>')
        for label, value in steps:
            bar = f'<span class="ol-fill" style="width:{abs(value)/20_000_000_000*100:.4f}%"></span>'
            out += (f'<div class="ol-step"><span>{esc(label)}</span><div class="ol-track" aria-hidden="true">'
                    f'<div class="ol-side">{bar if value < 0 else ""}</div><div class="ol-side">{bar if value > 0 else ""}</div>'
                    f'</div><strong>{"+" if value > 0 else ""}{amount(value)}</strong></div>')
        out += ('</div><p class="lr-meta">The six signed flows sum to the $1.682B increase. Net borrowing is '
                '$5.284B short-term inflow + $8.941B net long-term proceeds − $1.623B repayments. Other flows '
                'are investment purchases, other investing and financing, and FX. The approximately $13.3B '
                'business-development disclosure describes the acquisition/IPR&amp;D spending already counted. '
                'May’s $9B debt issue is already in proceeds and is not unused financing.</p>')
    out += '<h3>Which resources can fund future payments?</h3>'
    resources = [("June 30 cash and equivalents", f["closing"]["value"], "quarter", "Balance sheet p. 7",
                  "Excludes restricted cash. A dated balance, not cash available today or earmarked for any particular repayment."),
                 ("Historical January–June operating cash flow", f["ocf"]["value"], "quarter", "Cash flows p. 8",
                  "Already reflected in June cash after other flows. Includes working-capital movements; future recurrence is not established. Do not add to June cash again.")]
    d = {x["key"]: x for x in r["disclosures"]}
    if "unused_june" in d:
        resources.append(("June 30 unused committed facilities", d["unused_june"]["value"], "quarter", "MD&A p. 31", d["unused_june"]["detail"]))
    for label, value, key, location, detail in resources:
        out += (f'<div class="ol-resource"><div>{esc(label)}</div><strong>{amount(value)}</strong>'
                f'<p class="lr-meta">{esc(detail)} {source(key, location)}</p></div>')
    out += ('<p><strong>Drawable credit: Unavailable.</strong> No credit agreement or renewal of the August 2026 '
            'facility is in this saved source set. Draw conditions, covenants, permitted uses and post-expiry '
            'availability are not established. Cash and unused commitments are not added into an available-liquidity total.</p>')
    out += '<div class="ol-table-wrap"><table class="ol-table"><thead><tr><th>Facility term reported at December 31, 2025</th><th>Commitment</th><th>Expiry</th></tr></thead><tbody>'
    for key, date in [("facility_2026", "August 2026"), ("facility_2029", "December 2029")]:
        out += f'<tr><td>{esc(f[key]["label"])}</td><td>{amount(f[key]["value"])}</td><td>{date}; exact day Unavailable</td></tr>'
    out += ('</tbody></table></div><p class="lr-meta">' + source("annual", "10-K Note 11 p. 76; MD&A p. 51") +
            '. These are the principal facilities described in the annual report, not a June facility-by-facility roll-forward. '
            'The annual unused total is $10.1B, including $10B supporting CP. The remaining $0.1B is not separately described.</p>')
    out += '<h3>What acquisitions and manufacturing payments compete for cash?</h3>'
    out += '<p>Amounts below retain their own dates and conditions. They are not a combined cash requirement.</p>'
    for row in r["disclosures"]:
        if row["key"] in {"unused_june", "cp_support"}:
            continue
        coverage_note = ("Historical cash use; no future coverage calculation applies." if row["key"] == "july_paid" else
                         "Funding coverage Unavailable: payment timing, future cash and drawable financing are not all established.")
        out += (f'<details><summary>{esc(row["label"])} · {amount(row["value"])}</summary>'
                f'<p class="lr-meta">{esc(row["period_end"])} · {esc(row["kind"])}</p>'
                f'<p>{esc(row["detail"])}</p><p class="lr-meta"><a href="{esc(row["source_url"])}" target="_blank" rel="noopener noreferrer">'
                f'{esc(row["form"] + " " + row["location"])}</a> · {esc(coverage_note)}</p></details>')
    contingent = [f[k]["value"] for k in ["contingent_current", "contingent_noncurrent"]]
    total = sum(contingent) if all(v is not None for v in contingent) else None
    out += (f'<p>Contingent-consideration fair value: {amount(total)} at June 30 '
            f'({amount(contingent[0])} current + {amount(contingent[1])} noncurrent). '
            'This is a valuation, not a dated payout schedule or milestone ceiling. It is not added to the '
            'acquisition amounts above. ' + source("quarter", "10-Q Note 8 p. 17") + '.</p>')
    out += financing_html(snapshot, money)
    out += '<h3>When do the notes come due?</h3>'
    out += ('<p>Historical notes grouped by due year at <strong>December 31, 2025</strong>. '
            'These are carrying amounts, not principal repayment amounts. Multi-year groups are combined. '
            'The June 30 repayment schedule is Unavailable; May issuance and half-year repayments are not allocated to these buckets.</p>')
    if r["notes_schedule"]:
        out += '<div class="ol-table-wrap"><table class="ol-table"><thead><tr><th>Due year(s)</th><th>Historical carrying amount</th></tr></thead><tbody>'
        for label, member in ll.NOTE_MEMBERS:
            out += f'<tr><td>{esc(label)}</td><td>{amount(f["notes_"+member]["value"])}</td></tr>'
        out += ('</tbody></table></div><p class="lr-meta">' + source("annual", "10-K Note 11 p. 76") +
                '. $42.842B notes − $339M other debt/adjustments + reported zero commercial paper = $42.503B total debt. '
                'The adjustment’s XBRL fact is positive; the printed table presents it as a deduction. '
                'June current borrowing of $7.050B is a balance-sheet classification, not an instrument-level dated payment schedule.</p>')
    else:
        out += '<p>Historical notes table Unavailable: ' + esc(r["notes_detail"]) + '</p>'
    out += ('<p><strong>Repayment conclusion:</strong> H1 operations generated cash after PP&amp;E spending, '
            'but acquisitions and shareholder payouts competed for that cash, and net borrowing contributed materially. '
            'Future coverage is Unavailable. The immediate evidence gaps are the updated debt payment schedule, '
            'facility terms and renewal, and acquisition/manufacturing payment dates.</p>')
    out += '<details><summary>Lilly review evidence and scope</summary><p class="lr-meta">'
    out += ('FY2025 10-K, June 2026 10-Q and August 5 earnings exhibit, plus the financing documents checked above. '
            'The SEC index was screened through October 15, 2026 for financing filings; this is not a complete review of all liability notes. '
            'Every new numeric input, exact period, context/dimension and reviewed-text source is recorded in the Lilly Excel Data sheet. '
            'Text disclosures are explicitly separated from inline facts. No forecast or investment rating.</p></details></section>')
    return out.replace("$", "&#36;")


def financing_html(snapshot, money):
    import lly_financing as lf
    audit = lf.for_snapshot(snapshot)
    if not audit or audit["status"] != "Checked":
        return '<h3>May debt terms</h3><p>Unavailable: the checked financing evidence is required.</p>'
    source = lambda key, label: ('<a href="' + esc(audit["sources"][key]["url"]) +
                                 '" target="_blank" rel="noopener noreferrer">' + esc(label) + '</a>')
    out = '<h3>Which May debt maturities are documented?</h3><p>' + esc(audit["conclusion"]) + '</p>'
    out += '<p class="lr-meta">Completed May 20, 2026 · initial principal, USD billions · '
    out += source("offering", "8-K Item 8.01") + '; ' + source("fixed", "Exhibit 4.3") + '; ' + source("floating", "Exhibit 4.4") + '</p>'
    out += '<div class="ol-table-wrap"><table class="ol-table"><thead><tr><th>Series</th><th>Initial principal</th><th>Stated maturity</th><th>Contract rate</th></tr></thead><tbody>'
    for row in audit["rows"]:
        rate = (f'{row["coupon"]:.3%}' if row["coupon"] is not None else
                f'Compounded SOFR + {row["sofr_margin"]:.3%}')
        out += (f'<tr><td>{esc(row["label"])}</td><td>{esc(money(row["initial_principal"],3))}</td>'
                f'<td>{esc(row["stated_maturity"])}</td><td>{esc(rate)}</td></tr>')
    out += '</tbody></table></div><p class="lr-meta">' + esc(audit["date_detail"]) + '</p>'
    out += ('<p><strong>No extra cash or debt is added:</strong> the issue is already reflected in June borrowing '
            'and H1 proceeds. Current outstanding principal by series is Unavailable. The table does not replace '
            'the missing full June repayment schedule; future coverage remains Unavailable.</p>')
    out += '<details><summary>Coupon conflict, early redemption and debt delisting</summary>'
    out += '<p>' + esc(audit["coupon_conflict"]) + ' ' + source("prospectus", "Final prospectus") + '.</p>'
    out += '<p>' + esc(audit["redemption_detail"]) + ' ' + source("fixed", "Fixed-note terms") + '; ' + source("floating", "Floating-note terms")
    out += '; <a href="' + esc(ll.SOURCES["quarter"]["source_url"]) + '" target="_blank" rel="noopener noreferrer">June 10-Q Note 4</a>.</p>'
    out += '<p>' + esc(audit["delisting_detail"]) + ' ' + source("delisting", "Form 25") + '.</p></details>'
    out += '<details><summary>SEC financing check through October 15, 2026</summary>'
    out += '<p>' + esc(audit["inventory_detail"]) + ' <a href="' + esc(audit["inventory"]["source_url"]) + '" target="_blank" rel="noopener noreferrer">SEC submissions index</a>.</p>'
    out += '<p>' + esc(audit["credit_detail"]) + ' ' + source("renewal_2025", "September 2025 10-Q, Note 7") + '.</p>'
    return out + '</details>'
