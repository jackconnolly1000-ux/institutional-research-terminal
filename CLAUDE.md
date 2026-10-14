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
│   ├── filing_xbrl.py   one fact from a filing's own inline XBRL (extension tags companyfacts lacks), with context, unit and checks (no Streamlit, tested)
│   ├── filing_review.py  display the subsequent-filing index and its review status
│   ├── budget.py    daily spending ledger for Claude calls, prices, how API errors are charged (no Streamlit, tested)
│   ├── theme.py     color tokens, named by meaning (the one place colors are defined)
│   ├── ui.py        CSS built from theme.py, finding rows, metrics panel, skeleton loaders, progress strip
│   ├── charts.py    price chart (drawing only, no network)
│   ├── samples/     the saved AAPL + STRL sample (profiles, price CSVs, manifest), built by tests/offline/build_sample.py
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

PowerShell's `$env:` settings last for that terminal session, so stop the app and open a fresh terminal before switching scenarios. The 8 real-filing tests read cached filings from `C:\Users\jackc\Stock Project\data\raw\sec` (outside the repo) and skip on a machine without them.

## What the app does today

**On `main` and live (Oct 11, 2026):** PR #1, SEC evidence pipeline, code risk comparison and new layout (squash-merged as `d5206ee`); PR #2, spending guard and saved sample (merge commit `f91af8a`); PR #3, icon font, Run analysis width and ticker-count copy (`b60a8a3`); PR #4, `streamlit==1.65.0` pin and the startup `[versions]` log line (`2e1a384`); PR #5, docs (`855ad3d`). Tested with 96 unit tests (8 of them on real filings cached on this laptop), offline browser scenarios on Streamlit 1.65.0, live EDGAR checks on seven companies, and real-key runs: AAPL + STRL on Oct 10 at 1:50 PM ET (131 s, $0.30, under the earlier 80,000-token budget, both answers complete) and STRL alone on Oct 11 with the spending guard (69 s, 34,325 input and 5,684 output tokens, about $0.125 by the app's prices). Limits found in testing are listed in README.md under "Known limits".

- Home screen: title "SEC Filing Research Terminal", subtitle "SEC filings, market data and AI summaries for public companies. A research tool, not investment advice.", one ticker picker (`st.multiselect`, up to 5), one primary **Run analysis** button, a muted line "Live analysis is limited to about one ticker a day. The saved sample is always available.", one outlined **View saved sample** button. Owner passcode field in the sidebar only when `OWNER_PASSCODE` is set
- While it runs: a progress strip (queued, working, done, partial, failed, skipped) and a tab per ticker with a skeleton loader and step label
- Results are saved in `st.session_state`; a summary line and the Excel download sit at the top
- **Evidence:** latest 10-K vs prior 10-K Item 1A (EDGAR's older filing pages are read when the prior 10-K isn't in the recent list), every 10-Q since that 10-K for risk-factor updates, MD&A from the latest periodic report, up to four 8-Ks from the last 180 days. Sections are found by their real headings; missing, failed, not applicable, "no material changes" and "incorporated by reference" are reported, never replaced with other text
- **Risk-factor comparison in code:** `compare.py` splits both 10-K sections into paragraphs and labels each one NEW (no close match), CHANGED (edited, figures changed, rewritten, text removed, minor edit), UNCHANGED or REMOVED, using word-level similarity (thresholds 0.97 / 0.50 / 0.30, checked on AAPL, FAST, STRL, MSFT, then WMT and JNJ held out). Before comparing, a one-sentence risk title is joined to the paragraph that follows it. Claude gets only new, changed and removed paragraphs, with code-assigned IDs; minor edits go as one-line diffs. A risk's change label comes from the paragraph it cites, never from the model. Unchanged paragraphs are listed by code under "Unchanged since the prior 10-K". Risks that appear only in management's discussion go in a separate group, "Other risks from management's discussion (not compared to last year)"
- **Request budget:** the whole request is measured with Anthropic's free token-counting endpoint and kept within 76,000 tokens (64,000 input + 12,000 output reserve; real answers used 4,867 to 6,765). The comparison is sent first and cut only between paragraphs; omitted characters are reported
- **Spending guard:** `budget.Ledger`, one per server process (`st.cache_resource`), caps live Claude spend at $0.25 per America/New_York day. Before each call it reserves the worst case (measured input + 12,000 output at Sonnet 5's $2/$10 per million tokens); a reply settles at `response.usage`; a 4xx releases the hold; a timeout, connection error or 5xx settles at the worst case. A ticker that doesn't fit is "skipped", not failed. The account's monthly limit (400 "You have reached your specified…" or 429 `enforced_spend_limit_reached`) shows "The monthly AI budget for this demo is used up." Cache hits don't touch the ledger. The counter resets on restart. Owner passcode: generate with `python3 -c "import secrets; print(secrets.token_urlsafe(24))"`, put it in Streamlit Secrets and `.streamlit/secrets.toml` as `OWNER_PASSCODE`; owner runs aren't blocked but still count
- **Saved sample:** `samples/` holds the Oct 10, 2026 AAPL + STRL run (evidence identical to the run's prompts), market data from that run's export, and price history through the Oct 9 close (retrieved Oct 11). "View saved sample" renders the same tabs and Excel with no network calls
- **Checks:** `stop_reason` and every required field are checked; sections are complete, empty, partial, missing, invalid, no input, or failed, each with its own message; only complete answers are cached. Excerpts are matched, fragments in order, in the cited source (for comparison findings, the 10-K itself). A finding that cites a "no material changes" section is rejected. Every figure in a finding is looked for in the cited source after normalizing formats ($14.7M = 14.7 million = $14,700 thousand; 15% = 15.0%); a miss is flagged on the card and in Excel, not rejected, since some figures are fair calculations. Impact (High, Medium, Low, Not assessed) is a labeled AI assessment. Banned words from the quality standard, and "new risk" claims, are flagged on each finding, not deleted
- **Market data:** numbers with unit, source field and retrieval time; "Period not stated" where Yahoo doesn't document one. Failures are shown and retried, never cached
- **SEC figures (Oct 12):** `xbrl.py` reads data.sec.gov company facts (cached per CIK for a day, trimmed to the tags it reads, failures never cached) and computes TTM revenue (RevenueFromContractWithCustomerExcludingAssessedTax, then Revenues; the tag used is recorded), gross margin, operating margin and free cash flow (operating cash flow minus capex). TTM = latest fiscal year + current year to date - prior year to date, or the fiscal year when the latest periodic filing is a 10-K; a period reported more than once uses the most recently filed value. A missing tag is "Not reported in SEC data", with no fallback. Each figure carries its period end and filings (form, period, filed, accession). Tested on real fixtures: AAPL gross margin TTM to Jun 27, 2026 = 48.65%, gross profit TTM to Mar 28, 2026 = $216,071M, STRL (December year, and a restated Q1 2022), JPM (no tags)
- Each tab (Phase 2 layout): company header; one metrics panel with two groups, "Price and valuation" (Yahoo: price, market cap, forward P/E) and "From SEC filings · TTM to <date>" (revenue, gross margin, operating margin, free cash flow, each listing its filings, one per line), labels, values and period lines aligned on one grid, the source and retrieval time stated once at the panel's foot; 5-year price chart; evidence list; a show filter (All, Catalysts, Risk factor changes, Other risks); findings as compact expandable rows ordered High, Medium, Low, Not assessed, with one plain-text line above each headline (impact, change label, "Figures to check"), no pills or badges anywhere, and "Potential implication", detail, impact basis, figures and the filing excerpt each under its own small heading; "What changed in the risk factors" with the unchanged list below it; "Other risks from management's discussion (not compared to last year)"; 8-K events dated from EDGAR, each labeled with its 8-K item from EDGAR (for example "Item 5.02 Director or officer change") instead of Claude's category. Questions for management and the Form 4 count were removed (Oct 10): the questions added text without evidence, and a filing count with no buy or sell direction can read as insider selling. Excel: market data (Yahoo and SEC rows, SEC rows with a Filings used column), findings, 8-K events and evidence sheets, numbers stored as numbers (the research-record layout is a later step)

These features render. That does not mean they're correct. AI-written findings and Yahoo numbers have not been verified; an excerpt match verifies only the quoted words. Label claims as verified or unverified.

`course_analytics.py` does not exist. Course features have to be built from scratch, starting with the benchmark tests.

## Debt and liquidity project (planned)

**Planned, not built (Oct 14, 2026).** Full plan: [docs/debt_liquidity_plan.md](docs/debt_liquidity_plan.md), covering the goal, scope, definitions, source rules, pilot companies (Eli Lilly, Oracle, Vistra), delivery sequence and acceptance criteria. Goal: show what a nonfinancial company owes, what cash and cash generation support it, what changed, and the SEC evidence for each conclusion.

- **Exists today:** TTM free cash flow in `xbrl.py` (operating cash flow minus purchases of PP&E). It's implemented and unit-tested on fixtures, **but not yet validated against the three pilot companies**. Since Oct 14: `xbrl.cash_and_equivalents` returns cash and cash equivalents at the latest 10-K/10-Q balance-sheet date from that filing's own USD instant fact, with its source metadata, or Unavailable; tested on the three pilots. `xbrl.current_ratio` returns current assets and current liabilities from that same filing and date (an amendment counts only if it covers both, or repeats the unchanged one) and their ratio, which has no tag; a zero or negative denominator gets an explanation, not a ratio. Pilots: LLY 1.35, ORCL 1.17, VST 0.97. `xbrl.baseline_gross_debt` adds a company's verified borrowing components (LLY: 54,908M at Jun 30, 2026; ORCL: 125,337M at Aug 31, 2026; VST: 19,895M at Jun 30, 2026 only when the checked filing document is supplied by accession), checks one filing's components against its reported total when present, and returns Unavailable for unchecked presentations or missing extension documents. The app does not fetch a document for this calculation or show these figures yet.
- **Filing review index:** live results list candidate 8-K, 424B, FWP, S-3 and 10-K/A or 10-Q/A filings dated from the latest balance sheet through the run date, using EDGAR's submissions index and relevant older pages. Each entry links to its EDGAR filing page and says Not checked because contents and exhibits have not been read by this feature. An incomplete index says so. The Excel Filing review sheet carries the same status; the frozen saved sample has no index. This does not yet implement the financing notice.
- **Planned:** cash (cash and cash equivalents excluding restricted cash, "Unavailable" when the fact can't be established), baseline gross debt, separate leases, net debt, current ratio, OCF/debt, FCF/debt, operating-income interest coverage, findings, two charts, Excel evidence export, reconciliation.
- **Open:** debt, interest and cash tag mappings are decided from the pilot filings, not guessed.

## Known problems (as of October 11, 2026)

In priority order. Delete a line once it's fixed.

1. **Numbers conflict with no labels.** For AAPL the gross margin card says 48.65% and the AI text says 50.1%. Every number must show its period (TTM, quarter, fiscal year) and source. Partly done: Yahoo values name their source field and say "Period not stated"; since Oct 12 the header's revenue, margins and free cash flow come from SEC XBRL with a TTM period and filings (AAPL gross margin 48.65% TTM to Jun 27, 2026). Still open: AI text figures (the 50.1%) carry no period label, and Excel still lists Yahoo's margins next to the SEC ones.
2. **Slow.** 108 seconds for AAPL + STRL with the Oct 10 changes (84.7 before; inputs and answers are now larger). Progress feedback is done; speed isn't. Filings are now cached per document for a day, so repeat runs are faster; first runs are not.
3. **The Excel export isn't a research record yet.** See the standard below. Numbers are now stored as numbers with period and source columns, findings carry their filing, and an Evidence sheet lists sources. The download is named Research_Record_<tickers>_<date>.xlsx. Still missing: a cover sheet, units in headers, wrapped text and set widths.
4. **Risk factors incorporated by reference aren't read.** Some filers (JPM) put Item 1A in an annual-report exhibit; the 10-K section is a pointer, so it shows as missing and there is no comparison. Reading the exhibit would fix it.
5. **"No close match" is a text test.** Joining one-sentence titles to their body text fixed STRL's contract-termination title. A heavily rewritten paragraph can land there (MSFT's FY2026 "We may experience outages…" rewrites last year's "We may have excessive outages…"). The closest prior paragraph is sent as context when word overlap is at least 0.20, and the label says "no close match", not "new risk".
6. **8-K exhibits aren't read.** Only each 8-K's primary document is sent; press releases usually sit in exhibit EX-99.1.
7. **Section extraction is tested on seven filers** (AAPL, FAST, STRL, MSFT, WMT, JNJ, JPM) plus synthetic cases. Other formats may fail; they show "Section not found", not wrong text.

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

1. Label every number with period and source (problem 1)
2. Speed: caching and progress (problem 2)
3. Rebuild the Excel export as a research record (problem 3)
4. Phase 2 interface (findings rows, filter, phone layout check), then the Excel research record (problem 3)
5. Course features: Monte Carlo simulation first, then LP allocation, then CAPM regression after the Nov 11 and 13 classes
