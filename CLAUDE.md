# Institutional Research Terminal: project instructions

## What this is

I'm Jack, a sophomore finance student at Villanova School of Business. I'm building the Institutional Research Terminal, a Streamlit web app that speeds up stock research by putting market data, SEC filings, and AI summaries in one dashboard. It's live at https://jack-research-terminal.streamlit.app/.

Stack: Python, Streamlit, Plotly, yfinance, CrewAI, and LLMs. I work in VS Code with Claude Code, and in Google Colab.

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
│   ├── sec_data.py  which SEC filings to use, and finding real section boundaries (no Streamlit, tested)
│   ├── analysis.py  evidence blocks, token budget, prompt and schema, response checks, excerpt matching (tested)
│   ├── market_data.py  Yahoo values as numbers with unit, period, source, retrieval time (tested)
│   ├── theme.py     color tokens, named by meaning (the one place colors are defined)
│   ├── ui.py        CSS built from theme.py, cards, chips, metric tiles, skeleton loaders, progress strip
│   ├── charts.py    price chart (drawing only, no network)
│   ├── requirements.txt
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

Layout from Oct 10, 2026 (on `main` and the live site). **Branch `phase-1-evidence`** (Oct 10, not merged or deployed) changes what the analysis is built on. Tested with 40 unit tests, offline browser scenarios, live EDGAR checks on AAPL, FAST, STRL and MSFT, and one real-key run of AAPL + STRL (108 s, $0.27, both answers complete).

- Home screen: title and subtitle ("A research tool, not investment advice"), one ticker picker (`st.multiselect`, up to 5), one primary **Run analysis** button, two outlined example buttons
- While it runs: a progress strip (queued, working, done, partial, failed) and a tab per ticker with a skeleton loader and step label (SEC filings, market data, Claude)
- Results are saved in `st.session_state`; a summary line and the Excel download sit at the top
- **Evidence (branch):** annual trend labels compare Item 1A of the latest 10-K with the prior 10-K, both periods shown. Every 10-Q since that 10-K is read for risk-factor updates (a 10-Q that incorporates an earlier one is flagged). MD&A comes from the latest 10-K or 10-Q; up to four 8-Ks from the last 180 days. Sections are found by their real headings (not tables of contents or cross-references); missing, failed, not applicable and "no material changes" are reported, never replaced with other text. An evidence list shows every source, its status, and how much was sent
- **Request budget (branch):** the whole request is measured with Anthropic's free token-counting endpoint and kept within 60,000 tokens (44,000 input + 16,000 output reserve). Sources share the input space; omitted characters are reported
- **Checks (branch):** Claude's `stop_reason` and every required field are checked. Sections are complete, empty, partial, missing, invalid, no input, or failed, each with its own message; only complete answers are cached. Each excerpt is matched, fragments in order, in the one source it cites ("Excerpt matched" means the words are there, not that the interpretation is right). Impact (High, Medium, Low, Not assessed) and trend are labeled AI assessments; "New" is withheld unless the whole prior section was sent
- **Market data (branch):** numbers with unit, source field and retrieval time; "Period unavailable" where Yahoo doesn't document one. Failures are shown and retried, never cached
- Each tab: company header, metric tiles, 5-year price chart, catalyst and risk cards (headline, summary, potential implication, detail, source and excerpt), 8-K events dated from EDGAR, questions for management. Excel: market data, findings, 8-K events and evidence sheets, numbers stored as numbers

These features render. That does not mean they're correct. AI-written findings and Yahoo numbers have not been verified; an excerpt match verifies only the quoted words. Label claims as verified or unverified.

`course_analytics.py` does not exist. Course features have to be built from scratch, starting with the benchmark tests.

## Known problems (as of October 10, 2026, branch `phase-1-evidence`)

In priority order. Delete a line once it's fixed.

1. **Numbers conflict with no labels.** For AAPL the gross margin card says 48.65% and the AI text says 50.1%. Every number must show its period (TTM, quarter, fiscal year) and source. Partly done on the branch: Yahoo values now name their source field and say "Period unavailable"; the conflict itself remains (a filing-based source such as SEC XBRL would give periods).
2. **Slow.** 108 seconds for AAPL + STRL on the branch (84.7 before; inputs and answers are now larger). Progress feedback is done; speed isn't. Filings are now cached per document for a day, so repeat runs are faster; first runs are not.
3. **The Excel export isn't a research record yet.** See the standard below. On the branch, numbers are stored as numbers with period and source columns, findings carry their filing, and an Evidence sheet lists sources. Still missing: the name, a cover sheet, units in headers, wrapped text and set widths.
4. **Annual comparison runs on partial sections.** In the Oct 10 real run, the 44,000-token input budget sent 35% of AAPL's prior 10-K Risk Factors and 59% of STRL's. Claude labeled a STRL tariff risk "New", but the prior 10-K mentions tariffs after the cut-off. "New" is now withheld when the prior section is partial, and Escalated/Unchanged say "partial prior text", but the comparison itself is still incomplete. Decide: a larger budget, sending the two 10-K sections first, or comparing them in a separate call.
5. **8-K exhibits aren't read.** Only each 8-K's primary document is sent; press releases usually sit in exhibit EX-99.1.
6. **Section extraction is tested on four filers** (AAPL, FAST, STRL, MSFT) plus synthetic cases. Other formats may fail; they show "Section not found", not wrong text.
7. **Phone layout:** 12 px of horizontal overflow at 390 px wide.

## Excel export standard

**Purpose: a research record.** Someone opening it later should see what the app found, when, and where each number came from.

- Rename it "Research Record." It is not a model, so don't call it "Institutional Model."
- A cover sheet with tickers, date and time run, app version, data sources, and a line saying it's not investment advice
- Numbers stored as numbers with proper formats ($B, %, x). Never as text.
- Every metric labeled with its period and source (for example, "TTM, yfinance" or "Q3 2026, 10-Q filed 2026-07-31")
- Clean data layout, following the course rule: one row per record, one header per column, one data type per field, no merged cells
- Catalysts and risks sheets: wrapped text, set column widths, styled and frozen headers, and the filing type and date next to each excerpt
- Units in every column header

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
4. Phase 2 interface (findings rows, filter, phone overflow); then the comparison budget (problem 4)
5. Course features: Monte Carlo simulation first, then LP allocation, then CAPM regression after the Nov 11 and 13 classes
