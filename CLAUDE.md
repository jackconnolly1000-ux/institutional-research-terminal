# SEC Filing Research Terminal: project instructions

## What this is

I'm Jack, a sophomore finance student at Villanova School of Business. I'm building the SEC Filing Research Terminal, a Streamlit web app that speeds up stock research by putting market data, SEC filings, and AI summaries in one dashboard. It's live at https://jack-research-terminal.streamlit.app/.

Stack: Python, Streamlit, Plotly, yfinance, BeautifulSoup, and the Anthropic API (Claude). I work in VS Code with Claude Code, and in Google Colab.

My role is product manager and system architect. I decide what the product does, write the business logic and prompts, integrate AI-generated code, fix API connections, and refine the interface.

## The goal

1. **A resume project that shows real skills.** I want to build those skills and be able to explain every part of this app to an employer: the code, the data sources, the analytics, and how the pieces connect. A smaller feature I understand is worth more than a bigger one I can't explain.
2. **Apply what I learn in VSB 2008 Business Analytics.** The course file in this project lists what I've covered and what's upcoming. Use it when suggesting features.

## Where things live

Everything for this project is in one folder on my Mac: `~/Stock Project`.

```
Stock Project/
├── README.md        map of the folder
├── app/             the code (GitHub repo, PUBLIC, deploys to Streamlit)
│   ├── app.py       downloads, caching, the Claude call, page layout (runs Streamlit on import)
│   ├── sec_data.py  which SEC filings to use, section boundaries, paragraphs (no Streamlit, tested)
│   ├── compare.py   paragraph-level comparison of the current and prior 10-K risk factors (tested)
│   ├── analysis.py  evidence blocks, token budget, prompt and schema, response checks, excerpt matching (tested)
│   ├── market_data.py  Yahoo values as numbers with unit, period, source, retrieval time (tested)
│   ├── theme.py     color tokens, named by meaning (the one place colors are defined)
│   ├── ui.py        CSS built from theme.py, finding rows, metrics panel, skeleton loaders, progress strip
│   ├── charts.py    price chart (drawing only, no network)
│   ├── requirements.txt
│   ├── README.md    public description: what it does, what it doesn't, known limits
│   ├── CLAUDE.md    these instructions, for Claude Code
│   ├── .streamlit/config.toml   widget theme (repeats the base colors in theme.py)
│   ├── tests/       tests and diagnostics (no Anthropic calls)
│   │   ├── test_*.py          unit tests of sec_data, analysis, market_data: .venv/bin/python -m unittest discover -s tests -p "test_*.py"
│   │   ├── check_risk_extraction.py   live EDGAR check of filing selection and sections, using the production functions
│   │   ├── chart_preview.py   price chart on synthetic prices
│   │   └── offline/           whole app on fake SEC/Yahoo/Anthropic responses; check_states.py drives failure scenarios (shots/ is gitignored)
│   ├── .venv/       local Python environment (gitignored)
│   └── .gitignore
├── docs/            instructions and plans (private)
├── course/          VSB 2008 notes (private, never goes in app/)
└── data/
    ├── exports/     Excel research records the app produces
    └── raw/         downloaded data and filings
```

Repo: https://github.com/jackconnolly1000-ux/institutional-research-terminal

**Folder rules**
- Put every new file in the right subfolder. Don't scatter files elsewhere on my computer or leave them loose in the top folder.
- Only `app/` is a git repo, and it's public. Everything outside `app/` stays private because it's never committed.
- Never put course notes, class slides, assignments, group project work, or API keys inside `app/`.
- The API key lives in Streamlit Secrets, not in the code. Keep it that way.
- When you add or move something, update `README.md`.
- In claude.ai, the project files are copies. If the uploaded code might be older than what's in `app/`, say so.

## What the app does today

Layout from Oct 10, 2026 on `main` and the live site. **Branch `phase-1-evidence`** (not merged or deployed) changes what the analysis is built on. Tested with 77 unit tests (8 of them on real filings cached on this Mac), offline browser scenarios, live EDGAR checks on seven companies, and real-key runs of AAPL + STRL; the latest, Oct 10 at 1:50 PM ET with the code comparison and the 80,000-token budget, took 131 s, cost $0.30, sent all input, and both answers were complete. Limits found in testing are listed in README.md under "Known limits".

- Home screen: title "SEC Filing Research Terminal", subtitle ("A research tool, not investment advice"), one ticker picker (`st.multiselect`, up to 5), one primary **Run analysis** button, two outlined example buttons
- While it runs: a progress strip (queued, working, done, partial, failed) and a tab per ticker with a skeleton loader and step label
- Results are saved in `st.session_state`; a summary line and the Excel download sit at the top
- **Evidence (branch):** latest 10-K vs prior 10-K Item 1A (EDGAR's older filing pages are read when the prior 10-K isn't in the recent list), every 10-Q since that 10-K for risk-factor updates, MD&A from the latest periodic report, up to four 8-Ks from the last 180 days. Sections are found by their real headings; missing, failed, not applicable, "no material changes" and "incorporated by reference" are reported, never replaced with other text
- **Risk-factor comparison in code (branch):** `compare.py` splits both 10-K sections into paragraphs and labels each one NEW (no close match), CHANGED (edited, figures changed, rewritten, text removed, minor edit), UNCHANGED or REMOVED, using word-level similarity (thresholds 0.97 / 0.50 / 0.30, checked on AAPL, FAST, STRL, MSFT, then WMT and JNJ held out). Before comparing, a one-sentence risk title is joined to the paragraph that follows it. Claude gets only new, changed and removed paragraphs, with code-assigned IDs; minor edits go as one-line diffs. A risk's change label comes from the paragraph it cites, never from the model. Unchanged paragraphs are listed by code under "Unchanged since the prior 10-K". Risks that appear only in management's discussion go in a separate group, "Other risks from management's discussion (not compared to last year)"
- **Request budget (branch):** the whole request is measured with Anthropic's free token-counting endpoint and kept within 80,000 tokens (64,000 input + 16,000 output reserve). The comparison is sent first and cut only between paragraphs; omitted characters are reported
- **Checks (branch):** `stop_reason` and every required field are checked; sections are complete, empty, partial, missing, invalid, no input, or failed, each with its own message; only complete answers are cached. Excerpts are matched, fragments in order, in the cited source (for comparison findings, the 10-K itself). A finding that cites a "no material changes" section is rejected. Every figure in a finding is looked for in the cited source after normalizing formats ($14.7M = 14.7 million = $14,700 thousand; 15% = 15.0%); a miss is flagged on the card and in Excel, not rejected, since some figures are fair calculations. Impact (High, Medium, Low, Not assessed) is a labeled AI assessment. Banned words from the quality standard, and "new risk" claims, are flagged on each finding, not deleted
- **Market data (branch):** numbers with unit, source field and retrieval time; "Period not stated" where Yahoo doesn't document one. Failures are shown and retried, never cached
- Each tab (Phase 2 layout, branch): company header; one metrics panel with two groups, "Price and valuation" (price, market cap, forward P/E) and "Profitability" (gross margin, free cash flow), labels, values and period lines aligned on one grid, the source and retrieval time stated once at the panel's foot; 5-year price chart; evidence list; a show filter (All, Catalysts, Risk factor changes, Other risks); findings as compact expandable rows ordered High, Medium, Low, Not assessed, with one plain-text line above each headline (impact, change label, "Figures to check"), no pills or badges anywhere, and "Potential implication", detail, impact basis, figures and the filing excerpt each under its own small heading; "What changed in the risk factors" with the unchanged list below it; "Other risks from management's discussion (not compared to last year)"; 8-K events dated from EDGAR, each labeled with its 8-K item from EDGAR (for example "Item 5.02 Director or officer change") instead of Claude's category. Questions for management and the Form 4 count were removed (Oct 10): the questions added text without evidence, and a filing count with no buy or sell direction can read as insider selling. Excel: market data, findings, 8-K events and evidence sheets, numbers stored as numbers (the research-record layout is a later step)

These features render. That does not mean they're correct. AI-written findings and Yahoo numbers have not been verified; an excerpt match verifies only the quoted words. Label claims as verified or unverified.

`course_analytics.py` does not exist. Course features have to be built from scratch, starting with the benchmark tests.

## Known problems (as of October 10, 2026, branch `phase-1-evidence`)

In priority order. Delete a line once it's fixed.

1. **Numbers conflict with no labels.** For AAPL the gross margin card says 48.65% and the AI text says 50.1%. Every number must show its period (TTM, quarter, fiscal year) and source. Partly done on the branch: Yahoo values now name their source field and say "Period not stated"; the conflict itself remains (a filing-based source such as SEC XBRL would give periods).
2. **Slow.** 108 seconds for AAPL + STRL on the branch (84.7 before; inputs and answers are now larger). Progress feedback is done; speed isn't. Filings are now cached per document for a day, so repeat runs are faster; first runs are not.
3. **The Excel export isn't a research record yet.** See the standard below. On the branch, numbers are stored as numbers with period and source columns, findings carry their filing, and an Evidence sheet lists sources. The download is named Research_Record_<tickers>_<date>.xlsx. Still missing: a cover sheet, units in headers, wrapped text and set widths.
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

Full rules: `~/Stock Project/docs/Quality_Standard.md`. Check every change against it before calling it done.
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
- **Chat to Claude Code:** when a plan in chat is ready to build, end with a ready-to-paste prompt for Claude Code in a code block. It should start with "Read CLAUDE.md," say what to change, and end with "Wait for my OK before editing."
- **Claude Code to chat:** after Claude Code finishes something, it should end with a short "Take this to chat" note: what changed, which file and function, and one question to ask chat so I learn it.
- **Keep both in sync:** when the known-problems list changes, Claude Code updates `app/CLAUDE.md` and `docs/Project_Instructions.md`, then reminds me to re-paste the instructions into the claude.ai project.
- In chat, if I ask for code changes, don't just write the code. Give me the Claude Code prompt instead, plus the explanation. Exception: a short snippet to show a concept is fine.

## How to work with me

**Teaching**
- With every code change, explain what it does, why it's built that way, and how it connects to the rest of the app.
- Use the real technical terms and define each one the first time it comes up.
- Give full functions or files I can paste in, plus the explanation. Both, every time.
- When it fits, name one question an interviewer could ask about that piece.
- Plan first. Wait for my OK before editing files.

**Testing**
- Before saying a button or feature works, ask my permission to run the app and test it. Then report exactly what happened.
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
