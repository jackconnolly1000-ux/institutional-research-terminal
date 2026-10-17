# Release 1 final reconciliation

Release 1 is complete within the agreed scope when this final reconciliation PR merges. Steps 5–7 merged as PRs #45 (two-date history), #46 (two common chart questions) and #47 (individual Excel parity). Financial review dates do not change: latest balance sheets are June 30, 2026 for LLY/VST and August 31, 2026 for ORCL; the saved financing screens stop at their stated dates. This audit does not claim a new SEC search or automatic refresh.

## Final corrections

- A missing history source file now yields the company's stated unavailable-review state, with no download or partial figures. General research remains reachable, and the session can return to a checked review after evidence is restored. It no longer leaks an uncaught filesystem exception into the page.
- The expanded app evidence now contains the annual history input records and reported lease inputs/controls: date, value, form, filed date, accession, exact tag, USD unit, context, scale, decimals, source and selection rule. Lease selection is explicit in the shared model and individual Excel Data blocks. Amounts, formulas and source files are unchanged.
- The roadmap no longer calls history unbuilt, describes current exports as five sheets, or treats historical test counts as the current baseline. The plan explicitly preserves Oracle's reported-interest-line exception; its borrowing-only composition remains Unavailable. Release completion does not close incomplete lease or funding evidence.

## Reproducible acceptance

`tests/offline/audit_release1.py` is read-only, offline and uses no AI service. It checks all three source-gated primary workbooks against the app models: ten core measures, ten annual/latest history rows, the two common charts, borrowing reconciliation, the funding conclusion, source URL entity/accession matches and full reported-input provenance. An actual-download directory can be required to match the reviewed bytes. It refuses a wrong-company or stale download instead of accepting similar visible figures.

```bash
python tests/offline/audit_release1.py
python tests/offline/audit_release1.py --raw ../data/raw/sec
python tests/offline/audit_release1.py --download-dir /path/to/downloads
```

The optional download directory contains `LLY.xlsx`, `ORCL.xlsx`, `VST.xlsx` copied from the actual three app downloads. `--raw` requires the saved annual and quarter filings: it re-reads 13 annual instant facts and reconciles TTM OCF/capital spending/FCF from all six full source filings without rewriting evidence. The audit validates 45 distinct reported fact records for LLY, 32 for ORCL and 54 for VST across current metrics, annual inputs, lease evidence and interest inputs. Existing full-filing tests also cover the company-specific readers and financing audits.

| Acceptance area | Evidence |
|---|---|
| Core ratios and formulas | `ratio_reconciliation.md`; independent fixture expectations and actual saved formula/value tests |
| History | `company_history.md`; exact annual contexts/values and no unsupported VST borrowing total |
| Charts | `core_charts.md`; source formulas, signed uses/results and two native charts per primary workbook |
| Excel parity | `excel_parity.md`; 8 LLY sheets, 10 ORCL, 10 VST; common guide and original detail/source blocks |
| Source/revision/unknown rules | Existing selector, one-filing, exact-period, dimension, unit, missing/zero and negative-value tests |
| Existing features | Offline company selector, source-gated downloads, experimental research navigation and archived AAPL/STRL example |
| Deployment | Live company views and all three actual workbook downloads checked after each merge |

## Remaining limitations

- These are frozen reviews of three validation companies. More companies and automated refresh are outside Release 1.
- Prior Vistra borrowing, net debt and flow/debt ratios remain Unavailable. June LLY/VST lease balances remain Unavailable; their December lease facts keep their dates. No complete obligations or lease extraction is claimed.
- Future funding coverage remains Unavailable for all three: complete remaining principal calendars, drawable credit, relevant conditions/headroom, payment timing/overlaps and resource accessibility are not jointly established. Historical cash generation, capacity and financing events are not projected or rolled into balance-sheet amounts.
- Interest bases remain company-specific. Oracle borrowing-only composition/capitalization, Lilly interim capitalization and Vistra receivables/Nuveen allocation/Other/all-in cost are unresolved. No ranking or contract-defined coverage is inferred.
- Workbook URLs are full, copyable source text; app links are clickable. Native desktop Excel and physical-phone testing are unavailable. Runtime recalculation, independently read formulas/cached values and responsive desktop/390 px rendering are verified. Public source links are checked for the correct entity and accession; this audit is not a fresh network availability test of every SEC URL.
- The optional combined workbook remains its original summary, not the full company exports. Existing experimental AI research limitations remain documented; no paid AI calls were made during this release work.

Validation: **412 tests passed** (407 before plus four release-audit tests and the missing-history AppTest); the offline app and archived sample passed with network connections disabled. The raw-source audit passed for all three companies. Changed Data source/selection blocks and expanded app evidence were rendered and inspected at desktop and 390 px widths. A comparison against PR #47 preserved every existing financial value and formula: existing cell edits were confined to 4 Lilly, 9 Oracle and 10 Vistra Data metadata cells. The app's missing-history state and recovery to another company were tested. Each merge's deployed views and actual downloads are checked before proceeding; no paid AI calls were made.
