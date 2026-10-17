# Release 1 ratio reconciliation

Checked against merged `main` at `0f7df28` (PR #43). This step changes presentation and export coverage, not the checked financial inputs or funding conclusions. The saved reviews remain historical.

## Findings and changes

The existing app ratios and Lilly's workbook calculations agreed with the checked evidence. Oracle's and Vistra's primary workbooks omitted current ratio, net debt, OCF/debt and FCF/debt even though the app displayed them. Each now has a `Debt and liquidity` sheet with the same ten measures, dates, units and formula-based calculations as Lilly. Historical interest coverage links to its existing company-specific detailed build; it is not rebuilt with a common denominator.

`ratio_review.py` reconciles the snapshot's inputs, exact FY/YTD source periods, coefficients, USD units, filing versions, derived results and nested input provenance. It supplies the app's calculation disclosure and workbook explanations. A contradictory saved review is refused rather than displaying stale ratios. Existing missing values remain Unavailable. The app disclosure now shows each result and its full period next to the formula and sources. “Current liabilities” is spelled out in the headline ratio label.

The workbook builders share `tests/offline/ratio_sheet.mjs`. Reported input rows retain their accession, filed date, tag, period, unit, selection rule and source URL. All dollar values are stored in full USD and displayed in millions. Percentages are fractions; multiples are dimensionless. Restrained borders and vertical separators follow the existing convention. The manifests bind all three exports to the ratio rules and saved source snapshots.

## Independent expected answers

USD millions unless a multiple or percentage. These inputs come from the pilot evidence and the checked cash-flow/interest reconciliations below, not a new extraction or forecast.

| Measure | Lilly, June 30, 2026 | Oracle, August 31, 2026 | Vistra, June 30, 2026 |
|---|---:|---:|---:|
| Current assets / current liabilities | 64,672 / 47,741 = **1.35x** | 55,630 / 47,514 = **1.17x** | 10,276 / 10,557 = **0.97x** |
| Baseline borrowing less cash and equivalents | 54,908 − 8,950 = **45,958** | 125,337 − 36,369 = **88,968** | 19,895 − 435 = **19,460** |
| TTM OCF / period-end borrowing | 28,083 / 54,908 = **51.1%** | 46,940 / 125,337 = **37.5%** | 5,121 / 19,895 = **25.7%** |
| TTM FCF / period-end borrowing | (28,083 − 9,893) / 54,908 = **33.1%** | (46,940 − 75,660) / 125,337 = **−22.9%** | (5,121 − 2,866) / 19,895 = **11.3%** |
| Historical operating-income interest coverage | 33,633 / 1,079 = **31.17x** | 23,057 / 5,104 = **4.52x** | 3,563 / 1,117 = **3.19x** |
| TTM period | July 1, 2025–June 30, 2026 | September 1, 2025–August 31, 2026 | July 1, 2025–June 30, 2026 |

The three dates and business models differ. This table is a reconciliation, not a ranking or peer comparison. Full precision is retained; only display values are rounded.

## Definitions and limits retained

- Current ratio uses **all current liabilities**, not only current borrowing. Both inputs share a date and filing. Current assets are not all cash.
- Net debt subtracts only cash and equivalents excluding restricted cash. Investments, restricted cash, revolvers and subsequent financing proceeds are not subtracted. Borrowing excludes operating and finance leases. Negative net debt remains valid.
- TTM flows are FY + current YTD − prior YTD. Flow/debt denominators are period-end carrying borrowing, not average debt. These ratios are not the share of future maturities funded, future cash availability or a repayment forecast.
- Lilly capital spending uses its checked other-PP&E tag. Oracle's reported OCF includes the specified customer prepayments; the existing separate quarterly exclusions and equity-proceeds bridge are unchanged. Vistra's capital-spending line includes nuclear fuel and LTSA prepayments. FCF excludes acquisitions, dividends and other cash uses for all three.
- Lilly derives operating income without earnings addbacks. Annual interest is net of capitalized interest; the interim capitalization basis is unstated. Oracle uses its reported interest line, whose full borrowing composition and capitalization basis remain Unavailable. Its separately disclosed finance-lease interest is not added or subtracted. Vistra uses the separate interest component before its capitalized-interest deduction, retaining the swap/extinguishment/Other reconciliation and its allocation limits. No capitalized-interest adjustment or interest-income offset is made.
- Historical interest coverage is not cash coverage, the contract-defined covenant test, covenant headroom, drawable credit or proof of Parent-accessible funds. No future funding gap is closed by these ratios.

## Checked evidence and reproduction

- [Lilly pilot evidence](pilot_evidence_lly.md), [Oracle pilot evidence](pilot_evidence_oracle.md), [Vistra pilot evidence](pilot_evidence_vistra.md): balance-sheet amounts, accessions and SEC source URLs.
- [Cash-flow reconciliation](pilot_cashflow_reconciliation.md): nine reported source periods, exact capital-spending definitions and independent TTM arithmetic.
- [Lilly coverage](lly_interest_coverage.md), [Oracle coverage](oracle_interest_coverage.md), [Vistra coverage](vistra_interest_coverage.md): exact durations, source contexts, numerator/denominator definitions and limits.

Rebuild the three individual workbooks using their existing `tests/offline/build_*_liquidity.mjs` scripts in the spreadsheet runtime. The app only serves saved bytes; it never rebuilds them or calls an AI service. The optional combined export and the experimental general research export are unchanged.

`tests/test_ratio_review.py` checks independent expected answers, refusals for period/unit/version/TTM-build conflicts, stale derived values and nested provenance, missing interest reviews, app evidence and actual individual workbook values/formulas/provenance. The builders exercise missing vs zero cash, valid negative net debt, zero/negative debt, missing/nonpositive current liabilities and missing OCF. Existing interest-builder boundary and reconciliation tests remain in place.

Validation: 396 tests passed (386 on the base plus 10 new); 31 focused app/export/reconciliation tests passed again after the final cleanup. The offline company selector, all three served individual downloads and the archived AAPL/STRL example passed with network calls disabled. Changed production HTML/CSS fragments were rendered and inspected at 1280 px and 390 px; this is static responsive-layout QA, not a physical-phone browser test. Changed workbook calculation tables, Data additions, About additions and Lilly's affected existing detail blocks were rendered and inspected. Formula-boundary checks passed in the spreadsheet runtime. A read-only comparison preserved 2,151 Lilly, 1,888 Oracle and 2,398 Vistra original cells and cached results outside the authorized Lilly summary edits and About additions; original charts, frozen panes and merges were preserved.

Deployment remains on `main` until this PR is reviewed and merged. No live deployment of this branch is claimed. Native desktop Excel recalculation is not available in this environment; calculations are tested in the spreadsheet runtime and saved formulas/cached results are independently inspected.
