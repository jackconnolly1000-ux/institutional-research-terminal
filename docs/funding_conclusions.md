# Dated funding conclusions

Interpretation checked October 16, 2026 against the existing saved evidence; Oracle re-checked October 17, 2026
against its August 31 principal calendar (`oracle_principal.json`, now bound evidence). No new filings,
forecasts, ratings or available-credit estimates are introduced. The June 30 Lilly/Vistra and
August 31 Oracle balance sheets remain historical. Later events stay on their own dates.

`funding_conclusions.py` owns the prose shown in the app and individual workbooks. It binds
each company to the exact source JSON fingerprints and requires the matching saved snapshot.
Missing or changed evidence makes its conclusion Unavailable. Workbook manifests also bind
the interpretation's fingerprint, so an edited interpretation cannot serve an older export.
The optional older combined pilot export retains its existing scope and is not a substitute
for the individual funding reviews.

## Conclusions and decisive evidence

| Company | Funding implication | Evidence needed to resolve future coverage |
| --- | --- | --- |
| Lilly | Acquisition and manufacturing spending compete with repayment resources. H1 cash generation after cash PP&E does not establish a surplus after acquisitions, payouts and future payments. | Remaining principal calendar, post-August facility renewal and draw conditions, acquisition/manufacturing payment timing and overlap. |
| Oracle | Equity proceeds and specified customer prepayments contributed to a quarter in which cash capex exceeded reported OCF. At August 31, $7.317B of note and term-loan principal was due over the next twelve months; August cash is not reserved for it or a forecast of future payment resources. | Current drawable revolver, commercial paper's balance and dates, future cash generation, timing of uncommenced leases and overlap among commitments. Note and term-loan principal dates are established. |
| Vistra | Dated late-2026 payments require attention to facility conditions and where cash sits. June reported liquidity is not current Parent-accessible cash. | Current borrowing base and draw conditions, Parent/subsidiary transfer constraints, acquisition/capital-call timing and completed redemption status. |

Each source claim links to the checked filing, location and accession in the app and workbook
Data area. Numerical inputs and existing calculations remain in their original sheets.
No sum combines current borrowing carrying amounts with principal maturities, restricted cash
with unrestricted cash, facility limits with proved drawable cash, or historical inflows with
the cash balance they already funded.

Detailed sources and reconciliations:

- [Lilly liquidity](lly_liquidity_review.md), [financing audit](lly_financing_audit.md) and
  [interest coverage](lly_interest_coverage.md).
- [Oracle liquidity](oracle_liquidity_reconciliation.md), [revolver audit](oracle_revolver_reconciliation.md)
  and [interest coverage](oracle_interest_coverage.md).
- [Vistra liquidity](vistra_liquidity_reconciliation.md) and [interest-component coverage](vistra_interest_coverage.md).

## Coverage interpretation

- **Lilly, TTM July 2025–June 2026:** 33,633M derived operating income / 1,079M reported
  interest = 31.17x. Annual interest is explicitly net of capitalized interest. Interim
  capitalization basis and capitalized amount are unstated. No addback is inferred.
- **Oracle, TTM September 2025–August 2026:** 23,057M reported operating income / 5,104M
  reported interest = 4.52x. Borrowing-only composition and capitalization basis remain
  Unavailable. Separately disclosed finance-lease interest is not added or subtracted.
- **Vistra, TTM July 2025–June 2026:** 3,563M reported operating income / 1,117M separate
  interest component = 3.19x, before the capitalized-interest deduction. The mixed-total
  bridge reconciles swaps, amortization, extinguishment, capitalization and Other.
  Receivables/Nuveen allocation and all-in financing-cost coverage remain Unavailable.

Different periods, operating-income derivation and interest definitions prevent treating
the displayed multiples as a company funding-strength ranking. All are historical accrual
earnings ratios, not future debt-service coverage, cash interest tests or covenant headroom.

## Exports and verification

Each individual export opens with **Funding conclusion**, followed by its existing detailed
sheets. The shared builder `tests/offline/funding_sheet.mjs` uses the production model, links
the summary coverage to the existing calculation and refuses a missing result rather than
showing zero. Prose is explicitly a checked snapshot. Manual workbook edits recalculate
formulas but require a new review of the prose.

Rebuild each company using its existing `build_*_liquidity.mjs` with `funding_sheet.mjs` and
`workbook_style.mjs` alongside it in a temporary directory, using the Codex artifact runtime.
`SKIP_UNCHANGED_RENDERS=1` renders the new conclusion, basis and appended evidence only.
The default also renders the existing detail views. No deployment dependency is added.

Verification covers evidence freshness, changed snapshots, cross-company isolation,
app/Excel text agreement, formula links, stale-download guards and preservation of existing
populated values, formulas and native charts. Desktop Excel execution is not claimed.
