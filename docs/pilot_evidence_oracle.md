# Pilot evidence: Oracle (ORCL)

Evidence for the second debt and liquidity pilot (see `debt_liquidity_plan.md`): filing values with sources and checks, hand calculations labeled as such, and open gaps. Checked values are the pilot's expected answers; Unavailable items and open gaps are not. Checked Oct 14, 2026. The saved debt and liquidity pilot uses the checked cash, borrowing and current-position values; other sections retain their own status.

**How it was checked:** each amount was read from the filing's HTML text and matched to the inline XBRL fact on that row (tag, period, dimensions, unit, scale), then compared with SEC companyfacts. Page numbers are the filing's printed page footers, found by splitting the document at its page breaks. In the 10-Q, printed page 1 is the balance sheet. Raw downloads are kept outside the repo in `Stock Project/data/raw/` (`xbrl/ORCL_*`, `sec/ORCL/`).

**Rounding rule:** as in the plan. A figure stated in billions to one decimal (for example "$125.0 billion") covers a range of ±$0.05 billion and is never treated as an exact millions figure.

**Fiscal year:** Oracle's year ends May 31. The quarter ended Aug 31, 2026 is Oracle's Q1 fiscal 2027; companyfacts labels it "fy 2026, Q1". The app must use period dates, not the companyfacts fiscal-year label.

## Filings

| Filing | Period | Filed | Accession | Link |
|---|---|---|---|---|
| 10-Q (balance-sheet date for the pilot) | 2026-08-31 | 2026-09-11 | 0001193125-26-389274 | https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.htm |
| 10-K | 2026-05-31 | 2026-06-22 | 0001193125-26-277521 | https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm |

Companyfacts: https://data.sec.gov/api/xbrl/companyfacts/CIK0001341439.json (CIK 1341439).

## Balance sheet at August 31, 2026 (10-Q, USD millions)

| Item | Amount | Location | Tag | In companyfacts |
|---|---|---|---|---|
| Cash and cash equivalents | 36,369 | Condensed Consolidated Balance Sheets, p. 1 | `CashAndCashEquivalentsAtCarryingValue` | Yes |
| Cash, cash equivalents and restricted cash | 38,934 | Cash flow statement, p. 5 | `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations` | Yes |
| Restricted cash | "$2.6 billion" | Notes, "Cash, Cash Equivalents and Restricted Cash", p. 6: "included within prepaid expenses and other current assets" | `RestrictedCash` (scale 9, stated in billions) | Yes, as 2,600 |
| Total current assets | 55,630 | Balance sheet, p. 1 | `AssetsCurrent` | Yes |
| Total current liabilities | 47,514 | Balance sheet, p. 1 | `LiabilitiesCurrent` | Yes |

- Cash and cash equivalents exclude restricted cash: the restricted cash sits in prepaid expenses and other current assets (p. 6). 38,934 - 36,369 = 2,565 is a hand calculation consistent with the rounded "$2.6 billion".
- Restricted cash at May 31, 2026 was "immaterial" (p. 6).

## Borrowing at August 31, 2026 (USD millions, carrying amounts)

| Line | Amount | Location | Tag | In companyfacts |
|---|---|---|---|---|
| Notes payable and other borrowings, current | 7,625 | 10-Q balance sheet, p. 1 | `NotesPayableCurrent` (no dimensions) | Yes |
| Notes payable and other borrowings, non-current | 117,712 | 10-Q balance sheet, p. 1 | `LongTermNotesAndLoans` (no dimensions) | Yes |
| Total (not a reported line in the 10-Q) | 125,337 | | none, hand calculation | |

**What the two balance-sheet lines contain.** The 10-Q has no borrowings table. The 10-K's Note 6: Notes Payable and Other Borrowings (pp. 83-84) itemizes the same two lines at May 31, 2026:

| May 31, 2026 (10-K Note 6) | Amount |
|---|---|
| Fixed- and floating-rate senior notes, term loan credit agreements ($5,137) and commercial paper notes ($1,468): "Total senior notes and other borrowings" (principal) | 130,105 |
| Unamortized discount/issuance costs | (564) |
| Hedge accounting fair value adjustments | — |
| Total notes payable and other borrowings (carrying amount) | 129,541 = 7,199 current + 122,342 non-current |

So the balance-sheet lines are carrying amounts of senior notes, term loans and commercial paper. Leases are not in them; they are reported separately (see Leases).

**The rounded "$125.0 billion" disclosure (10-Q Note 2, p. 9).** The sentence gives "the $125.0 billion and $128.1 billion of senior notes and other long-term borrowings and the related fair value hedges, if any, that we had outstanding as of August 31, 2026 and May 31, 2026" (tag `DebtInstrumentCarryingAmount`, dimension `LongtermDebtTypeAxis = SeniorNotesAndOtherLongTermBorrowingsMember`, scale 9). Its scope and basis, checked against the 10-K at May 31:

- 129,541 carrying - 1,468 commercial paper = 128,073, which rounds to the stated $128.1 billion. Principal excluding commercial paper (130,105 - 1,468 = 128,637) would round to $128.6 billion. So, at May 31, the disclosure is the **carrying amount of long-term borrowings, excluding commercial paper**. These are hand calculations from rounded filing figures.
- At Aug 31, the two balance-sheet lines sum to 125,337 against the rounded "$125.0 billion" (124,950 to 125,050). The filing does not state what makes up the difference.

**Commercial paper at Aug 31, 2026: Unavailable.** The filings give conflicting presentations, and none states the ending balance:

| Source | What it says | Tag |
|---|---|---|
| 10-K Note 6, p. 84 | Commercial paper notes 1,468 at May 31, 2026 (2,294 at May 31, 2025) | in the Note 6 table; the text tags "$1.5 billion" as `NotesPayable` with `CreditFacilityAxis = CommercialPaperMember` |
| 10-Q cash flow statement, p. 5 | "Repayments of commercial paper, net": "—" for Q1 fiscal 2027; (238) for Q1 fiscal 2026 | `RepaymentsOfCommercialPaper`, nil for Q1 fiscal 2027 |
| 10-Q MD&A, p. 33 | "$1.1 billion of cash used for repayment of commercial paper" during Q1 fiscal 2027 | not tagged |
| 10-Q cash flow statement, p. 5 | "Repayments of senior notes, term loan credit agreements and other borrowings" (4,202); no line for commercial paper issuances | `RepaymentsOfDebt` |

The filings do not explain the difference between the "—" and the $1.1 billion. Possible explanations, none stated in the filing: the commercial paper repayment is presented inside the 4,202 line, or issuances offset repayments. Either way, the Aug 31 commercial paper balance cannot be verified, and none is estimated here. The same kind of mismatch appears in the 10-K: the fiscal 2026 cash flow statement shows commercial paper "(Repayments of) proceeds from issuances of commercial paper, net" of (2,285) (p. 68, `ProceedsFromRepaymentsOfCommercialPaper`), while the MD&A (p. 52) gives "$851 million of cash used for repayment of commercial paper, net". It is recorded, not resolved.

**Conclusion:** baseline borrowing at Aug 31, 2026 is the sum of Oracle's two reported balance-sheet borrowing lines, 7,625 + 117,712 = 125,337 (a hand calculation; no total line is reported in the 10-Q). Do not add the "$125.0 billion" to them; it is a rounded, narrower subset of the same debt. The composition of the 125,337 at Aug 31, including commercial paper, is not stated.

**Implemented (Oct 14, 2026):** `xbrl.baseline_gross_debt(facts, "ORCL")` adds `NotesPayableCurrent` + `LongTermNotesAndLoans` from one filing at the anchor date: 125,337 at Aug 31, 2026 (10-Q 0001193125-26-389274), and 129,541 at May 31, 2026 (10-K 0001193125-26-277521), matching that 10-K's Note 6 total. It does not add the rounded "$125.0 billion" subset, leases or capex-financing cash flows, and its caveats are scoped to the filing used: the Aug 31 10-Q result states that commercial paper and the capex-financing balance are Unavailable there and not inferred from the total; the May 31 10-K result states Note 6's commercial paper of 1,468M; for a filing not reviewed here the result is Unavailable ("presentation not checked for this filing"), with its components kept for review.

**Short-term financing related to capital expenditures: balance Unavailable.** Traced through the cash flow statements, balance-sheet labels, notes and tagged facts:

| Where checked | Finding |
|---|---|
| Cash flow statements | 10-Q p. 5: "(Repayments of) proceeds from short-term financing related to capital expenditures, net" (830) for Q1 fiscal 2027, 1,958 for Q1 fiscal 2026. 10-K p. 68: 3,345 for fiscal 2026, 1,422 for fiscal 2025, "—" for fiscal 2024. Oracle-specific tags `orcl:ProceedsFromRepaymentsOfShort-TermFinancingRelatedToCapitalExpendituresNet` (10-Q) and `orcl:ProceedsFromShort-TermFinancingRelatedToCapitalExpendituresNet` (10-K); flows only, no balances. |
| Balance-sheet labels | No balance-sheet line names this financing (10-Q p. 1, 10-K p. 64). |
| Borrowings note | Not in the 10-K Note 6 table (pp. 83-84), which itemizes senior notes, term loans and commercial paper and reconciles exactly to the two borrowing lines. |
| Tagged balances | No instant-dated fact for it in either filing. The tagged liability balances at each date are notes payable, accounts payable, other current and non-current liabilities, income taxes payable and lease liabilities; none is labeled as this financing. |
| Notes and MD&A text | Mentioned only as cash flows (10-K p. 52; 10-Q pp. 33-34). No accounting policy, note or balance found. |

Its outstanding balance, terms and balance-sheet line are not disclosed in the sections checked. At May 31, 2026 it is not one of the items in the Note 6 table that makes up the borrowing lines (senior notes, term loans, commercial paper; the only "other borrowings" item is zero). At Aug 31, 2026 there is no itemization, so its place is not stated. Where it sits (for example within other current liabilities) is not stated either. **No cash-flow amount is added to debt**, and no overlap with the reported borrowing lines is assumed.

## Leases at August 31, 2026 (10-Q Note 6: Leases and Other Commitments, pp. 12-13, USD millions)

Recognized on the balance sheet; shown separately, never added to borrowing.

| Item | Amount | Tag | In companyfacts |
|---|---|---|---|
| Operating lease liabilities, current | 4,027 | `OperatingLeaseLiabilityCurrent` | Yes |
| Operating lease liabilities, non-current | 30,594 | `OperatingLeaseLiabilityNoncurrent` (also its own balance-sheet line, p. 1) | Yes |
| Total operating lease liabilities | 34,621 | `OperatingLeaseLiability` | Yes |
| Finance lease liabilities, current | 749 | `FinanceLeaseLiabilityCurrent` | Yes |
| Finance lease liabilities, non-current | 8,436 | `FinanceLeaseLiabilityNoncurrent` | Yes |
| Total finance lease liabilities | 9,185 | `FinanceLeaseLiability` | Yes |

The balance-sheet line items that hold the current operating lease liabilities and the finance lease liabilities are not restated here; the 10-Q's inline XBRL links them to other current and other non-current liabilities, which still needs confirming by hand.

## Interest expense (USD millions)

| Period | Amount | Location | Tag | In companyfacts |
|---|---|---|---|---|
| Q1 fiscal 2027 (2026-06-01 to 2026-08-31) | 1,428 | 10-Q statement of operations, p. 2; MD&A, p. 32 | `InterestExpense` (no dimensions) | Yes |
| Q1 fiscal 2026 (2025-06-01 to 2025-08-31) | 923 | Same, comparative column | `InterestExpense` (no dimensions) | Yes |
| Fiscal 2026 (2025-06-01 to 2026-05-31) | 4,599 | 10-K MD&A, p. 50 | `InterestExpense` (no dimensions) | Yes |

- Hand calculation from filing figures: TTM to Aug 31, 2026 = 4,599 + 1,428 - 923 = 5,104. All three inputs are undimensioned facts in companyfacts.
- **Basis:** interest expense is its own line, before non-operating income, which "consists primarily of interest income" (10-Q p. 32). So it is before any offset for interest income.
- **Capitalized interest: not stated.** No mention of capitalized interest was found in the 10-K or the 10-Q (full-text search), and companyfacts has no capitalized-interest tag for Oracle. With construction in progress of 48,546 (10-Q p. 9), some interest may be capitalized, but the filings checked do not say. The label cannot say "net of capitalized interest", and nothing is added.
- **Other components not stated:**
  - Finance lease interest (126 in the quarter, Note 6 p. 12) is reported within finance lease expense; whether it is also inside the "Interest expense" line is not stated.
  - Interest on significant financing components of customer contracts is "recognized separately from revenue" and was "immaterial" in the quarter (p. 7); the line it is recorded in is not stated.
- Cash paid for interest, fiscal 2026: 3,896 (10-K p. 68). Context only.

## Customer prepayments with a significant financing component

- During Q1 fiscal 2027 Oracle **received $11.4 billion of customer prepayments** that included a significant financing component (10-Q notes, "Customer Prepayments and Sales of Financing Receivables", p. 7). None were received in Q1 fiscal 2026.
- They are reflected in **deferred revenues** and recognized over the period of performance (p. 7). Deferred revenues (current) were 14,686 at Aug 31, 2026 vs 9,916 at May 31 (balance sheet, p. 1). How much of the $11.4 billion is current versus non-current deferred revenue is not stated in the sections checked.
- This is cash received and a performance obligation, not an outstanding debt balance or an off-balance-sheet commitment. It is not added to borrowing.
- **Effect on cash flow:** the $11.4 billion is inside the quarter's $23.1 billion net cash from operating activities (10-Q MD&A, pp. 33-34). OCF-based measures (OCF/debt, FCF) for this quarter therefore include it, and a TTM figure would carry it for four quarters. The app should state this next to any OCF or FCF figure for Oracle.

## Obligations and commitments outside baseline debt

None of these is added to borrowing, lease liabilities or any ratio.

| Item | Amount as disclosed | Reporting date | Location | Status |
|---|---|---|---|---|
| Additional lease commitments, "substantially all related to data center arrangements", expected to commence between Q2 fiscal 2027 and fiscal 2029, terms of 15 to 19 years | "$288 billion" | 2026-08-31 | 10-Q Note 6, p. 13 (tag `orcl:LesseeOperatingLeaseLeaseNotYetCommencedLeaseCommitments`, an Oracle extension tag, scale 9; not in companyfacts, which carries only standard taxonomies) | Future commitment; "not reflected on our condensed consolidated balance sheets ... or in the maturities table" |
| Unconditional purchase and certain other obligations with terms of one year or more, "primarily related to long-term supply arrangements for purchasing components for cloud infrastructure assets and power supply arrangements for data centers" | 34,150 (by fiscal year: 5,449; 6,176; 3,863; 4,318; 6,768; 954; thereafter 6,622) | 2026-08-31 | 10-Q Note 6, p. 13 (tag `UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount`) | Future commitment; unrecorded |
| Guarantee of a lessor's borrowing, for a data center lease included in the lease commitments; the borrowing "matures in September 2026" | "up to $3.3 billion" | 2026-05-31 | 10-K Note 9: Leases and Other Commitments, p. 90 | Guarantee; not stated as recognized. **Status at Aug 31, 2026 not stated:** the 10-Q does not mention it (no "guarantee" text found in the 10-Q). |
| Additional lease commitments at the 10-K date (same disclosure as the $288 billion, earlier date) | "$260 billion" | 2026-05-31 | 10-K Note 9, p. 90 | Superseded by the 10-Q figure; shown for change only |
| Unconditional purchase and certain other obligations at the 10-K date, "primarily related to data center power arrangements" | 13,309 | 2026-05-31 | 10-K Note 9, p. 90 | Superseded by the 10-Q's 34,150 |
| Purchase commitments entered into after May 31, 2026, "for cloud infrastructure assets that commence in fiscal 2027 and have a term of five years" | "$19 billion" | after 2026-05-31 (10-K subsequent-event text) | 10-K Note 9, p. 90 | Future commitment. Whether it is inside the 10-Q's 34,150 is not stated; do not add it to that total. |

**Overlap:** the 10-Q presents the two as separate disclosures: leases not yet commenced under "Leases", and supplier purchase obligations under "Unconditional Obligations". It does not state whether the purchase obligations exclude every lease component; power supply arrangements for data centers could in principle contain one. **No combined amount is presented**; the two are shown separately.

**First-release obligations note for Oracle (decided Oct 14, 2026):**
- **Shown, as separate Aug 31, 2026 disclosures and never totaled:** the $288 billion of leases not yet commenced, and the 34,150 of unconditional purchase and certain other obligations.
- **Shown as a May 31, 2026 historical contingent exposure only:** the guarantee of up to $3.3 billion of a lessor's borrowing. The 10-K says the related lease is among its additional lease commitments and the borrowing matures in September 2026. Its later status is unverified. It is not current debt, and its maximum is not added to the lease figure.
- **Dated context only:** the $19 billion of purchase commitments entered after May 31, 2026, because the filings do not establish whether they are inside the Aug 31 34,150.
- **Left out of the note:** customer prepayments (a cash flow, see above), tax liabilities, and legal matters without stated amounts. The superseded May 31 lease ($260 billion) and purchase obligation (13,309) figures stay in this evidence file only.

Also not borrowing:
- 6.50% Series D Mandatory Convertible Preferred Stock, 4,954 in stockholders' equity (10-Q balance sheet, p. 1). It is equity, not debt.
- The ATM common stock program was fully used during the quarter ended Aug 31, 2026: about 141 million shares for net proceeds of $19.9 billion (10-Q Note 7, p. 13; MD&A, p. 35). It is equity, inside the quarter.

**Sections checked:**
- **10-Q:** balance sheet (p. 1), statement of operations (p. 2), cash flow statement (p. 5); notes on restricted cash and customer prepayments (pp. 6-7; note number not recorded); Note 2 fair value (p. 9); Note 3 property, plant and equipment (p. 9); Note 6 Leases and Other Commitments (pp. 12-13); Note 7 Stockholders' Equity (p. 13); MD&A interest expense (p. 32), liquidity, cash flows, recent financing and contractual obligations (pp. 33-35).
- **10-K:** MD&A interest expense (p. 50) and liquidity (p. 52); balance sheet (p. 64); cash flow statement and supplemental data (p. 68); Note 6 Notes Payable and Other Borrowings (pp. 83-84); Note 9 Leases and Other Commitments, including unconditional obligations and guarantees (p. 90).
- **Skimmed for stated commitment amounts, none found:** 10-K Note 15 Legal Proceedings (p. 103) and 10-Q Note 11 Legal Proceedings (pp. 19-20), where Oracle says it does not expect material losses; 10-K income tax note (p. 99) and 10-Q Note 8, which describe audits and uncertain tax positions. Uncertain tax position amounts were not extracted; they are tax liabilities, not financing commitments.
- **Full-text searches of both documents:** capitalized interest, short-term financing, commercial paper, not yet commenced, unconditional, guarantee, purchase obligation, significant financing component, letter of credit, reasonably possible.
- **Tagged facts listed:** every fact in both filings whose tag mentions commercial paper, short-term, financing, payable, other liabilities or accrued.

## Financing filings since the balance sheet

No relevant financing filing identified among 8-K, 8-K/A, 424B2 and FWP filings filed from August 31, 2026 through October 14, 2026, checked as of October 14, 2026.

The complete EDGAR filing list (submissions JSON, 1,000 most recent filings back to 2016-05-03) was retrieved Oct 14, 2026 at 2:46 PM laptop time; the newest filing in it was dated October 1, 2026. Forms in the range: 8-K (2), 10-Q, DEF 14A, DEFA14A, Forms 3/4/144. No 8-K/A, 424B2 or FWP. Both 8-Ks and their exhibits were screened by content.

| Event date | Filed | Form, items | Accession | What it is | Amounts |
|---|---|---|---|---|---|
| 2026-09-10 | 2026-09-10 | 8-K, 2.02, 8.01, 9.01 | [0001193125-26-387905](https://www.sec.gov/Archives/edgar/data/1341439/000119312526387905/) | Q1 fiscal 2027 earnings release (EX-99.1). It reports that "During Q1 FY 2027" Oracle completed the sale of $20 billion of common stock (before commissions) through its ATM program. That sale was equity and was completed within the quarter ended Aug 31, 2026, so it is not a post-balance-sheet event and is already in the Aug 31 figures. Item 8.01 declares dividends on the preferred ($1,625 per share) and common ($0.50 per share) stock. | None that is debt or facility capacity. The $20 billion is equity proceeds (before commissions; $19.9 billion net per the 10-Q). The dividends are declared payments to stockholders. |
| 2026-09-12 | 2026-09-14 | 8-K, 8.01, 9.01 | [0001193125-26-389753](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389753/) | Press release: the Executive Chair cancelled his Rule 10b5-1 stock sale plan; no shares were sold under it. | None |

## Open gaps

1. Commercial paper at Aug 31, 2026 is not stated, and the filings' commercial paper cash flows conflict (10-Q "—" vs $1.1 billion; 10-K (2,285) vs $851 million). The composition of the 125,337 at Aug 31 is unknown.
2. "Short-term financing related to capital expenditures": balance, terms and balance-sheet line not disclosed in the sections checked. It is not added to debt. Revisit if a later filing discloses a balance.
2a. The $3.3 billion lessor-borrowing guarantee: status after its September 2026 maturity is not stated in any filing checked.
3. Interest expense: capitalized interest is not stated, and whether finance lease interest and significant-financing-component interest are inside the "Interest expense" line is not stated. The label must say the basis is not stated beyond "before interest income".
4. Confirm by hand the balance-sheet lines that hold current operating lease liabilities and finance lease liabilities.
5. The overlap between the leases not yet commenced and the unconditional purchase obligations is not stated; keep them separate.
6. Uncertain tax position amounts not extracted (tax liabilities, outside the financing scope).
