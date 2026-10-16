# Company-review reader audit

Checked October 16, 2026 from the current three company reviews, their individual Excel exports
and saved SEC evidence. No new financial amounts, forecasts or company rankings are introduced.

## Confirmed issues and repairs

| Finding | Repair |
| --- | --- |
| The leading cash-flow sentence omitted TTM while the funding conclusions discuss half-year/quarter flows. | The leading sentence explicitly says TTM. Existing period labels and calculations remain. |
| One generic October 14 review stamp could be mistaken for the date of every section. | The app identifies the balance-sheet-fact check separately. Workbook About statements distinguish liquidity, financing, interest and funding-interpretation review dates. Financial dates remain June 30 or August 31. |
| Lilly Repayment review said the SEC inventory was incomplete even though the later financing audit screened it through October 15. | The scope row now states the financing-candidate cutoff and preserves the limit that all liability notes have not been reviewed. |
| Oracle app/Excel still described an incomplete later inventory despite a saved follow-up index check. | Re-ran the production selector on the exact saved index. Only the two already reviewed September 8-K candidates are listed after August 31. The audit now binds that index fingerprint and candidate set. Borrowing balances and drawable capacity do not change. |
| Coverage-source summaries listed broad filing pages that omitted some statement/interest pages. | Each company's coverage references now identify its operations statement and interest-note locations. The source facts and ratios do not change. |
| Funding headings produced the same heading-anchor text in three hidden tabs. | Each funding heading names its ticker so its primary anchor is distinct. |
| Oracle's shared-cash-pool note was visibly clipped. | Separate label and wrapped explanation in the existing row, with sufficient row height. |
| Downloaded About sheets referenced repository-relative documentation paths. | Replace them with full public GitHub documentation URLs. SEC primary-source URLs remain separate. |
| Lilly's alternate-folder workbook check validated the default evidence folder. | Validate the evidence folder actually supplied by the caller, including the source fingerprints. |

## Evidence and scope

The [Oracle index audit](oracle_revolver_reconciliation.md) records the exact saved index SHA256,
candidate forms, cutoff and reproducibility checks. The late September proxy and ownership forms
are not treated as financing candidates or new borrowing simply because they were filed later.
The generic live index can still show Not checked for new or mismatched documents.

All 28 unique app source URLs were checked. Twenty-five returned content through the retrieval
tool. Two large Vistra documents (the annual report and June credit amendment) exceeded its size
limit; Oracle's annual report returned an internal retrieval error. Those three URL/document
identities were checked against the saved sources and fingerprints, but a full live refetch is
not claimed. A tool failure is not treated as a broken public link or missing filing evidence.
Source metadata was compared with the saved filings/registries: company identifier, accession,
document, financial period and filing date. Excel numeric inputs and app metrics continue to use their existing checked models.
No stale date is relabeled as today's cash, current drawable credit or a complete remaining
principal schedule. Historical interest ratios retain their company-specific denominator limits.

## Verification

Regression checks cover index filtering/cutoffs/history coverage, source freshness, review dates,
coverage locations, app/Excel scope agreement, documentation URLs and the alternate-folder guard.
Workbook checks compare existing numeric results and formulas and native charts with the originals.
All 370 unit tests pass. The offline complete review and saved sample pass with network calls disabled.
The three workbooks preserve 309 (LLY), 263 (Oracle) and 385 (Vistra) existing numeric/formula cells,
their cached results and the native chart XML. Desktop and 390px static layouts were inspected;
the static phone-width preview is not a test on a physical mobile device.
Changed sheets/ranges are rendered and inspected. The deployed company tabs and all three actual
downloads are checked after publication. No Run analysis action or paid AI call is used.

Unresolved evidence remains Unavailable: current drawable amounts and covenant headroom, complete
updated principal schedules, selected commitment timing/overlap, and the stated interest-composition
or capitalization gaps. This audit does not supply forecasts or a complete review of every liability note.
