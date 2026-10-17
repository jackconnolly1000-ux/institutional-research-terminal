# SEC Filing Research Terminal: project instructions

## What this is

I'm Jack, a sophomore finance student at Villanova School of Business. I'm building the Debt & Liquidity Research Terminal, a Streamlit app that traces checked SEC facts through reconciled calculations to dated funding and repayment conclusions for three validation companies (LLY, ORCL, VST). General filing research and AI summaries remain a separate experimental workflow. It's live at https://sec-filing-research-terminal.streamlit.app/.

Stack: Python, Streamlit, Plotly, yfinance, BeautifulSoup, and the Anthropic API (Claude). I work in VS Code with Claude Code, and in Google Colab.

Deployment: Streamlit Cloud deploys `main`, runs Python 3.12 (set in App settings) and installs the pinned `streamlit==1.65.0`. After each deploy, the `[versions]` line in the Cloud log confirms the running Python, Streamlit and pandas versions.

My role is product manager and system architect. I decide what the product does, write the business logic and prompts, integrate AI-generated code, fix API connections, and refine the interface.

## The goal

1. **A resume project that shows real skills.** I want to build those skills and be able to explain every part of this app to an employer: the code, the data sources, the analytics, and how the pieces connect. A smaller feature I understand is worth more than a bigger one I can't explain.
2. **Apply what I learn in VSB 2008 Business Analytics.** The course file in this project lists what I've covered and what's upcoming. Use it when suggesting features.

## Where things live

Everything for this project is in one folder on my Lenovo laptop (Windows 11): `C:\Users\jackc\Stock Project`. The Mac is retired.

```
Stock Project/
├── README.md        map of the folder
├── app/             the code (GitHub repo, PUBLIC, deploys to Streamlit)
│   ├── app.py       downloads, caching, the Claude call, page layout (runs Streamlit on import)
│   ├── sec_data.py  which SEC filings to use, section boundaries, paragraphs (no Streamlit, tested)
│   ├── compare.py   paragraph-level comparison of the current and prior 10-K risk factors (tested)
│   ├── analysis.py  evidence blocks, token budget, prompt and schema, response checks, excerpt matching (tested)
│   ├── market_data.py  Yahoo values as numbers with unit, period, source, retrieval time (tested)
│   ├── xbrl.py      TTM figures and dated balance-sheet metrics from companyfacts; verified debt can also use filing_xbrl for extension facts (no Streamlit, tested)
│   ├── filing_xbrl.py   one exact instant or duration from a filing's own inline XBRL, with context, unit and checks (no Streamlit, tested)
│   ├── filing_review.py  display the subsequent-filing index and its review status
│   ├── reviewed_financing.py  ten accession-specific Vistra financing filing checks; unknown filings stay Not checked
│   ├── cash_generation.py  exact-duration OCF and capital spending for six checked pilot filings; includes the LLY-specific capex tag
│   ├── borrowing_leases.py  checked borrowing/lease presentation shared by the app and individual workbooks; dated lease facts in samples/borrowing_leases.json
│   ├── export_guide.py  individual workbook contents/reading rules; shared layout at tests/offline/export_guide.mjs
│   ├── core_charts.py  two checked chart questions, shared by app and individual workbooks
│   ├── company_history.py  checked two-date company history; annual facts in samples/company_history.json
│   ├── ratio_review.py  reconcile saved ratio values, input provenance, exact TTM periods and company-specific bases for the app and individual workbooks
│   ├── company_review.py  the default page: company selector, saved review (cash-flow chart, borrowing breakdown, selected obligations, unresolved questions) and checked workbook downloads
│   ├── simulation_view.py  the Oracle "Stress scenario (illustrative)" panel: editable assumptions, four decisions, histogram, stability check, scenario Excel download
│   ├── liquidity_simulation.py  Release 2 illustrative Monte Carlo: Oracle's 12-month cash vs dated uses under triangular OCF; seeded; never a funding conclusion (tested)
│   ├── oracle_principal.py  Oracle's August 31, 2026 principal by instrument and date from the 10-K's tagged debt table; term-loan schedule from stated terms; commercial paper Unavailable; samples/oracle_principal.json built by tests/offline/build_oracle_principal.py (tested)
│   ├── oracle_revolver.py  exact saved-source revolver audit: dated commitment/advances, historical undrawn arithmetic, draw conditions and unresolved availability
│   ├── liquidity_pilot.py  frozen LLY/ORCL/VST company reviews, same-filing net debt, flow/debt ratios and formula-based Excel export; samples/liquidity_pilots.json is rebuilt by tests/offline/build_liquidity_pilot.py
│   ├── budget.py    daily spending ledger for Claude calls, prices, how API errors are charged (no Streamlit, tested)
│   ├── theme.py     color tokens, named by meaning (the one place colors are defined)
│   ├── ui.py        CSS built from theme.py, finding rows, metrics panel, skeleton loaders, progress strip
│   ├── charts.py    price chart (drawing only, no network)
│   ├── samples/     saved company reviews, their workbooks and manifests, and the archived AAPL + STRL example (profiles, price CSVs, manifest; built by tests/offline/build_sample.py)
│   ├── docs/pilot_cashflow_reconciliation.md  six checked source periods, capex definitions and independent TTM calculations
│   ├── docs/debt_liquidity_plan.md  debt and liquidity plan (planned work, tracked)
│   ├── docs/pilot_evidence_lly.md   Eli Lilly pilot evidence: filing values with sources, checks and open gaps
│   ├── docs/pilot_evidence_oracle.md  Oracle pilot evidence: filing values with sources, checks and open gaps
│   ├── docs/pilot_evidence_vistra.md  Vistra pilot evidence: filing values with sources, checks and open gaps
│   ├── docs/oracle_case_study.md   Oracle case study: what the checked filings establish about funding near-term obligations, with a five-minute app and Excel walkthrough
│   ├── requirements.txt
│   ├── README.md    public description: what it does, what it doesn't, known limits
│   ├── CLAUDE.md    these instructions, for Claude Code
│   ├── .streamlit/config.toml   widget theme (repeats the base colors in theme.py)
│   ├── tests/       tests and diagnostics (no Anthropic calls)
│   │   ├── test_*.py          unit tests of sec_data, analysis, market_data, budget, ui, xbrl, the saved sample (commands under "Running the tests")
│   │   ├── fixtures/          real SEC company facts for AAPL, STRL, JPM and the pilots LLY, ORCL, VST, trimmed to the tags xbrl.py reads; make_fixtures.py rebuilds them from data/raw/xbrl; VST_2026Q2_ixbrl.htm is a trimmed copy of Vistra's 10-Q inline XBRL (make_filing_fixture.py)
│   │   ├── check_risk_extraction.py   live EDGAR check of filing selection and sections, using the production functions
│   │   ├── chart_preview.py   price chart on synthetic prices
│   │   └── offline/           whole app on fake SEC/Yahoo/Anthropic responses; check_states.py drives failure scenarios, check_sample.py the saved sample (shots/ is gitignored)
│   ├── .venv/       local Python environment (gitignored)
│   ├── .gitattributes   keeps line endings LF on every machine, matching Streamlit Cloud
│   └── .gitignore
├── docs/            instructions and plans (private)
├── course/          VSB 2008 notes (private, never goes in app/)
└── data/
    ├── exports/     Excel research records the app produces
    └── raw/         downloaded data and filings
```

Repo: https://github.com/jackconnolly1000-ux/sec-filing-research-terminal

**Folder rules**
- Put every new file in the right subfolder. Don't scatter files elsewhere on my computer or leave them loose in the top folder.
- Only `app/` is a git repo, and it's public. Everything outside `app/` stays private because it's never committed.
- Never put course notes, class slides, assignments, group project work, or API keys inside `app/`.
- The API key lives in Streamlit Secrets, not in the code. Keep it that way.
- When you add or move something, update `README.md`.
- In claude.ai, the project files are copies. If the uploaded code might be older than what's in `app/`, say so.

**Running the tests** (from `app/`; Windows uses `.venv\Scripts\`, Mac/Linux `.venv/bin/`)

| | Windows (PowerShell) | Mac/Linux |
|---|---|---|
| Build the environment | `py -3.12 -m venv .venv; .venv\Scripts\python -m pip install -r requirements.txt` | `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt` |
| Unit tests | `.venv\Scripts\python -m unittest discover -s tests -p "test_*.py"` | `.venv/bin/python -m unittest discover -s tests -p "test_*.py"` |
| Browser test setup (once; Playwright isn't in requirements.txt because the live app doesn't need it) | `.venv\Scripts\python -m pip install playwright; .venv\Scripts\python -m playwright install chromium` | `.venv/bin/pip install playwright && .venv/bin/python -m playwright install chromium` |
| Saved sample: start the app | `$env:MOCK_NO_NETWORK='1'; .venv\Scripts\streamlit run tests/offline/run_offline.py --server.port 8601 -- app.py` | `MOCK_NO_NETWORK=1 .venv/bin/streamlit run tests/offline/run_offline.py --server.port 8601 -- app.py` |
| Saved sample: check (second terminal) | `.venv\Scripts\python tests/offline/check_sample.py 8601 tests/offline/shots/sample` | `.venv/bin/python tests/offline/check_sample.py 8601 tests/offline/shots/sample` |
| Failure states: start the app | `$env:MOCK_DELAY='2'; $env:MOCK_CUTOFF='STRL'; $env:MOCK_ONE_10K='FAST'; $env:MOCK_FAIL_ONCE='yahoo,8k'; .venv\Scripts\streamlit run tests/offline/run_offline.py --server.port 8601 -- app.py` | `MOCK_DELAY=2 MOCK_CUTOFF=STRL MOCK_ONE_10K=FAST MOCK_FAIL_ONCE=yahoo,8k .venv/bin/streamlit run tests/offline/run_offline.py --server.port 8601 -- app.py` |
| Failure states: check (second terminal) | `.venv\Scripts\python tests/offline/check_states.py 8601 tests/offline/shots/states` | `.venv/bin/python tests/offline/check_states.py 8601 tests/offline/shots/states` |

PowerShell's `$env:` settings last for that terminal session, so stop the app and open a fresh terminal before switching scenarios. The 9 original full-document checks (8 section/comparison checks and the Vistra reader check), plus the six-document cash-flow reconciliation, read cached filings from `C:\Users\jackc\Stock Project\data\raw\sec` (outside the repo) and skip on a machine without them.

## What the app does today

**Release 1 state (October 17, 2026 UTC; financial review dates unchanged):** steps 1–7 are merged in PRs #42–#47 (current base `635b962`). Step 8 completes on merge of the final reconciliation PR. The three frozen reviews have reconciled borrowing/lease presentation, ten core measures, checked annual-versus-latest history, two common chart questions, company-specific funding/repayment detail and individual Excel evidence exports. The combined workbook is an optional core summary. General filing research, existing catalysts and the archived AAPL/STRL example remain intact. The final acceptance suite has 412 tests; full-document checks require the separately saved public filings, while committed fixtures support offline reproduction. See `docs/release1_reconciliation.md` for checks and limits.

**Default page: Debt & Liquidity**
- Title "Debt & Liquidity Research Terminal" (page tab too). A segmented company selector, Eli Lilly (LLY), Oracle (ORCL), Vistra (VST), opens LLY by default; the selected review shows directly, with no Run analysis action and no enclosing expander (`company_review.render_app`)
- Each review is frozen and dated: LLY and VST balance sheets at Jun 30, 2026, ORCL at Aug 31, 2026; balance-sheet facts checked Oct 14, interpretation checked Oct 16 (Oracle re-checked Oct 17 against its August 31 principal calendar, which `funding_conclusions.py` now binds; one shared interpretation fingerprint gates all three workbooks). Opening one makes no SEC, Yahoo or Anthropic request and needs no secrets: `ANTHROPIC_API_KEY` and `SEC_CONTACT_EMAIL` are read only inside general filing research
- Shown per company: cash and equivalents (excluding restricted cash), baseline gross debt (borrowing, excluding leases), net debt, current ratio, TTM operating cash flow, capital spending, free cash flow, OCF/debt and FCF/debt, the borrowing breakdown, a dated funding conclusion, historical interest coverage (LLY 31.17x, ORCL 4.52x, VST 3.19x, each with its own denominator limits), selected obligations outside borrowing, unresolved items, and a "Calculations and filing evidence" disclosure. Oracle adds its August 31 principal calendar by instrument (`oracle_principal.py`; commercial paper Unavailable), May 31 maturity schedule, cash reconciliation, repayment funding and revolver audit; Vistra its repayment review and checked financing filings after June 30; Lilly its H1 cash review and May debt terms
- Two-date history preserves overlapping FY/TTM windows and older Vistra borrowing as Unavailable. Common charts answer what remained after capital spending and how checked cash/borrowing balances changed; VST compares cash only. The evidence disclosure includes annual history and lease input provenance.
- One primary download per company (`Lilly_Liquidity_2026-06-30.xlsx`, `Oracle_Liquidity_2026-08-31.xlsx`, `Vistra_Liquidity_2026-06-30.xlsx`) plus "Optional combined export" (original metric summary and sources, not the full reviews). Individual workbooks open with Funding conclusion and a contents/reading guide. Each workbook is the saved file in `samples/`, served only while its manifest's SHA-256 fingerprints match the saved sources; otherwise the button is replaced by "Unavailable". Workbook bytes are never rebuilt by the app
- States: a missing or unreadable `samples/liquidity_pilots.json` shows "Saved reviews unavailable"; a review edited out of shape shows "<ticker> review unavailable"; a selection from an older session falls back to LLY. The company selection survives a visit to general research (`persist_state="session"`)
- Detailed method, sources and limits: `docs/debt_liquidity_plan.md` and the per-topic files in `docs/` (pilot evidence, reconciliations, `funding_conclusions.md`, `review_clarity_audit.md`)

**Secondary page: General filing research — experimental**
- Reached by a tertiary button under the subtitle; "Debt and liquidity reviews" returns. The page is session state, not a widget, so results, ticker picks and the company selection survive switching
- The original tool, unchanged in behavior: ticker picker (`st.multiselect`, up to 5), primary **Run analysis**, progress strip and per-ticker tabs, results in `st.session_state`, "Download Excel" (Research_Record_<tickers>_<date>.xlsx). With either secret missing, Run analysis is disabled and a notice names the missing setting; without a contact email no SEC request is made and the 6-ticker fallback list is used. Owner passcode field in the sidebar only when `OWNER_PASSCODE` is set
- **Archived filing-research example:** "View archived example (AAPL, STRL · Oct 10, 2026)" loads `samples/` (analysis run Oct 10, 2026; prices through the Oct 9 close, retrieved Oct 11; SEC figures as filed by Oct 10) with no network calls
- **Evidence:** latest 10-K vs prior 10-K Item 1A (EDGAR's older filing pages are read when the prior 10-K isn't in the recent list), every 10-Q since that 10-K for risk-factor updates, MD&A from the latest periodic report, up to four 8-Ks from the last 180 days. Sections are found by their real headings; missing, failed, not applicable, "no material changes" and "incorporated by reference" are reported, never replaced with other text
- **Risk-factor comparison in code:** `compare.py` labels each paragraph NEW (no close match), CHANGED (edited, figures changed, rewritten, text removed, minor edit), UNCHANGED or REMOVED, using word-level similarity (thresholds 0.97 / 0.50 / 0.30). One-sentence risk titles are joined to the paragraph that follows. Claude gets only new, changed and removed paragraphs, with code-assigned IDs. A risk's change label comes from the paragraph it cites, never from the model. Risks only in management's discussion go under "Other risks from management's discussion (not compared to last year)"
- **Request budget:** measured with Anthropic's free token-counting endpoint and kept within 76,000 tokens (64,000 input + 12,000 output reserve); the comparison is sent first and cut only between paragraphs; omitted characters are reported
- **Spending guard:** `budget.Ledger`, one per server process (`st.cache_resource`), caps live Claude spend at $0.25 per America/New_York day. Before each call it reserves the worst case (measured input + 12,000 output at Sonnet 5's $2/$10 per million tokens); a reply settles at `response.usage`; a 4xx releases the hold; a timeout, connection error or 5xx settles at the worst case. A ticker that doesn't fit is "skipped", not failed. The account's monthly limit (400 "You have reached your specified…" or 429 `enforced_spend_limit_reached`) shows "The monthly AI budget for this demo is used up." Cache hits don't touch the ledger. The counter resets on restart. Owner passcode: generate with `python3 -c "import secrets; print(secrets.token_urlsafe(24))"`, put it in Streamlit Secrets and `.streamlit/secrets.toml` as `OWNER_PASSCODE`; owner runs aren't blocked but still count
- **Checks:** `stop_reason` and every required field are checked; only complete answers are cached. Excerpts are matched, fragments in order, in the cited source. A finding that cites a "no material changes" section is rejected. Figures in a finding are looked for in the cited source after normalizing formats; a miss is flagged, not rejected. Impact (High, Medium, Low, Not assessed) is a labeled AI assessment. Banned words and "new risk" claims are flagged on each finding
- **Market and SEC figures:** Yahoo price, market cap and forward P/E with source field and retrieval time ("Period not stated" where undocumented); SEC XBRL TTM revenue, gross margin, operating margin and free cash flow with period end and filings (`xbrl.py`). A missing tag is "Not reported in SEC data"
- **Financing filing review:** live results list candidate 8-K, 424B, FWP, S-3 and 10-K/A or 10-Q/A filings since the latest balance sheet, each Not checked unless it is one of the accession-specific Vistra or Oracle filings checked by hand (`reviewed_financing.py`)
- Each tab: company header, metrics panel, 5-year price chart, evidence list, show filter, findings rows ordered by impact, "What changed in the risk factors" with the unchanged list, other risks, 8-K events labeled with their EDGAR item. Excel: market data, findings, 8-K events, evidence and filing review sheets, numbers stored as numbers

These features render. That does not mean they're correct. The debt and liquidity figures were checked by hand against the cited filings (see the evidence files); AI-written findings and Yahoo numbers have not been verified, and an excerpt match verifies only the quoted words. Label claims as verified or unverified.

`course_analytics.py` does not exist. Course features have to be built from scratch, starting with the benchmark tests.

## Known problems (as of October 16, 2026)

In priority order. Delete a line once it's fixed.

1. **The debt and liquidity reviews are frozen.** They cover three companies at a latest checked balance-sheet date each (Jun 30 or Aug 31, 2026), with one prior annual observation for comparable history. Older Vistra borrowing is not checked, so its older net debt and flow/debt ratios remain Unavailable. Nothing refreshes them; a newer 10-Q isn't read until the review is rebuilt and checked by hand. Live analysis does not compute these metrics for other tickers.
2. **Lease and funding answers remain partly Unavailable.** Leases: Oracle's August 31, 2026 operating (34.621B) and finance (9.185B) lease liabilities are shown separately from borrowing, and its 288B of leases not yet commenced is shown as a commitment. Lilly's and Vistra's June 30, 2026 10-Q reviews establish no lease liability amounts, so June 30 amounts are Unavailable; the latest reported amounts are at Dec 31, 2025 (Lilly: 1,362M operating, no finance leases described; Vistra: 105M operating and 222M finance). No review has a complete lease or obligations extraction, and lease interest is not added to any coverage ratio. Funding: future funding coverage is Unavailable for all three. The decisive unknowns are the remaining principal calendar (Lilly has only the May 2026 issuance schedule, and a per-note calendar isn't supported by its saved filings, per `docs/lly_principal_calendar_check.md`; Oracle's note and term-loan principal is dated at Aug 31, but its commercial paper is not), drawable credit and draw conditions (Lilly's post-August facility renewal, Oracle's current revolver availability, Vistra's borrowing base), covenant headroom, the timing and overlap of acquisition, manufacturing, capital-call and uncommenced-lease payments, Vistra's Parent-accessible cash, and all-in financing cost. Each is stated in its review; none is estimated.
3. **Numbers conflict with no labels in general research.** For AAPL the SEC gross margin is 48.65% TTM to Jun 27, 2026 and the AI text says 50.1% with no period. Excel still lists Yahoo's margins next to the SEC ones.
4. **General research is slow.** 108 seconds for AAPL + STRL on Oct 10. Filings are cached per document for a day, so repeat runs are faster; first runs are not.
5. **The general research Excel export isn't a research record yet.** Still missing: a cover sheet, units in headers, wrapped text and set widths. (The three company workbooks already have About sheets, formulas and sources.)
6. **Risk factors incorporated by reference aren't read.** Some filers (JPM) put Item 1A in an annual-report exhibit, so it shows as missing.
7. **"No close match" is a text test.** A heavily rewritten paragraph can land there (MSFT's FY2026 "We may experience outages…"). The label says "no close match", not "new risk".
8. **8-K exhibits aren't read by the AI pipeline.** Only each 8-K's primary document is sent; the hand-checked Vistra and Oracle financing filings cite their exhibits separately.
10. **Section extraction is tested on seven filers** (AAPL, FAST, STRL, MSFT, WMT, JNJ, JPM) plus synthetic cases. Other formats show "Section not found", not wrong text.

## Excel export standard

**Purpose: a research record.** Someone opening it later should see what the app found, when, and where each number came from.

- Rename it "Research Record." It is not a model, so don't call it "Institutional Model."
- A cover sheet with tickers, date and time run, app version, data sources, and a line saying it's not investment advice
- Numbers stored as numbers with proper formats ($B, %, x). Never as text.
- Every metric labeled with its period and source (for example, "TTM, yfinance" or "Q3 2026, 10-Q filed 2026-07-31")
- Clean data layout, following the course rule: one row per record, one header per column, one data type per field, no merged cells
- Catalysts and risks sheets: wrapped text, set column widths, styled and frozen headers, and the filing type and date next to each excerpt
- Units in every column header

## Quality standard

Full rules: `C:\Users\jackc\Stock Project\docs\Quality_Standard.md`. Check every change against it before calling it done.
1. Plain words: no hype words, no dramatic verbs without the number, no emoji, exclamation marks or ALL CAPS, sentence case, no investment language.
2. Every number shows its period and source. Unknowns are stated ("Period not stated", "Not verified"), never guessed.
3. Color and badges only when they mean something; one primary action; designed loading, empty and error states; checked at 390 px.
4. AI findings cite their filing and show the excerpt check; impact follows the written definition; code enforces what it can.
5. Excel: Arial 10, $ millions, formulas not pasted values, no merged cells (use Center Across Selection), sources on a Data sheet, an About sheet. Code: comments explain why, no dead code, a README that states limits; commit messages have a short first line (under about 60 characters) saying what changed, with a body only when the reason isn't obvious.

## Chat or Claude Code: tell me which

I use two tools on this project, and both read these same instructions. I often won't know which one a task belongs in, so **at the start of any answer where it matters, tell me in one line: "Do this in chat" or "Do this in Claude Code," and why.**

| Do it in chat (claude.ai project) | Do it in Claude Code (VS Code, `app/` folder) |
|---|---|
| Planning what to build next | Changing any code |
| Learning a concept or getting quizzed | Fixing a bug |
| Design ideas and feedback on screenshots | Running the app and testing buttons |
| Course questions and how a method works | Anything touching more than one file |
| Writing resume or interview wording | Committing and pushing to GitHub |
| Reviewing a diff I paste in | Reading the whole current codebase |

Rule of thumb: thinking and learning go in chat. Touching files goes in Claude Code.

**How to pass work between them**
- **Chat to Claude Code:** when a plan in chat is ready to build, end with a ready-to-paste prompt for Claude Code in a code block. It should start with "Read CLAUDE.md," say what to change, and name anything that needs my OK (see the next rule).
- **When Claude Code waits for my OK:** only before paid runs, deleting things, or changes outside a branch. Otherwise it proceeds on a branch and reports what it did.
- **Merging (standing rule since Oct 17, 2026):** open each PR, then merge it into `main` once its tests and checks pass, without asking. After every merge, check the live site (each company loads with no error and offers its downloads) and fix anything broken right away.
- **Claude Code to chat:** after Claude Code finishes something, it should end with a one-line "Take this to chat" note: what changed, and which file and function. The question to ask chat so I learn it goes in `C:\Users\jackc\Stock Project\docs\Learning_Questions.md` (date, question, file and function), appended as a new entry, not in the reply.
- **Keep both in sync:** when the known-problems list changes, Claude Code updates `app/CLAUDE.md` and `docs/Project_Instructions.md`, then reminds me to re-paste the instructions into the claude.ai project.
- In chat, if I ask for code changes, don't just write the code. Give me the Claude Code prompt instead, plus the explanation. Exception: a short snippet to show a concept is fine.

## How to work with me

**Teaching**
- With every code change, explain what it does, why it's built that way, and how it connects to the rest of the app.
- Use the real technical terms and define each one the first time it comes up.
- Give full functions or files I can paste in, plus the explanation. Both, every time.
- When it fits, name one question an interviewer could ask about that piece.
- Plan first. Wait for my OK only where the handoff rule says (paid runs, deleting things, changes outside a branch); otherwise proceed on a branch, merge when checks pass, check the live site and report.

**Testing**
- Before saying a button or feature works, run the app and test it, then report exactly what happened. Offline and saved-sample runs are free; real-key runs need my OK.
- For course methods, test the known answers first (benchmarks are in the course file).

**Rules**
- Be blunt about quality. If something looks amateur or isn't practical, say so.
- Don't invent user counts, metrics, or features. Describe only what's confirmed built and working.
- This is a research tool. Don't present its output as investment advice or recommendations.
- Every package in `requirements.txt` is pinned with `==`. To change a version: bump one package, rebuild a fresh `.venv` from `requirements.txt`, run the browser test and a real-key run, then commit.
- Don't describe course topics marked Upcoming as things I know.
- Lead with the short answer, then the detail.

## Order of work

**Release 1: Debt & Liquidity as the product.** Agreed Oct 16, 2026. One step per pull request; each keeps the checked financial models, numbers, source gates and workbook bytes unchanged unless the step says otherwise:

1. Reconcile the roadmap with `main` (CLAUDE.md, README, `docs/debt_liquidity_plan.md`).
2. Make Debt & Liquidity the primary experience: default company selector, no Run analysis action or expander, saved reviews without secrets or network, general research as secondary access, AAPL/STRL labeled as the archived example.
3. Borrowing and lease presentation.
4. Ratio reconciliation.
5. Two-date comparable history.
6. Two core charts.
7. Individual Excel parity.
8. Final source and app reconciliation.

Steps 1–2 are merged as PR #42 (`7e984f1`); step 3 is merged as PR #43 (`0f7df28`, 386 unit tests). The app and individual workbooks separate borrowing components, dated operating/finance lease liabilities and uncommenced leases. June LLY/VST lease balances remain Unavailable; December balances retain their own dates. See `docs/borrowing_lease_presentation.md`.

Step 4 is merged as PR #44 (`f0f246f`): current ratio, net debt, OCF/debt, FCF/debt and historical interest coverage reconcile to the checked inputs. Oracle and Vistra now include the core ratio table in their individual workbooks, matching Lilly and the app. `ratio_review.py` checks exact periods, units, filing versions, derived values and input provenance. No financial input, funding conclusion, catalyst or interest denominator changes. See `docs/ratio_reconciliation.md`. Step 5 merged as PR #45 (`5fb46ce`) with two-date history; annual and later TTM flows are labeled as overlapping twelve-month windows. Older Vistra debt and dependent ratios stay Unavailable. Step 6 merged as PR #46 (`f967a22`) with two source-backed chart questions; Vistra compares cash only because older borrowing is unsupported. Step 7 merged as PR #47 (`635b962`) with contents/reading guides, scoped annual-versus-latest history bases and explicit combined-summary labeling. Step 8 completes on merge of the final reconciliation PR: read-only release audit, full source metadata, missing-file guard, final output checks and roadmap reconciliation. No new metrics, companies or estimated funding capacity. See `docs/release1_reconciliation.md`. Release 1 is then complete within its three-company frozen-review scope; the remaining evidence gaps stay explicit.

**Outside the Release 1 order:** refresh automation (known problem 1), new financial metrics, additional companies, the remaining experimental general-research issues, and course features. Steps 3–8 present and reconcile the existing evidence; they don't resolve the Unavailable items in problem 2 unless a step says so.

**Deferred** (the plan's later phases): full financing terms and covenants, recalculating debt and cash from later financing events, complete obligations analysis, industry peers, stress scenarios, category assessments. Never: grades, default probabilities or recommendations.

**Release 2: liquidity stress simulation (chosen Oct 17, 2026; planned, not built).** An Oracle-first, illustrative Monte Carlo scenario. It asks how often checked August 31 cash plus uncertain operating cash flow falls short of the obligations the filings date over the next twelve months, comparing two decisions (capex level; the revolver as a hypothetical). It applies VSB 2008 simulation and never changes a funding conclusion. Built Oct 17: model and tests (`liquidity_simulation.py`), the Oracle app panel "Stress scenario (illustrative)" with editable assumptions and a histogram (`simulation_view.py`), a separate scenario Excel download, and `docs/liquidity_simulation.md` (method, results, interview walkthrough). Possible addition: OCF–prepayment correlation. Full plan and open questions: `docs/release2_plan.md`.

**Course features** (simulation is the core of Release 2), in this order: Monte Carlo simulation first, then LP allocation, then CAPM regression after the Nov 11 and 13 classes.
