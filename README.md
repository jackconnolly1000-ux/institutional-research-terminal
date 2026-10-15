# SEC Filing Research Terminal

A Streamlit app that reads a company's SEC filings and market data and summarizes them for stock research. It is a research tool, not investment advice.

Live app: https://sec-filing-research-terminal.streamlit.app/ (the `main` branch).

## What it does

For up to five tickers:

- Downloads the latest 10-K, the prior 10-K, every 10-Q filed since the latest 10-K, and up to four 8-Ks from the last 180 days from SEC EDGAR.
- Finds the Risk Factors (Item 1A) and Management's Discussion and Analysis sections by their headings. A section that can't be found is reported as missing, not replaced with other text.
- Compares the two 10-Ks' risk factors paragraph by paragraph in code (`compare.py`) and labels each paragraph new, changed, unchanged or removed.
- Sends the changed and new paragraphs, the 10-Q updates, MD&A and the 8-Ks to Claude (Anthropic API), which returns catalysts, risk-factor changes, other risks from management's discussion and 8-K events, each tied to one source.
- Checks the answer: whether it was complete, whether every field is valid, whether each quoted excerpt appears word for word in the cited filing, and whether each figure in a finding appears in that filing.
- Shows revenue, gross margin, operating margin and free cash flow for the trailing twelve months (TTM) from SEC XBRL company facts (`xbrl.py`): the figures companies tag in their own 10-K and 10-Q filings. Each names its period and the filings it came from.
- Shows price, market cap and forward P/E from Yahoo Finance with their source field and retrieval time, and a five-year price chart.
- Exports the results to Excel.
- Limits spending on live AI calls to $0.25 a day (see Spending limit below).
- Shows a saved AAPL + STRL sample with no live calls, from the "View saved sample" button.

## What it doesn't do

- It doesn't give investment advice, price targets or ratings.
- It doesn't verify the AI's interpretation. An "Excerpt matched" label means the quoted words are in the filing, not that the summary is right.
- The general AI evidence pipeline doesn't read exhibits: risk factors incorporated by reference from an annual-report exhibit (as JPM does) and 8-K press releases (EX-99.1) are not sent to Claude. The separately checked Vistra financing notice cites selected exhibits.
- It doesn't know the period behind most Yahoo Finance values; those show "Period not stated". Yahoo's margins and free cash flow are still in the Excel export, labeled that way, next to the SEC figures.

## Known limits

- Oracle's saved review also includes a June–August cash reconciliation and funding analysis
  (`oracle_liquidity.py`, `oracle_liquidity_view.py`). It separates the specified customer-prepayment
  contribution from other OCF and equity proceeds, shows dated lease and purchase payments, and links
  the reviewed revolver agreement. The Oracle cash-analysis download contains formulas, sources and a
  native chart; `samples/oracle_liquidity.manifest.json` binds it to the checked JSON review.
  The original combined evidence download is preserved. Historical funding exclusions are not forecasts
  or estimates of recurring OCF. August drawable credit, covenant headroom and remaining debt principal
  dates remain Unavailable. Source audit and rebuild instructions: `docs/oracle_liquidity_reconciliation.md`.

- A free saved debt and liquidity pilot is available for LLY, ORCL and VST, checked October 14, 2026. It shows each company's dated cash, baseline gross debt, net debt and current ratio, their reported inputs and source 10-Q, and a separate Excel evidence download with formulas. Vistra's checked subsequent financing changes are included. The saved company reviews also show checked TTM operating cash flow, reported capital spending, free cash flow and flow/debt ratios, a borrowing breakdown, and selected obligations with their dates and recognition status. Oracle's customer prepayments and Vistra's capex definition are stated beside the flows. This is a frozen review, not a live update or a complete obligations analysis; interest coverage is not included. Oracle now includes its historical May 31 principal maturity schedule, its reconciliation to carrying debt, and two checked later 8-Ks. No August maturity schedule or current revolver availability is inferred; see `docs/oracle_maturity_reconciliation.md`. Reconciliation: `docs/pilot_cashflow_reconciliation.md`. The existing AAPL/STRL saved analysis is separate.

- Live results include a dated EDGAR index of 8-Ks, debt-offering form candidates and periodic-report amendments since the latest balance sheet. For Vistra's June 30, 2026 balance sheet, ten filings through October 14 were manually screened for financing, with source documents linked; the September offering documents refer to one completed $1.5 billion issuance. Oracle’s August 31 anchor also joins its two checked September 8-Ks and exhibits. Other companies and later or unmatched filings remain "Not checked." A retrieval gap is labeled incomplete. The saved sample predates this index.
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
- The saved sample is frozen: the analysis is from Oct 10, 2026 and the price history ends at the Oct 9 close (retrieved Oct 11), and its SEC figures count only filings made by Oct 10 (retrieved Oct 11). It doesn't update.

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

Streamlit Secrets (`.streamlit/secrets.toml`) needs `ANTHROPIC_API_KEY` and `SEC_CONTACT_EMAIL` (SEC EDGAR asks every automated request to name a contact), and optionally `OWNER_PASSCODE`.

## Tests

```
.venv/bin/python -m unittest discover -s tests -p "test_*.py"      # Mac/Linux
.venv\Scripts\python -m unittest discover -s tests -p "test_*.py"  # Windows
```

Unit tests import the production modules (`sec_data.py`, `compare.py`, `analysis.py`, `market_data.py`, `budget.py`, `xbrl.py`) and make no network calls. `tests/offline/` runs the whole app on fake SEC, Yahoo and Anthropic responses; `tests/check_risk_extraction.py` checks section extraction against live EDGAR filings without calling Anthropic.
