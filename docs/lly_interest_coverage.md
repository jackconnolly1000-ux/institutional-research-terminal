# Lilly historical interest coverage

Checked October 15, 2026. TTM July 1, 2025–June 30, 2026:

**Derived operating income 33,633M / reported interest expense 1,079M = 31.17x.**

This is historical accrual-based earnings coverage. It is not cash interest coverage, an adjusted earnings measure, a covenant calculation, a financing authorization or a future repayment forecast. No rating or repayment surplus is inferred.

## Sources and exact periods

| Role | Duration | Source | Location |
| --- | --- | --- | --- |
| FY2025 | January 1–December 31, 2025 | [10-K filed February 12, 2026](https://www.sec.gov/Archives/edgar/data/59478/000005947826000013/lly-20251231.htm), 0000059478-26-000013 | Operations p. 57; Borrowings Note 11 p. 77; single-segment explanation in Note 17 |
| Current H1 | January 1–June 30, 2026 | [10-Q filed August 5, 2026](https://www.sec.gov/Archives/edgar/data/59478/000005947826000081/lly-20260630.htm), 0000059478-26-000081 | Operations p. 5; Segment Note 11 p. 23 |
| Prior H1 | January 1–June 30, 2025 | Same August 2026 10-Q's comparative column | Same locations |

TTM = FY2025 + H1 2026 − H1 2025. No overlapping quarters are summed. The prior half is the comparative **493M** reported in the current 10-Q, not an older 492.7M companyfacts value or the 249M three-month comparative. Current interest is 677M for six months, not 345M for three months.

## Interest denominator and capitalization basis

All three facts use `us-gaap:InterestExpenseNonoperating`, USD, scale 6, decimals −6. Annual context c-1 is undimensioned. The quarterly reader permits exactly `us-gaap:StatementBusinessSegmentsAxis = lly:ReportableSegmentMember`, supported by Lilly's explicit single-reportable-segment description; it rejects absent, additional or different dimensions. Current context c-397 is H1 2026; c-398 is H1 2025. This rule is Lilly-specific.

| Input | USD millions |
| --- | ---: |
| FY2025 interest on borrowings | 895 |
| Add H1 2026 reported interest | 677 |
| Less H1 2025 reported interest | (493) |
| TTM reported expense | **1,079** |

The annual Note 11 caption explicitly describes borrowing interest net of capitalized interest. The interim segment table labels the line interest expense without explicitly stating its capitalization basis. The app and workbook state that distinction. Neither the amount capitalized nor total interest incurred is established here. No capitalization amount is assumed zero, added to or subtracted from expense; no interest-income offset is applied. The result is not labeled gross interest incurred or wholly confirmed net-of-capitalization TTM expense.

## Numerator: derived and reconciled, not a reported subtotal

Lilly does not report an `OperatingIncomeLoss` fact or operating-income subtotal in these statements. The selected numerator is explicitly derived from the consolidated operations table:

Revenue − cost of sales − R&D − SG&A − acquired IPR&D expense − asset impairment, restructuring and other special charges.

| Statement input, USD millions | FY2025 | H1 2026 | H1 2025 |
| --- | ---: | ---: | ---: |
| Revenue | 65,179 | 42,773 | 28,286 |
| Cost of sales | 11,052 | 6,845 | 4,672 |
| R&D | 13,337 | 7,329 | 6,070 |
| SG&A | 11,094 | 6,364 | 5,221 |
| Acquired IPR&D expense | 2,910 | 3,360 | 1,726 |
| Impairment/restructuring/special charges | 484 | 982 | 35 |
| **Derived operating income** | **26,302** | **17,893** | **10,562** |
| Pretax income, reported control | 25,731 | 18,097 | 10,233 |
| Tagged nonoperating income (expense) | (571) | 204 | (329) |
| **Control: pretax − tagged nonoperating** | **26,302** | **17,893** | **10,562** |

The standard `NonoperatingIncomeExpense` tag is positive income and negative expense, opposite the printed Other—net (income) expense row convention. Preserve the tagged sign and subtract it in the control. Each period must reconcile independently before coverage is calculated.

TTM numerator: 26,302 + 17,893 − 10,562 = **33,633M**. Acquired IPR&D and special charges remain expenses. There are no normalization addbacks, and the cash acquisition/IPR&D lines are not substituted for accrual expenses.

## Selection, reproducibility and missing data

`lly_interest.py` reads the actual inline facts. Operating inputs come only from the unique consolidated operations table identified by the required standard tags. This matters because rounded MD&A IPR&D repeats (for example 3.4B versus 3,360M) otherwise conflict with the detailed statement. The generic XBRL reader is not relaxed to choose convenient duplicates. Missing/ambiguous statements, conflicting facts, wrong units, periods, entities or dimensions are refused.

`tests/fixtures/LLY_2025_interest.htm` and `LLY_2026H1_interest.htm` preserve the real operations tables, interest facts, contexts, units and competing rounded IPR&D repeats. The fixture builder requires the checked full-source fingerprints. The sample builder verifies the annual/quarterly hashes and the extracted-input fingerprint before freezing `samples/lly_interest.json`. Runtime loading checks the input fingerprint, basis and recalculated result; a stale or edited review is Unavailable.

Missing numerator or denominator facts never become zero. A supported denominator or numerator remains available independently. A nonpositive TTM denominator blocks division. Valid negative operating income produces negative coverage. The workbook also blocks the ratio when any operating reconciliation fails and propagates missing inputs rather than presenting a healthy result.

The Lilly app and workbook use the same saved model; all reported inputs retain tag, duration, context, dimensions, unit, scale, decimals, accession, source and selection rule. Derived operating income and coverage have no SEC tag. The original metrics, cash build, contractual maturity schedule, catalysts and other-company reviews remain intact.
