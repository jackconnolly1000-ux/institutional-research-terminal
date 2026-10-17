# Oracle borrowing principal calendar at August 31, 2026

Checked October 17, 2026 from the two saved Oracle filings. Model: `oracle_principal.py`. Saved result: `samples/oracle_principal.json` (rebuilt by `tests/offline/build_oracle_principal.py`). Tests: `tests/test_oracle_principal.py`. No new filing was downloaded, and no AI service was used.

**Result:** $125.567B of senior-note and term-loan principal was outstanding at August 31, 2026, every amount with a date. $7.317B of it falls due from September 2026 through August 2027. Commercial paper is excluded: its August balance and maturity dates are not reported, so it stays Unavailable. Neither a principal calendar nor this section establishes funding coverage or drawable credit.

## Sources

| Document | Accession | Used for |
|---|---|---|
| [10-K for fiscal 2026](https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm), filed Jun 22, 2026 | 0001193125-26-277521 | Note 6 debt table, pp. 83–84: each series' principal at May 31, 2026, tagged `us-gaap:DebtInstrumentCarryingAmount` by `DebtInstrumentAxis` or `CreditFacilityAxis` member, with `DebtInstrumentMaturityDate`, original `DebtInstrumentFaceAmount` and stated rate. Maturity buckets p. 84. Term-loan amortization and extension terms, pp. 85–86. Commercial paper, p. 86. |
| [10-Q for Aug 31, 2026](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.htm), filed Sep 11, 2026 | 0001193125-26-389274 | Balance sheet p. 1 (current 7,625M, noncurrent 117,712M). Cash flows p. 5 (4,202M grouped repayments; commercial-paper row zero; no borrowing proceeds). Note 2 p. 9: senior notes and other long-term borrowings at carrying value, $125.0B (tagged with decimals −8). MD&A p. 33: about $3.1B of scheduled debt repayments, about $1.1B of commercial-paper repayment, and $4.6B of long-term borrowings reclassified to current. |

The 10-Q has no borrowing note and no maturity table. The calendar is therefore the 10-K's instrument list carried to August 31 under the rules below.

## Principal versus carrying value

*Principal* is the amount repaid at maturity. *Carrying value* is what the balance sheet shows: principal less unamortized discounts and debt issuance costs (and any hedge adjustment, which was zero at May 31, 2026). At May 31: $130.105B principal − $564M = $129.541B carrying debt, matching the balance sheet.

Oracle tags each series' table amount with `DebtInstrumentCarryingAmount`, but the table amounts are principal before the $564M deduction. They sum to the reported $130,105M "Total senior notes and other borrowings". `DebtInstrumentFaceAmount` on each member is the original issue amount: for the term loan that is $5,630M borrowed, against $5,137M outstanding.

## How each instrument is carried to August 31

| Instruments | Rule | Evidence |
|---|---|---|
| 55 senior notes maturing after Aug 31, 2026 (53 fixed-rate, 2 floating-rate) | Principal carried forward unchanged | Notes don't amortize. No borrowing proceeds in the quarter. Long-term carrying value fell from $128.1B to $125.0B (each to the nearest $0.1B). That decline matches the scheduled maturities below plus discount amortization, which leaves no room for an unreported redemption of any series (the smallest is $500M). |
| $3,000M 2.65% notes due July 15, 2026 | Shown as matured, not in the calendar | Its stated maturity is before Aug 31. MD&A reports about $3.1B of *scheduled* repayments, and this was the only note scheduled to mature in June–August. The 10-Q doesn't name the series repaid. |
| Term loan ($5,630M borrowed, due Aug 16, 2027) | Contract schedule, calculated | 1.25% of the amount borrowed each quarter through June 30, 2026; then 2.50% quarterly from Sep 30, 2026 through Jun 30, 2027; the remainder on Aug 16, 2027. Calculated: $70.375M per installment (paid through Jun 30, 2026), then $140.75M, and a $4,504M remainder. The schedule reproduces the reported $5,419M (May 31, 2025) and $5,137M (May 31, 2026) to under $0.5M. It assumes no prepayment. Oracle may extend the final date by up to 2 years (lenders by a further 2). |
| Commercial paper ($1,468M at May 31) | **Unavailable** at Aug 31 | No maturity dates are disclosed and the August balance is not reported. Total carrying borrowing ($125,337M) less the rounded long-term figure implies about $287M–$387M, a range only. |

**The grouped $4,202M repayment line is never subtracted.** Scheduled principal in June–August was $3,070.375M (the July notes plus the June 30 installment), which agrees with MD&A's rounded $3.1B. The remaining $1,131.6M is consistent with MD&A's "about $1.1B" commercial-paper repayment, but the cash-flow commercial-paper row is a reported zero and the 10-Q doesn't split the grouped line. So the residual isn't used to reduce commercial paper.

## Calendar at August 31, 2026 (USD millions, principal only)

| Period | Principal | Contents |
|---|---:|---|
| Remainder FY2027 (Sep 1, 2026–May 31, 2027) | 2,672.25 | $2,250M 2.80% notes due Apr 1, 2027; term-loan installments Sep 30, Dec 31, Mar 31 ($140.75M each) |
| FY2028 (Jun 1, 2027–May 31, 2028) | 10,144.75 | Jun 30, 2027 installment; $4,504M term-loan remainder Aug 16, 2027; notes due Nov 2027 ($2,750M), Mar 2028 ($2,000M), May 2028 ($750M) |
| FY2029 | 5,500 | |
| FY2030 | 7,250 | |
| FY2031 | 9,750 | |
| Thereafter (FY2032 onward) | 90,250 | Combined; the instrument list gives each date |
| **Total, excluding commercial paper** | **125,567** | 120,500 notes + 5,067 term loan |

Next twelve months (Sep 1, 2026–Aug 31, 2027): $7,317M = $2,250M of notes + $563M of term-loan installments + the $4,504M remainder. Commercial paper Unavailable.

FY2028 through Thereafter equal the 10-K's May 31 buckets. Only fiscal 2027 changes: the July notes and June installment fell due before August 31, and commercial paper (counted in the 10-K's fiscal 2027 bucket) is no longer included.

## Checks (all agree)

| Check | Expected | Calculated | Result |
|---|---:|---:|---|
| Instrument principal sums to reported total, May 31 | 130,105 | 130,105 | Agrees exactly |
| Principal − discount = carrying debt, May 31 | 129,541 | 129,541 | Agrees exactly |
| Term-loan schedule vs reported balance, May 31, 2025 / 2026 | 5,419 / 5,137 | 5,418.875 / 5,137.375 | Agrees (filing rounds to $1M) |
| Instruments by fiscal year vs the 10-K's six maturity buckets | 7,210; 10,145; 5,500; 7,250; 9,750; 90,250 | 7,210.625; 10,144.75; then exact | Agrees within $1M. The 10-K bucket counts commercial paper in fiscal 2027. |
| Long-term carrying, May 31 ($128.1B, rounded) vs principal − CP − discount | 128,100 ± 50 | 128,073 | Agrees |
| Scheduled June–August principal vs MD&A "$3.1 billion" | 3,100 ± 50 | 3,070.375 | Agrees |
| Implied Aug 31 discount and costs vs May 31's 564M | ≤ 564 | 517–617 (range) | Consistent; not reported, so no exact figure |
| Grouped repayments − scheduled principal vs MD&A "$1.1 billion" CP | 1,100 ± 50 | 1,131.625 | Consistent, not adopted |
| Term loan newly due within 12 months vs MD&A "$4.6 billion" reclassified | 4,600 ± 50 | 4,644.75 | Agrees |

## App and Excel

- **App:** the Oracle review's new section "Which borrowing principal is due after August 31?" sits at the top of the existing maturity section. It shows the twelve-month table, the fiscal-year table, a reconciliation disclosure and all 57 instruments outstanding (commercial paper shown as Unavailable). The historical May 31 schedule follows unchanged. The repayment review's undated-items list now points to this calendar and keeps commercial paper and interest Unavailable. That wording appears only while the saved calendar loads and checks.
- **Excel:** `Oracle_Liquidity_2026-08-31.xlsx`, sheet **Payment dates**, from row 35. It has the twelve-month and fiscal-year tables (`SUMIFS` over the instrument and term-loan rows), the reconciliation, the term-loan amortization (formulas from the borrowed amount) and the 58-row instrument table. Each row carries its tag, context and accession. Blue cells are reported inputs; black cells are formulas. Repayment review A40, A53 and D53 carry the app's updated wording. A29 on Payment dates points to the block.
  - The workbook is normally built with the Codex artifact runtime, which isn't on this laptop. So `tests/offline/add_oracle_principal_block.py` edits only those two worksheet XML parts of the reviewed PR #49 file and refuses any other starting file. Every other part, including the charts, styles and other sheets, is byte-identical.
  - The 96 new formula cells were recalculated in desktop Excel and match their cached values, and the workbook has no formula errors.
  - The manifest adds `principal_sha256`, so a changed calendar makes the download Unavailable. If the workbook is ever rebuilt with `build_oracle_liquidity.mjs`, that builder needs the same block added; until then, rerun this script on its output.

## Limits

- Commercial paper at August 31, both the balance and the maturity dates, is Unavailable.
- Unamortized discount and issuance costs at August 31 are not reported; only a range is implied.
- Term-loan amounts are calculated, assume no prepayment and move if the termination date is extended.
- Make-whole redemptions or new issuance after August 31 are outside this review. The saved financing screen through October 15 found no later borrowing (`oracle_revolver_reconciliation.md`).
- Interest payments are excluded.
- **Not funding coverage:** cash, OCF, prepayments, equity proceeds and the revolver are not matched to these dates here. The funding conclusion and its "remaining principal dates" unknown are interpretation-gated and haven't been re-reviewed in this change.
