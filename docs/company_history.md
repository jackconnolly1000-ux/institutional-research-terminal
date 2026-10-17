# Two-date company history

Release 1 step 5. Prior annual balance sheets are read from the saved full 10-Ks and checked against companyfacts, the printed rows and their inline contexts. `tests/offline/build_company_history.py` reproduces `samples/company_history.json`; runtime requires its checked fingerprint, one USD date/accession, no dimensions, and agreement with the existing ratio model.

USD millions unless a ratio:

| Annual date | Cash | Current assets | Current liabilities | Borrowing | Net debt | Current ratio |
|---|---:|---:|---:|---:|---:|---:|
| LLY 2025-12-31 | 7,268 | 55,629 | 35,228 | 42,503 | 35,235 | 1.58x |
| ORCL 2026-05-31 | 31,289 | 46,567 | 41,764 | 129,541 | 98,252 | 1.12x |
| VST 2025-12-31 | 785 | 9,179 | 11,814 | Unavailable | Unavailable | 0.78x |

The prior annual cash, current-asset and current-liability rows match the undimensioned USD instant in the annual filing itself: Lilly context c-16, Oracle context C_f62bade6-47e1-4441-9bb3-1e534300c2f2, Vistra context c-7. Cash means cash and equivalents excluding restricted cash, not a claim of current drawable or Parent-accessible funds. Full form, filed date, accession, context, tag, unit, source URL and raw-source hash are retained in the history data and workbook Data records.

Lilly borrowing is 1,635 + 40,868 = 42,503; Oracle is 7,199 + 122,342 = 129,541. Both match their existing checked annual presentations and own totals. Vistra's annual borrowing presentation is not checked in the existing mapping. The older receivables/repurchase scope remains unresolved. Its older borrowing, net debt, OCF/debt and FCF/debt remain Unavailable rather than summing a partial presentation.

Annual OCF/capital spending reuse the independently checked source facts in `pilot_cashflow_reconciliation.md`: LLY 16,813 / 7,841, ORCL 31,977 / 55,663, VST 4,070 / 2,752. Annual FCF is respectively 8,972 / −23,686 / 1,318. Annual interest coverage uses the existing reconciled annual columns: 26,302 / 895 = 29.39x; 20,606 / 4,599 = 4.48x; 1,906 / 1,107 = 1.72x. Lilly's annual interest is explicitly net of capitalization; Oracle's basis is unstated; Vistra's selected component precedes capitalization. Later TTM bases retain their existing limitations.

The app and each individual workbook compare these observations with the latest checked dates. Fiscal-year and later TTM flows are **both twelve months and overlap**. Headers and exact start/end dates distinguish them; no interim annualization or independent-period growth rate is calculated. No subsequent financing event is rolled into a balance sheet. Baseline borrowing excludes leases. Current ratios use all current liabilities. Negative FCF is retained.

The History workbook sheet uses formulas referencing reported annual inputs in Data, the existing detailed annual interest columns, and the latest Debt and liquidity table. Unsupported values are literal Unavailable with reasons. Existing metric cells, cash/repayment schedules, catalysts, charts and funding conclusions remain intact. Download manifests bind the history code, selected annual facts and current source model.

Checks: independent expected answers, source fingerprint refusal, visible dates/source links, explicit unsupported Vistra history, every exported history value and formula, and the existing full app/export suite. Desktop/phone layout QA uses production HTML/CSS at 1280/390 px; spreadsheet-runtime renders and recalculation are inspected. Native desktop Excel is not available. The release workflow verifies the deployed app and actual download bytes after merging each step.
