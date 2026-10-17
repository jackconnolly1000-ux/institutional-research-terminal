"""Oracle's dated borrowing principal at August 31, 2026, for the company review (model: oracle_principal.py)."""
from datetime import date

from ui import esc


def render(snapshot, money):
    """Oracle's August 31 principal by instrument and date; commercial paper stays Unavailable.

    Shown directly under the dated lease and purchase payments, so everything due soon reads in one place."""
    import oracle_principal as op
    from oracle_principal import percent
    cash = snapshot.get("metrics", {}).get("cash", {})
    if (snapshot.get("ticker"), cash.get("accession"), cash.get("period_end")) != ("ORCL", op.QUARTERLY["accession"], op.ANCHOR):
        return ""
    review = op.load()
    output = '<section class="lr-maturity"><h3>Which borrowing principal is due after August 31?</h3>'
    if review is None:
        return output + '<p>Unavailable: the saved principal calendar is missing or its checks do not agree.</p></section>'
    rec, near = review["reconciliation"], review["next_twelve_months"]
    link = lambda doc, text: f'<a href="{esc(doc["source_url"])}" target="_blank" rel="noopener noreferrer">{esc(text)}</a>'
    tl = review["term_loan"]
    output += (f'<p class="lr-meta">At August 31, 2026 · principal, excluding interest · instruments from the '
               f'{link(review["annual"], "10-K debt table, Note 6, pp. 83–84")}, carried forward with the '
               f'{link(review["quarter"], "August 10-Q")} · checked {esc(review["checked_as_of"])}</p>')
    installments = sum(s["amount"] for s in tl["installments"] if op.ANCHOR < s["date"] <= near["end"])
    output += (f'<p class="lr-answer">{esc(money(near["principal"], 3))} of senior-note and term-loan principal falls due '
               f'from September 2026 through August 2027: {esc(money(2_250_000_000, 3))} of notes on April 1, 2027, and the '
               f'term loan’s {esc(money(installments, 3))} of installments and {esc(money(tl["final"]["amount"], 3))} remainder on '
               'August 16, 2027. Commercial paper is not included: its August balance and maturity dates are not reported.</p>')
    output += '<div class="lr-grid"><div><h4>Next twelve months</h4><div class="ol-table-wrap"><table class="ol-table">'
    output += '<thead><tr><th>Due</th><th>Instrument</th><th>Principal</th></tr></thead><tbody>'
    for row in near["rows"]:
        day = date.fromisoformat(row["date"])
        # Installments are 2.50% of $5,630M, $140.75M each: shown exactly, since rounding hides that they sum to $563M
        amount = (f'${row["amount"] / 1_000_000:,.2f}M' if row["amount"] % 1_000_000 else money(row["amount"], 3))
        label = "Term loan installment" if row["label"].startswith("Term loan, scheduled") else row["label"]
        output += (f'<tr><td>{esc(f"{day:%b} {day.day}, {day:%Y}")}</td><td>{esc(label)}</td>'
                   f'<td>{esc(amount)}</td></tr>')
    output += (f'<tr><td>No dates disclosed</td><td>Commercial paper</td><td>Unavailable</td></tr></tbody></table></div>'
               '<p class="lr-meta">Term-loan installments are 2.50% of the $5.630B borrowed, calculated from its stated amortization. They assume no prepayment and are '
               'not separately reported. Oracle may extend the August 16, 2027 date by up to two years.</p></div>')
    output += '<div><h4>By fiscal year</h4><div class="ol-table-wrap"><table class="ol-table">'
    output += '<thead><tr><th>Fiscal year</th><th>Period</th><th>Principal</th></tr></thead><tbody>'
    for bucket in review["calendar"]:
        nice = lambda iso: (lambda d: f"{d:%b} {d.day}, {d:%Y}")(date.fromisoformat(iso))
        period = (f'{nice(bucket["start"])} – {nice(bucket["end"])}' if bucket["end"] else f'From {nice(bucket["start"])}')
        output += f'<tr><td>{esc(bucket["label"])}</td><td>{esc(period)}</td><td>{esc(money(bucket["principal"], 3))}</td></tr>'
    output += (f'<tr><td>Total</td><td>Excludes commercial paper</td><td>{esc(money(rec["known_principal_excluding_cp"], 3))}</td></tr>'
               '</tbody></table></div><p class="lr-meta">FY2028 includes the term-loan remainder. Only fiscal 2027 differs from '
               'the May 31 schedule: the July 2026 notes and the June 30 installment fell due before August 31, and '
               'commercial paper is no longer counted.</p></div></div>')
    lo, hi = rec["commercial_paper_range"]
    dlo, dhi = rec["implied_discount_range"]
    output += '<details><summary>How principal reconciles to reported borrowing</summary>'
    output += (f'<p><strong>Principal versus carrying value.</strong> The August balance sheet reports '
               f'{esc(money(rec["carrying_reported"], 3))} of borrowing at carrying value ({esc(money(rec["current_reported"], 3))} '
               f'current, {esc(money(rec["noncurrent_reported"], 3))} noncurrent). Carrying value is principal less unamortized '
               'discounts and issuance costs. At May 31 those were $564M: $130.105B principal less $564M equals $129.541B '
               'carrying debt.</p>')
    output += (f'<p><strong>Long-term borrowing.</strong> Senior-note and term-loan principal of '
               f'{esc(money(rec["known_principal_excluding_cp"], 3))} compares with long-term carrying value the 10-Q reports '
               f'as $125.0B, rounded to $0.1B (Note 2, p. 9). The implied August discount and issuance costs are '
               f'{esc(money(dlo))}–{esc(money(dhi))}, consistent with $564M at May 31 less amortization. They are not '
               'reported at August 31, so no exact figure is shown.</p>')
    output += (f'<p><strong>Commercial paper.</strong> $1.468B at May 31, with no maturity dates disclosed. Total carrying '
               f'borrowing less the rounded long-term figure leaves about {esc(money(lo))}–{esc(money(hi))} at August 31. '
               'That range rests on a rounded fact, so the August balance is Unavailable.</p>')
    note = review["matured"][0]
    output += (f'<p><strong>June–August repayments.</strong> The July 2026 notes ({esc(money(note["principal_may_31"], 3))}, '
               f'{esc(percent(note["stated_rate"]))}%) matured on July 15, 2026, '
               f'and the term loan’s June 30 installment was scheduled at $70.4M. Together, '
               f'{esc(money(rec["scheduled_principal_quarter"], 3))} agrees with MD&A’s “$3.1 billion … scheduled repayments of '
               f'debt”. The cash-flow line groups {esc(money(rec["repayments_quarter"], 3))} of note, term-loan and other '
               'repayments. MD&A separately describes about $1.1B of commercial-paper repayment, while the commercial-paper '
               'row is a reported zero. The 10-Q does not assign the grouped line to instruments, so it is not subtracted '
               'from any balance.</p>')
    output += ('<p class="lr-meta">No borrowing proceeds are reported for the quarter. MD&A’s $4.6B of long-term borrowing '
               'reclassified to current agrees with the term loan’s June 2027 installment and remainder entering the '
               'twelve-month window. A principal calendar is not funding coverage and does not establish drawable credit.</p>')
    output += f'<p class="lr-meta">Sources: {link(review["annual"], "10-K Note 6, pp. 83–86")} · {link(review["quarter"], "10-Q pp. 1, 5, 9 and 33")}</p></details>'
    output += f'<details><summary>All {len(review["remaining"])} instruments outstanding at August 31</summary>'
    output += '<div class="ol-table-wrap"><table class="ol-table"><thead><tr><th>Instrument</th><th>Maturity</th><th>Principal</th><th>Basis</th></tr></thead><tbody>'
    for row in review["remaining"]:
        value = "Unavailable" if row["principal_aug_31"] is None else money(row["principal_aug_31"], 3)
        output += (f'<tr><td>{esc(row["label"])}</td><td>{esc(row["maturity"] or "Not disclosed")}</td>'
                   f'<td>{esc(value)}</td><td>{esc(row["status"])}</td></tr>')
    output += '</tbody></table></div></details></section>'
    return output
