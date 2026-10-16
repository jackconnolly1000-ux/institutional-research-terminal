# SEC Filing Research Terminal: project instructions

## What this is

I'm Jack, a sophomore finance student at Villanova School of Business. I'm building the SEC Filing Research Terminal, a Streamlit web app that speeds up stock research by putting market data, SEC filings, and AI summaries in one dashboard. It's live at https://sec-filing-research-terminal.streamlit.app/.

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
│   ├── company_review.py  the default page: company selector, saved review (cash-flow chart, borrowing breakdown, selected obligations, unresolved questions) and checked workbook downloads
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

**On `main` and live (checked Oct 16, 2026, merge `9efb069`, PR #41):** PRs #1–#5 (Oct 11) built the AI filing-research pipeline, spending guard and AAPL + STRL sample. PRs #6–#41 (Oct 11–16) built the debt and liquidity work: SEC XBRL figures, the filing-level inline XBRL reader, checked cash, current ratio, baseline gross debt and cash flows for Eli Lilly, Oracle and Vistra, saved company reviews with dated funding conclusions, interest coverage, Oracle maturities and revolver audit, Vistra financing filings, and one checked Excel workbook per company. 370 unit tests passed on `main` (2 skip on a machine without the cached filings).

**Release 1 steps 1–2 (branch `debt-liquidity-primary`, draft PR, not merged as of Oct 16, 2026):** the roadmap below is reconciled with `main`, and Debt & Liquidity is the default page. 379 unit tests pass, 9 of them new page tests (`tests/test_app_pages.py`).

**Default page: Debt & Liquidity**
- Title "Debt & Liquidity Research Terminal" (page tab too). A segmented company selector, Eli Lilly (LLY), Oracle (ORCL), Vistra (VST), opens LLY by default; the selected review shows directly, with no Run analysis action and no enclosing expander (`company_review.render_app`)
- Each review is frozen and dated: LLY and VST balance sheets at Jun 30, 2026, ORCL at Aug 31, 2026; balance-sheet facts checked Oct 14, interpretation checked Oct 16. Opening one makes no SEC, Yahoo or Anthropic request and needs no secrets: `ANTHROPIC_API_KEY` and `SEC_CONTACT_EMAIL` are read only inside general filing research
- Shown per company: cash and equivalents (excluding restricted cash), baseline gross debt (borrowing, excluding leases), net debt, current ratio, TTM operating cash flow, capital spending, free cash flow, OCF/debt and FCF/debt, the borrowing breakdown, a dated funding conclusion, historical interest coverage (LLY 31.17x, ORCL 4.52x, VST 3.19x, each with its own denominator limits), selected obligations outside borrowing, unresolved items, and a "Calculations and filing evidence" disclosure. Oracle adds its May 31 maturity schedule, cash reconciliation, repayment funding and revolver audit; Vistra its repayment review and checked financing filings after June 30; Lilly its H1 cash review and May debt terms
- One download per company (`Lilly_Liquidity_2026-06-30.xlsx`, `Oracle_Liquidity_2026-08-31.xlsx`, `Vistra_Liquidity_2026-06-30.xlsx`) plus "Optional combined export". Each workbook is the saved file in `samples/`, served only while its manifest's SHA-256 fingerprints match the saved sources; otherwise the button is replaced by "Unavailable". Workbook bytes are never rebuilt by the app
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

1. **The debt and liquidity reviews are frozen.** They cover three companies at one balance-sheet date each (Jun 30 or Aug 31, 2026). Nothing refreshes them; a newer 10-Q isn't read until the review is rebuilt and checked by hand. Live analysis does not compute these metrics for other tickers.
2. **Key debt answers remain Unavailable.** Current drawable credit and covenant headroom, updated principal schedules after the latest 10-K (Oracle's is May 31; Lilly's June principal), June 30 lease liabilities for LLY and VST, several commitment timings and overlaps, and all-in financing cost. Each is stated in its review; none is estimated.
3. **Numbers conflict with no labels in general research.** For AAPL the SEC gross margin is 48.65% TTM to Jun 27, 2026 and the AI text says 50.1% with no period. Excel still lists Yahoo's margins next to the SEC ones.
4. **General research is slow.** 108 seconds for AAPL + STRL on Oct 10. Filings are cached per document for a day, so repeat runs are faster; first runs are not.
5. **The general research Excel export isn't a research record yet.** Still missing: a cover sheet, units in headers, wrapped text and set widths. (The three company workbooks already have About sheets, formulas and sources.)
6. **Risk factors incorporated by reference aren't read.** Some filers (JPM) put Item 1A in an annual-report exhibit, so it shows as missing.
7. **"No close match" is a text test.** A heavily rewritten paragraph can land there (MSFT's FY2026 "We may experience outages…"). The label says "no close match", not "new risk".
8. **8-K exhibits aren't read by the AI pipeline.** Only each 8-K's primary document is sent; the hand-checked Vistra and Oracle financing filings cite their exhibits separately.
9. **Section extraction is tested on seven filers** (AAPL, FAST, STRL, MSFT, WMT, JNJ, JPM) plus synthetic cases. Other formats show "Section not found", not wrong text.

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
- **When Claude Code waits for my OK:** only before paid runs, merges to `main`, deleting things, or changes outside a branch. Otherwise it proceeds on a branch and reports what it did.
- **Claude Code to chat:** after Claude Code finishes something, it should end with a one-line "Take this to chat" note: what changed, and which file and function. The question to ask chat so I learn it goes in `C:\Users\jackc\Stock Project\docs\Learning_Questions.md` (date, question, file and function), appended as a new entry, not in the reply.
- **Keep both in sync:** when the known-problems list changes, Claude Code updates `app/CLAUDE.md` and `docs/Project_Instructions.md`, then reminds me to re-paste the instructions into the claude.ai project.
- In chat, if I ask for code changes, don't just write the code. Give me the Claude Code prompt instead, plus the explanation. Exception: a short snippet to show a concept is fine.

## How to work with me

**Teaching**
- With every code change, explain what it does, why it's built that way, and how it connects to the rest of the app.
- Use the real technical terms and define each one the first time it comes up.
- Give full functions or files I can paste in, plus the explanation. Both, every time.
- When it fits, name one question an interviewer could ask about that piece.
- Plan first. Wait for my OK only where the handoff rule says (paid runs, merges to `main`, deleting things, changes outside a branch); otherwise proceed on a branch and report.

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

**Release 1: Debt & Liquidity as the product.** One step per pull request; each keeps the checked financial models, numbers, source gates and workbook bytes unchanged unless the step says otherwise.

1. Reconcile the roadmap with `main` (CLAUDE.md, README, `docs/debt_liquidity_plan.md`). Done on branch `debt-liquidity-primary`, draft PR, Oct 16, 2026.
2. Make Debt & Liquidity the primary experience: default company selector, no Run analysis action or expander, saved reviews without secrets or network, general research as secondary access, AAPL/STRL labeled as the archived example. Done on the same branch.
3. Later Release 1 steps: not yet written down in this repository. Add them here from the agreed plan before starting step 3.

**Remaining, not scheduled:** known problems 1–2 above (refreshing a review for a newer 10-Q, and the Unavailable items) and 3–9 for general research, in that priority.

**Left out of steps 1–2 on purpose:** comparable company history (plan step 7), new financial metrics, refresh automation and additional companies. Each needs its own scoped step.

**Deferred** (the plan's later phases): full financing terms and covenants, recalculating debt and cash from later financing events, complete obligations analysis, industry peers, stress scenarios, category assessments. Never: grades, default probabilities or recommendations.

**Course features**, in this order: Monte Carlo simulation first, then LP allocation, then CAPM regression after the Nov 11 and 13 classes.
