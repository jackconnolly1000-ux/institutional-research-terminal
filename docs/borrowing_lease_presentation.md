# Borrowing and lease presentation

Release 1 step 3, checked October 16, 2026. This presents existing checked evidence; it does not update the balance sheets or calculate a combined debt-and-lease measure.

## Reconciliation (USD millions)

| Company | Baseline borrowing | Lease liabilities shown separately | Leases not yet commenced |
|---|---|---|---|
| LLY, June 30, 2026 | Current 7,050 + noncurrent 47,858 = **54,908** | June amounts Unavailable. December 31, 2025 operating: 222 current + 1,140 noncurrent = **1,362**, derived. Finance leases are not reported in the annual note checked; this is not zero. | Unavailable: no checked amount in the saved pilot evidence. |
| ORCL, August 31, 2026 | Current 7,625 + noncurrent 117,712 = **125,337** | Operating: 4,027 + 30,594 = **34,621**. Finance: 749 + 8,436 = **9,185**. Both match their reported totals at August 31. | **$288 billion**, as disclosed in rounded billions; future commitment, outside recognized liabilities and the lease maturity table. Annual payment dates remain Unavailable. |
| VST, June 30, 2026 | Long-term current 1,876 + long-term noncurrent 17,719 + short-term **reported zero** + receivables financing 300 = **19,895** | June amounts Unavailable. December 31, 2025 operating: 13 + 92 = **105**. Finance: 4 + 218 = **222**. Both match their reported annual totals. | Unavailable: no checked amount in the saved pilot evidence. |

Source locations and SEC document links are in the three `pilot_evidence_*.md` files. The app and individual workbooks display the same dates and filing locations. Each new workbook input keeps its tag, accession, filing date and SEC URL on Data. Lease source records also retain the inline context, scale, decimals and saved-document SHA-256.

No leases enter baseline borrowing, net debt, OCF/debt or FCF/debt. Older lease balances are never substituted for missing June balances. Oracle's borrowing lines do not establish an instrument breakdown. Vistra's project debt is already inside long-term debt; neither its principal subset nor its separately presented Nuveen/affiliate obligations is added again. Existing funding conclusions and interest-coverage bases are unchanged.

## Files and rebuild

- `borrowing_leases.py`: checks the borrowing sum, filing/date/unit consistency and lease component controls; produces the shared app/workbook presentation.
- `samples/borrowing_leases.json`: selected lease facts re-read from saved full filings using `filing_xbrl.read_instant`, with expected amounts from the pilot evidence. It is not a universal or complete lease extractor.
- `tests/offline/build_borrowing_lease_evidence.py [raw-sec-folder]`: reproduces these source records without network access. Default folder is `../data/raw/sec`.
- `tests/offline/borrowing_lease_sheet.mjs`: adds Borrowing and leases to each individual workbook, appends Data records and About guidance, and verifies formulas, missing-input behavior and renders. The three existing `build_*_liquidity.mjs` scripts call it. Use the Codex artifact runtime, with the scripts and runtime `node_modules` link in a temporary working directory.
- Individual workbook manifests bind the borrowing/lease module plus its evidence bytes, as well as the existing source models and workbook bytes. A changed model or evidence invalidates the download until the workbook is rebuilt.

The optional combined export retains its existing scope. Release 1 step 7 will review export parity more broadly.

## Remaining evidence gaps

- LLY and VST: June 30 lease liabilities and checked amounts for leases not yet commenced are Unavailable. The December balances are historical context only.
- LLY: finance lease amounts are not established; no zero is inferred.
- ORCL: the exact balance-sheet line allocation for current operating and finance lease liabilities remains unconfirmed by hand. No allocation is invented. Uncommenced-lease annual timing and overlap with other commitments remain unresolved.
- No new funding coverage, instrument classification, forecast or company ranking is introduced.

## Verification

386 unit tests pass (379 before this step), and `tests/offline/check_liquidity_app.py` passes with all network calls disabled, including the archived AAPL/STRL example. Checks cover the reconciled values above, missing versus zero, older dates, incompatible borrowing inputs, conflicting lease totals/units/dimensions and stale-download gates. Spreadsheet builders exercise source edits and missing inputs before restoring the checked data. Existing workbook cells, formulas and charts are compared with the pre-change files.

Streamlit AppTest verifies company switching and the exact download bytes without network or secrets. Production HTML/CSS is rendered at 1280px and 390px for visual inspection. The cloud browser cannot reach the local branch server; a deployed browser check remains for after merge. No paid AI calls are made.
