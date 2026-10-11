"""Price chart for the SEC Filing Research Terminal.

Drawing only: no Streamlit, no yfinance, no network calls. app.py fetches the data
(get_price_history) and passes it in, so this module can be tested with any DataFrame
(see tests/chart_preview.py).
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import theme as T


# Colors come from theme.py. Up/down candles and volume are semantic (positive/negative);
# the moving averages carry no meaning, so they use hues outside the semantic set.
CHART_UP, CHART_DOWN = T.POSITIVE_SOLID, T.NEGATIVE_SOLID
CHART_GRID, CHART_TEXT, CHART_MUTED, CHART_PANEL = T.BORDER, T.TEXT, T.TEXT_MUTED, T.SURFACE
CHART_FONT = T.FONT_STACK
# Plotly hard-codes the selected/hover range-button fill to near-white (#F4FAFF), so the button label
# needs a gray that reads on both that and the dark page: #787b86 is about 4:1 on each.
RANGE_BUTTON_TEXT = "#787b86"
CHART_WINDOWS = ["1M", "3M", "6M", "YTD", "1Y", "5Y"]
CHART_DEFAULT_WINDOW = "6M"
CHART_CONFIG = {  # Plotly toolbar: keep zoom, pan, reset and download; drop tools a price chart doesn't need
    "displaylogo": False,
    # zoomIn/zoomOut also zoom the price axis, which can push it below $0; the range buttons replace them
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d", "toggleSpikelines", "zoomIn2d", "zoomOut2d"],
}


def _window_start(hist: pd.DataFrame, window: str) -> pd.Timestamp:
    """First trading day inside a range-button window, e.g. '6M' = the last six months of bars."""
    last = hist.index[-1]
    if window == "5Y":
        start = hist.index[0]
    elif window == "YTD":
        start = pd.Timestamp(year=last.year, month=1, day=1)
    else:
        start = last - pd.DateOffset(months={"1M": 1, "3M": 3, "6M": 6, "1Y": 12}[window])
    return hist.index[hist.index >= start][0]


def _window_view(hist: pd.DataFrame, window: str) -> dict:
    """Axis ranges for one window. Plotly doesn't refit the y-axis when the x-range changes,
    so each button sets the price and volume ranges itself."""
    start = _window_start(hist, window)
    shown = hist.loc[start:]
    low, high = shown["Low"].min(), shown["High"].max()
    pad = max((high - low) * 0.06, high * 0.01)  # the floor keeps a flat window from collapsing to one line
    x_range = [(start - pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
               (hist.index[-1] + pd.Timedelta(days=2)).strftime("%Y-%m-%d")]
    return {
        "xaxis.range": x_range, "xaxis2.range": x_range,
        "yaxis.range": [max(0, low - pad), high + pad],
        "yaxis2.range": [0, max(shown["Volume"].max(), 1) * 1.1],  # max(..., 1): some tickers report zero volume
    }


def build_price_chart(hist: pd.DataFrame, events: list) -> go.Figure:
    """Candlesticks + 50/200-day moving averages + volume + SEC filing markers.
    events: list of (filing_date 'YYYY-MM-DD', form type) tuples from fetch_firm_data()."""
    close = hist["Close"]
    first_bar, last_bar = hist.index[0], hist.index[-1]
    up_day = close >= hist["Open"]

    # SEC filing markers. Filings can land on market holidays, so each one is pinned to the first trading
    # day on or after its date. Filings outside the price history are dropped instead of stretching the
    # x-axis into empty space (the old chart's bug).
    marker_days = {}
    for date_str, form in events or []:
        # Strict format: lenient parsing turns "2026-04-17/2026-04-20" into a fake time and time zone
        filed = pd.to_datetime(date_str, format="%Y-%m-%d", errors="coerce")
        if pd.isna(filed) or filed < first_bar or filed > last_bar:
            continue
        session = hist.index[hist.index >= filed][0]
        marker_days.setdefault(session, []).append(f"{form} filed {filed:%Y-%m-%d}")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.78, 0.22], vertical_spacing=0.03)

    fig.add_trace(go.Candlestick(
        x=hist.index, open=hist["Open"], high=hist["High"], low=hist["Low"], close=close, name="Price",
        showlegend=False, text=[" · ".join(marker_days.get(d, [])) for d in hist.index],
        increasing=dict(line=dict(color=CHART_UP, width=1), fillcolor=CHART_UP),
        decreasing=dict(line=dict(color=CHART_DOWN, width=1), fillcolor=CHART_DOWN),
    ), row=1, col=1)

    # Simple moving averages: the mean close of the last 50 / 200 trading days. NaN until enough bars exist.
    for days, color, dash in [(50, T.SERIES_SMA_FAST, "solid"), (200, T.SERIES_SMA_SLOW, "dot")]:
        fig.add_trace(go.Scatter(
            x=hist.index, y=close.rolling(days).mean(), name=f"{days}D SMA", mode="lines",
            line=dict(color=color, width=1.2, dash=dash), hovertemplate="%{y:$,.2f}",
        ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=hist.index, y=hist["Volume"], name="Volume", showlegend=False,
        marker=dict(color=[CHART_UP if u else CHART_DOWN for u in up_day], opacity=0.45, line_width=0),
        hovertemplate="Vol %{y:.3s}<extra></extra>",
    ), row=2, col=1)

    if marker_days:
        days = sorted(marker_days)
        fig.add_trace(go.Scatter(
            x=days, y=[0.035] * len(days), yaxis="y3", mode="markers", name="SEC filing",
            marker=dict(symbol="diamond", size=9, color=T.INFO_SOLID, line=dict(color=T.BG, width=1)),
            hoverinfo="skip",  # the filing shows in the candle's hover instead, on the exact trading day
        ))

    # Remove weekends and market holidays so candles sit next to each other with no gaps.
    holidays = pd.bdate_range(first_bar, last_bar).difference(hist.index)
    rangebreaks = [dict(bounds=["sat", "mon"]), dict(values=holidays.strftime("%Y-%m-%d").tolist())]

    views = {w: _window_view(hist, w) for w in CHART_WINDOWS}
    default = views[CHART_DEFAULT_WINDOW]
    last_close, last_color = close.iloc[-1], (CHART_UP if up_day.iloc[-1] else CHART_DOWN)

    fig.update_xaxes(
        rangebreaks=rangebreaks, showgrid=False, linecolor=CHART_GRID, tickfont=dict(color=CHART_MUTED),
        # Zoom limits: you can't pan or zoom out past the first or last bar
        minallowed=(first_bar - pd.Timedelta(days=3)).strftime("%Y-%m-%d"),
        maxallowed=(last_bar + pd.Timedelta(days=5)).strftime("%Y-%m-%d"),
        showspikes=True, spikemode="across", spikesnap="cursor", spikecolor=CHART_MUTED,
        spikethickness=1, spikedash="dot", rangeslider_visible=False, hoverformat="%a %b %d, %Y",
    )
    fig.update_layout(
        height=480, margin=dict(l=8, r=64, t=36, b=30), dragmode="zoom", hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=CHART_FONT, size=11, color=CHART_TEXT),
        hoverlabel=dict(bgcolor=CHART_PANEL, bordercolor=CHART_GRID, font=dict(color=CHART_TEXT)),
        legend=dict(orientation="h", x=1, xanchor="right", y=1.0, yanchor="bottom",
                    bgcolor="rgba(0,0,0,0)", font=dict(color=CHART_MUTED, size=11)),
        xaxis=dict(range=default["xaxis.range"]),
        xaxis2=dict(range=default["xaxis2.range"]),
        yaxis=dict(range=default["yaxis.range"], minallowed=0, side="right", tickprefix="$",
                   tickformat=",.0f" if last_close >= 20 else ",.2f",  # cents matter for low-priced stocks
                   hoverformat=",.2f", gridcolor=CHART_GRID, zeroline=False, tickfont=dict(color=CHART_MUTED)),
        yaxis2=dict(range=default["yaxis2.range"], minallowed=0, side="right", tickformat="~s", nticks=3,
                    gridcolor=CHART_GRID, zeroline=False, tickfont=dict(color=CHART_MUTED)),
        # Overlay axis for the filing markers: fixed 0-1 scale, so markers stay at the bottom of the price pane
        yaxis3=dict(overlaying="y", range=[0, 1], visible=False, fixedrange=True),
        updatemenus=[dict(
            type="buttons", direction="right", x=0, xanchor="left", y=1.0, yanchor="bottom",
            pad=dict(t=0, b=6, l=0, r=0), showactive=True, active=CHART_WINDOWS.index(CHART_DEFAULT_WINDOW),
            bgcolor="rgba(0,0,0,0)", borderwidth=0, font=dict(color=RANGE_BUTTON_TEXT, size=12),
            buttons=[dict(label=w, method="relayout", args=[views[w]]) for w in CHART_WINDOWS],
        )],
        shapes=[dict(type="line", xref="paper", x0=0, x1=1, yref="y", y0=last_close, y1=last_close,
                     line=dict(color=last_color, width=1, dash="dot"))],
        # Last-close tag sits on the right price axis, like a trading terminal
        annotations=[dict(xref="paper", x=1, xanchor="left", xshift=2, yref="y", y=last_close, yanchor="middle",
                          text=f"<b>{last_close:,.2f}</b>", showarrow=False, bgcolor=last_color,
                          font=dict(color="#ffffff", size=11), borderpad=3)],
    )
    return fig
