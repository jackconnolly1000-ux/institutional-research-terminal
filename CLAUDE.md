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
│   ├── app.py
│   ├── requirements.txt
│   ├── CLAUDE.md    these instructions, for Claude Code
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

Tested in a browser on October 9, 2026:

- Home screen: ticker input, two preset buttons (Load Tech, Load Industrials), Run Terminal, and a suggestion list with a Select button
- Results for each ticker: metric cards (insider count over 90 days, price, forward P/E, gross margin, FCF, market cap), a candlestick chart with 8-K and 10-Q markers, AI-written catalysts and risks with filing excerpts, 8-K events, executive Q&A prep, and an Excel download
- Run Terminal took about 75 seconds for two tickers

These features render. That does not mean they're correct. The numbers and AI-written facts have not been verified. Treat every feature as unverified until it's checked against the code or tested. Label claims as verified or unverified.

`course_analytics.py` does not exist. The repo has only `app.py` (540 lines) and `requirements.txt`. Course features have to be built from scratch, starting with the benchmark tests.

## Known problems (as of October 9, 2026)

In priority order. Delete a line once it's fixed.

1. **The input box is out of sync with what runs.** Clicking Load Industrials changes the suggestion to STRL, and Run Terminal then analyzes FAST and STRL, but the input box still shows AAPL. The user sees one ticker and gets results for others. Likely cause (from reading `app.py` around line 421, not yet confirmed by running): the presets update `st.session_state.tickers_input`, but the `st_keyup` component (from `streamlit-keyup`) doesn't redraw its box when its `value` changes after the first render.
2. **Select does nothing visible.** Clicking it leaves the input box unchanged. Probably the same cause as problem 1, since Select also writes to session state. In my test the suggestion already matched, so this needs a retest with a different ticker.
3. **Garbled dollar amounts.** Streamlit markdown reads text between two `$` signs as a math formula, so AI text with dollar figures renders as broken monospace. Seen in both the AAPL and FAST results. Escape `$` before rendering.
4. **Numbers conflict with no labels.** For AAPL the gross margin card says 48.65% and the AI text says 50.1%. Every number must show its period (TTM, quarter, fiscal year) and source.
5. **Slow.** About 75 seconds for two tickers, with only a status line while it runs. Add caching (`st.cache_data`) and real progress feedback.
6. **The Excel export is a raw data dump.** See the standard below.
7. **Layout:** empty bars above and below the ticker input (cause found: lines 417 and 433 open and close a `<div>` in separate `st.markdown` calls, so the styled div renders empty; same pattern at lines 445 and 471); a white input box that clashes with the dark theme; four identical blue buttons with no visual hierarchy; Select sits far from its suggestion; clicking a preset wipes the current results without warning.
8. **Content:** "Load Tech (AAPL)" loads one stock and "Load Industrials" loads two (FAST, STRL), so neither is a basket. The "LIVE FEED" badge probably overclaims, since yfinance data is usually delayed (verify). The subtitle promises "Form 4 Insider Velocity" but the app shows a count. "CapEx & Growth Catalysts" mostly holds items that aren't capex. One 8-K date shows as "2026-04-17/2026-04-20."
9. **Minor:** the ticker input doesn't show up in the page's accessibility tree, so screen readers may not find it. Check.

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
- Don't describe course topics marked Upcoming as things I know.
- Lead with the short answer, then the detail.

## Order of work

1. Fix the input sync, presets, and Select (problems 1 and 2)
2. Fix the dollar sign rendering (problem 3)
3. Label every number with period and source (problem 4)
4. Speed: caching and progress (problem 5)
5. Rebuild the Excel export as a research record (problem 6)
6. Layout and content cleanup (problems 7 to 9)
7. Course features: Monte Carlo simulation first, then LP allocation, then CAPM regression after the Nov 11 and 13 classes
