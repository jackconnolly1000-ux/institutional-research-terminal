"""Oracle's remaining borrowing principal by instrument and date at August 31, 2026.

The fiscal 2026 10-K tags every borrowing series in inline XBRL: its outstanding principal at May 31, 2026
(us-gaap:DebtInstrumentCarryingAmount on the debt table, before the 564M unamortized discount) and its exact
maturity date. The August 10-Q has no borrowing note, so the August calendar is the May instrument list carried
forward only where the evidence supports it:
- a senior note's principal does not amortize; one whose stated maturity fell in June–August is shown as matured,
  because MD&A reports about $3.1B of *scheduled* repayments and that note was the only scheduled maturity
  (with the term loan's June 30 installment), and the 10-Q reports no borrowing proceeds in the quarter;
- the term loan amortizes on its stated contract schedule, calculated from the 10-K's terms, not reported;
- commercial paper has no disclosed maturity dates, and its August balance is not reported: Unavailable.
The grouped $4,202M repayment line is never subtracted. It is checked against these facts, not used to make
them agree. Rounded 10-Q facts give ranges, not exact values. A principal calendar is not funding coverage.
No Streamlit, no network: callers pass the saved filings (or the trimmed test fixtures).
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

import filing_xbrl as fx

SAMPLE = Path(__file__).parent / "samples/oracle_principal.json"
CIK = "0001341439"
AS_OF = "2026-05-31"          # instrument list
ANCHOR = "2026-08-31"         # calendar date
FY2026 = ("2025-06-01", "2026-05-31")
QUARTER = ("2026-06-01", "2026-08-31")
BASE = "https://www.sec.gov/Archives/edgar/data/1341439/"
ANNUAL = {"form": "10-K", "filed": "2026-06-22", "accession": "0001193125-26-277521",
          "source_url": BASE + "000119312526277521/orcl-20260531.htm", "document": "orcl-20260531.htm",
          "location": "Note 6, pp. 83–85"}
QUARTERLY = {"form": "10-Q", "filed": "2026-09-11", "accession": "0001193125-26-389274",
             "source_url": BASE + "000119312526389274/orcl-20260831.htm", "document": "orcl-20260831.htm",
             "location": "Balance sheet p. 1; cash flows p. 5; Note 2 p. 9; MD&A pp. 31–33"}
CHECKED = "2026-10-17"
AXES = ("us-gaap:DebtInstrumentAxis", "us-gaap:CreditFacilityAxis")
TERM_LOAN = "orcl:TermLoanCreditAgreementDueAugust2027ThreeMember"
COMMERCIAL_PAPER = "us-gaap:CommercialPaperMember"
LONG_TERM = ("us-gaap:LongtermDebtTypeAxis", "orcl:SeniorNotesAndOtherLongTermBorrowingsMember")
MILLION = 1_000_000

# The 10-K buckets, checked in oracle_financing; used here as a control on the instrument list.
BUCKETS_MAY = {"Fiscal 2027": 7_210, "Fiscal 2028": 10_145, "Fiscal 2029": 5_500, "Fiscal 2030": 7_250,
               "Fiscal 2031": 9_750, "Thereafter": 90_250}

# Text the tagged facts can't carry. Each is checked against the saved filing text by its test.
TERM_LOAN_TERMS = {
    "borrowed_tag": "us-gaap:DebtInstrumentFaceAmount",
    "first_rate": 0.0125, "first_dates": ["2024-09-30", "2024-12-31", "2025-03-31", "2025-06-30", "2025-09-30",
                                          "2025-12-31", "2026-03-31", "2026-06-30"],
    "second_rate": 0.025, "second_dates": ["2026-09-30", "2026-12-31", "2027-03-31", "2027-06-30"],
    "final_date": "2027-08-16",
    "text": ("an amount equal to the amount borrowed reduced by any prepayments multiplied by 1.25% on September 30, "
             "2024 and quarterly thereafter until June 30, 2026; an amount equal to the amount borrowed reduced by any "
             "prepayments multiplied by 2.50% on September 30, 2026 and quarterly thereafter until June 30, 2027; and "
             "any remaining unpaid principal balance ... will become fully due and payable on August 16, 2027"),
    "extension": ("The termination date may be extended at Oracle's sole option by up to 2 years, and further at "
                  "each lender's option by up to 2 years."),
    "location": "10-K Note 6, Term Loan Credit Agreements, pp. 85–86",
}
QUARTER_TEXT = {
    "scheduled": {"amount": 3_100 * MILLION, "phrase": "$3.1 billion of cash used for scheduled repayments of debt",
                  "location": "10-Q MD&A, liquidity, p. 33"},
    "commercial_paper": {"amount": 1_100 * MILLION, "phrase": "$1.1 billion of cash used for repayment of commercial paper",
                         "location": "10-Q MD&A, liquidity, p. 33"},
    "reclassified": {"amount": 4_600 * MILLION,
                     "phrase": "$4.6 billion of long-term borrowings that were reclassified to current liabilities",
                     "location": "10-Q MD&A, working capital, p. 33"},
}


def fiscal_year(day: str) -> int:
    """Oracle's fiscal year ends May 31: June 2026–May 2027 is fiscal 2027."""
    d = date.fromisoformat(day)
    return d.year + 1 if d.month >= 6 else d.year


def bucket_of(day: str) -> str:
    fy = fiscal_year(day)
    return f"Fiscal {fy}" if fy <= 2031 else "Thereafter"


def _dates(document: Path, tag: str) -> dict:
    """{(axis, member): (date text, context id)} for one ix:nonNumeric date tag over fiscal 2026, Oracle only."""
    root = ET.parse(document).getroot()
    contexts = fx._contexts(root)
    out = {}
    for f in root.iter(f"{{{fx.IX}}}nonNumeric"):
        if f.get("name") != tag:
            continue
        ctx = contexts[f.get("contextRef")]
        if (ctx["start"], ctx["end"]) != FY2026 or len(ctx["dimensions"]) != 1:
            continue
        if not (ctx["entity_identifier"] or "").endswith(CIK.lstrip("0")):
            raise ValueError("A maturity date belongs to another entity")
        key = tuple(ctx["dimensions"][0])
        value = "".join(f.itertext()).strip()
        if key in out and out[key][0] != value:
            raise ValueError(f"Conflicting maturity dates for {key[1]}")
        out[key] = (date.fromisoformat(value).isoformat(), f.get("contextRef"))
    return out


def _members(document: Path) -> list:
    """Every (axis, member) with a DebtInstrumentCarryingAmount at May 31, 2026."""
    root = ET.parse(document).getroot()
    contexts = fx._contexts(root)
    seen = []
    for f in root.iter(f"{{{fx.IX}}}nonFraction"):
        if f.get("name") != "us-gaap:DebtInstrumentCarryingAmount":
            continue
        ctx = contexts[f.get("contextRef")]
        if ctx["instant"] == AS_OF and len(ctx["dimensions"]) == 1 and ctx["dimensions"][0][0] in AXES:
            key = tuple(ctx["dimensions"][0])
            if key not in seen:
                seen.append(key)
    return seen


def _kind(member: str) -> str:
    if member == COMMERCIAL_PAPER:
        return "Commercial paper"
    if member == TERM_LOAN:
        return "Term loan"
    if "Floating" in member:
        return "Floating-rate senior notes"
    if "Fixed" in member:
        return "Fixed-rate senior notes"
    return "Other borrowings"


def _fact(document, accession, tag, instant, dims=()):
    return fx.read_instant(document, accession, tag, instant, dimensions=dims)


def percent(rate):
    """2.80, 3.125, 6.15: the filing's own precision (at least two decimals)."""
    text = f"{rate:.3f}"
    return text[:-1] if text.endswith("0") else text


def _rate_text(kind, rate, face, maturity):
    month = date.fromisoformat(maturity).strftime("%B %Y")
    millions = f"${face // MILLION:,}M" if face else "Amount not tagged"
    if kind == "Floating-rate senior notes":
        return f"{millions}, Compounded SOFR plus {percent(rate)}%, due {month}"
    if kind == "Term loan":
        return f"Term loan, {millions} borrowed, SOFR plus {percent(rate)}%, due {month}"
    return f"{millions}, {percent(rate)}%, due {month}"


def _range(fact):
    """A rounded fact as an inclusive-exclusive range in dollars (decimals -8 is ±50M)."""
    decimals = int(fact["decimals"])
    half = 10 ** (-decimals) // 2 if decimals < 0 else 0
    return fact["value"] - half, fact["value"] + half


def term_loan_schedule(borrowed: int) -> dict:
    """The stated amortization: calculated to the dollar, never reported per installment."""
    first = [{"date": d, "amount": round(borrowed * TERM_LOAN_TERMS["first_rate"]),
              "basis": "1.25% of the amount borrowed"} for d in TERM_LOAN_TERMS["first_dates"]]
    second = [{"date": d, "amount": round(borrowed * TERM_LOAN_TERMS["second_rate"]),
               "basis": "2.50% of the amount borrowed"} for d in TERM_LOAN_TERMS["second_dates"]]
    paid = sum(i["amount"] for i in first + second)
    final = {"date": TERM_LOAN_TERMS["final_date"], "amount": borrowed - paid,
             "basis": "Remaining unpaid principal; the date can be extended at Oracle's option"}
    balance = lambda day: borrowed - sum(i["amount"] for i in first + second if i["date"] <= day)
    return {"borrowed": borrowed, "installments": first + second, "final": final,
            "balance_may_31_2025": balance("2025-05-31"), "balance_may_31_2026": balance(AS_OF),
            "balance_aug_31_2026": balance(ANCHOR), "prepayments": "None identified; the formula assumes none."}


def build(annual_document: Path, quarter_document: Path) -> dict:
    annual_document, quarter_document = Path(annual_document), Path(quarter_document)
    acc, qacc = ANNUAL["accession"], QUARTERLY["accession"]
    maturities = _dates(annual_document, "us-gaap:DebtInstrumentMaturityDate")
    instruments, problems = [], []
    for axis, member in _members(annual_document):
        dims = [(axis, member)]
        principal = _fact(annual_document, acc, "us-gaap:DebtInstrumentCarryingAmount", AS_OF, dims)
        if principal["value"] is None:
            problems.append(f"{member}: {principal['detail']}")
            continue
        if principal["value"] == 0:
            continue   # repaid before May 31, 2026 (a reported dash)
        kind = _kind(member)
        face = _fact(annual_document, acc, "us-gaap:DebtInstrumentFaceAmount", AS_OF, dims)
        maturity = maturities.get((axis, member))
        rate = _rate(annual_document, member, axis) if kind != "Commercial paper" else None
        instruments.append({
            "member": member, "axis": axis, "kind": kind,
            "maturity": maturity[0] if maturity else None,
            "maturity_context": maturity[1] if maturity else None,
            "face_amount": face["value"], "stated_rate": rate,
            "principal_may_31": principal["value"], "principal_context": principal["context_id"],
            "principal_tag": "us-gaap:DebtInstrumentCarryingAmount",
            "label": ("Commercial paper notes" if kind == "Commercial paper" else
                      _rate_text(kind, rate, face["value"], maturity[0]) if maturity else member),
        })
    total = _fact(annual_document, acc, "us-gaap:DebtInstrumentCarryingAmount", AS_OF)
    carrying = _fact(annual_document, acc, "us-gaap:DebtLongtermAndShorttermCombinedAmount", AS_OF)
    discount = _fact(annual_document, acc, "us-gaap:DebtInstrumentUnamortizedDiscountPremiumAndDebtIssuanceCostsNet", AS_OF)
    lt_may = _fact(annual_document, acc, "us-gaap:DebtInstrumentCarryingAmount", AS_OF, [LONG_TERM])
    lt_aug = _fact(quarter_document, qacc, "us-gaap:DebtInstrumentCarryingAmount", ANCHOR, [LONG_TERM])
    current_aug = _fact(quarter_document, qacc, "us-gaap:NotesPayableCurrent", ANCHOR)
    noncurrent_aug = _fact(quarter_document, qacc, "us-gaap:LongTermNotesAndLoans", ANCHOR)
    repaid = fx.read_duration(quarter_document, qacc, "us-gaap:RepaymentsOfDebt", *QUARTER)
    cp_row = fx.read_duration(quarter_document, qacc, "us-gaap:RepaymentsOfCommercialPaper", *QUARTER)
    inputs = {"principal_total_may": total, "carrying_may": carrying, "discount_may": discount,
              "long_term_carrying_may": lt_may, "long_term_carrying_aug": lt_aug, "current_aug": current_aug,
              "noncurrent_aug": noncurrent_aug, "repayments_quarter": repaid, "commercial_paper_row_quarter": cp_row}
    problems += [f"{k}: {v['detail']}" for k, v in inputs.items() if v["value"] is None]
    if problems or not instruments:
        return {"status": "Unavailable", "detail": "; ".join(problems) or "No borrowing instruments found."}

    tl = next(i for i in instruments if i["member"] == TERM_LOAN)
    cp = next(i for i in instruments if i["member"] == COMMERCIAL_PAPER)
    schedule = term_loan_schedule(tl["face_amount"])
    checks = []

    def check(label, expected, actual, tolerance, detail):
        diff = actual - expected
        checks.append({"label": label, "expected": expected, "actual": actual, "difference": diff,
                       "tolerance": tolerance, "status": "Agrees" if abs(diff) <= tolerance else "Differs",
                       "detail": detail})

    may_sum = sum(i["principal_may_31"] for i in instruments)
    check("Instrument principal sums to the reported principal total", total["value"], may_sum, 0,
          "Every tagged series at May 31, 2026, including the term loan and commercial paper.")
    check("Principal less unamortized discount and issuance costs equals carrying debt",
          carrying["value"], total["value"] - discount["value"], 0, "May 31, 2026, Note 6 p. 84.")
    for label, day, reported in (("May 31, 2025", "2025-05-31", 5_419 * MILLION), ("May 31, 2026", AS_OF, tl["principal_may_31"])):
        check(f"Term-loan schedule matches its reported balance at {label}", reported,
              schedule["balance_may_31_2025" if day != AS_OF else "balance_may_31_2026"], MILLION // 2,
              "Calculated from the stated amortization; the filing rounds to millions.")
    # Notes by stated date + the term loan's calculated split + commercial paper in fiscal 2027 (the 10-K's basis)
    by_bucket = {k: 0 for k in BUCKETS_MAY}
    for i in instruments:
        if i["member"] in (TERM_LOAN, COMMERCIAL_PAPER):
            continue
        by_bucket[bucket_of(i["maturity"])] += i["principal_may_31"]
    by_bucket["Fiscal 2027"] += cp["principal_may_31"]
    for step in schedule["installments"] + [schedule["final"]]:
        if step["date"] > AS_OF:
            by_bucket[bucket_of(step["date"])] += step["amount"]
    for label, reported in BUCKETS_MAY.items():
        check(f"{label} instruments match the 10-K maturity bucket", reported * MILLION, by_bucket[label], MILLION,
              "The 10-K bucket counts commercial paper in fiscal 2027; term-loan installments are calculated "
              "to the dollar while the bucket is rounded to millions.")

    # August 31: carry forward only what the evidence supports
    matured, remaining = [], []
    for i in instruments:
        row = dict(i)
        if i["member"] == COMMERCIAL_PAPER:
            row.update(principal_aug_31=None, status="Unavailable",
                       detail="No maturity dates are disclosed, and the August 31 balance is not reported.")
            remaining.append(row)
        elif i["member"] == TERM_LOAN:
            row.update(principal_aug_31=schedule["balance_aug_31_2026"], status="Calculated",
                       detail="May 31 principal less the scheduled June 30, 2026 installment, from the stated terms. "
                              "Individual installments are not separately reported.")
            remaining.append(row)
        elif i["maturity"] <= ANCHOR:
            row.update(principal_aug_31=0, status="Matured",
                       detail=(f"Stated maturity {i['maturity']}, before August 31. MD&A reports about $3.1B of "
                               "scheduled debt repayments in the quarter; this was the only senior note scheduled "
                               "to mature then. The 10-Q does not name the series repaid."))
            matured.append(row)
        else:
            row.update(principal_aug_31=i["principal_may_31"], status="Carried forward",
                       detail="Fixed principal; no borrowing proceeds and no unscheduled redemption are reported "
                              "for June–August (see checks).")
            remaining.append(row)

    notes_aug = sum(r["principal_aug_31"] for r in remaining if r["member"] not in (TERM_LOAN, COMMERCIAL_PAPER))
    known_lt = notes_aug + schedule["balance_aug_31_2026"]
    lt_lo, lt_hi = _range(lt_aug)
    carrying_aug = current_aug["value"] + noncurrent_aug["value"]
    scheduled = sum(r["principal_may_31"] for r in matured) + sum(
        s["amount"] for s in schedule["installments"] if AS_OF < s["date"] <= ANCHOR)
    implied_discount = (known_lt - lt_hi, known_lt - lt_lo)
    cp_range = (carrying_aug - lt_hi, carrying_aug - lt_lo)
    lt_may_lo, lt_may_hi = _range(lt_may)
    check("Long-term carrying at May 31 (rounded 10-K fact) contains principal less discount, excluding commercial paper",
          lt_may["value"], total["value"] - cp["principal_may_31"] - discount["value"], lt_may_hi - lt_may["value"],
          "128.1B is tagged with decimals -8 (to the nearest $100M).")
    check("Scheduled June–August principal agrees with MD&A's rounded scheduled repayments",
          QUARTER_TEXT["scheduled"]["amount"], scheduled, 50 * MILLION,
          "MD&A rounds to $0.1B; this checks the matured note and June 30 installment, it does not prove which "
          "instrument each dollar repaid.")
    checks.append({"label": "Implied August 31 unamortized discount and issuance costs (long-term)",
                   "expected": discount["value"], "actual": None, "range": list(implied_discount),
                   "difference": None, "tolerance": None,
                   # With no new issuance the August balance can only be at or below May's, and not negative.
                   "status": "Consistent" if implied_discount[0] <= discount["value"] and implied_discount[1] >= 0 else "Differs",
                   "detail": ("Known long-term principal less the rounded 125.0B carrying fact. Not reported at "
                              "August 31; it should be slightly below May's 564M as discount amortizes. A range, "
                              "not a forced reconciliation.")})
    residual = repaid["value"] - scheduled
    checks.append({"label": "Grouped repayments less scheduled principal, compared with MD&A's commercial-paper repayment",
                   "expected": QUARTER_TEXT["commercial_paper"]["amount"], "actual": residual,
                   "difference": residual - QUARTER_TEXT["commercial_paper"]["amount"], "tolerance": 50 * MILLION,
                   "status": "Consistent, not adopted" if abs(residual - QUARTER_TEXT["commercial_paper"]["amount"]) <= 50 * MILLION else "Differs",
                   "detail": ("The cash-flow commercial-paper row is a reported zero and the 10-Q does not split the "
                              "$4,202M line by instrument. The residual is not subtracted from commercial paper.")})
    reclass = schedule["installments"][-1]["amount"] + schedule["final"]["amount"]
    check("Term-loan principal newly due within twelve months agrees with MD&A's rounded reclassification",
          QUARTER_TEXT["reclassified"]["amount"], reclass, 50 * MILLION,
          "June 30, 2027 installment plus the August 16, 2027 remainder entered the twelve-month window.")

    def bucket_label(day):
        return "Remainder FY2027" if fiscal_year(day) == 2027 else bucket_of(day).replace("Fiscal ", "FY")
    calendar = {}
    rows = [(r["maturity"], r["principal_aug_31"], r["label"]) for r in remaining
            if r["member"] not in (TERM_LOAN, COMMERCIAL_PAPER)]
    rows += [(s["date"], s["amount"], f"Term loan, scheduled installment ({s['basis']})")
             for s in schedule["installments"] if s["date"] > ANCHOR]
    rows += [(schedule["final"]["date"], schedule["final"]["amount"], "Term loan, remaining principal")]
    for day, amount, _ in rows:
        calendar[bucket_label(day)] = calendar.get(bucket_label(day), 0) + amount
    order = ["Remainder FY2027", "FY2028", "FY2029", "FY2030", "FY2031", "Thereafter"]
    starts = {"Remainder FY2027": ("2026-09-01", "2027-05-31"), "FY2028": ("2027-06-01", "2028-05-31"),
              "FY2029": ("2028-06-01", "2029-05-31"), "FY2030": ("2029-06-01", "2030-05-31"),
              "FY2031": ("2030-06-01", "2031-05-31"), "Thereafter": ("2031-06-01", None)}
    near = sorted([r for r in rows if ANCHOR < r[0] <= "2027-08-31"])
    status = "Checked" if all(c["status"] in ("Agrees", "Consistent", "Consistent, not adopted") for c in checks) else "Differs"
    return {
        "ticker": "ORCL", "status": status, "as_of": ANCHOR, "instrument_date": AS_OF, "checked_as_of": CHECKED,
        "annual": ANNUAL, "quarter": QUARTERLY, "term_loan_terms": TERM_LOAN_TERMS, "quarter_text": QUARTER_TEXT,
        "instruments": instruments, "matured": matured, "remaining": remaining, "term_loan": schedule,
        "calendar": [{"label": k, "start": starts[k][0], "end": starts[k][1], "principal": calendar.get(k, 0),
                      "excludes": "Commercial paper (Unavailable)"} for k in order],
        "next_twelve_months": {"start": "2026-09-01", "end": "2027-08-31",
                               "rows": [{"date": d, "amount": a, "label": l} for d, a, l in near],
                               "principal": sum(a for _, a, _ in near),
                               "excludes": "Commercial paper (Unavailable)"},
        "reconciliation": {
            "known_principal_excluding_cp": known_lt, "notes": notes_aug, "term_loan": schedule["balance_aug_31_2026"],
            "commercial_paper": None, "commercial_paper_range": list(cp_range),
            "long_term_carrying_reported": lt_aug["value"], "long_term_carrying_range": [lt_lo, lt_hi],
            "carrying_reported": carrying_aug, "current_reported": current_aug["value"],
            "noncurrent_reported": noncurrent_aug["value"], "implied_discount_range": list(implied_discount),
            "repayments_quarter": repaid["value"], "commercial_paper_row_quarter": cp_row["value"],
            "scheduled_principal_quarter": scheduled,
            "principal_total_aug": None,
            "principal_total_range": [known_lt + cp_range[0], known_lt + cp_range[1]],
        },
        "inputs": {k: {key: v[key] for key in ("tag", "value", "period", "context_id", "dimensions", "scale",
                                              "decimals", "accession")} | ({"start": v["start"]} if "start" in v else {})
                   for k, v in inputs.items()},
        "checks": checks,
        "limits": [
            "Commercial paper at August 31 is Unavailable: no balance or maturity dates are reported.",
            "Unamortized discount and issuance costs at August 31 are not reported; only a range is implied.",
            "Term-loan installments and the August 16, 2027 remainder are calculated from the stated terms, assume no "
            "prepayment and can move if Oracle extends the termination date (up to 2 years at its option).",
            "Notes can be redeemed early under make-whole terms; none is reported for June–August, and later "
            "redemptions are outside this review.",
            "Principal excludes interest. This calendar is not funding coverage and says nothing about drawable credit.",
        ],
    }


def _rate(document: Path, member: str, axis: str):
    """The stated rate (coupon, or the margin over SOFR) at May 31, 2026, a percentage fact."""
    root = ET.parse(document).getroot()
    contexts = fx._contexts(root)
    for f in root.iter(f"{{{fx.IX}}}nonFraction"):
        if f.get("name") != "us-gaap:DebtInstrumentInterestRateStatedPercentage":
            continue
        ctx = contexts[f.get("contextRef")]
        if ctx["instant"] == AS_OF and [tuple(d) for d in ctx["dimensions"]] == [(axis, member)]:
            value, _ = fx._number(f)
            return float(value * 100) if value is not None else None
    return None


def principal_between(review: dict, start: str, end: str | None) -> int:
    """Dated note and term-loan principal due from start through end (None = no end), after August 31.
    Commercial paper is excluded: it has no dates."""
    notes = sum(r["principal_aug_31"] for r in review["remaining"]
                if r["member"] not in (TERM_LOAN, COMMERCIAL_PAPER) and start <= r["maturity"] <= (end or "9999-12-31"))
    steps = review["term_loan"]["installments"] + [review["term_loan"]["final"]]
    loan = sum(s["amount"] for s in steps if ANCHOR < s["date"] and start <= s["date"] <= (end or "9999-12-31"))
    return notes + loan


def fingerprint() -> str:
    return hashlib.sha256(SAMPLE.read_bytes()).hexdigest()


def load(folder: Path | None = None) -> dict | None:
    """The saved calendar, refused unless every check agrees."""
    path = (Path(folder) / SAMPLE.name) if folder else SAMPLE
    try:
        review = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return review if review.get("status") == "Checked" else None
