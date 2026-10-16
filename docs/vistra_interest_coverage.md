# Vistra historical interest-component coverage

Checked October 16, 2026. TTM July 1, 2025–June 30, 2026:

**Reported consolidated operating income 3,563M / reported interest component 1,117M = 3.19x.**

The denominator is the debt note's separate Interest expense component, before its capitalized-interest deduction. It is not the statement's mixed Interest expense and related charges total. Receivables/Nuveen allocation, Other detail and a fully allocated all-in financing-cost measure remain Unavailable. This historical accrual ratio is not cash or future repayment coverage, covenant headroom or a verified draw authorization.

## Checked sources and durations

| Role | Exact duration | Filing and source | Operating income | Interest component | Mixed total |
| --- | --- | --- | ---: | ---: | ---: |
| FY2025 | January 1–December 31, 2025 | [10-K filed February 27, 2026](https://www.sec.gov/Archives/edgar/data/1692819/000169281926000006/vistra-20251231.htm), 0001692819-26-000006; operations p. 79, interest table p. 121 | 1,906 | 1,107 | 1,179 |
| Add H1 2026 | January 1–June 30, 2026 | [10-Q filed August 10, 2026](https://www.sec.gov/Archives/edgar/data/1692819/000169281926000019/vistra-20260630.htm), 0001692819-26-000019; operations p. 1, Note 12 p. 28 | 2,052 | 557 | 575 |
| Less H1 2025 | January 1–June 30, 2025 | Same current 10-Q's comparative column and locations | 395 | 547 | 622 |
| Independent prior check | January 1–June 30, 2025 | [10-Q filed August 8, 2025](https://www.sec.gov/Archives/edgar/data/1692819/000169281925000085/vistra-20250630.htm), 0001692819-25-000085; operations p. 1, Note 9 p. 30 | 395 | 547 | 622 |
| TTM, USD millions | FY2025 + current H1 − prior H1 | The independent check is not added | **3,563** | **1,117** | **1,132** |

The selected tags are `us-gaap:OperatingIncomeLoss`, `vistra:PostEmergenceInterestPaidAndAccrued` and `us-gaap:InterestExpenseNonoperating` respectively. All inputs are undimensioned USD facts, scale 6, decimals −6, entity CIK 1692819. Annual, current and original-prior contexts are c-1; the current filing's H1 2025 comparative uses c-7. Three-month facts, parent-only operating losses and segment facts remain in the fixtures but are never substituted. All eight H1 2025 comparative facts agree with their original filing.

## Expense reconciliation and XBRL signs

USD millions; parentheses reduce expense. Every column independently matches the reported total.

| Printed expense component | FY2025 | H1 2026 | H1 2025 | TTM |
| --- | ---: | ---: | ---: | ---: |
| Selected interest component | 1,107 | 557 | 547 | **1,117** |
| Unrealized swap (gain) loss | 67 | (7) | 74 | (14) |
| Debt issuance cost/discount/premium amortization | 46 | 21 | 22 | 45 |
| Extinguishment (gain) loss | 0 | 35 | 0 | 35 |
| Less capitalized interest | (125) | (82) | (56) | (151) |
| Other | 84 | 51 | 35 | 100 |
| **Reconstructed mixed total** | **1,179** | **575** | **622** | **1,132** |
| Reported mixed total | 1,179 | 575 | 622 | 1,132 |
| Difference | 0 | 0 | 0 | 0 |

Raw facts retain their filed signs. `vistra:UnrealizedGainLossOnInterestRateSwapDerivatives` is −67M / +7M / −74M. `us-gaap:GainsLossesOnExtinguishmentOfDebt` is 0 / −35M / 0. Both are gain-positive in these filings, opposite the printed expense rows. The build reverses them. `us-gaap:InterestCostsCapitalizedAdjustment` is positive 125 / 82 / 56 and is subtracted only in this mixed-total reconciliation. Amortization uses `us-gaap:AmortizationOfDebtDiscountPremium`; Other uses `us-gaap:InterestExpenseOther`.

Thus 1,117 − 14 + 45 + 35 − 151 + 100 = 1,132M TTM. The 1,117M component is already before capitalization is deducted; adding 151M would count it again. Subtracting it would create a differently defined measure. Neither adjustment is made to coverage, and interest income from the separate other-income note is not offset.

## Extension definition and limits

The saved June 2026 [schema](https://www.sec.gov/Archives/edgar/data/1692819/000169281926000019/vistra-20260630.xsd) defines the interest extension as a monetary duration item, debit balance, not abstract. Its [labels](https://www.sec.gov/Archives/edgar/data/1692819/000169281926000019/vistra-20260630_lab.xml) give the standard Post-Emergence, Interest Paid And Accrued label and terse Interest expense label. Documentation repeats the name and supplies no receivables/Nuveen allocation or cash-settlement definition. The swap extension is monetary, duration, credit balance; its negated labels match the expense presentation. The schema and label-file fingerprints are checked by the sample builder.

The receivables facility records interest on amounts advanced. Nuveen's forward repurchase obligation also carries interest (current debt-note discussion pp. 27–28). The checked filings do not establish which part of those costs sits in the selected component versus Other, or what Other contains. The unrealized swap line does not identify cash swap settlements or their allocation. None is assumed zero, added to the denominator or assigned by guesswork. A full all-in borrowing/financing-cost denominator remains Unavailable.

Operating income is the consolidated reported subtotal, with no adjusted-earnings addbacks. It retains reported operating and commodity-hedge effects and need not represent recurring cash generation. The ratio is not a covenant test or proof that subsidiary funds can service parent obligations.

## Implementation and verification

`vistra_interest.py` uses the existing strict duration reader for 32 source facts from three checked documents. Wrong dates, units, dimensions, entities, tags or accessions are refused. The mixed-total reconciliation and original comparative match gate coverage. Missing bridge inputs cannot silently become zero. A zero or negative TTM denominator blocks division; a valid consolidated operating loss remains negative coverage.

The fixture builder retains all real occurrences, including parent and segment facts. The saved-model builder requires the three source and two taxonomy fingerprints plus the extracted-input fingerprint. Runtime loading recalculates and checks the frozen inputs and disclosure limits. Future or changed filings need a new review and do not inherit these conclusions.

The app and Vistra Excel use the same checked model. Cash review contains the period build, TTM bridge, ratio and original-prior comparison. Data retains raw signs and provenance. About records definitions and limits. The workbook manifest binds the new source, refusing stale exports. Existing cash generation, repayment dates, facilities, catalysts, source distinctions and other-company exports are preserved.
