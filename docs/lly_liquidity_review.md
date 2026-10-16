# Lilly: dated liquidity and repayment review

Reviewed October 15, 2026, using the saved FY2025 10-K, June 2026 10-Q and August 5 earnings exhibit. This is not a complete current SEC filing inventory. The app and Lilly workbook use `samples/lly_liquidity.json`, built by `lly_liquidity.py`; this document records interpretation and remaining gaps.

## Sources and reproducibility

| Document | Filed | Accession | Locations used |
| --- | --- | --- | --- |
| [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/59478/000005947826000013/lly-20251231.htm) | February 12, 2026 | 0000059478-26-000013 | MD&A p. 51; Note 11 pp. 76–77 |
| [June 2026 10-Q](https://www.sec.gov/Archives/edgar/data/59478/000005947826000081/lly-20260630.htm) | August 5, 2026 | 0000059478-26-000081 | Balance sheet p. 7; cash flows p. 8; Note 4 pp. 12–14; Note 8 p. 17; MD&A p. 31 |
| [August 5 earnings exhibit](https://www.sec.gov/Archives/edgar/data/59478/000005947826000077/q226lillysalesandearningsp.htm), 8-K Ex. 99.1 | August 5, 2026 | 0000059478-26-000077 | Highlights and Other announcements |

`SOURCES` records SHA256 fingerprints for the three full saved documents. The fixture builder and sample builder refuse changed or missing source files before reusing hand-reviewed text disclosures. The primary 8-K contains earnings items, not a new financing agreement. The selected numerical fixtures retain the filing's actual facts, units and contexts, including competing dates and dimensions. The reader checks Lilly's CIK, USD, exact periods and explicitly named dimensions. All amounts below are USD millions unless stated otherwise.

Inline facts and reviewed text are distinct in the JSON and workbook Data sheet. In particular, June's $10.1B unused credit, unpaid acquisition cash, subsequent acquisitions and manufacturing statements are reviewed text; they are not invented undimensioned XBRL facts. No extension-tag definition is inferred. Every input retains accession, document, location, date, source kind and hash; inline facts also retain tag, context, dimensions, scale and decimals.

## What funded the cash increase?

| January–June 2026 contribution | Signed cash effect |
| --- | ---: |
| Operating cash flow | 16,023 |
| Cash PP&E spending | (5,259) |
| Acquisitions net of cash acquired, plus purchased in-process R&D | (13,291) |
| Dividends plus share repurchases | (7,051) |
| Net borrowing | 12,602 |
| Other investing/financing and FX | (1,342) |
| Cash increase | 1,682 |

Opening cash 7,268 + increase 1,682 = closing cash 8,950. Investing cash flow reconciles to (19,312), financing to 4,956 and FX to 15. The first half is not the existing TTM period; the TTM metrics are preserved.

OCF less cash PP&E was **10,764**. Acquisition and IPR&D cash was 9,805 + 3,486 = **13,291**; it already explains the rounded $13.3B business-development statement. Dividends and buybacks were 3,094 + 3,957 = **7,051**. Net borrowing was short-term 5,284 + long-term net proceeds 8,941 − repayments 1,623 = **12,602**. The May $9B face-value issue is already represented in net cash proceeds; it is not future unused funding.

Cash growth does not establish a future repayment surplus. Historical OCF includes working-capital movements; its recurrence is not established. OCF, capex and debt proceeds are already reflected in closing cash and are not added again as available resources. No equity or customer-prepayment exclusion is inferred for Lilly from Oracle's analysis.

## Debt due years: historical carrying amounts

Note 11's table uses `us-gaap:DebtInstrumentCarryingAmount`, with exactly `us-gaap:DebtInstrumentAxis` and the appropriate `lly:NotesDue...Member`. At December 31, 2025:

| Notes due | Carrying amount |
| --- | ---: |
| 2026 | 1,632 |
| 2027 | 2,516 |
| 2028 | 3,256 |
| 2029 | 3,077 |
| 2030 | 2,132 |
| 2031–2040, combined | 11,582 |
| 2041–2050, combined | 4,543 |
| 2051–2060, combined | 8,280 |
| 2061–2070, combined | 5,824 |
| Total notes | 42,842 |

42,842 − other debt/adjustments 339 + commercial paper (reported zero) = reported total debt **42,503**. The XBRL `OtherLongTermDebt` input is positive 339; the printed row is a deduction. The workbook preserves the positive input and applies an explicit −1 presentation coefficient. It does not silently rewrite the source sign.

This is **not a principal cash maturity schedule**. The multi-year buckets are not individual-year payments. June 2026 current borrowing of 7,050 is a balance-sheet classification; current debt less CP does not establish dated principal. The May issuance and half-year repayments are not assigned to annual buckets. An updated June principal schedule and exact repayment dates are **Unavailable**.

## Credit facilities: commitment is not drawable cash

The annual report says unused committed facilities were **10,100** at December 31, of which 10,000 supports CP. Principal facilities described: 4,000 expiring December 2029 and a 6,000 364-day facility expiring August 2026. Exact expiry days and the remaining 100's separate composition are not provided in these disclosures. Annual facts are dimensioned by `DebtInstrumentRedemptionPeriodAxis` and the named maturity member; the printed paragraph supplies August, while the member supplies only 2026.

The 10-Q reports **10,100 unused** at June 30, again 10,000 supporting CP. This does not independently establish June facility-by-facility composition, current draw conditions, permitted uses or post-August renewal. No credit agreement is saved in this Lilly source set. Do not add CP market capacity to supporting bank facilities as independent funding pools. Do not carry June unused commitments past an expiry as current credit availability.

**Drawable credit and covenant headroom: Unavailable.** Cash plus unused commitments is not presented as a verified liquidity total.

## Acquisitions and manufacturing compete for cash

| Amount | Basis/date | Treatment |
| --- | --- | --- |
| 208 Kelonia + 88 Centessa = 296 unpaid cash | June 30, Note 4 p. 13 | Payment dates unstated. Separate from paid cash and contingent fair value. |
| Approximately 2,000 already paid | July infectious-disease acquisitions, MD&A p. 31 | Subsequent historical use; do not subtract from June cash and label the remainder current cash. Other July flows unknown. |
| Up to 3,900 | July acquisitions, Note 4 pp. 13–14 | Includes upfront and possible milestones. Includes the approximately 2,000; no combined total or precise implied remainder. |
| Approximately 2,800 at closing | Pending AtaiBeckley, disclosed August 5 in MD&A | Conditional closing payment, not a June 30 debt balance. Closing date/completion and funding allocation not established here. |
| 814 current + 1,704 noncurrent = 2,518 | June 30 contingent-consideration fair value, Note 8 | Exact Level 3 dimension. A valuation, not a payment calendar or contractual ceiling. Not added to acquisition amounts. |
| Approximately 806 | June 30 venture fund commitments | Expected over up to ten years; individual call dates unknown. |
| Up to approximately 10,000 | December 31 manufacturing/supply arrangements for medicines in development | Conditional payments if specified purchases are not met; durations generally up to eight years. No annual allocation, updated June ceiling, or overlap total inferred. |
| Additional 4,500 | August 5 Indiana manufacturing announcement | Announced investment commitment. Release does not establish contractual cash schedule, spend to date or overlap with capex/supply arrangements. Not added to debt or the 10,000 ceiling. |

**Future funding coverage: Unavailable.** The sources establish historical cash generation and spending, selected conditional amounts and some due-year classifications. They do not jointly establish future dated principal, acquisition/manufacturing payment dates, future OCF or drawable facilities. No forecasts, runway, coverage percentages or blanket funding surplus/shortfall are fabricated.

## Remaining work

Prioritize finding the facility renewal/agreement and later financing disclosures, then exact principal payment schedules and acquisition closing/payment updates. The saved set has not been compared with a current SEC inventory for this task. June lease liabilities, tax/litigation, collaborations and other contingent/investment obligations remain outside this selected review. Existing company metrics, catalysts and other-company reviews are preserved.
