# Debt and liquidity: first-release plan

Status (checked against `main` at `9efb069`, Oct 16, 2026): **delivery steps 1–6 and 8–10 are built for the three pilots as frozen, dated reviews; step 7 is partly built.** With Release 1 steps 1–2 (branch `debt-liquidity-primary`, PR #42, not merged), the saved reviews become the app's default page. See "Release 1 status" at the end for what is built, remaining and deferred.

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
| TTM free cash flow: `NetCashProvidedByUsedInOperatingActivities` minus `PaymentsToAcquirePropertyPlantAndEquipment`, with period end, form, filed date and accession | `xbrl.py` | Implemented and unit-tested on AAPL, STRL and JPM fixtures. **Generic FCF reconciles for ORCL and VST. LLY uses another capex tag; the saved review reads all six checked source filings through `cash_generation.py`.** See `pilot_cashflow_reconciliation.md`. |
| TTM revenue, gross margin, operating margin (`OperatingIncomeLoss` is the operating income input coverage would use) | `xbrl.py` | Implemented and unit-tested on fixtures. Not validated against the pilots. |
| "Financing and liquidity" category on AI findings (`FINANCING_LIQUIDITY`) | `analysis.py`, `ui.py` | Exists. It is Claude's unverified label, not a calculation. |
| Cash and cash equivalents at the latest 10-K/10-Q balance-sheet date (`xbrl.cash_and_equivalents`): the anchor filing's own USD instant, with form, filed date, accession, tag, units and selection rule; amendments to that period replace it with a note; differing later comparatives are flagged, not used | `xbrl.py` | Implemented and unit-tested; matches the LLY, ORCL and VST evidence values. Shown in the frozen pilot view; not yet part of live analysis. |
| Current ratio (`xbrl.current_ratio`): `AssetsCurrent` / `LiabilitiesCurrent` at the anchor date, both from one filing (an amendment replaces the pair only if it reports both); derived, no tag; zero or negative liabilities explained, not divided | `xbrl.py` | Implemented and unit-tested; matches the LLY (1.35), ORCL (1.17) and VST (0.97) evidence values. Shown in the frozen pilot view; not yet part of live analysis. |
| Baseline gross debt (`xbrl.baseline_gross_debt`): per-company verified components in `BORROWING_PRESENTATIONS` (LLY: `DebtCurrent` + `LongTermDebtNoncurrent`; ORCL: `NotesPayableCurrent` + `LongTermNotesAndLoans`; VST: three standard components plus one filing extension), all from one filing at the anchor date; checked against the filer's own total when the same filing reports it; derived, no tag; companies without a verified presentation get Unavailable | `xbrl.py` | Tested for LLY (54,908M at Jun 30, 2026; 42,503M at Dec 31, 2025), ORCL (125,337M at Aug 31, 2026; 129,541M at May 31, 2026), and VST (19,895M at Jun 30, 2026 when the checked 10-Q document is supplied by accession). Caveats belong to the checked filing; an unchecked filing or a missing/unreadable extension document gives Unavailable, retaining readable components. Shown in the frozen pilot view; no live filing-document fetch yet. |
| Filing-level inline XBRL reader (`filing_xbrl.read_instant`): one USD instant fact by exact prefixed tag and date, undimensioned, with context, unit, scale, sign and fixed-zero handling; conflicting, wrong-period, wrong-unit or dimensioned facts return Unavailable | `filing_xbrl.py` | Tested on saved filing data: VST accounts receivable financing 300M (context c-8); used by `baseline_gross_debt` when the checked filing document is supplied by accession. |
| Dated EDGAR filing inventory: candidate 8-K, 424B, FWP, S-3 and periodic-report amendment forms since the latest balance sheet; retrieves relevant older submission pages or labels gaps incomplete | `sec_data.py`, `filing_review.py`, `app.py` | Indexed links shown in an app expander and Excel Filing review sheet. `reviewed_financing.py` joins ten accession-specific, manually checked Vistra filings for the June 30, 2026 anchor: six 8-Ks and four offering documents. The offering documents support one completed issuance. Later or unmatched candidates stay Not checked; an incomplete index remains incomplete. Oracle's August 31, 2026 anchor joins its two checked September 8-Ks and exhibits (`oracle_financing.py`); its saved index through October 15 lists no other later candidate. Lilly's later filings were screened through October 15 in `lly_financing.py` (`lly_financing_audit.md`) and shown in its saved review, but are not joined to the live index. |
| Saved pilot display and Excel evidence: cash, gross debt, same-filing net debt and current ratio for the three pilots | `liquidity_pilot.py`, `samples/liquidity_pilots.json` | Free frozen view, checked Oct 14, 2026; does not overwrite existing analysis results or make a Claude call. Each metric traces to its inputs. Net debt refuses missing inputs, differing dates, units or filing versions and keeps valid negative results. Excel uses formulas referencing reported input rows. Live analysis does not yet fetch the VST document or populate these metrics. |
| Checked TTM OCF, reported capital spending, FCF and flow/debt ratios | `cash_generation.py`, `filing_xbrl.read_duration`, `liquidity_pilot.py` | Six source filings checked and shown in frozen company reviews; LLY has a specifically verified capex tag. Exact durations and CIK checked. Selected obligations and Oracle lease disclosures shown separately through `company_review.py`; no amount is added to borrowing. See `pilot_cashflow_reconciliation.md`. |
| Historical operating-income interest coverage | `lly_interest.py`, `oracle_interest.py`, `vistra_interest.py` and their views | Built for the three pilots: LLY 31.17x, ORCL 4.52x (reported Interest expense line), VST 3.19x (separately reported interest component), each with its stated denominator limits (`lly_interest_coverage.md`, `oracle_interest_coverage.md`, `vistra_interest_coverage.md`). |
| Complete lease extraction and obligations review | none | Not built; selected manually checked disclosures do not establish completeness. |

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
- All existing unit tests still pass (370 on `main` at `9efb069`; 379 on PR #42), and the offline and saved-sample browser checks still pass.
- Vistra's limits are written in the app's README "Known limits".
- No grades, default probabilities or recommendations appear anywhere.
- Copy meets `C:\Users\jackc\Stock Project\docs\Quality_Standard.md`.

## Decisions to resolve

1. **Cash tag:** confirmed for LLY, ORCL and VST (`us-gaap:CashAndCashEquivalentsAtCarryingValue`; restricted cash is excluded in each, per the pilot evidence files). Still open for other filers: how the app establishes that the fact excludes restricted cash. When it cannot, or when a company reports only a total that includes restricted cash, the result is Unavailable.
2. **Debt tags:** which tags make up baseline gross debt for each pilot, and how overlap is detected (for example a total tag alongside its current and noncurrent parts).
3. **Interest expense tag:** which tag reports interest expense on borrowings for each pilot. The basis is decided (see the coverage definition). Dimensioned facts, such as LLY's segment-tagged 10-Q interest expense, are usable only for a specific company after an extractor checks the inline XBRL context (tag, segment member, no other dimensions, periods, units, accession) and agreement with the printed table. LLY's single reportable segment supports an LLY-specific decision, not a universal rule. Decided Oct 15, 2026: `lly_interest.py` applies that Lilly-only check, and the saved review shows 31.17x TTM to June 30, 2026 (derived operating income 33,633M / reported interest expense 1,079M), labeled because the interim line doesn't state its capitalization basis (`lly_interest_coverage.md`). ORCL (4.52x) and VST (3.19x) are decided in their own coverage files.
4. **Unsupported filers:** how the app detects banks, non-USD and non-U.S. GAAP filers.
5. **Order of work:** decided Oct 16, 2026: Release 1 makes Debt & Liquidity the product; see "Order of work" in `CLAUDE.md`.
6. **Public README:** decided: the README leads with Debt & Liquidity now that the reviews are built.


### Lilly dated review (October 15, 2026)

`lly_liquidity.py` and `samples/lly_liquidity.json` supply the app and Lilly workbook with reconciled H1 cash sources/uses, annual due-year carrying balances, dated unused facilities, selected acquisition payments and manufacturing commitments. See `docs/lly_liquidity_review.md`. Updated June principal, drawable facilities and future payment coverage remain Unavailable. Other reviews and catalysts are preserved.


## Release 1 status (Oct 16, 2026)

Release 1 order (agreed Oct 16, 2026). One step per pull request; each keeps the checked financial models, numbers, source gates and workbook bytes unchanged unless the step says otherwise:

1. Reconcile the roadmap with `main` (CLAUDE.md, README, `docs/debt_liquidity_plan.md`).
2. Make Debt & Liquidity the primary experience: default company selector, no Run analysis action or expander, saved reviews without secrets or network, general research as secondary access, AAPL/STRL labeled as the archived example.
3. Borrowing and lease presentation.
4. Ratio reconciliation.
5. Two-date comparable history.
6. Two core charts.
7. Individual Excel parity.
8. Final source and app reconciliation.

"Delivery sequence" steps above are the original build plan; Release 1 steps are this numbered list. Where a delivery step has a first version on `main`, the Release 1 step brings it to the agreed presentation and checks.

**Built** (on `main` unless noted):
- Delivery steps 1–6 for LLY, ORCL and VST: pilot data, cash, current ratio, baseline gross debt and net debt, financing filings notice (Vistra and Oracle joined to the live index by accession; Lilly screened in its own audit), obligations notes, validated FCF, OCF/debt, FCF/debt and historical interest coverage (LLY 31.17x, ORCL 4.52x, VST 3.19x).
- First versions of delivery steps 8–10: the cash-flow and maturity/payment charts, one checked workbook per company plus the combined export, and the reconciliation files in `docs/`. Release 1 steps 6–8 revisit them.
- Delivery step 7, partly: metrics and short factual findings (dated funding conclusions) are shown; comparable history is not (Release 1 step 5).
- Release 1 steps 1–2 (branch `debt-liquidity-primary`, PR #42, not merged): roadmap reconciled; the reviews are the default page, open from a company selector without Run analysis, and load without secrets or network. General filing research is secondary and labeled experimental; AAPL/STRL is the archived filing-research example.

**Remaining:**
- Release 1 steps 3–8, not started.
- Leases: Oracle's August 31, 2026 operating (34.621B) and finance (9.185B) lease liabilities are shown separately from borrowing, and its 288B of leases not yet commenced is shown as a commitment. Lilly's and Vistra's June 30, 2026 10-Qs report no lease liabilities, so June 30 amounts are Unavailable; the latest reported amounts are at Dec 31, 2025 (Lilly: 1,362M operating, no finance leases described; Vistra: 105M operating and 222M finance). No review has a complete lease or obligations extraction, and lease interest is not added to any coverage ratio.
- Funding: future funding coverage is Unavailable for all three. The decisive unknowns are the remaining principal calendar (Lilly has only the May 2026 issuance schedule; Oracle only its May 31 schedule), drawable credit and draw conditions (Lilly's post-August facility renewal, Oracle's current revolver availability, Vistra's borrowing base), covenant headroom, the timing and overlap of acquisition, manufacturing, capital-call and uncommenced-lease payments, Vistra's Parent-accessible cash, and all-in financing cost. Each is stated in its review; none is estimated.
- Outside Release 1: supported-filer detection for banks, non-USD and non-U.S. GAAP filers (decision 4), the live pipeline computing these metrics beyond the three pilots, and refreshing a review when a newer filing arrives (today each review is rebuilt and checked by hand).

**Deferred:** the later phases listed under "Delivery sequence" (financing terms, covenants, recalculating debt and cash from later events, full obligations analysis, peers, stress scenarios, category assessments), plus more companies and refresh automation. Never: grades, default probabilities, recommendations.
