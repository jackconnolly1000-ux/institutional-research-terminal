# Oracle debt maturities and financing review

Checked October 14, 2026, using the saved SEC documents. This extends the frozen company review. It does not reconstruct a current debt maturity schedule or calculate a funding forecast.

## Principal schedule

Source: [10-K for May 31, 2026, Note 6, pp. 83–85](https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm), filed June 22, 2026, accession `0001193125-26-277521`. The table is on printed p. 84 and states future principal payments for **all borrowings**. Interest and leases are excluded. Fiscal years end May 31.

| Due period | Principal, USD millions |
|---|---:|
| Fiscal 2027 (Jun 1, 2026–May 31, 2027) | 7,210 |
| Fiscal 2028 | 10,145 |
| Fiscal 2029 | 5,500 |
| Fiscal 2030 | 7,250 |
| Fiscal 2031 | 9,750 |
| Thereafter (fiscal 2032 onward, combined) | 90,250 |
| Reported principal total | 130,105 |

Independently checked against the printed table:

- 7,210 + 10,145 + 5,500 + 7,250 + 9,750 + 90,250 = **130,105M principal**.
- Principal less **564M** unamortized discounts and issuance costs = **129,541M carrying debt**, matching Note 6 and the May balance sheet.
- The first five fiscal years total **39,855M**, or **30.6%** of that principal total.
- The chart shows the five annual buckets. The **90,250M thereafter** amount is separately labeled as a combined amount, not an annual bar.

`oracle_financing.build()` reads the six exact standard maturity tags, `DebtInstrumentFaceAmount`, `DebtInstrumentUnamortizedDiscountPremiumAndDebtIssuanceCostsNet`, and `DebtLongtermAndShorttermCombinedAmount` through `filing_xbrl.read_instant()`. All selected facts use instant May 31, 2026, context `C_f62bade6-47e1-4441-9bb3-1e534300c2f2`, USD, scale 6, decimals -6, with no dimensions. The selected context's entity CIK must be Oracle's. The six bucket tags are recorded in `BUCKETS` and in the saved evidence, not inferred from another company's presentation. Missing, negative, conflicting, wrong-date, wrong-unit or wrong-entity inputs prevent the schedule total.

## August balance sheet and quarter flows

Source: [10-Q for August 31, 2026](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.htm), filed September 11, 2026, accession `0001193125-26-389274`.

- Balance sheet p. 1: **36,369M cash**, **7,625M current borrowing**, **117,712M noncurrent borrowing**. These carrying amounts retain their existing verified calculation.
- Cash flows p. 5, June 1–August 31: **19,909M net common-stock proceeds** (`us-gaap:ProceedsFromIssuanceOfCommonStock`) and **4,202M debt repayments** (`us-gaap:RepaymentsOfDebt`). Exact duration, USD and company CIK checked. Context `C_f2f9ad85-08df-4e59-8948-bfd9405570de`, scale 6, decimals -6.
- MD&A p. 33 describes about **3.1B** scheduled debt repayments and **1.1B** commercial-paper repayments. The cash-flow commercial-paper line shows a dash. The previously recorded presentation difference remains unresolved.
- **No updated debt maturity table is disclosed in the saved 10-Q.** Its lease maturity table is not a borrowing maturity table. The May fiscal 2027 bucket includes months already elapsed by August 31. Neither subtracting the quarter's combined repayments from that bucket nor treating 7,625M current carrying debt as remaining fiscal 2027 principal is supported.
- Cash, historical TTM FCF, and the May principal buckets are not combined into a future funding surplus, shortfall or coverage ratio. The quarter's equity proceeds are already reflected in August balances, and are not added again.

## Later 8-K checks

Read the full saved main documents and their Exhibit 99.1. Official SEC filing indexes independently confirm dates and forms:

| Event / filed | Filing | Finding |
|---|---|---|
| Sep 10 / Sep 10, 2026 | [8-K …-387905](https://www.sec.gov/Archives/edgar/data/1341439/000119312526387905/0001193125-26-387905-index.htm); [earnings exhibit](https://www.sec.gov/Archives/edgar/data/1341439/000119312526387905/orcl-ex99_1.htm) | Q1 results and declared dividends. The exhibit says the **20B gross equity sale happened during Q1**, before the balance sheet. It is the same equity program as the 10-Q's 19,909M net proceeds, not another transaction or later borrowing. |
| Sep 12 / Sep 14, 2026 | [8-K …-389753](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389753/0001193125-26-389753-index.htm); [exhibit](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389753/d20034dex991.htm) | Executive Chair cancelled his Rule 10b5-1 sale plan. No shares were sold under it. No corporate financing event identified. |

Neither establishes new borrowing after August 31. This feature verifies the two saved filings; it does not independently recreate a complete post-balance-sheet submissions inventory. The earlier inventory review is documented in `pilot_evidence_oracle.md`. Live inventories join these findings only on exact accession, form, filed date, event date and the August 31 anchor. Unknown or later documents remain **Not checked**, and incomplete indexes retain that status. No event changes the dated balance-sheet amounts.

## Facility terms and limits

The 10-K Note 6, p. 85 reports a **10B** five-year unsecured revolver entered March 6, 2026, with no outstanding borrowing at May 31, maturing March 6, 2031 subject to the agreement. Capacity is neither cash nor additional debt. August 31 availability is not established by the saved 10-Q. Revolver and commercial-paper program capacities are not added as separate liquidity sources.

The reported covenant is **Consolidated EBITDA / Consolidated Net Interest Expense ≥ 3.0x**, using the agreement's definitions. Oracle reports compliance at May 31. The review does not calculate current compliance or headroom and does not substitute operating-income interest coverage for that contractual measure. Underlying credit-agreement exhibits have not been fully reviewed for this feature.

Open issues: current maturity schedule, current revolver availability, commercial-paper composition/presentation, capex financing balance, the $3.3B lessor guarantee's later status, complete covenants and financing terms. Interest coverage is still not built.

## Reproduction and export

1. `tests/fixtures/make_oracle_maturity_fixture.py` preserves all 71 real maturity/control facts and 6 quarterly financing facts, their contexts and units, without changing values. It reads the two full saved Oracle filings outside the repository.
2. `tests/offline/build_oracle_financing.py` rebuilds `samples/oracle_financing.json` with production readers and reconciliation checks. No network or paid calls.
3. The review attaches only to the checked August Oracle snapshot. Excel adds **Oracle maturities**, **Oracle debt inputs**, and **Oracle financing**. Stored amounts are full USD, displayed in millions; dates are numeric Excel dates. Formulas link reported inputs, reconcile totals, and calculate the five-year share. The native chart covers the five annual buckets. There is no inferred August maturity schedule or duplicated equity issuance.
