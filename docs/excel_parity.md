# Individual workbook parity — Release 1 step 7

Each primary company download contains its full review. The optional combined file retains its original core metric summary and source rows; it is not a substitute for the three complete company workbooks. The app now explains this distinction next to the downloads.

## Reading path

Funding conclusion opens first, with obligations/resources/competing uses/unknowns and the checked company-specific coverage basis. Its new contents guide identifies every actual worksheet and the question it answers. It is a tab guide, not a new financial model. Reading notes explain dates, USD storage versus million display, overlapping FY/TTM windows, unknowns, and the existing blue-input/green-cross-sheet/black-calculation convention. Green is not a claim of favorable or recurring cash.

Borrowing and leases, Debt and liquidity, History and Core charts share the common financial models with the app. Existing company-specific cash, repayment, financing and interest sections remain. Data retains the source facts and metadata; About retains definitions and methodology. The chart sheet points readers to these source blocks. New tables use restrained outer borders and vertical separators, matching the existing style.

## Audit corrections

History's shared notes previously inherited later-TTM capitalization amounts and 10-Q-specific caveats. The annual and later-TTM interest bases are now described separately without applying a TTM amount to an annual figure. Latest-only borrowing/OCF caveats are explicitly scoped to the latest column. Prior Vistra borrowing remains Unavailable with a plain explanation instead of an internal repository path. All numbers, formula references, dates, source records, funding conclusions and company-specific limitations remain unchanged.

## Evidence access and limits

Excel source URLs remain full, copyable text. The spreadsheet runtime does not author native hyperlink actions and its HYPERLINK formula has no supported calculated result; no unsupported formula or fabricated cached value is used. The guide explicitly tells the reader to copy a URL into a browser. App source links remain clickable. This is a known usability limit, not missing SEC evidence.

`export_guide.py` supplies the contents and scope, while `tests/offline/export_guide.mjs` authors the guide and reading notes. Their hashes gate all three downloads, alongside the existing source, ratio, history and chart gates. An out-of-date export is refused. Tests compare the guide to actual tabs, preserve funding conclusions, check dated interest bases and verify refusal after a layout change. Builders reconcile calculations and exercise formula boundaries before export; tests independently read saved formulas and values. All changed Funding conclusion, History, Core charts and About regions are rendered and inspected, and the app download explanations are checked at desktop and phone widths. No paid AI service is used.

Validation: 407 tests pass (403 before plus four export checks); the offline selector, served downloads and archived example pass without network. All changed output regions were inspected, including the revised date-scoped History notes and desktop/390 px app layouts. A cell-by-cell comparison against PR #46 preserved every existing formula and financial value; changes to existing cells were confined to explanatory History column D text. Workbook sheets total 8 for LLY and 10 each for ORCL/VST. Native desktop Excel and a physical-phone test are unavailable; source-bound runtime recalculation, independently read saved results and responsive rendering are checked. Live app and actual downloads are verified after merge.

**Update, October 17, 2026.** Source URLs in the three company workbooks are now native hyperlinks (134 Lilly, 140 Oracle, 175 Vistra), added after the build by `tests/offline/add_workbook_hyperlinks.py`. It edits only worksheet XML and relationship parts, and checked in desktop Excel: every link opens its own URL, with no formula errors. Links keep the existing text style, because blue text means a reported input. The guide sentences now say to select a URL. A workbook rebuilt by the spreadsheet runtime needs this script run again.
