"""Page styling and HTML components for the Institutional Research Terminal:
CSS built from theme.py tokens, skeleton loaders, a run-progress strip, metric tiles, and
catalyst / risk / 8-K cards.

Every piece of AI or filing text goes through esc() before it reaches HTML. Filings and model
output can contain "<", "&" or "$", and unsafe_allow_html=True renders whatever it's given.
"""
from __future__ import annotations

import html

import streamlit as st

import theme as T


def _tint(hex_color: str, alpha: float = 0.16, base: str = T.SURFACE) -> str:
    """Blend a color into the card surface. Chips use a 16% tint as their background."""
    fg = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    bg = [int(base[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(alpha * f + (1 - alpha) * b):02x}" for f, b in zip(fg, bg))


def esc(text) -> str:
    """Make model and filing text safe to drop into an HTML card.
    - html.escape: '<' and '&' can't act as markup
    - '$' -> &#36;: '$5B ... $3B' isn't read as math
    - line breaks -> <br>: st.markdown ends an HTML block at a blank line, so a blank line in AI text
      would push the rest of the card out as Markdown (an indented line even becomes a code block
      showing raw tags). With no raw newlines left, the whole card stays one HTML block."""
    text = html.escape(str(text)).replace("$", "&#36;")
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


TONES = {  # tone name -> (solid edge, text color, chip background)
    "positive": (T.POSITIVE_SOLID, T.POSITIVE_TEXT, _tint(T.POSITIVE_SOLID)),
    "negative": (T.NEGATIVE_SOLID, T.NEGATIVE_TEXT, _tint(T.NEGATIVE_SOLID)),
    "caution": (T.CAUTION_SOLID, T.CAUTION_TEXT, _tint(T.CAUTION_SOLID)),
    "info": (T.INFO_SOLID, T.INFO_TEXT, _tint(T.INFO_SOLID)),
    "neutral": (T.BORDER, T.TEXT_MUTED, T.SURFACE_HOVER),
}


def inject_css() -> None:
    tone_css = "\n".join(
        f".tone-{name} {{ --tone-edge: {edge}; --tone-text: {text}; --tone-bg: {bg}; }}"
        for name, (edge, text, bg) in TONES.items()
    )
    st.markdown(f"""<style>
:root {{
  --bg: {T.BG}; --surface: {T.SURFACE}; --surface-hover: {T.SURFACE_HOVER}; --border: {T.BORDER};
  --text: {T.TEXT}; --text-strong: {T.TEXT_STRONG}; --text-muted: {T.TEXT_MUTED}; --accent: {T.ACCENT};
  --font: {T.FONT_STACK};
}}
{tone_css}

/* One font everywhere. Before, paragraphs, headings/lists and metrics each used a different font. */
.stApp, .stApp div, .stApp span, .stApp p, .stApp li, .stApp a, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp h5, .stApp label, .stApp input, .stApp button, .stApp summary {{ font-family: var(--font); }}
.stApp code, .stApp pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
.stApp {{ background: var(--bg); }}
h1.irt-title {{ font-size: 1.5rem; font-weight: 650; color: var(--text-strong); margin: 0; padding: 0; letter-spacing: -0.01em; }}
p.irt-subtitle {{ color: var(--text-muted); margin: 2px 0 18px 0; font-size: 0.9rem; }}

/* Buttons: one filled primary action (Run). Everything else is outlined. */
.stButton button[kind="secondary"] {{ background: transparent; border: 1px solid var(--border); color: var(--text);
  min-height: 0; padding: 0.2rem 0.75rem; font-size: 0.85rem; }}
.stButton button[kind="secondary"]:hover {{ background: var(--surface); border-color: var(--text-muted); color: var(--text-strong); }}
.stButton button[kind="primary"] {{ font-weight: 600; }}

/* Tabs */
.stTabs [data-baseweb="tab"] {{ font-weight: 600; }}

/* Cards and chips */
.irt-card {{ background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--tone-edge, var(--border));
  border-radius: 6px; padding: 12px 14px; margin: 0 0 10px 0; }}
.irt-card-head {{ display: flex; gap: 8px; align-items: baseline; justify-content: space-between; }}
.irt-card-title {{ color: var(--text-strong); font-weight: 600; font-size: 0.95rem; line-height: 1.35; }}
.irt-card-body {{ color: var(--text); font-size: 0.9rem; line-height: 1.5; margin: 6px 0 0 0; }}
.irt-chips {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }}
.irt-chip {{ display: inline-block; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.02em; line-height: 1.6;
  padding: 0 8px; border-radius: 999px; color: var(--tone-text); background: var(--tone-bg); white-space: nowrap; }}
.irt-card details {{ margin-top: 8px; }}
.irt-card summary {{ color: var(--text-muted); font-size: 0.8rem; cursor: pointer; }}
.irt-card summary:hover {{ color: var(--text); }}
.irt-card blockquote {{ margin: 6px 0 0 0; padding: 6px 10px; border-left: 2px solid var(--border);
  color: var(--text-muted); font-size: 0.85rem; line-height: 1.5; }}

/* Section headers replace the emoji subheaders */
.irt-h {{ display: flex; align-items: center; gap: 8px; margin: 22px 0 10px 0; padding-bottom: 6px;
  border-bottom: 1px solid var(--border); color: var(--text-strong); font-size: 1rem; font-weight: 650; }}
.irt-count {{ color: var(--text-muted); font-weight: 500; font-size: 0.85rem; }}
.irt-note {{ color: var(--text-muted); font-size: 0.8rem; margin: -4px 0 10px 0; }}

/* Company header */
.irt-company {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px; margin: 4px 0 12px 0; }}
.irt-company .tk {{ font-size: 1.35rem; font-weight: 700; color: var(--text-strong); }}
.irt-company .nm {{ font-size: 1.05rem; color: var(--text); }}
.irt-company .meta {{ font-size: 0.85rem; color: var(--text-muted); }}

/* Metric tiles, grouped by what they measure */
.irt-metrics {{ display: grid; grid-template-columns: 2fr 3fr 1fr; gap: 12px; margin-bottom: 8px; }}
@media (max-width: 900px) {{ .irt-metrics {{ grid-template-columns: 1fr; }} }}
.irt-group-label {{ color: var(--text-muted); font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em;
  text-transform: uppercase; margin-bottom: 6px; }}
.irt-tiles {{ display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; gap: 8px; }}
.irt-tile {{ background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 10px 12px; min-width: 0; }}
.irt-tile .lbl {{ color: var(--text-muted); font-size: 0.78rem; }}
.irt-tile .val {{ color: var(--text-strong); font-size: 1.2rem; font-weight: 650; font-variant-numeric: tabular-nums; margin-top: 2px; }}
.irt-tile .src {{ color: var(--text-muted); font-size: 0.7rem; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

/* 8-K timeline */
.irt-event {{ display: grid; grid-template-columns: 96px 1fr; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--border); }}
.irt-event:last-child {{ border-bottom: none; }}
.irt-event .date {{ color: var(--text-muted); font-variant-numeric: tabular-nums; font-size: 0.85rem; padding-top: 2px; }}
.irt-event details {{ margin-top: 2px; }}

/* Questions for management */
ol.irt-questions {{ margin: 0; padding-left: 1.3rem; }}
ol.irt-questions li {{ color: var(--text); font-size: 0.92rem; line-height: 1.5; margin: 0 0 8px 0; padding-left: 4px; }}

/* Ticker chips in the picker: show the full company name instead of cutting it off */
.stMultiSelect [data-baseweb="tag"] {{ max-width: none; }}
.stMultiSelect [data-baseweb="tag"] span {{ max-width: none; }}

/* Run progress strip */
.irt-progress {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 12px 0; }}
.irt-progress .irt-chip {{ font-size: 0.78rem; padding: 2px 10px; }}

/* Skeleton loaders: gray blocks shaped like the content that's coming, so the layout doesn't jump */
.sk {{ background: linear-gradient(90deg, var(--surface) 0%, var(--surface-hover) 45%, var(--surface) 90%);
  background-size: 200% 100%; animation: sk-shimmer 1.4s ease-in-out infinite; border-radius: 6px; }}
@keyframes sk-shimmer {{ from {{ background-position: 100% 0; }} to {{ background-position: -100% 0; }} }}
@media (prefers-reduced-motion: reduce) {{ .sk {{ animation: none; }} }}
.sk-status {{ color: var(--text-muted); font-size: 0.85rem; margin: 0 0 12px 0; }}
.sk-row {{ display: grid; gap: 8px; }}
</style>""", unsafe_allow_html=True)


def chip(text: str, tone: str = "neutral") -> str:
    return f'<span class="irt-chip tone-{tone}">{esc(text)}</span>'


def section_header(title: str, count: int | None = None, note: str | None = None) -> str:
    c = f'<span class="irt-count">{count}</span>' if count is not None else ""
    n = f'<div class="irt-note">{esc(note)}</div>' if note else ""
    return f'<div class="irt-h" role="heading" aria-level="3">{esc(title)}{c}</div>{n}'


def company_header(ticker: str, name: str, industry: str, form_type: str) -> str:
    return (f'<div class="irt-company"><span class="tk">{esc(ticker)}</span><span class="nm">{esc(name)}</span>'
            f'<span class="meta">{esc(industry)} · Latest filing analyzed: {esc(form_type)}</span></div>')


def metric_tiles(groups: list) -> str:
    """groups: [(group label, [(label, value, source), ...]), ...]"""
    out = []
    for group_label, tiles in groups:
        cells = "".join(
            f'<div class="irt-tile"><div class="lbl">{esc(lbl)}</div><div class="val">{esc(val)}</div>'
            f'<div class="src" title="{esc(src)}">{esc(src)}</div></div>' for lbl, val, src in tiles)
        out.append(f'<section><div class="irt-group-label">{esc(group_label)}</div><div class="irt-tiles">{cells}</div></section>')
    return f'<div class="irt-metrics">{"".join(out)}</div>'


def _excerpt(quote: str) -> str:
    if not quote:
        return ""
    return (f'<details><summary>Filing excerpt</summary><blockquote>{esc(quote)}</blockquote></details>')


def catalyst_card(item: dict) -> str:
    impact = str(item.get("impact", "MEDIUM")).upper()
    tone = T.CATALYST_IMPACT_TONE.get(impact, "neutral")
    chips = chip(f"{impact.title()} impact", tone) + chip(item.get("category", ""), "neutral")
    return (f'<div class="irt-card tone-{tone}"><div class="irt-card-title">{esc(item.get("target", ""))}</div>'
            f'<div class="irt-chips">{chips}</div><p class="irt-card-body">{esc(item.get("description", ""))}</p>'
            f'{_excerpt(item.get("quote", ""))}</div>')


def risk_card(item: dict) -> str:
    impact = str(item.get("impact", "MEDIUM")).upper()
    tone = T.IMPACT_TONE.get(impact, "neutral")
    trend_tone, trend_label = T.TREND_CHIP.get(str(item.get("trend", "STABLE")).upper(), ("neutral", "Stable"))
    chips = chip(f"{impact.title()} impact", tone) + chip(trend_label, trend_tone) + chip(item.get("category", ""), "neutral")
    return (f'<div class="irt-card tone-{tone}"><div class="irt-card-title">{esc(item.get("target", ""))}</div>'
            f'<div class="irt-chips">{chips}</div><p class="irt-card-body">{esc(item.get("description", ""))}</p>'
            f'{_excerpt(item.get("quote", ""))}</div>')


def event_rows(events: list) -> str:
    """8-K events as a newest-first timeline instead of a grid of green boxes."""
    rows = []
    for e in sorted(events, key=lambda e: str(e.get("event_date", "")), reverse=True):
        rows.append(f'<div class="irt-event"><div class="date">{esc(e.get("event_date", ""))}</div><div>'
                    f'<p class="irt-card-body" style="margin:0">{chip(e.get("category", ""), "info")}&nbsp; {esc(e.get("takeaway", ""))}</p>'
                    f'{_excerpt(e.get("quote", ""))}</div></div>')
    return f'<div class="irt-card">{"".join(rows)}</div>'


def progress_strip(statuses: dict) -> str:
    """statuses: {ticker: (state, detail)}, state in queued / working / done / failed."""
    style = {"queued": ("neutral", "○"), "working": ("info", "●"), "done": ("positive", "✓"), "failed": ("negative", "✕")}
    chips = []
    for ticker, (state, detail) in statuses.items():
        tone, mark = style[state]
        chips.append(chip(f"{mark} {ticker} · {detail}", tone))
    return f'<div class="irt-progress" role="status" aria-live="polite">{"".join(chips)}</div>'


def skeleton(ticker: str, status: str) -> str:
    """Placeholder shaped like one ticker's results: header, metric tiles, chart, two card columns.
    The status line is real text (screen readers announce it); the gray blocks are aria-hidden."""
    def block(h, w="100%", mt=0):
        return f'<div class="sk" style="height:{h}px;width:{w};margin-top:{mt}px"></div>'
    tiles = '<div class="sk-row" style="grid-template-columns:2fr 3fr 1fr;gap:12px">' + "".join(
        block(78) for _ in range(3)) + "</div>"
    cards = "".join(block(118, mt=10) for _ in range(3))
    cols = (f'<div class="sk-row" style="grid-template-columns:1fr 1fr;gap:16px;margin-top:22px">'
            f'<div>{block(20, "40%")}{cards}</div><div>{block(20, "40%")}{cards}</div></div>')
    return (f'<div role="status" aria-live="polite" aria-busy="true">'
            f'<p class="sk-status">{esc(ticker)} · {esc(status)}</p>'
            f'<div aria-hidden="true">{block(26, "38%")}{block(14, "24%", 8)}<div style="height:14px"></div>'
            f'{tiles}{block(480, mt=16)}{cols}</div></div>')
