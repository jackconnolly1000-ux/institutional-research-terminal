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
| Cash and cash equivalents at the latest 10-K/10-Q balance-sheet date (`xbrl.cash_and_equivalents`): the anchor filing's own USD instant, with form, filed date, accession, tag, units and selection rule; amendments to that period replace it with a note; differing later comparatives are flagged, not used | `xbrl.py` | Implemented and unit-tested; matches the LLY, ORCL and VST evidence values. Not shown in the app yet. |
| Current ratio (`xbrl.current_ratio`): `AssetsCurrent` / `LiabilitiesCurrent` at the anchor date, both from one filing (an amendment replaces the pair only if it reports both); derived, no tag; zero or negative liabilities explained, not divided | `xbrl.py` | Implemented and unit-tested; matches the LLY (1.35), ORCL (1.17) and VST (0.97) evidence values. Not shown in the app yet. |
| Debt, leases, interest expense, other ratios | none | Not built |

## First-release scope (planned)

1. Audit the existing app and data pipeline
2. Add reliable SEC financial inputs
3. Normalize borrowing
4. Calculate supported debt and liquidity ratios
5. Present short factual findings and comparable company history
6. Add two charts, each answering a specific financial question
7. Provide an Excel evidence export
8. Reconcile displayed values to their sources
9. Show a "financing filings since the balance sheet" notice (see definitions)
10. Show a short sourced note for major obligations or commitments outside baseline debt (see definitions)

Supported filers: USD, U.S. GAAP, nonfinancial operating companies. Banks (for example JPM) and specialized issuers need separate methods and get an "unsupported" result, not a calculation.

## Financial definitions (planned)

- **Cash (initial):** cash and cash equivalents, excluding restricted cash, as of the balance-sheet date. Each value carries its source metadata (see source rules). When the supported fact cannot be established from the filing, the result is "Unavailable" with the reason, not zero and not a substitute figure. Tag confirmed for LLY, ORCL and VST: `us-gaap:CashAndCashEquivalentsAtCarryingValue`, which in each pilot's filing excludes restricted cash (see the pilot evidence files). For other filings it is used only when the filing supports that it excludes restricted cash; otherwise the result is Unavailable.
- **Baseline gross debt:** reported carrying amounts of interest-bearing borrowing, excluding operating and finance leases.
- **Leases:** operating and finance lease liabilities, shown separately and never added to baseline gross debt.
- **Net debt:** baseline gross debt minus cash as defined above. Restricted cash and investments are not subtracted automatically. Negative net debt is a valid result and is kept.
- **Current ratio:** current assets / current liabilities, both from the same balance-sheet date.
- **Free cash flow (initial):** TTM operating cash flow minus stated purchases of property, plant and equipment. This is the existing `xbrl.py` calculation.
- **OCF/debt and FCF/debt:** compatible TTM flows divided by period-end baseline gross debt.
- **Operating-income interest coverage (decided Oct 14, 2026):** TTM operating income / TTM reported interest expense on borrowings, before any offset for interest income. When the filing says the expense is net of capitalized interest, the ratio says so (for example "Operating income / reported interest expense on borrowings (net of capitalized interest)"). It is never labeled "gross interest incurred". Capitalized interest is never added to this denominator; if interest incurred (expensed plus capitalized) is supported later, it is a separately named measure. If the TTM interest inputs can't be established reliably from the filing's tagged data, the TTM ratio is "Unavailable"; an older fiscal-year expense is never substituted into a current TTM ratio.
- **Financing filings since the balance sheet (decided Oct 14, 2026):** a sourced notice listing filings made after the balance-sheet date that report financing: 8-K and 8-K/A filings and debt-offering filings (for example 424B2 prospectuses and FWPs) and their exhibits, screened by their contents, not only by 8-K item number. Each entry shows event date, filed date, form and item, accession and link, a factual description, and whether any stated amount is outstanding debt, facility capacity, or another amount. Events are never rolled into the dated balance-sheet debt or cash. When nothing relevant is found, the notice says: "No relevant financing filing identified among [filing types] filed from [date] through [date], checked as of [date]." It never claims that no financing occurred.
- **Obligations outside baseline debt (decided Oct 14, 2026):** when a pilot filing discloses a major obligation or commitment that is not in baseline gross debt (for example Oracle's future lease commitments for leases not yet commenced), the app shows a short note stating what it is, the amount as disclosed, its reporting date, whether it is recognized on the balance sheet, and its filing, location and accession. It is never added to debt, lease liabilities or any ratio. Which items count as "major" is decided per pilot from the filing and recorded in that pilot's evidence file.

## Source rules (planned)

- Every reported value keeps its period end, form, filed date, accession number, XBRL tag, units, and any selection or revision rule applied (for example "most recently filed value for this period").
- A derived value (net debt, gross debt summed from components, every ratio) has no XBRL tag of its own. It lists every input fact it was calculated from, each with that fact's full source metadata, plus the formula used.
- Check debt components for overlap before adding them, and check that inputs share comparable dates before calculating.
- A missing value is "Unavailable", never zero.
- An empty financing-filings or obligations notice ("No relevant financing filing identified…" or no obligations listed) is allowed only after the intended filings were retrieved and reviewed successfully. If retrieval or review is incomplete, the notice says "Not checked" with the reason, never "No relevant filing found".
- Rounding: a tagged value is compared with a printed figure after rounding the tagged value to the printed figure's precision, half away from zero (for example $492.7 million tagged matches $493 million printed in a table "in millions"). Amounts calculated from rounded printed figures are labeled as hand calculations, not exact SEC facts.
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
4a. **Financing filings notice:** screen filings after each pilot's balance-sheet date and check the result by hand against EDGAR (LLY evidence: `docs/pilot_evidence_lly.md`).
4b. **Obligations outside baseline debt:** record each pilot's disclosed major commitments in its evidence file and show the note.
5. **Validate existing FCF** against LLY, ORCL and VST, before FCF is used in any ratio.
6. **Flow ratios:** OCF/debt, then FCF/debt once step 5 passes, and operating-income interest coverage after the interest expense tag is decided.
7. **Display:** metrics, short factual findings, comparable company history.
8. **Two charts**, each with its question written as its title.
9. **Excel evidence export** with a row per value and its full source metadata.
10. **Reconciliation:** every displayed value traced to its source value.

Later phases (not in the first release): debt maturities, financing terms, covenants, recalculating debt and cash from subsequent financing events (the first release only lists them), detailed analysis of commitments and other obligations outside debt (the first release only notes them), appropriate industry peers, stress scenarios, category assessments. Deferred: overall grades, default probabilities and stock recommendations.

## Acceptance criteria (first release)

- For each pilot, every reported input matches the value hand-read from the filing exactly, or is "Unavailable" with a stated reason.
- Ratios and other derived values usually don't appear in a filing. For each pilot they match a result hand-calculated independently from the hand-read inputs, to the stated rounding, or are "Unavailable" with a stated reason.
- Every displayed and exported reported value shows period end, form, filed date, accession, tag, units and selection rule. Every derived value shows its formula and lists each input fact with that metadata; it carries no tag of its own.
- Unit tests cover: missing value is Unavailable, not zero; nonpositive denominator explained; negative FCF and negative net debt kept; no overlapping year-to-date sums; overlapping debt components not double-counted; mismatched dates refused; leases excluded from gross debt; unsupported filer (bank) refused.
- Financing notice: for each pilot, the listed filings match a hand check of EDGAR for the same dates; no listed amount changes balance-sheet debt or cash; facility capacity is never shown as borrowing; an empty result uses the "No relevant financing filing identified…" wording with filing types, date range and check date.
- Notices: a failed or incomplete retrieval or review shows "Not checked" with the reason, never an empty result (unit-tested).
- Obligations note: each note matches the filing's disclosed amount, date and location and states whether the item is on the balance sheet; no such amount changes debt, lease liabilities or any ratio.
- Interest coverage: the label states the basis, including "net of capitalized interest" when the filing says so; capitalized interest is never added to the denominator; unit tests cover Unavailable when a TTM interest input is missing, and refuse a fiscal-year expense in a TTM ratio.
- The existing 96 unit tests still pass, and the offline and saved-sample browser checks still pass.
- Vistra's limits are written in the app's README "Known limits".
- No grades, default probabilities or recommendations appear anywhere.
- Copy meets `C:\Users\jackc\Stock Project\docs\Quality_Standard.md`.

## Decisions to resolve

1. **Cash tag:** confirmed for LLY, ORCL and VST (`us-gaap:CashAndCashEquivalentsAtCarryingValue`; restricted cash is excluded in each, per the pilot evidence files). Still open for other filers: how the app establishes that the fact excludes restricted cash. When it cannot, or when a company reports only a total that includes restricted cash, the result is Unavailable.
2. **Debt tags:** which tags make up baseline gross debt for each pilot, and how overlap is detected (for example a total tag alongside its current and noncurrent parts).
3. **Interest expense tag:** which tag reports interest expense on borrowings for each pilot. The basis is decided (see the coverage definition). Dimensioned facts, such as LLY's segment-tagged 10-Q interest expense, are usable only for a specific company after an extractor checks the inline XBRL context (tag, segment member, no other dimensions, periods, units, accession) and agreement with the printed table. LLY's single reportable segment supports an LLY-specific decision, not a universal rule. Until such an extractor passes those checks, the app's TTM coverage stays Unavailable.
4. **Unsupported filers:** how the app detects banks, non-USD and non-U.S. GAAP filers.
5. **Order of work:** where this project sits relative to the course features in `CLAUDE.md`.
6. **Public README:** when to mention this work in `README.md`. Not until something is built.
