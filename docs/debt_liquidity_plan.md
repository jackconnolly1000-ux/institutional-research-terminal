# Debt and liquidity: first-release plan

Status (Oct 14, 2026): **planned, not built.** Only the items under "Existing code" are implemented. Everything else in this file is a plan, and nothing here should be described as working until its acceptance criteria pass.

## Goal

Help a researcher answer four questions about a nonfinancial public company:

1. What does it owe?
2. What cash and cash generation support those obligations?
3. What changed?
4. Which SEC evidence supports each conclusion?

The tool is for my own stock research and to show accounting, analysis, product and technical judgment to recruiters. It is a research tool, not investment advice.

## Existing code

| Item | Where | Status |
|---|---|---|
| TTM free cash flow: `NetCashProvidedByUsedInOperatingActivities` minus `PaymentsToAcquirePropertyPlantAndEquipment`, with period end, form, filed date and accession | `xbrl.py` | Implemented and unit-tested on AAPL, STRL and JPM fixtures. **Not yet validated against the three pilot companies.** |
| TTM revenue, gross margin, operating margin (`OperatingIncomeLoss` is the operating income input coverage would use) | `xbrl.py` | Implemented and unit-tested on fixtures. Not validated against the pilots. |
| "Financing and liquidity" category on AI findings (`FINANCING_LIQUIDITY`) | `analysis.py`, `ui.py` | Exists. It is Claude's unverified label, not a calculation. |
| Balance-sheet values, cash, debt, leases, interest expense, ratios | none | Not built |

## First-release scope (planned)

1. Audit the existing app and data pipeline
2. Add reliable SEC financial inputs
3. Normalize borrowing
4. Calculate supported debt and liquidity ratios
5. Present short factual findings and comparable company history
6. Add two charts, each answering a specific financial question
7. Provide an Excel evidence export
8. Reconcile displayed values to their sources

Supported filers: USD, U.S. GAAP, nonfinancial operating companies. Banks (for example JPM) and specialized issuers need separate methods and get an "unsupported" result, not a calculation.

## Financial definitions (planned)

- **Cash (initial):** cash and cash equivalents, excluding restricted cash, as of the balance-sheet date. Each value carries its source metadata (see source rules). When the supported fact cannot be established from the filing, the result is "Unavailable" with the reason, not zero and not a substitute figure. The tag that represents this fact must be confirmed from the pilot filings; see "Decisions to resolve".
- **Baseline gross debt:** reported carrying amounts of interest-bearing borrowing, excluding operating and finance leases.
- **Leases:** operating and finance lease liabilities, shown separately and never added to baseline gross debt.
- **Net debt:** baseline gross debt minus cash as defined above. Restricted cash and investments are not subtracted automatically. Negative net debt is a valid result and is kept.
- **Current ratio:** current assets / current liabilities, both from the same balance-sheet date.
- **Free cash flow (initial):** TTM operating cash flow minus stated purchases of property, plant and equipment. This is the existing `xbrl.py` calculation.
- **OCF/debt and FCF/debt:** compatible TTM flows divided by period-end baseline gross debt.
- **Operating-income interest coverage:** TTM operating income / gross borrowing interest expense. Always labeled with this full name.

## Source rules (planned)

- Every reported value keeps its period end, form, filed date, accession number, XBRL tag, units, and any selection or revision rule applied (for example "most recently filed value for this period").
- A derived value (net debt, gross debt summed from components, every ratio) has no XBRL tag of its own. It lists every input fact it was calculated from, each with that fact's full source metadata, plus the formula used.
- Check debt components for overlap before adding them, and check that inputs share comparable dates before calculating.
- A missing value is "Unavailable", never zero.
- A nonpositive denominator gives an explanation instead of a ratio.
- Valid negative cash flows and negative net debt are kept, not hidden.
- Overlapping year-to-date periods are never summed. TTM follows the existing rule: latest fiscal year + current year to date - prior year to date.
- Debt and interest tag mappings are decided from each pilot's filings, not assumed to be universal.

## Pilot companies

Separate validation cases, in this order:

1. **Eli Lilly (LLY):** first case.
2. **Oracle (ORCL):** second case.
3. **Vistra (VST):** third case. Where its sector complexity exceeds the basic framework, the app and docs state the limit.

AAPL and STRL fixtures may test extraction mechanics. They don't replace the pilot cases.

## Delivery sequence (planned)

The steps are done in this order. Each change is small enough to review on its own, and related steps can share a pull request (for example, cash and current ratio, or borrowing and net debt). Nothing merges until its tests and acceptance checks pass.

1. **Pilot data:** download LLY, ORCL and VST company facts to `C:\Users\jackc\Stock Project\data\raw\xbrl`; record by hand, from each latest 10-K or 10-Q, the reported cash, debt lines, lease lines, current assets and liabilities, and interest expense, with their page and accession. These hand-read values are the expected answers.
2. **Cash:** cash and cash equivalents excluding restricted cash, point in time, with source metadata and the Unavailable result.
3. **Current ratio:** current assets and current liabilities from the same date.
4. **Borrowing:** map debt tags per pilot from the filings, check overlap, compute baseline gross debt; leases separately; then net debt.
5. **Validate existing FCF** against LLY, ORCL and VST, before FCF is used in any ratio.
6. **Flow ratios:** OCF/debt, then FCF/debt once step 5 passes, and operating-income interest coverage after the interest expense tag is decided.
7. **Display:** metrics, short factual findings, comparable company history.
8. **Two charts**, each with its question written as its title.
9. **Excel evidence export** with a row per value and its full source metadata.
10. **Reconciliation:** every displayed value traced to its source value.

Later phases (not in the first release): debt maturities, financing terms, covenants, subsequent financing events, appropriate industry peers, stress scenarios, category assessments. Deferred: overall grades, default probabilities and stock recommendations.

## Acceptance criteria (first release)

- For each pilot, every reported input matches the value hand-read from the filing exactly, or is "Unavailable" with a stated reason.
- Ratios and other derived values usually don't appear in a filing. For each pilot they match a result hand-calculated independently from the hand-read inputs, to the stated rounding, or are "Unavailable" with a stated reason.
- Every displayed and exported reported value shows period end, form, filed date, accession, tag, units and selection rule. Every derived value shows its formula and lists each input fact with that metadata; it carries no tag of its own.
- Unit tests cover: missing value is Unavailable, not zero; nonpositive denominator explained; negative FCF and negative net debt kept; no overlapping year-to-date sums; overlapping debt components not double-counted; mismatched dates refused; leases excluded from gross debt; unsupported filer (bank) refused.
- The existing 96 unit tests still pass, and the offline and saved-sample browser checks still pass.
- Vistra's limits are written in the app's README "Known limits".
- No grades, default probabilities or recommendations appear anywhere.
- Copy meets `C:\Users\jackc\Stock Project\docs\Quality_Standard.md`.

## Decisions to resolve

1. **Cash tag:** confirm from the pilot filings which tag reports cash and cash equivalents excluding restricted cash, and what to do when a company reports only a total that includes restricted cash (initial answer: Unavailable).
2. **Debt tags:** which tags make up baseline gross debt for each pilot, and how overlap is detected (for example a total tag alongside its current and noncurrent parts).
3. **Interest expense tag:** which tag reports gross borrowing interest expense for each pilot, and the result when only a net figure is reported.
4. **Unsupported filers:** how the app detects banks, non-USD and non-U.S. GAAP filers.
5. **Order of work:** where this project sits relative to the course features in `CLAUDE.md`.
6. **Public README:** when to mention this work in `README.md`. Not until something is built.
