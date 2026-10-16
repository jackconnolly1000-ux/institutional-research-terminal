# Oracle historical reported-line interest coverage

Checked October 16, 2026 from the saved filings below. TTM September 1, 2025–August 31, 2026:

**Reported operating income 23,057M / reported Interest expense 5,104M = 4.52x.**

This is an accrual earnings ratio using Oracle's reported expense line. Borrowing-only interest coverage, capitalization basis, covenant headroom and drawable capacity remain Unavailable. No forecast, adjusted operating income or cash interest measure is substituted.

## Exact sources and periods

| Role | Duration | Source | Operating income, USD millions | Interest expense, USD millions | Lease-note interest, USD millions |
| --- | --- | --- | ---: | ---: | ---: |
| FY2026 | June 1, 2025–May 31, 2026 | [10-K filed June 22, 2026](https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm), 0001193125-26-277521 | 20,606 | 4,599 | 279 |
| Add Q1 FY2027 | June 1–August 31, 2026 | [10-Q filed September 11, 2026](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.htm), 0001193125-26-389274 | 6,728 | 1,428 | 126 |
| Less Q1 FY2026 | June 1–August 31, 2025 | Same current 10-Q's comparative column | 4,277 | 923 | 48 |
| TTM | September 1, 2025–August 31, 2026 | FY2026 + Q1 FY2027 − Q1 FY2026 | **23,057** | **5,104** | **357** |

The annual statements of operations are on printed p. 65; annual MD&A interest discussion is p. 50. Quarterly operations are p. 2; quarterly MD&A interest discussion is p. 32. The numerator is reported `us-gaap:OperatingIncomeLoss`, without addbacks. Interest uses exactly `us-gaap:InterestExpense`. Finance-lease context uses `us-gaap:FinanceLeaseInterestExpense`, separately disclosed in annual Leases Note 9 p. 88 and quarterly Note 6 p. 12.

All selected facts are undimensioned USD facts, scale 6, decimals −6, entity CIK 1341439. Annual context is `C_24317829-d237-4c29-bae3-2e46dd1ae625`; current quarter is `C_f2f9ad85-08df-4e59-8948-bfd9405570de`; comparative is `C_a0bdcecc-b2bf-40f4-8106-f50197737571`. Segment operating-income facts are retained in the test fixture but never substituted for consolidated income. Agreeing repeats count once. Exact dates and accessions are required; no quarter annualization or overlapping quarters are summed.

## Interest composition and capitalization

- The statements display Interest expense separately before non-operating income, which MD&A says consists primarily of interest income and other items. The denominator is used before any interest-income offset. Its tag records a positive expense even though the statement prints a parenthesized deduction from operating income.
- MD&A explains the increase primarily by higher average borrowing from senior-note issues, partly offset by scheduled debt repayments. This is not a full component reconciliation or proof that the line contains only borrowing interest.
- Full-text searches of both saved filings for capitalized/capitalised interest, interest capitalization, interest costs and related terminology do not establish a capitalization basis or amount. Capitalized interest and total interest incurred remain Unavailable. No amount is assumed zero, added or subtracted.
- Finance-lease interest is 279 + 126 − 48 = 357M TTM. The filings do not reconcile this note disclosure to the selected Interest expense line. It is context only and is neither added nor subtracted, avoiding unsupported double counting.
- The annual revenue policy (p. 71) discusses contract interest as interest expense or interest income in non-operating income (expenses), net. Annual customer-prepayment disclosure (p. 73) and the quarterly note (p. 7) describe the related significant-financing-component interest as immaterial. That is not zero or an exact amount. The quarterly note says it is separate from revenue without supplying a quantitative reconciliation to the selected line. Borrowing-only interest and coverage cannot be isolated.

The app and workbook therefore label **reported-line** coverage and explicitly leave these unsupported measures Unavailable. The ratio does not establish cash available for repayments. Prepayment cash receipts and equity proceeds are not earnings or added to the numerator. Operating income includes reported operating charges; it is not adjusted EBITDA.

## Covenant distinction

Oracle's revolver requires contract-defined Consolidated EBITDA / Consolidated Net Interest Expense of at least 3.0x. The contract includes specified adjustments, cash interest, finance-lease interest and interest-income netting. This historical operating-income/reported-expense ratio uses different definitions. It is not compared with 3.0x to calculate headroom, and it does not establish current compliance or drawable credit. See the existing [revolver audit](oracle_revolver_reconciliation.md).

## Reproducibility and output checks

`oracle_interest.py` reads exact durations using the existing strict `filing_xbrl.read_duration`, checks entity, units, dimensions, source fingerprint and accession, and calculates each TTM component independently. Missing inputs are not zero; zero or negative TTM expense blocks division, while valid operating losses remain negative coverage. Missing supplemental lease context does not invalidate otherwise supported reported-line coverage.

The two trimmed fixtures retain all real facts for the selected tags, including competing segment facts. `tests/fixtures/make_oracle_interest_fixture.py` and `tests/offline/build_oracle_interest.py` require the checked full-source hashes. The frozen `samples/oracle_interest.json` input fingerprint is verified at runtime with recalculation and unchanged disclosure limits. A stale or mismatched review is Unavailable.

The Oracle workbook's existing Cash analysis sheet adds the formula build; its Data sheet retains the nine reported inputs, dates, tags, contexts, dimensions, units and fingerprints. About explains composition and limitations. Its manifest also binds the new coverage source. The existing cash bridge, repayment review, contractual dates, revolver analysis, chart and other-company exports are preserved.
