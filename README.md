# SEC Filing Research Terminal

A Streamlit app that reads a company's SEC filings and market data and summarizes them for stock research. It is a research tool, not investment advice.

Live app: https://jack-research-terminal.streamlit.app/ (the `main` branch).

## What it does

For up to five tickers:

- Downloads the latest 10-K, the prior 10-K, every 10-Q filed since the latest 10-K, and up to four 8-Ks from the last 180 days from SEC EDGAR.
- Finds the Risk Factors (Item 1A) and Management's Discussion and Analysis sections by their headings. A section that can't be found is reported as missing, not replaced with other text.
- Compares the two 10-Ks' risk factors paragraph by paragraph in code (`compare.py`) and labels each paragraph new, changed, unchanged or removed.
- Sends the changed and new paragraphs, the 10-Q updates, MD&A and the 8-Ks to Claude (Anthropic API), which returns catalysts, risks, 8-K events and questions for management, each tied to one source.
- Checks the answer: whether it was complete, whether every field is valid, and whether each quoted excerpt appears word for word in the cited filing.
- Shows market data from Yahoo Finance with its source field and retrieval time, and a five-year price chart.
- Exports the results to Excel.

## What it doesn't do

- It doesn't give investment advice, price targets or ratings.
- It doesn't verify the AI's interpretation. An "Excerpt matched" label means the quoted words are in the filing, not that the summary is right.
- It doesn't read exhibits: risk factors incorporated by reference from an annual-report exhibit (as JPM does) and 8-K press releases (EX-99.1) are not read.
- It doesn't know the period behind most Yahoo Finance values; those show "Period unavailable".

## Known limits

- "No close match in the prior 10-K" is a text test. A heavily rewritten paragraph can be labeled that way; the closest prior paragraph is shown as context.
- Section extraction has been checked on seven filers (AAPL, FAST, STRL, MSFT, WMT, JNJ, JPM). Other filing layouts may not be recognized.
- Each request is capped at 60,000 tokens. When the evidence is larger, the rest is omitted and the omission is shown.
- A first run takes about a minute per ticker.

## Running it

```
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

Streamlit Secrets (`.streamlit/secrets.toml`) needs `ANTHROPIC_API_KEY` and `SEC_CONTACT_EMAIL` (SEC EDGAR asks every automated request to name a contact).

## Tests

```
.venv/bin/python -m unittest discover -s tests -p "test_*.py"
```

Unit tests import the production modules (`sec_data.py`, `compare.py`, `analysis.py`, `market_data.py`) and make no network calls. `tests/offline/` runs the whole app on fake SEC, Yahoo and Anthropic responses; `tests/check_risk_extraction.py` checks section extraction against live EDGAR filings without calling Anthropic.
