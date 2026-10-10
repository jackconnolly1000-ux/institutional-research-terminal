"""Preview the price chart on synthetic prices. No Yahoo, no SEC, no Anthropic calls.

Run from the app/ folder:
    streamlit run tests/chart_preview.py

Check by eye: opens on 6M; each range button refits the price axis; you can't pan or zoom
past the first or last bar or below $0; no gaps for weekends or holidays; hovering a
blue-diamond day shows the filing in the hover box.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make app/ importable
from charts import CHART_CONFIG, build_price_chart  # noqa: E402

st.set_page_config(page_title="Chart preview", layout="wide")
st.title("Chart preview (synthetic data)")

# Seeded random walk: about 5 years of business days ending Fri 2026-10-09, minus a few market holidays
rng = np.random.default_rng(7)
days = pd.bdate_range("2021-10-11", "2026-10-09").difference(pd.to_datetime([
    "2025-11-27", "2025-12-25", "2026-01-01", "2026-01-19", "2026-02-16",
    "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07"]))
close = 140 * np.exp(np.cumsum(rng.normal(0.0006, 0.017, len(days))))
open_ = close * np.exp(rng.normal(0, 0.006, len(days)))
hist = pd.DataFrame({
    "Open": open_,
    "High": np.maximum(open_, close) * np.exp(np.abs(rng.normal(0, 0.007, len(days)))),
    "Low": np.minimum(open_, close) * np.exp(-np.abs(rng.normal(0, 0.007, len(days)))),
    "Close": close,
    "Volume": rng.lognormal(17.8, 0.35, len(days)),
}, index=days)

# Same shape as fetch_firm_data()'s event_markers. The last three must be dropped:
# older than the data, malformed, and after the last bar.
events = [("2026-07-31", "10-Q"), ("2026-07-30", "8-K"), ("2026-06-11", "8-K"), ("2026-04-30", "8-K"),
          ("2026-01-29", "8-K"), ("2019-01-02", "8-K"), ("2026-04-17/2026-04-20", "8-K"), ("2026-10-12", "8-K")]

st.plotly_chart(build_price_chart(hist, events), use_container_width=True, theme=None, config=CHART_CONFIG)
st.caption(f"Synthetic data. {len(hist):,} daily bars, {hist.index[0]:%Y-%m-%d} to {hist.index[-1]:%Y-%m-%d}.")
