"""Match Oracle's checked obligations to dated resource evidence without forecasting cash.

The saved filings do not establish funds available at future payment dates. Coverage therefore
stays unavailable, including when historical cash happens to exceed one payment bucket.
"""
import oracle_financing as financing
import oracle_liquidity as liquidity
import oracle_revolver


def build(review: dict, annual: dict) -> dict:
    """Keep payment bases, historical cash and conditional credit capacity distinct."""
    result = {"as_of": liquidity.END, "status": "Unavailable", "detail": "",
              "resources": [], "obligations": [], "historical_debt": []}
    if (review.get("status") != "Checked" or review.get("accession") != financing.QUARTER_ACCESSION
            or review.get("period_start") != liquidity.START or review.get("period_end") != liquidity.END):
        return {**result, "detail": "The checked August 31 Oracle liquidity review is required."}
    facts, cash, facility = review["inputs"], review["cash"], review["facility"]
    result["revolver"] = oracle_revolver.load()
    resources = [
        ("cash", "Cash excluding restricted cash", "closing_cash", liquidity.END, liquidity.END,
         "August cash pool, not reserved for future payments. Operating needs, capital spending and other "
         "obligations compete for it. Availability at payment dates is Unavailable."),
        ("restricted", "Restricted cash", None, liquidity.END, liquidity.END,
         "Excluded from the general repayment pool. Release timing and permitted uses are Unavailable."),
        ("ocf", "Reported operating cash flow", "ocf", liquidity.START, liquidity.END,
         "Historical cash generation, including the specified prepayments. Already reflected in closing cash. "
         "Future OCF and future operating costs are Unavailable."),
        ("prepay", "Specified customer prepayments", "prepay", liquidity.START, liquidity.END,
         "Part of reported OCF and already in closing cash. Supports future customer performance obligations. "
         "Future prepayments and related service costs are Unavailable."),
        ("equity", "ATM equity proceeds, net", "equity", liquidity.START, liquidity.END,
         "Already in closing cash. The $20B gross ATM program was fully utilized. No unused capacity "
         "or additional future equity proceeds are established."),
    ]
    for key, label, fact_key, start, end, detail in resources:
        result["resources"].append({"key": key, "label": label, "input_key": fact_key,
            "value": cash["restricted_at_end"] if key == "restricted" else facts[fact_key]["value"],
            "period_start": start, "period_end": end, "detail": detail,
            "source_url": review["source_url"], "accession": review["accession"],
            "location": "10-Q cash flows p. 5; Note 1 pp. 6–7; Note 7 pp. 13–14"})
    result["resources"].append({"key": "revolver", "label": "Original revolver commitment",
        "input_key": "facility_commitment", "value": facility["commitment"],
        "period_start": facility["agreement_date"], "period_end": facility["original_maturity"],
        "detail": "Potential working-capital and general corporate financing under §2.21, subject to "
            "§4.02 draw conditions and the contractual covenant. May 31 undrawn commitment was $10B. "
            "An amount actually drawable is Unavailable at each reviewed date, including August 31. "
            "No extension beyond March 6, 2031 is assumed. Commercial-paper capacity is not added.",
        "source_url": facility["source_url"], "accession": facility["accession"],
        "location": "Credit agreement §§2.21, 4.02, 6.02(c); 10-K Note 6 p. 85"})
    classes = {
        "operating": ("Operating leases", "Undiscounted payments including interest",
            "Operating needs and capex also use cash. Do not deduct lease payments already inside OCF twice."),
        "finance": ("Finance leases", "Undiscounted payments including interest",
            "Includes principal and interest. Do not deduct any interest already inside OCF twice."),
        "purchase": ("Purchase and other obligations", "Unconditional obligations with terms of at least one year",
            "Cloud supplies and power commitments may overlap capex, unpaid capex or leases. No combined total."),
    }
    for i, (period, start, end) in enumerate(liquidity.DUE):
        for kind, (label, basis, competing) in classes.items():
            schedule = review["schedules"][kind]
            value = schedule["rows"][i]["value"] if schedule["status"] == "Checked" else None
            # A commitment's original expiry is a limit, not proof that it will fund a bucket.
            within = end is not None and end <= facility["original_maturity"]
            if within:
                candidate = "August cash pool; conditional revolver. No payment allocation established."
            elif start < facility["original_maturity"]:
                candidate = "August cash pool; revolver expires within this bucket. Funding after expiry is Unavailable."
            else:
                candidate = "Future cash or new financing Unavailable. Original revolver expires before this bucket."
            reason = "Dated cash allocation, future OCF and drawable credit are not established."
            if value is None:
                reason = "Payment amount Unavailable: " + schedule["detail"] + " " + reason
            if end is None:
                reason += " Thereafter combines multiple years with no final payment date."
            result["obligations"].append({"key": f"{kind}_{i}", "period": period,
                "due_start": start, "due_end": end, "label": label, "value": value, "basis": basis,
                "candidate_resources": candidate, "competing_uses": competing,
                "funding_available": None, "coverage": None, "coverage_detail": reason,
                "source_url": review["source_url"], "accession": review["accession"],
                "location": "10-Q Note 6, pp. 12–13"})
    if (annual.get("status") == "Checked" and annual.get("accession") == financing.ACCESSION
            and annual.get("as_of") == financing.AS_OF):
        result["historical_debt"] = [{"label": f["label"], "value": f["value"],
            "due_start": f["due_start"], "due_end": f["due_end"], "tag": f["tag"],
            "context_id": f["context_id"], "accession": annual["accession"],
            "source_url": annual["source_url"], "as_of": annual["as_of"]}
            for f in annual["buckets"]]
    result["gaps"] = [
        {"label": "Remaining borrowing principal and interest at August 31", "value": None,
         "detail": "Current borrowing is carrying value, not a dated principal schedule. "
             "The May principal schedule is historical. Quarter repayments cannot be assigned to its buckets."},
        {"label": "Operating leases not yet commenced", "value": facts["not_commenced"]["value"],
         "detail": "Expected commencement in FY2027–2029 and 15–19 year terms do not establish payment dates. "
             "Annual amounts and overlap with other commitments are Unavailable."},
        {"label": "Unpaid capital expenditures", "value": facts["unpaid_capex"]["value"],
         "detail": "Noncash quarter disclosure. Payment dates and overlap with purchase obligations are Unavailable. "
             "It is not added to historical cash capex."},
    ]
    result["conclusion"] = ("The filings establish payment buckets, but do not establish funds available "
        "for them. Coverage and a repayment surplus or shortfall are Unavailable for every future bucket. "
        "Cash is one shared pool. Historical OCF, prepayments and equity proceeds are not added to it again.")
    return {**result, "status": "Checked"}


def for_snapshot(snapshot: dict) -> dict | None:
    review = liquidity.for_snapshot(snapshot)
    if review is None:
        return None
    return build(review, financing.for_snapshot(snapshot) or {})
