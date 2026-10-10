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
│   ├── app.py       data fetching, Claude call, page layout
│   ├── theme.py     color tokens, named by meaning (the one place colors are defined)
│   ├── ui.py        CSS built from theme.py, cards, chips, metric tiles, skeleton loaders, progress strip
│   ├── charts.py    price chart (drawing only, no network)
│   ├── requirements.txt
│   ├── CLAUDE.md    these instructions, for Claude Code
│   ├── .streamlit/config.toml   widget theme (repeats the base colors in theme.py)
│   ├── tests/       diagnostic scripts (no Anthropic calls)
│   │   ├── chart_preview.py   price chart on synthetic prices
│   │   └── offline/           whole app on fake SEC/Yahoo/Anthropic responses + Playwright screenshots (shots/ is gitignored)
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

New layout, October 10, 2026. Tested locally with Playwright: offline on fake data (`tests/offline`), the chart on synthetic prices (`tests/chart_preview.py`), and one real-key run of AAPL + STRL. Not yet checked on the live site.

- Home screen: title and subtitle ("A research tool, not investment advice"), one ticker picker (`st.multiselect`, search by ticker or company name, up to 5, full company names in the chips), one primary **Run analysis** button, and two outlined example buttons (Example: AAPL, Example: FAST + STRL)
- While it runs: a progress strip with one chip per ticker (queued, working, done with seconds, failed), and a tab per ticker showing a skeleton loader with a step label ("Reading SEC filings (step 1 of 2)", "Summarizing filings with Claude (step 2 of 2)")
- Results are saved in `st.session_state`, so clicking Download, a preset, or changing the selection doesn't wipe them (a caption says when the selection no longer matches). A summary line (tickers, run time in ET, how many succeeded) and the Excel download sit at the top, then one tab per ticker
- Each tab: company header, metric tiles grouped as Market (price, market cap), Valuation and profitability (forward P/E, gross margin, FCF), and Insider filings (Form 4 count, last 90 days), each with a source line; a 5-year daily candlestick chart (opens on 6M, range buttons 1M to 5Y, 50- and 200-day moving averages, volume, SEC filing dates as diamonds); Catalysts and Risks as cards with impact and trend chips and a collapsed filing excerpt; 8-K events as a dated list; numbered questions for management
- A failed ticker gets a card naming the ticker and the reason; the others still show
- Real-key run of AAPL + STRL took 84.7 seconds

These features render. That does not mean they're correct. The numbers and AI-written facts have not been verified. Treat every feature as unverified until it's checked against the code or tested. Label claims as verified or unverified.

`course_analytics.py` does not exist. The repo has `app.py` (about 480 lines), `theme.py`, `ui.py`, `charts.py`, `requirements.txt`, `.streamlit/config.toml`, and `tests/`. Course features have to be built from scratch, starting with the benchmark tests.

## Known problems (as of October 10, 2026)

In priority order. Delete a line once it's fixed.

1. **Numbers conflict with no labels.** For AAPL the gross margin card says 48.65% and the AI text says 50.1%. Every number must show its period (TTM, quarter, fiscal year) and source.
2. **Slow.** About 75 seconds for two tickers (84.7 seconds for AAPL + STRL on Oct 10). Progress feedback is done (Oct 10: progress strip and per-ticker skeleton loaders); speed isn't. Add caching (`st.cache_data`) where it helps.
3. **The Excel export is a raw data dump.** See the standard below.
4. **Content:** One 8-K date shows as "2026-04-17/2026-04-20."
5. **Failures cached as results in `get_comprehensive_financials`:** any yfinance error returns all "N/A" and `st.cache_data` keeps it for an hour. It's called inside `fetch_firm_data`, so the N/A cards are also baked into that cache. Failed 8-K downloads are also skipped silently. Fix like `extract_unified_profile`: raise instead, and fetch the financials outside the cached SEC function.
6. **Claude's reply can be cut off, and the missing parts show as empty.** Real-key run Oct 10: STRL showed 0 8-K events and 0 questions for management (AAPL got 4 and 3). Likely cause, not yet verified: `extract_unified_profile` calls Claude with `max_tokens=4000` and never checks `response.stop_reason`, so a reply cut off at the limit is used as is, and `.get(..., [])` turns the missing fields into empty lists. STRL's 14 long catalyst and risk items come first in the schema, so the 8-K and question fields come last and get dropped. The page then says "No recent material events found," and the result is cached for an hour.
7. **The YoY risk comparison can silently run without prior-year text.** In `fetch_firm_data` (around lines 161-171), the prior-year filing fetch is wrapped in `except Exception: pass`, and a failed download leaves `prior_risk` as "PRIOR YEAR FILING NOT AVAILABLE". Either way Claude does the "YoY Delta" with nothing to compare against, the NEW/ESCALATED/STABLE trend labels mean nothing, the user isn't told, and the result is cached for an hour. **Verified Oct 9 by `tests/check_risk_extraction.py` (AAPL, FAST, STRL), and worse than that:**
   - All three compare 10-Q vs 10-Q (quarter over quarter), never 10-K vs 10-K.
   - The text sent as "risk factors" isn't the Risk Factors section for any of them. AAPL: a cross-reference in MD&A, so mostly MD&A text. FAST: its 10-Q risk section is one "no material changes" sentence (155 chars, under the 4,000 filter), so the fallback slice sends inline XBRL tags (`us-gaap:...Member 2026-04-01`). STRL: a quoted cross-reference, then MD&A.
   - The "MD&A" text starts at the table of contents and runs through the financial statements for FAST and STRL (AAPL's MD&A is correct).
   - Even a 10-K vs 10-K comparison would get the wrong text: `max(key=len)` picks a cross-reference match that runs to the end of the document (signatures included), not the real section. For FAST the real section exists as a smaller match ("ITEM 1A. RISK FACTORS", ending at Item 1B).
   - Real 10-K Risk Factors sections are about 50,000-85,000 chars, so the 20,000 / 18,000 cuts drop most of each section.
   - Excerpt check (Oct 10, AAPL export, `--excerpts`): 10 of 11 "Filing Excerpt" quotes appear word for word in the text sent to Claude. The 11th is a sentence from the prior quarter's 10-Q (sent in the "prior risk factors" slot, which holds MD&A text) with the word "also" added, shown as a current catalyst.

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
4. Content cleanup (problem 4)
5. Course features: Monte Carlo simulation first, then LP allocation, then CAPM regression after the Nov 11 and 13 classes
