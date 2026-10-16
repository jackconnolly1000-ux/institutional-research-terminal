# Pilot evidence: Eli Lilly (LLY)

Evidence for the first debt and liquidity pilot (see `debt_liquidity_plan.md`): filing values with sources and checks, hand calculations labeled as such, and open gaps. Checked values are the pilot's expected answers; Unavailable items and open gaps are not. Checked Oct 14, 2026. The saved debt and liquidity pilot uses the checked cash, borrowing and current-position values; other sections retain their own status.

**How it was checked:** each amount was read from the filing's HTML text (row label and column) and matched to the inline XBRL fact on that row, then compared with SEC companyfacts. Page numbers are the filing's printed page footers. Any value marked "provisional" has not been checked against the filed table and is not an acceptance value (none at present). Raw downloads are retained outside the public repository; the workbook records SEC document URLs and accessions.

**Rounding rule:** a tagged value is compared with a printed figure after rounding the tagged value to the printed figure's precision, half away from zero. Example: companyfacts' $492.7 million rounds to $493 million, which matches the $493 million printed in a table "in millions".

## Filings

| Filing | Period | Filed | Accession | Link |
|---|---|---|---|---|
| 10-Q (balance-sheet date for the pilot) | 2026-06-30 | 2026-08-05 | 0000059478-26-000081 | https://www.sec.gov/Archives/edgar/data/59478/000005947826000081/lly-20260630.htm |
| 10-K | 2025-12-31 | 2026-02-12 | 0000059478-26-000013 | https://www.sec.gov/Archives/edgar/data/59478/000005947826000013/lly-20251231.htm |

Companyfacts: https://data.sec.gov/api/xbrl/companyfacts/CIK0000059478.json (CIK 59478).

## Balance sheet at June 30, 2026 (10-Q, USD millions)

| Item | Amount | Location | Tag | In companyfacts |
|---|---|---|---|---|
| Cash and cash equivalents | 8,950 | Consolidated Condensed Balance Sheets, p. 7 | `CashAndCashEquivalentsAtCarryingValue` | Yes |
| Cash, cash equivalents and restricted cash (cash flow statement) | 8,950 | Cash flow statement, p. 8 | `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations` | Yes. Equal to the line above, so no restricted cash is included. |
| Total current assets | 64,672 | Balance sheet, p. 7 | `AssetsCurrent` | Yes |
| Total current liabilities | 47,741 | Balance sheet, p. 7 | `LiabilitiesCurrent` | Yes |

## Borrowing at June 30, 2026 (10-Q, USD millions, carrying amounts)

Two presentations of the same debt. **Do not add them together.**

| Presentation | Line | Amount | Location | Tag (dimensions) | In companyfacts |
|---|---|---|---|---|---|
| A, balance sheet | Short-term borrowings and current maturities of long-term debt | 7,050 | Balance sheet, p. 7 | `DebtCurrent` (none) | Yes |
| A, balance sheet | Long-term debt | 47,858 | Balance sheet, p. 7 | `LongTermDebtNoncurrent` (none) | Yes |
| B, fair value table | Short-term commercial paper borrowings, carrying amount | 5,284 | Note 8: Financial Instruments, p. 17 | `CommercialPaper` (carrying amount, commercial paper, Level 2) | No: dimensioned |
| B, fair value table | Long-term debt, including current portion, carrying amount | 49,624 | Note 8, p. 17 | `LongTermDebt` (carrying amount, Level 2) | No: dimensioned |

- A: 7,050 + 47,858 = 54,908. B: 5,284 + 49,624 = 54,908. The two agree.
- Current maturities of long-term debt are not reported as their own line; 7,050 - 5,284 = 1,766 is a hand calculation.
- Fair value of the same debt (5,280 and 46,555) is not carrying amount and is not used.
- Context, not debt: $10.1 billion of unused committed bank credit facilities (MD&A, liquidity). This is facility capacity, not borrowing.

December 31, 2025 (10-K, companyfacts): `DebtCurrent` 1,635 + `LongTermDebtNoncurrent` 40,868 = `DebtLongtermAndShorttermCombinedAmount` 42,503 (a total that overlaps its parts); `CommercialPaper` 0.

## Leases (USD millions)

| Item | Amount | Date | Location | Tag | Status |
|---|---|---|---|---|---|
| Operating lease liabilities, current | 222 | 2025-12-31 | 10-K Note 10: Leases, p. 76; on the balance sheet within "Other current liabilities" | `OperatingLeaseLiabilityCurrent` (no dimensions, context c-16, USD, scale 6) | Checked Oct 14, 2026: printed table cell matches the tagged fact and companyfacts |
| Operating lease liabilities, noncurrent | 1,140 | 2025-12-31 | 10-K Note 10, p. 76; within "Other noncurrent liabilities" | `OperatingLeaseLiabilityNoncurrent` (no dimensions, context c-16, USD, scale 6) | Checked Oct 14, 2026, same way |
| Operating lease liabilities at 2026-06-30 | Unavailable | | | | The 10-Q does not report them |
| Finance leases | Unavailable | | | | Note 10 describes only operating leases; no finance lease tags in companyfacts. Not reported is not zero. |

## Interest expense on borrowings (USD millions)

| Period | Amount | Location | Tag | In companyfacts |
|---|---|---|---|---|
| FY2025 | 895 | 10-K Note 11: Borrowings, p. 77, "Interest expense on borrowings", in a table described as "net of capitalized interest" | `InterestExpenseNonoperating` (no dimensions) | Yes |
| Q2 2026 (3 months) | 345 | 10-Q Note 11: Segment Information, p. 23 | `InterestExpenseNonoperating`, segment-dimensioned (see below) | No |
| Six months 2026 | 677 | Same | Same | No |
| Six months 2025 | 493 | Same (comparative column) | Same | Not from this filing. Companyfacts has 492.7 from the 2025 Q2 10-Q (accession 0000059478-25-000204, filed 2025-08-07); by the rounding rule it matches 493. |

**Inline XBRL contexts checked (10-Q, accession 0000059478-26-000081):**

| Context | Period | Printed value | Tag | Dimensions | Unit | Scale / decimals |
|---|---|---|---|---|---|---|
| c-395 | 2026-04-01 to 2026-06-30 | 345 | `us-gaap:InterestExpenseNonoperating` | one: `StatementBusinessSegmentsAxis` = `lly:ReportableSegmentMember` | iso4217:USD | 6 / -6 |
| c-396 | 2025-04-01 to 2025-06-30 | 249 | same | same, no others | iso4217:USD | 6 / -6 |
| c-397 | 2026-01-01 to 2026-06-30 | 677 | same | same, no others | iso4217:USD | 6 / -6 |
| c-398 | 2025-01-01 to 2025-06-30 | 493 | same | same, no others | iso4217:USD | 6 / -6 |

These agree with the printed Note 11 table. Lilly reports a single reportable segment, which supports an LLY-specific decision to use these facts; it is not a universal rule. **The app's TTM coverage stays Unavailable until an extractor performs these checks and passes.**

- Hand calculation from rounded filing figures, not an exact SEC fact: 895 + 677 - 493 = 1,079 USD millions, TTM to June 30, 2026.
- Capitalized interest: the FY2025 10-K states the expense is net of capitalized interest but discloses no amount. Companyfacts' `InterestCostsCapitalized` stops at FY2013. The coverage denominator stays reported interest expense, labeled "net of capitalized interest"; capitalized interest is not added.

## Financing filings since the balance sheet

No relevant financing filing identified among 8-K, 8-K/A, 424B2 and FWP filings filed from June 30, 2026 through October 14, 2026, checked as of October 14, 2026.

The complete EDGAR filing list (submissions JSON, 1,000 most recent filings back to 2021-12-16) was retrieved Oct 14, 2026 at 2:10 PM laptop time; the newest filing in it was dated October 8, 2026. Forms screened by content: 8-K and its exhibits, 8-K/A, 424B2, FWP.

| Event date | Filed | Form, items | Accession | What it is | Amounts |
|---|---|---|---|---|---|
| 2026-08-05 | 2026-08-05 | 8-K, 2.02 and 9.01 | [0000059478-26-000077](https://www.sec.gov/Archives/edgar/data/59478/000005947826000077/) | Q2 2026 earnings release (EX-99.1). Screened for debt, borrowing, credit facility, commercial paper, notes, leases, financing, repayment and interest: no financing content. | None relevant |

No 8-K/A, 424B2 or FWP was filed in the range. The May 2026 $9.0 billion notes (424B2 and FWP filed May 6 to 8, 8-K Item 8.01 on May 20) predate June 30 and are already in the balance sheet above.

## Obligations and commitments outside baseline debt

None of these is added to debt, lease liabilities or any ratio. Which ones count as "major" for the app's note is still to be decided; all items with a stated amount found in the sections checked are listed.

| Item | Amount as disclosed | Reporting date | Location | Status |
|---|---|---|---|---|
| Contract manufacturing and supply agreements for medicines in development: payments if specified purchase amounts are not met, over terms generally up to 8 years | "up to approximately $10 billion" | 2025-12-31 | 10-K MD&A, liquidity and capital resources, p. 51 | Future, conditional commitment; not recognized as a liability. Not updated in the 10-Q, which refers back to the 10-K. |
| Pending acquisition of AtaiBeckley Inc., subject to closing conditions | "approximately $2.8 billion" payable at closing | Disclosed 2026-08-05, after quarter end | 10-Q MD&A, Financial Condition and Liquidity, p. 31 | Future commitment; not recognized |
| Unfunded commitments to invest in venture capital funds, paid over up to 10 years | "approximately $806 million" ($902 million at 2025-12-31, 10-K p. 51) | 2026-06-30 | 10-Q MD&A, p. 31; Note 8 | Future commitment; not recognized |
| Contingent consideration from business combinations | $814 million current + $1,704 million noncurrent | 2026-06-30 | 10-Q Note 8: Financial Instruments, p. 17 (tags `BusinessCombinationContingentConsiderationLiabilityCurrent` / `Noncurrent`) | Recognized liability, within other current and other noncurrent liabilities; not borrowing |
| Development milestone and royalty payments under collaboration and R&D arrangements | No aggregate amount stated | 2025-12-31 | 10-K MD&A, off-balance sheet discussion, pp. 52-53; Note 3 referenced | Conditional on future events; not recognized. The 10-K says they are generally not material individually in a year. |

Related, not commitments: in July 2026, after the balance sheet, Lilly paid about $2.0 billion to acquire companies (10-Q p. 31). Lilly states it has no off-balance sheet arrangements with a material current or likely future effect (10-K p. 52).

**Sections checked:** 10-K MD&A liquidity and capital resources through the off-balance sheet discussion (pp. 50-53, read in full), Note 10: Leases, Note 11: Borrowings; 10-Q MD&A Financial Condition and Liquidity (pp. 30-31, read in full), Note 8: Financial Instruments. Both documents were also searched in full for: contractual obligation, purchase obligation, material cash requirement, commitment, not yet commenced, guarantee, off-balance, unconditional, capital commitment, milestone payments, agreed to acquire, definitive agreement. **Not reviewed for amounts:** the 10-K and 10-Q contingencies notes (litigation), income tax notes, and 10-K Note 3 (collaborations) and Note 7 (investments) in detail. Other commitments may exist in those sections.

## Open gaps

1. Decide which of the obligations above count as "major" for the app's note.
2. Build and test an extractor for LLY's segment-dimensioned interest facts before any TTM coverage is shown.
3. Contingencies, income tax, collaboration and investment notes not reviewed for commitment amounts.
4. Debt source for the app: decided Oct 14, 2026 as presentation A (balance sheet, `DebtCurrent` + `LongTermDebtNoncurrent`), implemented in `xbrl.baseline_gross_debt`. Presentation B is not added.

## Saved company review: cash generation

The frozen app review now shows checked TTM operating cash flow, reported capital spending, FCF and flow/debt ratios. Full reconciliation, exact source periods, tag definitions and caveats: [pilot_cashflow_reconciliation.md](pilot_cashflow_reconciliation.md). The selected obligations note is incomplete and does not add commitments or lease liabilities to baseline borrowing. Existing open gaps remain open.


## Dated funding review (October 15, 2026)

Implemented in `lly_liquidity.py`, the app and Lilly-only Excel. See [the dated review](lly_liquidity_review.md) for H1 cash reconciliation, historical carrying amounts by due year, facilities, unpaid and subsequent acquisitions, contingent-consideration valuation, and manufacturing commitments. This adds a selected Note 4/Note 8 review; it does not close all contingency/investment gaps. The updated June principal schedule, drawable facilities/renewal and detailed payment calendars remain Unavailable.


## Financing inventory update (October 15, 2026)

The [financing audit](lly_financing_audit.md) compares saved documents to the SEC index through October 15 and records the missing May debt documents. Eight initial series totaling $9B have stated maturities; they are already in June debt/proceeds and are not a current outstanding-principal schedule. No supported August 2026 facility renewal or drawable amount was identified. The app and Lilly Excel add the contractual dates and flag the 8-K/certificate coupon conflict.
