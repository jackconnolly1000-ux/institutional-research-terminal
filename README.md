# Debt & Liquidity Research Terminal

A Streamlit app that shows what a nonfinancial public company owes, the cash and cash generation behind it, and the SEC filing evidence for each figure. It is a research tool, not investment advice.

Live app: https://sec-filing-research-terminal.streamlit.app/ (the `main` branch). The repository keeps its original name, `sec-filing-research-terminal`.

## What it does

### Debt & Liquidity (the default page)

Pick Eli Lilly (LLY), Oracle (ORCL) or Vistra (VST) and its saved review opens. Each review is frozen at one balance-sheet date (LLY and VST: June 30, 2026; ORCL: August 31, 2026), with balance-sheet facts checked October 14 and the interpretation checked October 16, 2026 (Oracle's re-checked October 17 against its principal calendar). Opening a review makes no SEC, Yahoo or Anthropic request and needs no secrets.

- Cash and equivalents (excluding restricted cash), baseline gross debt (borrowing, excluding leases), net debt and current ratio, each traced to the 10-Q fact it came from.
- Two-date company history compares the prior annual balance sheet with the latest checked date. Fiscal-year and later TTM flows are labeled as overlapping twelve-month windows; unsupported older Vistra borrowing and dependent ratios stay Unavailable. Sources and method: `docs/company_history.md`.
- The app and each individual workbook reconcile current ratio, net debt, TTM OCF/debt, FCF/debt and historical interest coverage. Oracle and Vistra have a `Debt and liquidity` worksheet matching Lilly's core calculation table. `ratio_review.py` and `tests/offline/ratio_sheet.mjs` keep periods, formulas, source provenance and company-specific limits consistent. See `docs/ratio_reconciliation.md`.
- Borrowing components, recognized operating/finance lease liabilities and leases not yet commenced shown separately. Lilly/Vistra June lease balances remain Unavailable; older December lease facts keep their own dates. Individual workbooks include the same Borrowing and leases sheet and source records (`borrowing_leases.py`; [method and limits](docs/borrowing_lease_presentation.md)).
- TTM operating cash flow, capital spending, free cash flow, and OCF/debt and FCF/debt as historical ratios, not repayment forecasts.
- Two common chart questions: what remained after capital spending, and how borrowing/cash changed across the checked dates. Vistra compares cash only because its older borrowing is unsupported. Workbook charts link to the same calculations and dates; see `docs/core_charts.md`.
- A dated funding conclusion, historical interest coverage with each company's denominator limits, selected obligations outside borrowing, and what remains unresolved.
- Company-specific reviews: Oracle's August 31 principal calendar by instrument (commercial paper Unavailable), May 31 maturity schedule, cash reconciliation, repayment funding and revolver audit; Vistra's repayment review and checked financing filings after June 30; Lilly's first-half cash review and May debt terms.
- One primary Excel workbook per company, with a contents guide, formulas, source facts and an About sheet, plus an optional combined summary. The company files contain the full review, history and charts; the combined file retains its original core metric summary and source rows. Source URLs in the company workbooks are clickable links (added by `tests/offline/add_workbook_hyperlinks.py`; the combined summary keeps plain-text URLs). One stale About-sheet sentence in the combined file was corrected on Oct 17 by `tests/offline/patch_combined_principal_note.py`, which rebinds its manifest. See `docs/excel_parity.md`. Each download is a saved file checked against its manifest's fingerprints; if a source changed, the download says Unavailable instead.

### General filing research — experimental (secondary page)

The original tool, reached from the link under the page subtitle. For up to five tickers it:

- Downloads the latest 10-K, the prior 10-K, every 10-Q filed since the latest 10-K, and up to four 8-Ks from the last 180 days from SEC EDGAR.
- Finds the Risk Factors (Item 1A) and Management's Discussion and Analysis sections by their headings. A section that can't be found is reported as missing, not replaced with other text.
- Compares the two 10-Ks' risk factors paragraph by paragraph in code (`compare.py`) and labels each paragraph new, changed, unchanged or removed.
- Sends the changed and new paragraphs, the 10-Q updates, MD&A and the 8-Ks to Claude (Anthropic API), which returns catalysts, risk-factor changes, other risks from management's discussion and 8-K events, each tied to one source.
- Checks the answer: whether it was complete, whether every field is valid, whether each quoted excerpt appears word for word in the cited filing, and whether each figure in a finding appears in that filing.
- Shows revenue, gross margin, operating margin and free cash flow for the trailing twelve months (TTM) from SEC XBRL company facts (`xbrl.py`), and price, market cap and forward P/E from Yahoo Finance with their source field and retrieval time, and a five-year price chart.
- Exports the results to Excel and limits spending on live AI calls to $0.25 a day (see Spending limit below).
- Opens an archived filing-research example (AAPL and STRL, analysis run October 10, 2026) with no live calls. Live runs need `ANTHROPIC_API_KEY` and `SEC_CONTACT_EMAIL`; without them Run analysis is disabled and says why, and the archived example still opens.

## Status

- **Release 1:** steps 1–7 merged as PRs #42–#47; the final reconciliation PR completes step 8 on merge. Ten core measures, checked two-date history, two common chart questions and individual evidence exports cover LLY, ORCL and VST only. Reproducible audit and remaining gaps: `docs/release1_reconciliation.md`.
- **Built:** the three saved company reviews and workbooks above, the Debt & Liquidity default page, and general filing research with its archived example.
- **Remaining:** refreshing a review when a newer 10-Q is filed (today each is rebuilt and checked by hand), and the items each review lists as Unavailable, such as current drawable credit, covenant headroom and updated principal schedules. Live analysis does not compute the debt and liquidity metrics for other tickers. More companies and refresh automation are not started and have no date.
- **Deferred** (the plan's later phases): full financing terms and covenants, recalculating debt and cash from later financing events, a complete obligations analysis, industry peers and stress scenarios. No grades, default probabilities or recommendations are planned. Plan and acceptance criteria: `docs/debt_liquidity_plan.md`.

## What it doesn't do

- It doesn't give investment advice, price targets or ratings.
- The debt and liquidity reviews don't update themselves and cover only LLY, ORCL and VST.
- It doesn't verify the AI's interpretation in general research. An "Excerpt matched" label means the quoted words are in the filing, not that the summary is right.
- The general AI evidence pipeline doesn't read exhibits: risk factors incorporated by reference from an annual-report exhibit (as JPM does) and 8-K press releases (EX-99.1) are not sent to Claude. The separately checked Vistra financing notice cites selected exhibits.
- It doesn't know the period behind most Yahoo Finance values; those show "Period not stated". Yahoo's margins and free cash flow are still in the general research Excel export, labeled that way, next to the SEC figures.

## Known limits

- Oracle's review has an illustrative stress scenario (`liquidity_simulation.py`, `simulation_view.py`). It's a seeded Monte Carlo of twelve-month ending cash under triangular operating cash flow, comparing capex decisions and a hypothetical revolver. It is labelled as a scenario from stated assumptions, never a forecast or funding conclusion, and it leaves out only operating-lease, finance-lease interest and other interest payments, which Oracle's policy places inside OCF. Finance-lease principal, short-term capex financing and purchase obligations aren't shown to overlap, so their effect is measured beside the base result. Percentages are shares of simulated trials, not probabilities, and only the end-of-window balance is tested. The OCF range is an assumption anchored to three checked periods. OCF and prepayments can be given a correlation (default 0; no filing evidence for it), and a table shows how −0.5, 0 and +0.5 change the spread but not the mean. Method and results: `docs/liquidity_simulation.md`.
- Oracle's August 31, 2026 principal calendar (`oracle_principal.py`, checked Oct 17) dates $125.567B of
  senior-note and term-loan principal from the 10-K's tagged instruments: $7.317B falls due Sep 2026–Aug 2027.
  Commercial paper's August balance and dates are Unavailable; term-loan installments are calculated from
  its stated terms; the grouped quarter repayment line is checked, not subtracted. It is not funding coverage.
  Excel: Payment dates, row 35 onward. Method and checks: `docs/oracle_principal_calendar.md`.
- The October 16 reader audit clarifies TTM versus half-year cash flows, separates balance-sheet
  check dates from later interpretation dates, and reconciles app/Excel filing-review scope.
  Oracle's saved SEC financing-candidate index through October 15 is now bound to its revolver
  audit; it identifies only the two already reviewed later 8-Ks and establishes no newer drawable
  amount. Individual workbook documentation references use public URLs. Findings and remaining
  limits: `docs/review_clarity_audit.md`.
- `funding_conclusions.py` adds dated funding conclusions to LLY, ORCL and VST using their
  existing checked evidence. The app and individual Excel exports show near-term obligations,
  resource access, competing uses and decisive unknowns. Historical interest definitions and
  periods differ; no funding-strength ranking or future coverage is inferred. Each individual
  export opens with Funding conclusion and retains its detail, sources and calculations.
  Changed evidence or interpretation refuses a stale conclusion/download. Method and limits:
  `docs/funding_conclusions.md`; shared export layout: `tests/offline/funding_sheet.mjs`.
- `vistra_interest.py` adds historical coverage of the separately reported interest component:
  TTM to June 30, 2026 operating income 3,563M / interest 1,117M = 3.19x. The app and primary
  Vistra Excel reconcile swaps, amortization, extinguishment, capitalized interest and Other to
  the mixed 1,132M total, retaining raw XBRL signs. The original H1 2025 filing independently
  agrees. Receivables/Nuveen allocation, Other detail and all-in financing cost remain Unavailable.
  Rebuild with `tests/offline/build_vistra_interest.py` then `tests/offline/build_vistra_liquidity.mjs`.
  Exact periods, definitions and limits: `docs/vistra_interest_coverage.md`.
- `oracle_interest.py` adds historical reported-line interest coverage to Oracle's app review and
  primary workbook: TTM to August 31, 2026 operating income 23,057M / reported Interest expense
  5,104M = 4.52x. Exact consolidated periods and source facts are retained. Capitalization basis,
  borrowing-only coverage, lease-interest overlap and contract covenant headroom remain Unavailable.
  Lease-note interest is not added. Rebuild the frozen inputs with `tests/offline/build_oracle_interest.py`
  and then `tests/offline/build_oracle_liquidity.mjs`. Sources and limits: `docs/oracle_interest_coverage.md`.
- Each saved company tab now has its own primary Excel download, including a Lilly-only
  review with calculations and source facts. The combined pilot export is under
  **Optional combined export**. All four saved workbooks use light vertical column separators
  and outside table/block borders. Financial inputs, formulas, source records and chart bindings
  are retained. `tests/offline/build_lly_liquidity.mjs` builds the Lilly workbook with the same
  `workbook_style.mjs` helper and artifact runtime as the other workbook builders.
- `oracle_repayment.py` matches all 21 checked lease and purchase payment buckets to dated
  resource evidence. The app and Oracle workbook use the same model. August cash is one shared,
  unallocated pool. Restricted cash is excluded; historical OCF, prepayments and equity proceeds
  are not added again. Conditional revolver funding stops at the original March 2031 expiry.
  Future coverage remains Unavailable: dated funding allocations, future OCF, drawable credit,
  remaining August debt principal/interest dates and several obligation overlaps are unresolved.
  (Since Oct 17, note and term-loan principal is dated; commercial paper and interest remain open.)
  The old May principal schedule is preserved as historical evidence, without a roll-forward.
  The Oracle workbook manifest checks the quarterly liquidity JSON, annual financing JSON and
  saved revolver audit. The builder invokes the pure Python repayment model using `CODEX_PRIMARY_RUNTIME_PYTHON`;
  deployment only reads the checked workbook and requires no additional dependency.
- `oracle_revolver.py` audits the exact seven saved Oracle documents. May 31 commitment of $10B
  less zero advances gives $10B of historical undrawn commitment, not verified drawable capacity.
  August balances remain Unavailable. The conditional $12B increase ceiling is not committed cash.
  LC treatment, reductions, draw conditions, the covenant and extensions have accession-specific
  sources. Rebuild `samples/oracle_revolver.json` with `tests/offline/build_oracle_revolver.py`
  before rebuilding the Oracle workbook. Changed raw files require review. Details and gaps:
  `docs/oracle_revolver_reconciliation.md`. No new filings were downloaded for this audit.

- The company reviews use larger section headings, concise borrowing labels and an Oracle chart
  measuring each cash contribution from zero. Opening/closing cash balances remain separate from quarter flows.
  The three liquidity workbooks outline tables and calculation blocks with light borders.
  Oracle's native Excel chart compares reported OCF, OCF excluding specified prepayments, and cash
  capex for June–August 2026 in USD millions. Black subtraction formulas stay black; green indicates
  cross-sheet links. Sources, numeric inputs, financial formulas and existing research are retained.
  The combined pilot download is a styled saved export (`samples/liquidity_pilots.xlsx`), bound to
  both source JSON files by `samples/liquidity_pilots.manifest.json`. It becomes Unavailable when
  those sources or the workbook differ. The general programmatic export remains available.
  Workbook styling is rebuilt with `tests/offline/workbook_style.mjs` and
  `tests/offline/style_pilot_workbook.mjs` using the Codex spreadsheet runtime. The latter imports
  the current saved export, or accepts a current downloaded pilot workbook as its second argument,
  verifies every metric against the snapshots, and preserves financial formulas and source rows.
  The three existing Oracle filter regions are retained as native Excel tables with filter controls.
  Dedicated Oracle and Vistra builders use the same style helper. No runtime dependency is added.

- Vistra's saved repayment review, checked October 15, adds the January–June cash reconciliation,
  selected repayment dates, project recourse and funding resources by borrower
  (`vistra_liquidity.py`, `vistra_liquidity_sources.py`, `vistra_liquidity_view.py`). Its separate
  individual Excel download has formulas, a native payment chart and filing/context evidence.
  `samples/vistra_liquidity.manifest.json` binds the workbook to its source JSON. June reported liquidity
  is not current drawable credit or cash all held at Parent. Current capacity, covenant headroom,
  parent-accessible cash and Helix calls remain Unavailable. Project debt and LC amounts are not added
  twice; the December 2025 maturity schedule is not rolled forward after refinancing. The September 30
  amendment's filing date is corrected to October 5 (accepted October 2 after hours). Sources, limits
  and rebuild steps: `docs/vistra_liquidity_reconciliation.md`. Existing reviews and research are preserved.

- Oracle's saved review also includes a June–August cash reconciliation and funding analysis
  (`oracle_liquidity.py`, `oracle_liquidity_view.py`). It separates the specified customer-prepayment
  contribution from other OCF and equity proceeds, shows dated lease and purchase payments, and links
  the reviewed revolver agreement. The Oracle cash-analysis download contains formulas, sources and a
  native chart; `samples/oracle_liquidity.manifest.json` binds it to the checked JSON review.
  The original combined evidence download is preserved. Historical funding exclusions are not forecasts
  or estimates of recurring OCF. August drawable credit, covenant headroom and remaining debt principal
  dates remain Unavailable. Source audit and rebuild instructions: `docs/oracle_liquidity_reconciliation.md`.

- The default saved debt and liquidity reviews are available for LLY, ORCL and VST, checked October 14, 2026. It shows each company's dated cash, baseline gross debt, net debt and current ratio, their reported inputs and source 10-Q, and a separate Excel evidence download with formulas. Vistra's checked subsequent financing changes are included. The saved company reviews also show checked TTM operating cash flow, reported capital spending, free cash flow and flow/debt ratios, a borrowing breakdown, and selected obligations with their dates and recognition status. Oracle's customer prepayments and Vistra's capex definition are stated beside the flows. This is a frozen review, not a live update or a complete obligations analysis; historical earnings coverage is shown for all three companies with their distinct interest-component and capitalization limits. Oracle now includes its historical May 31 principal maturity schedule, its reconciliation to carrying debt, and two checked later 8-Ks. No August maturity schedule or current revolver availability is inferred; see `docs/oracle_maturity_reconciliation.md`. Reconciliation: `docs/pilot_cashflow_reconciliation.md`. The archived AAPL/STRL filing-research example is separate.

- Live results include a dated EDGAR index of 8-Ks, debt-offering form candidates and periodic-report amendments since the latest balance sheet. For Vistra's June 30, 2026 balance sheet, ten filings through October 14 were manually screened for financing, with source documents linked; the September offering documents refer to one completed $1.5 billion issuance. Oracle’s August 31 anchor also joins its two checked September 8-Ks and exhibits. Other companies and later or unmatched filings remain "Not checked." A retrieval gap is labeled incomplete. The archived example predates this index.
- "No close match in the prior 10-K" is a text test. A heavily rewritten paragraph can be labeled that way; the closest prior paragraph is shown as context.
- Section extraction has been checked on seven filers (AAPL, FAST, STRL, MSFT, WMT, JNJ, JPM). Other filing layouts may not be recognized.
- Each request is capped at 76,000 tokens (64,000 of input, 12,000 of output). When the evidence is larger, the rest is omitted and the omission is shown.
- The figures check is a text match. It normalizes formats ($14.7M, 14.7 million, $14,700 thousand) and ignores dates and form names, but a figure written very differently from the filing (for example "2.00 to 1.00" vs "2.00x") is flagged even when it's right, and a fair calculation such as a percent change is always flagged.
- Claude doesn't always follow the prompt's rules, so the code flags what it can instead of trusting the text. In the Oct 10, 2026 test run (AAPL and STRL) it:
  - did not list a second source for figures taken from one (a $35.3 million buyback figure, flagged as not in the cited source);
  - wrote "new risk factors" for paragraphs the code only found to have no close match in the prior 10-K (flagged as wording);
  - named internal source IDs such as "QU3" or "R_CMP" in its summaries (not flagged).
- The figures check also flags fair sums, such as $86.3 billion of purchase obligations reported as $57.0 billion and $29.3 billion. The card says some flags are calculations.
- The wording check can flag financial uses it doesn't recognize, such as "subject to a leverage test".
- A first run takes about a minute per ticker (131 seconds for AAPL and STRL on Oct 10, 2026).
- Public live runs fit about one ticker a day. A worst-case call costs $0.248 against the $0.25 daily cap.
- A skipped ticker still downloads its filings first, because the cost check needs the measured size of the request. The skip message appears only after the filings download.
- A call that runs across midnight ET isn't counted on either day: `settle()` drops a reservation from a previous day, because the new day already started from zero. This affects at most one call, and the Anthropic monthly limit still applies.
- The daily spending counter is kept in memory and resets when the app restarts, so a restart allows another day's worth. The Anthropic account's monthly limit is the hard stop.
- SEC TTM figures use six US GAAP tags: RevenueFromContractWithCustomerExcludingAssessedTax (then Revenues), GrossProfit, OperatingIncomeLoss, NetCashProvidedByUsedInOperatingActivities and PaymentsToAcquirePropertyPlantAndEquipment. A company that tags these differently shows "Not reported". Banks are the main case: JPMorgan files no gross profit, operating income or capital expenditure tag, and tags Revenues only in its 10-K, so all four of its figures show "Not reported".
- TTM is the latest fiscal year plus this year to date minus last year to date, or the fiscal year itself when the latest filing is a 10-K. When a period was reported more than once (a restatement, or last year's figures repeated in a 10-Q), the most recently filed value is used.
- The archived AAPL/STRL example is frozen: the analysis is from Oct 10, 2026 and the price history ends at the Oct 9 close (retrieved Oct 11), and its SEC figures count only filings made by Oct 10 (retrieved Oct 11). It doesn't update.

## Spending limit

Every live Claude call first reserves its worst-case cost (measured input tokens plus the 12,000-token output reserve, at the prices in `budget.py`), then settles at the cost the API reports. If the worst case doesn't fit in what's left of today's $0.25 (America/New_York day), the ticker is skipped and its tab says so. Answers served from the app's cache cost nothing and skip the counter. A request the API rejects (4xx) is released; a timeout, connection error or 5xx is charged at the worst case, since it may have been billed. When the account's monthly limit is reached, the tab says the monthly AI budget is used up.

The owner can run past the daily cap (the spend still counts) by entering a passcode in the sidebar. Set `OWNER_PASSCODE` in Streamlit Secrets and in `.streamlit/secrets.toml`; generate it with:

```
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

If `OWNER_PASSCODE` isn't set, the sidebar field doesn't appear. The passcode is never read from the URL.

## Running it

```
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

On Windows, use `py -3.12 -m venv .venv` and `.venv\Scripts\` in place of `.venv/bin/`.

The Debt & Liquidity page needs no secrets. Live general research needs `ANTHROPIC_API_KEY` and `SEC_CONTACT_EMAIL` in Streamlit Secrets (`.streamlit/secrets.toml`; SEC EDGAR asks every automated request to name a contact), and optionally `OWNER_PASSCODE`.

## Tests

```
.venv/bin/python -m unittest discover -s tests -p "test_*.py"      # Mac/Linux
.venv\Scripts\python -m unittest discover -s tests -p "test_*.py"  # Windows
```

Unit tests import the production modules (`sec_data.py`, `compare.py`, `analysis.py`, `market_data.py`, `budget.py`, `xbrl.py`) and make no network calls. `tests/test_app_pages.py` runs the whole app in Streamlit's AppTest with no secrets and every outside connection refused: default page, company selection, navigation, kept selections, missing and stale reviews, the archived example and download bytes. `tests/offline/` runs the whole app on fake SEC, Yahoo and Anthropic responses; `tests/check_risk_extraction.py` checks section extraction against live EDGAR filings without calling Anthropic.
