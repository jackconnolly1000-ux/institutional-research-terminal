"""Dated presentation of checked borrowing and lease evidence; no new debt calculation."""
import hashlib
import json
from pathlib import Path

SAMPLE = Path(__file__).parent / "samples/borrowing_leases.json"
LABELS = {
    "us-gaap:DebtCurrent": "Current borrowing",
    "us-gaap:LongTermDebtNoncurrent": "Noncurrent borrowing",
    "us-gaap:NotesPayableCurrent": "Current borrowing",
    "us-gaap:LongTermNotesAndLoans": "Noncurrent borrowing",
    "us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent": "Long-term debt, current portion",
    "us-gaap:LongTermDebtAndCapitalLeaseObligations": "Long-term debt, noncurrent",
    "us-gaap:ShortTermBorrowings": "Short-term borrowings",
    "vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed": "Accounts receivable financing",
}
LOCATIONS = {"LLY": "10-Q balance sheet, p. 7", "ORCL": "10-Q balance sheet, p. 1",
             "VST": "10-Q balance sheet, p. 2; Note 12, p. 20"}
BORROWING_NOTES = {
    "LLY": "Current borrowing includes short-term borrowings and current maturities. The Note 8 fair-value carrying amounts describe the same debt and are not added.",
    "ORCL": "The 10-Q does not split these borrowing lines by instrument. Commercial paper and the capex-financing balance remain Unavailable. The rounded $125.0B disclosure is not added.",
    "VST": "Project-level debt is already included in long-term debt. Nuveen's purchase obligation and affiliate margin-deposit financing remain separate. Note 12's debt itemization contains no lease line.",
}


def fingerprint():
    return hashlib.sha256(Path(__file__).read_bytes() + SAMPLE.read_bytes()).hexdigest()


def build(snapshot, evidence=None):
    """Keep older lease dates; refuse missing or inconsistent evidence instead of guessing."""
    ticker = snapshot["ticker"]
    checked = (evidence if evidence is not None else json.loads(SAMPLE.read_text()))["companies"][ticker]
    debt = snapshot["metrics"]["gross_debt"]
    anchor = snapshot["metrics"]["cash"]
    if (anchor["accession"], anchor["period_end"]) != (checked["anchor_accession"], checked["anchor_date"]):
        raise ValueError("Borrowing and lease presentation was checked for a different filing")
    borrowing = []
    for f in debt["inputs"]:
        if (f["accession"], f["period_end"], f["unit"]) != (anchor["accession"], anchor["period_end"], "USD"):
            raise ValueError("Borrowing components do not share the checked filing and date")
        borrowing.append({**f, "filing_label": f["label"], "label": LABELS[f["tag"]], "location": LOCATIONS[ticker],
                          "source_url": snapshot["source_url"]})
    if any(f["value"] is None for f in borrowing) or sum(f["value"] for f in borrowing) != debt["value"]:
        raise ValueError("Borrowing components do not reconcile to baseline gross debt")
    facts = checked["facts"]
    leases = []
    for name, prefix in (("Operating lease liabilities", "Operating"), ("Finance lease liabilities", "Finance")):
        current = facts.get(prefix + "LeaseLiabilityCurrent")
        noncurrent = facts.get(prefix + "LeaseLiabilityNoncurrent")
        total = facts.get(prefix + "LeaseLiability")
        if current is None or noncurrent is None:
            if ticker != "LLY" or prefix != "Finance":
                raise ValueError("Checked lease components are missing")
            leases.append({"label": name, "value": None, "period_end": anchor["period_end"],
                "detail": "No checked June amount. The 10-K describes operating leases only; finance leases are not reported, which is not zero.",
                "source_url": snapshot["source_url"], "location": "10-Q review; June amount not established",
                "supporting_source_url": facts["OperatingLeaseLiabilityCurrent"]["source_url"],
                "supporting_location": "10-K Note 10, p. 76",
                "form": "10-Q", "filed": anchor["filed"], "accession": anchor["accession"]})
            continue
        for f in (current, noncurrent, total) if total else (current, noncurrent):
            if (f["unit"] != "iso4217:USD" or f["value"] is None or f["value"] < 0 or f["dimensions"]
                    or f["period"] != f["period_end"]
                    or (f["period_end"], f["accession"]) != (current["period_end"], current["accession"])):
                raise ValueError("Lease inputs do not share a checked USD instant")
        value = current["value"] + noncurrent["value"]
        if total and total["value"] != value:
            raise ValueError("Lease components do not reconcile to the reported total")
        leases.append({**current, "label": name, "tag": None, "value": value,
                       "formula": "Current + noncurrent lease liability", "inputs": [current, noncurrent],
                       "reported_total": total, "detail": "Recognized liability; excluded from baseline borrowing."})
    commitment = facts.get("not_commenced")
    if commitment:
        if (commitment["unit"] != "iso4217:USD" or commitment["dimensions"]
                or commitment["period"] != anchor["period_end"] or commitment["value"] is None
                or commitment["value"] < 0):
            raise ValueError("Uncommenced lease commitment does not match the checked USD instant")
        commitment = {**commitment, "detail": "Amount reported in rounded billions. Future commitment, not a recognized lease liability. Expected to commence Q2 fiscal 2027–fiscal 2029, with 15–19 year terms. Annual payment timing is Unavailable."}
    else:
        commitment = {"label": "Leases not yet commenced", "value": None, "period_end": anchor["period_end"],
                      "detail": "No checked amount for leases not yet commenced is established in the saved pilot evidence. Unavailable does not mean zero.",
                      "source_url": snapshot["source_url"], "location": "Saved pilot evidence; 10-Q review",
                      "form": "10-Q", "filed": anchor["filed"], "accession": anchor["accession"]}
    return {"ticker": ticker, "company": snapshot["company_name"], "period_end": anchor["period_end"],
            "borrowing": borrowing, "baseline": debt["value"], "borrowing_note": BORROWING_NOTES[ticker],
            "leases": leases, "commitment": commitment,
            "latest_leases_available": all(f["value"] is not None and f["period_end"] == anchor["period_end"] for f in leases)}


def render_borrowing(model, money):
    from ui import esc
    output = '<h3>What makes up the borrowing?</h3>'
    source = model["borrowing"][0]
    output += (f'<p class="lr-meta">At {esc(model["period_end"])} · carrying amounts · '
               f'<a href="{esc(source["source_url"])}" target="_blank" rel="noopener noreferrer">{esc(source["location"])}</a></p>')
    for fact in model["borrowing"]:
        value = "$0 · reported" if fact["value"] == 0 else money(fact["value"], 3)
        output += f'<div class="lr-row"><span>{esc(fact["label"])}</span><strong>{esc(value)}</strong></div>'
    output += f'<div class="lr-row"><span>Baseline gross debt · sum above</span><strong>{esc(money(model["baseline"], 3))}</strong></div>'
    output += f'<p class="lr-meta">{esc(model["borrowing_note"])} These components exclude leases and are separate from total current liabilities.</p>'
    return output


def render_leases(model, money):
    from ui import esc
    output = '<section class="lr-obligations lr-leases"><h3>Which leases sit outside borrowing?</h3>'
    output += '<p class="lr-meta">Recognized lease liabilities and leases not yet commenced are shown separately. Neither is added to baseline gross debt, net debt or the flow/debt ratios.</p>'
    if not model["latest_leases_available"]:
        output += (f'<p><strong>Lease liabilities at {esc(model["period_end"])}: Unavailable.</strong> '
                   'No lease liability amounts were established in the checked 10-Q. Older balances below retain their own dates.</p>')
    for fact in [*model["leases"], model["commitment"]]:
        detail = fact["detail"]
        if fact.get("inputs"):
            a, b = fact["inputs"]
            detail = f'Current {money(a["value"], 3)} + noncurrent {money(b["value"], 3)} = {money(fact["value"], 3)}. ' + detail
        digits = 0 if fact is model["commitment"] else 3
        output += (f'<article class="lr-obligation"><div><p><strong>{esc(fact["label"])}</strong></p>'
                   f'<p>{esc(money(fact["value"], digits))}</p><div class="lr-meta">As of {esc(fact["period_end"])}</div></div>'
                   f'<div><p>{esc(detail)}</p><a class="lr-meta" href="{esc(fact["source_url"])}" '
                   f'target="_blank" rel="noopener noreferrer">{esc(fact["location"])}</a>')
        if fact.get("supporting_source_url"):
            output += (f' · <a class="lr-meta" href="{esc(fact["supporting_source_url"])}" '
                       f'target="_blank" rel="noopener noreferrer">{esc(fact["supporting_location"])}</a>')
        output += '</div></article>'
    return output + '</section>'
