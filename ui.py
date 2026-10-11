"""Page styling and HTML components for the SEC Filing Research Terminal:
CSS built from theme.py tokens, skeleton loaders, a run-progress strip, the metrics panel, and
finding and 8-K rows.

Every piece of AI or filing text goes through esc() before it reaches HTML. Filings and model
output can contain "<", "&" or "$", and unsafe_allow_html=True renders whatever it's given.
"""
from __future__ import annotations

import html
import re

import streamlit as st

import sec_data
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


# Column-count classes for the metrics panel (see the CSS comment there); up to 6 tiles per panel
_GRID_CSS = " ".join(f".irt-cols-{n} {{ grid-template-columns: repeat({n}, minmax(0, 1fr)); }} "
                     f".irt-span-{n} {{ grid-column: span {n}; }}" for n in range(1, 7))


def inject_css() -> None:
    tone_css = "\n".join(
        f".tone-{name} {{ --tone-edge: {edge}; --tone-text: {text}; --tone-bg: {bg}; }}"
        for name, (edge, text, bg) in TONES.items()
    )
    st.markdown(f"""<style>
:root {{
  --bg: {T.BG}; --surface: {T.SURFACE}; --surface-hover: {T.SURFACE_HOVER}; --border: {T.BORDER};
  --border-strong: {T.BORDER_STRONG}; --link: {T.INFO_TEXT};
  --text: {T.TEXT}; --text-strong: {T.TEXT_STRONG}; --text-muted: {T.TEXT_MUTED}; --accent: {T.ACCENT};
  --font: {T.FONT_STACK};
}}
{tone_css}

/* One font everywhere. Before, paragraphs, headings/lists and metrics each used a different font. */
.stApp, .stApp div, .stApp span, .stApp p, .stApp li, .stApp a, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp h5, .stApp label, .stApp input, .stApp button, .stApp summary {{ font-family: var(--font); }}
.stApp code, .stApp pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
.stApp {{ background: var(--bg); }}
/* Streamlit draws a red-to-yellow gradient line across the top of every app; it carries no meaning */
[data-testid="stDecoration"] {{ display: none; }}
/* Streamlit's default top padding is about 6rem; the toolbar should sit near the top */
.main .block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; }}
/* Page header: title, then a one-line description under it. A div, not an h1: Streamlit adds a
   link-anchor icon to markdown headings, which pushed the description sideways. */
.irt-header {{ margin: 0 0 14px 0; }}
.irt-title {{ font-size: 1.4rem; font-weight: 700; color: var(--text-strong); line-height: 1.25; letter-spacing: -0.01em; }}
.irt-header .irt-sub {{ color: var(--text-muted); font-size: 0.85rem; margin-top: 2px; }}
p.irt-subtitle {{ color: var(--text-muted); margin: 0; font-size: 0.85rem; }}

/* Buttons: one filled primary action (Run). Everything else, including Download, is outlined and compact. */
.stButton button[kind="secondary"], .stDownloadButton button {{ background: transparent; border: 1px solid var(--border);
  color: var(--text); min-height: 0; padding: 0.3rem 0.85rem; font-size: 0.85rem; white-space: nowrap; }}
.stButton button[kind="secondary"]:hover, .stDownloadButton button:hover {{ background: var(--surface);
  border-color: var(--text-muted); color: var(--text-strong); }}
.stButton button[kind="primary"] {{ font-weight: 600; }}
/* A clicked button keeps focus, and Streamlit draws a heavy ring on it (the outlined Download box). Keep the ring
   for keyboard users only. */
.stButton button:focus:not(:focus-visible), .stDownloadButton button:focus:not(:focus-visible) {{ box-shadow: none; outline: none; }}
/* The results bar: Streamlit columns have fixed widths, so a long label wrapped inside its column. A marker span
   in the row lets CSS size these columns to their content instead. */
[data-testid="stHorizontalBlock"]:has(.irt-mark-results) {{ align-items: center; flex-wrap: wrap; gap: 8px 16px;
  padding: 10px 0; margin-top: 6px; border-top: 1px solid var(--border); }}
[data-testid="stHorizontalBlock"]:has(.irt-mark-results) > [data-testid="column"]:first-child {{ flex: 1 1 260px !important; width: auto !important; }}
[data-testid="stHorizontalBlock"]:has(.irt-mark-results) > [data-testid="column"]:last-child {{ flex: 0 0 auto !important; width: auto !important; }}
/* Streamlit gives each element inside a column a fixed pixel width and gives markdown a negative bottom margin;
   in this row that kept the text column full width and made the button overlap it */
[data-testid="stHorizontalBlock"]:has(.irt-mark-results) > [data-testid="column"] {{ min-width: 0 !important; }}
[data-testid="stHorizontalBlock"]:has(.irt-mark-results) [data-testid="element-container"] {{ width: auto !important; }}
[data-testid="stHorizontalBlock"]:has(.irt-mark-results) [data-testid="stMarkdownContainer"] {{ margin-bottom: 0 !important; }}

/* Tabs */
.stTabs [data-baseweb="tab"] {{ font-weight: 600; }}

/* Cards (notices and failures). No pills or badges anywhere: labels are plain text. */
.irt-card {{ background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--tone-edge, var(--border));
  border-radius: 6px; padding: 12px 14px; margin: 0 0 10px 0; }}
.irt-card-head {{ display: flex; gap: 8px; align-items: baseline; justify-content: space-between; }}
.irt-card-title {{ color: var(--text-strong); font-weight: 600; font-size: 0.95rem; line-height: 1.35; }}
.irt-card-body {{ color: var(--text); font-size: 0.9rem; line-height: 1.5; margin: 6px 0 0 0; }}
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

/* Metrics panel: one grid. Columns: every tile the same width whichever group it's in. Rows: group heading, label,
   value, period; groups and tiles use CSS subgrid, so every label, value and period line sits on the same row across
   the panel even when a heading or period wraps. The source line is said once, at the foot. Column counts are classes,
   not inline CSS variables: Streamlit drops custom properties from inline styles. */
.irt-metrics {{ display: grid; grid-template-rows: auto auto auto auto auto; background: var(--surface);
  border: 1px solid var(--border); border-radius: 6px; margin-bottom: 8px; }}
.irt-group {{ display: grid; grid-template-columns: subgrid; grid-template-rows: subgrid; grid-row: 1 / span 4;
  padding: 14px 0 14px; min-width: 0; }}
.irt-group + .irt-group {{ border-left: 1px solid var(--border); }}
.irt-group-head {{ grid-column: 1 / -1; grid-row: 1; padding: 0 20px 10px; color: var(--text); font-size: 0.85rem; font-weight: 600; }}
.irt-tile {{ display: contents; }}
.irt-tile .lbl, .irt-tile .val, .irt-tile .src {{ padding: 0 20px; min-width: 0; }}
.irt-tile .lbl {{ grid-row: 2; color: var(--text-muted); font-size: 0.78rem; }}
.irt-tile .val {{ grid-row: 3; color: var(--text-strong); font-size: 1.25rem; font-weight: 650; font-variant-numeric: tabular-nums;
  margin-top: 2px; }}
.irt-tile .src {{ grid-row: 4; color: var(--text-muted); font-size: 0.72rem; margin-top: 2px; line-height: 1.35; }}  /* wraps, never clipped */
.irt-metrics-foot {{ grid-column: 1 / -1; grid-row: 5; border-top: 1px solid var(--border); padding: 8px 20px;
  color: var(--text-muted); font-size: 0.72rem; }}
{_GRID_CSS}
/* Narrower screens: groups stack; tiles share three columns so they still line up across groups */
@media (max-width: 900px) {{
  .irt-metrics {{ grid-template-columns: 1fr !important; grid-template-rows: none; }}
  .irt-group {{ grid-column: 1 / -1; grid-row: auto; grid-template-rows: none; grid-template-columns: repeat(3, minmax(0, 1fr)); }}
  .irt-group + .irt-group {{ border-left: 0; border-top: 1px solid var(--border); }}
  .irt-metrics-foot {{ grid-row: auto; }}
}}

/* Finding rows: each finding is its own card, so an expanded one visibly holds its details.
   Expanding needs no rerun (HTML details). */
.irt-list {{ display: flex; flex-direction: column; gap: 8px; margin-bottom: 8px; }}
.irt-row {{ background: var(--surface); border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }}
.irt-row > summary {{ display: grid; grid-template-columns: 1fr auto; gap: 12px; padding: 12px 16px; cursor: pointer; list-style: none; }}
.irt-row > summary::-webkit-details-marker {{ display: none; }}
.irt-row > summary:hover {{ background: var(--surface-hover); }}
.irt-row > summary:focus {{ outline: none; }}
.irt-row > summary:focus-visible {{ outline: 2px solid var(--accent); outline-offset: -2px; }}
/* Open: stronger outline, an accent bar down the left edge of the whole card, and a divider between the row and its details */
.irt-row {{ position: relative; }}
.irt-row[open] {{ border-color: var(--border-strong); }}
.irt-row[open]::before {{ content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--accent); z-index: 1; }}
.irt-row[open] > summary {{ background: var(--surface-hover); }}
/* One line of plain text above the headline: impact, change label, checks */
.irt-row .row-meta {{ color: var(--text-muted); font-size: 0.75rem; font-weight: 600; margin-bottom: 4px; }}
.irt-row .row-meta:empty {{ display: none; }}
.irt-row .row-head {{ color: var(--text-strong); font-weight: 600; font-size: 0.95rem; line-height: 1.35; }}
.irt-row .row-text {{ color: var(--text); font-size: 0.86rem; line-height: 1.5; margin-top: 4px; max-width: 72ch; }}
/* Small headings inside a row ("Potential implication", "Detail", "Filing excerpt"), each on its own line, with the
   content indented beneath a thin rule */
.irt-row .sub-label {{ color: var(--text-muted); font-size: 0.72rem; font-weight: 600; letter-spacing: 0.02em; margin: 0 0 4px 0; }}
.irt-row .impl {{ margin-top: 12px; max-width: 72ch; }}
.irt-row .impl-body, .irt-row .sub-body {{ border-left: 2px solid var(--border); padding-left: 12px; color: var(--text);
  font-size: 0.86rem; line-height: 1.5; }}
.irt-row .irt-sub {{ margin-top: 16px; max-width: 80ch; }}
.stApp .irt-row .sub-body > p:first-child, .stApp .irt-row .sub-body > blockquote:first-child,
.stApp .irt-row .sub-body > ul:first-child {{ margin-top: 0; }}
.stApp .irt-row ul.irt-points {{ margin: 0; padding-left: 1.1rem; }}
.stApp .irt-row ul.irt-points li {{ font-size: 0.86rem; line-height: 1.5; margin: 0 0 4px 0; }}
.irt-row .row-src {{ color: var(--text-muted); font-size: 0.75rem; text-align: right; white-space: nowrap;
  display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }}
/* The toggle says what a click does; the words change with the state (details/summary already tells screen readers) */
.irt-row .toggle {{ color: var(--link); font-weight: 600; }}
.irt-row .toggle::before {{ content: "Show details"; }}
.irt-row[open] .toggle::before {{ content: "Hide details"; }}
.irt-row .toggle::after {{ content: "›"; display: inline-block; margin-left: 6px; transition: transform .15s; }}
.irt-row[open] .toggle::after {{ transform: rotate(90deg); }}
.irt-row .row-body {{ border-top: 1px solid var(--border); margin: 0 16px; padding: 4px 0 16px;
  font-size: 0.86rem; line-height: 1.5; color: var(--text); }}
/* Streamlit's own markdown styles set p and blockquote to 1rem; these selectors outrank them so details aren't
   larger than the row they belong to */
.stApp .irt-row .row-body p, .stApp .irt-row .row-body blockquote {{ font-size: 0.86rem; line-height: 1.5; }}
.stApp .irt-row .row-body p {{ margin: 8px 0 0 0; }}
.stApp .irt-row .row-body p.irt-note {{ font-size: 0.8rem; }}
.irt-row blockquote {{ margin: 10px 0 0 0; padding: 0; border: 0; color: var(--text-muted); font-style: italic; }}
.irt-row a {{ color: var(--link); }}
.irt-row .phone-only {{ display: none; }}
.irt-criteria {{ font-size: 0.8rem; color: var(--text-muted); margin: 0 0 8px 0; }}
.irt-criteria summary {{ cursor: pointer; }}
.irt-criteria ul {{ margin: 6px 0 0 0; padding-left: 1.1rem; line-height: 1.5; }}
@media (prefers-reduced-motion: reduce) {{ .irt-row .toggle::after {{ transition: none; }} }}
/* Phones: a collapsed row is the meta line and headline; summary and implication move into the expanded row */
@media (max-width: 640px) {{
  /* Streamlit's toolbar overlaps the top of the page on phones; this keeps the title clear of it */
  .main .block-container {{ padding-top: 3.2rem; }}
  .irt-row > summary {{ grid-template-columns: 1fr; padding: 12px 14px; }}
  .irt-row .row-src {{ text-align: left; white-space: normal; order: -1; flex-direction: row; justify-content: space-between;
    align-items: baseline; }}
  .irt-row .row-body {{ margin: 0 14px; }}
  .irt-row .desk-only {{ display: none; }}
  .irt-row .phone-only {{ display: block; }}
  /* Two columns: tiles become ordinary blocks, so a third tile wraps to a new row instead of adding a column */
  .irt-group {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .irt-tile {{ display: block; padding: 0 16px 14px; }}
  .irt-tile .lbl, .irt-tile .val, .irt-tile .src {{ padding: 0; }}
  .irt-group-head, .irt-metrics-foot {{ padding-left: 16px; padding-right: 16px; }}
}}

/* Evidence list */
.irt-evidence {{ margin: 10px 0; }}
.irt-evidence.panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 8px 12px; }}
.irt-evidence summary {{ color: var(--text-muted); font-size: 0.85rem; cursor: pointer; }}
.irt-evidence ul {{ list-style: none; padding: 0; margin: 8px 0; }}
.irt-evidence li {{ padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 0.85rem; color: var(--text); }}
.irt-evidence .sid {{ display: inline-block; min-width: 64px; color: var(--text-muted); font-variant-numeric: tabular-nums; }}
.irt-card a, .irt-evidence a {{ color: var(--link); }}
.irt-evidence .ev-status {{ color: var(--text-muted); }}
.irt-evidence .ev-status.problem, .irt-progress .problem {{ color: var(--text-strong); font-weight: 600; }}

/* Numbered lists: unchanged and removed risk-factor paragraphs */
ol.irt-ol {{ margin: 0; padding-left: 1.3rem; }}
ol.irt-ol li {{ color: var(--text); font-size: 0.92rem; line-height: 1.5; margin: 0 0 8px 0; padding-left: 4px; }}

/* Ticker chips in the picker: show the full company name instead of cutting it off */
.stMultiSelect [data-baseweb="tag"] {{ max-width: none; }}
.stMultiSelect [data-baseweb="tag"] span {{ max-width: none; }}

/* Run progress strip */
.irt-progress {{ display: flex; flex-wrap: wrap; gap: 4px 20px; margin: 4px 0 12px 0; color: var(--text-muted); font-size: 0.85rem; }}
.irt-progress b {{ color: var(--text); font-weight: 600; margin-right: 4px; }}

/* Skeleton loaders: gray blocks shaped like the content that's coming, so the layout doesn't jump */
.sk {{ background: var(--surface); animation: sk-pulse 1.6s ease-in-out infinite; border-radius: 6px; }}
@keyframes sk-pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.55; }} }}
@media (prefers-reduced-motion: reduce) {{ .sk {{ animation: none; }} }}
.sk-status {{ color: var(--text-muted); font-size: 0.85rem; margin: 0 0 12px 0; }}
.sk-row {{ display: grid; gap: 8px; }}
</style>""", unsafe_allow_html=True)


def section_header(title: str, count: int | None = None, note: str | None = None) -> str:
    c = f'<span class="irt-count">{count}</span>' if count is not None else ""
    n = f'<div class="irt-note">{esc(note)}</div>' if note else ""
    return f'<div class="irt-h" role="heading" aria-level="3">{esc(title)}{c}</div>{n}'


def company_header(ticker: str, name: str, industry: str) -> str:
    return (f'<div class="irt-company"><span class="tk">{esc(ticker)}</span><span class="nm">{esc(name)}</span>'
            f'<span class="meta">{esc(industry)}</span></div>')


def format_metric(value, unit: str) -> str:
    """Display text for a numeric market-data value; None shows as an em dash."""
    if value is None:
        return "—"
    if unit == "fraction":
        return f"{value * 100:.1f}%"
    if unit == "multiple":
        return f"{value:.1f}x"
    for size, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if abs(value) >= size:
            return f"${value / size:,.2f}{suffix}"
    return f"${value:,.2f}"


def metric_tiles(groups: list) -> str:
    """groups: [(heading, caption, [(label, value, period line), ...]), ...]. One panel; each group spans as many of the
    panel's equal columns as it has tiles. Captions (source and retrieval time) go once in the panel's foot: one line
    when every group shares a source, otherwise one per group."""
    if not groups:
        return ""
    out = []
    for heading, _, tiles in groups:
        cells = "".join(
            f'<div class="irt-tile"><div class="lbl">{esc(lbl)}</div><div class="val">{esc(val)}</div>'
            f'<div class="src">{esc(period)}</div></div>' for lbl, val, period in tiles)
        out.append(f'<section class="irt-group irt-span-{len(tiles)}"><div class="irt-group-head">{esc(heading)}</div>{cells}</section>')
    captions = [c for _, c, _ in groups]
    foot = captions[0] if len(set(captions)) == 1 else " · ".join(f"{h}: {c}" for h, c, _ in groups)
    total = sum(len(t) for _, _, t in groups)
    return (f'<div class="irt-metrics irt-cols-{total}">{"".join(out)}'
            f'<div class="irt-metrics-foot">Source: {esc(foot)}</div></div>')


def notice(title: str, body: str, tone: str = "neutral") -> str:
    return (f'<div class="irt-card tone-{tone}" role="status"><div class="irt-card-title">{esc(title)}</div>'
            f'<p class="irt-card-body">{esc(body)}</p></div>')


IMPACT_NOTE = ("Impact is an AI assessment of magnitude relative to the company, timing and certainty. "
               "A stated dollar figure alone doesn't make an item High.")


def _count(counts: dict, label: str) -> int:
    return sum(v for k, v in counts.items() if k.split(" (")[0] == label)


def trend_note(comparison: dict) -> str:
    if comparison["status"] == "available":
        c = comparison["counts"]
        return (f"Risk factors in the {comparison['current']} compared paragraph by paragraph with the {comparison['prior']}: "
                f"{_count(c, 'NEW')} with no close match, {_count(c, 'CHANGED')} changed, {c.get('REMOVED', 0)} removed, "
                f"{_count(c, 'UNCHANGED')} unchanged. Change labels come from that comparison in code; impact is an AI assessment.")
    return f"No annual comparison. {comparison['reason']}"


def trend_text(item: dict) -> str:
    """The change label for a risk finding, in words, with the code's reason ("Changed since the prior 10-K: edited")."""
    label = T.TREND_CHIP[item["trend"]][1]
    return f"{label}: {item['trend_reason']}" if item.get("trend_reason") else label


def unchanged_list(comparison: dict) -> str:
    """Opening sentences of the paragraphs the code found unchanged. Written by code, not sent to Claude."""
    if comparison["status"] != "available" or not comparison["unchanged"]:
        return ""
    items = "".join(f"<li>{esc(t)}</li>" for t in comparison["unchanged"])
    return (f'<details class="irt-evidence"><summary>Unchanged since the prior 10-K ({len(comparison["unchanged"])})</summary>'
            f'<p class="irt-note">Opening sentences of paragraphs the code found unchanged. They were not sent to Claude.</p>'
            f'<ol class="irt-ol">{items}</ol></details>')


def analysis_banner(a: dict) -> str:
    status = a["response_status"]
    if status == "complete":
        return ""
    body = {
        "incomplete": ("Claude's answer was cut off at the output limit, so some sections are incomplete or missing. "
                       "This answer was not cached; Run analysis tries again."),
        "refused": "Claude declined to answer for these sources. Nothing below is an empty result.",
        "no_output": "Claude returned no structured answer. Run analysis tries again.",
        "failed": f"The analysis didn't run: {a.get('error', 'unknown error')}. Filing evidence and market data are still shown.",
    }[status]
    return notice("Analysis incomplete" if status == "incomplete" else "Analysis unavailable", body, "caution")


_STATUS_LABEL = {"found": "Extracted", "no_material_changes": "No material changes reported", "not_applicable": "Not applicable",
                 "missing": "Section not found", "failed": "Download failed", "none_in_window": "None in window"}
_PROBLEM = {"missing", "failed"}   # shown in stronger text, not color


def evidence_list(coverage: list, comparison: dict, budget: dict | None) -> str:
    """Every source the analysis used or tried to use, with its status and how much of it was sent."""
    sent = [c for c in coverage if c["id"]]
    omitted = sum(c["omitted_chars"] for c in sent)
    total = sum(c["chars"] for c in sent)
    problems = sum(1 for c in coverage if c["status"] in ("missing", "failed"))
    summary = [f"{len(sent)} sources"]
    if omitted:
        summary.append(f"{omitted:,} of {total:,} characters omitted to fit the request budget")
    if problems:
        summary.append(f"{problems} missing or failed")
    summary.append("annual comparison available" if comparison["status"] == "available" else "annual comparison unavailable")
    rows = []
    for c in coverage:
        link = (f'<a href="{esc(c["url"])}" target="_blank" rel="noopener">{esc(c["label"])}</a>' if c.get("url") else "")
        cut = (f' · sent {c["sent_chars"]:,} of {c["chars"]:,} characters' if c["omitted_chars"]
               else (f' · {c["chars"]:,} characters' if c["chars"] else ""))
        note = f'<div class="irt-note" style="margin:2px 0 0 0">{esc(c["note"])}</div>' if c["note"] and c["status"] != "found" else ""
        label = _STATUS_LABEL.get(c["status"], c["status"])
        if c.get("compared"):
            label = "Compared in code, not sent"
        elif c["id"] == "R_CMP":
            label = "Changes sent"
        status = f'<span class="ev-status{" problem" if c["status"] in _PROBLEM and not c.get("compared") else ""}">{esc(label)}</span>'
        rows.append(f'<li><span class="sid">{esc(c["id"] or "–")}</span> {esc(c["role"])} · {status}'
                    f'<div class="irt-note" style="margin:2px 0 0 0">{link}{esc(cut)}</div>{note}</li>')
    if comparison["status"] == "available" and comparison["removed"]:
        removed = "".join(f"<li>{esc(t)}</li>" for t in comparison["removed"])
        rows.append(f'<li><span class="sid">R#</span> Removed since the prior 10-K ({len(comparison["removed"])}), opening sentences'
                    f'<ol class="irt-ol">{removed}</ol></li>')
    tokens = (f'<p class="irt-note">Request: {budget["input_tokens"]:,} input tokens ({budget["count"]}) plus up to '
              f'{budget["output_reserve"]:,} output tokens, within a {budget["limit"]:,}-token budget.</p>' if budget else "")
    return (f'<details class="irt-evidence panel"><summary>Evidence: {esc(" · ".join(summary))}</summary>'
            f'<ul>{"".join(rows)}</ul>{tokens}</details>')


NO_INPUT = {
    "risks": "No usable risk-factor section was found (no 10-K comparison and no 10-Q update), so there was nothing to review.",
    "other_risks": "Management's discussion (MD&A) wasn't found in the latest 10-K or 10-Q, so there was nothing to review.",
    "events": f"No 8-Ks filed in the last {sec_data.EIGHT_K_WINDOW_DAYS} days, so there was nothing to review.",
}


def section_state(sec: dict, name: str) -> str:
    """A message for every section status except a complete list, so missing output never reads as "none found"."""
    status, dropped = sec["status"], len(sec.get("dropped", []))
    msg = {
        "empty": f"Claude reviewed the sources and reported no {name.replace('_', ' ')}.",
        "partial": "Claude's answer was cut off; this list may be incomplete.",
        "missing": "Not available: Claude's answer ended before this section.",
        "invalid": f"Claude's answer for this section didn't pass validation ({dropped} item{'s' * (dropped != 1)} rejected).",
        "no_input": NO_INPUT.get(name, "Nothing was available for this section."),
        "failed": "Not available: the analysis didn't run.",
    }.get(status, "")
    if status == "complete" and dropped:
        msg = f"{dropped} item{'s' * (dropped != 1)} rejected by validation and not shown."
    return f'<p class="irt-note irt-state">{esc(msg)}</p>' if msg else ""


EXCERPT_NOTE = {"matched": "Excerpt check: matched. The quoted words appear in this filing. That does not confirm the "
                           "interpretation above.",
                "not_matched": "Excerpt check: not matched. The code couldn't find these words in the cited filing.",
                "too_short": "Excerpt check: too short to check.",
                "no_quote": "No excerpt given."}


def _section(label: str, inner: str) -> str:
    """A labeled block inside an expanded row: a small heading on its own line, its content indented below."""
    return f'<div class="irt-sub"><div class="sub-label">{esc(label)}</div><div class="sub-body">{inner}</div></div>'


def _excerpt_block(item: dict) -> str:
    """Quote, its check, the caveat, and the source links, shown inside an expanded row. All plain text."""
    src, ex = item.get("source", {}), item.get("excerpt", {})
    elsewhere = f' Found instead in {", ".join(ex["found_in"])}.' if ex.get("found_in") else ""
    link = (f'<a href="{esc(src["url"])}" target="_blank" rel="noopener">{esc(src.get("label", "filing"))}</a>'
            if src.get("url") else esc(src.get("label", "")))
    others = "".join(f'<p class="irt-note">Figures also from {esc(o.get("role", ""))}: '
                     f'<a href="{esc(o["url"])}" target="_blank" rel="noopener">{esc(o.get("label", ""))}</a></p>'
                     for o in item.get("other_sources", []) if o.get("url"))
    check = EXCERPT_NOTE.get(ex.get("status"), "Excerpt not checked.") + elsewhere
    return _section("Filing excerpt",
                    f'<blockquote>{esc(item.get("quote", ""))}</blockquote>'
                    f'<p class="irt-note excerpt-check">{esc(check)}</p>'
                    f'<p class="irt-note">{esc(src.get("role", ""))}: {link}</p>{others}')


CATEGORY_LABELS = {"DEMAND": "Demand", "PRICING_MARGINS": "Pricing and margins", "COSTS_SUPPLY_CHAIN": "Costs and supply chain",
                   "CAPEX_CAPACITY": "Capital spending and capacity", "CAPITAL_ALLOCATION": "Capital allocation",
                   "COMPETITION": "Competition", "REGULATORY_LEGAL": "Regulatory and legal",
                   "FINANCING_LIQUIDITY": "Financing and liquidity", "OPERATIONS": "Operations",
                   "LEADERSHIP_GOVERNANCE": "Leadership and governance", "OTHER": "Other", "LEADERSHIP": "Leadership",
                   "M&A / CONTRACT": "M&A or contract", "FINANCIAL": "Financial", "COMPLIANCE": "Compliance",
                   "OPERATIONAL": "Operational"}


def _wording(item: dict) -> str:
    flags = item.get("wording_flags") or []
    return _section("Wording check", f'<p>{esc(", ".join(flags))} (words the quality standard bans; left as Claude '
                                     'wrote them).</p>') if flags else ""


def _figures_flag(item: dict) -> str:
    """Figures in the finding that the code couldn't find in the cited source. Shown on the row, not hidden:
    some are fair calculations (a percent change), others mean the finding rests on another source."""
    missing = item.get("unsupported_figures") or []
    if not missing:
        return ""
    return _section("Figures to check", f'<p>Not found in the cited source: {esc(", ".join(missing))}.</p>'
                    '<p class="irt-note">Some may be calculations from the source, such as a percent change. '
                    'Check them against the filing.</p>')


_ABBREV = re.compile(r"(\b[A-Z]\.|\b(?:Inc|Corp|Co|Ltd|No|vs|approx|e\.g|i\.e|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\.)$")


def sentences(text: str) -> list[str]:
    """Split AI text into sentences without changing a word. A break after "U.S." or "Inc." is not a sentence end."""
    parts, out = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9$(\"“])", (text or "").strip()), []
    for p in parts:
        if out and _ABBREV.search(out[-1]):
            out[-1] += " " + p
        else:
            out.append(p)
    return [p for p in out if p]


def _paragraphs(text: str) -> str:
    """One sentence: a paragraph. Several: one short point per sentence, so the detail isn't a block of text."""
    parts = sentences(text)
    if len(parts) <= 1:
        return f'<p>{esc(text)}</p>'
    return '<ul class="irt-points">' + "".join(f"<li>{esc(p)}</li>" for p in parts) + "</ul>"


def source_short(src: dict) -> str:
    """'10-Q · quarter ended Jun 27, 2026' for the right-hand side of a row."""
    from datetime import date
    fmt = lambda d: date.fromisoformat(d).strftime("%b %-d, %Y") if d else ""
    form = src.get("form", "")
    if form == "10-K":
        return f"10-K · year ended {fmt(src.get('period'))}"
    if form == "10-Q":
        return f"10-Q · quarter ended {fmt(src.get('period'))}"
    return f"{form} · filed {fmt(src.get('filed'))}" if form else ""


def _row(meta: str, headline: str, text_html: str, src: dict, body: str, kind: str) -> str:
    """meta: one line of plain text above the headline (impact, change label, checks). No pills or badges."""
    return (f'<details class="irt-row" data-kind="{kind}"><summary><div><div class="row-meta">{meta}</div>'
            f'<div class="row-head">{esc(headline)}</div><div class="desk-only">{text_html}</div></div>'
            f'<div class="row-src"><span>{esc(source_short(src))}</span><span class="toggle" aria-hidden="true"></span></div></summary>'
            f'<div class="row-body"><div class="phone-only">{text_html}</div>{body}</div></details>')


IMPACT_TEXT = {"HIGH": "High", "MEDIUM": "Medium", "LOW": "Low", "NOT_ASSESSED": "Not assessed"}


def _meta(parts: list) -> str:
    return " · ".join(esc(p) for p in parts if p)


def finding_row(item: dict, kind: str) -> str:
    """kind: catalyst, risk (risk-factor change) or other_risk. Collapsed: a plain meta line, headline, summary and
    the potential implication as its own labeled block (desktop). Expanded: detail as short points, impact basis,
    checks, quote and source links, each under its own small heading."""
    meta = _meta([f"Impact: {IMPACT_TEXT[item['impact']]}", trend_text(item) if "trend" in item else "",
                  "Figures to check" if item.get("unsupported_figures") else ""])
    text = (f'<div class="row-text">{esc(item["summary"])}</div>'
            f'<div class="impl"><div class="sub-label">Potential implication</div>'
            f'<div class="impl-body">{esc(item["implication"])}</div></div>')
    body = (_section("Detail", _paragraphs(item["detail"]))
            + _section("Impact basis (AI assessment)",
                       f'<p>{esc(item["impact_basis"])}</p>'
                       f'<p class="irt-note">Category: {esc(CATEGORY_LABELS.get(item["category"], item["category"]))}</p>')
            + f'{_figures_flag(item)}{_wording(item)}{_excerpt_block(item)}')
    return _row(meta, item["headline"], text, item.get("source", {}), body, kind)


def findings_list(items: list, kind: str) -> str:
    """Rows ordered High, Medium, Low, Not assessed; within a level, the order the model gave."""
    ordered = sorted(items, key=lambda i: list(IMPACT_TEXT).index(i["impact"]))
    return f'<div class="irt-list">{"".join(finding_row(i, kind) for i in ordered)}</div>' if items else ""


def impact_criteria() -> str:
    return ('<details class="irt-criteria"><summary>How impact is rated (AI assessment)</summary><ul>'
            '<li>High: likely to change company-level revenue, margins, cash flow or liquidity materially within about two years, '
            'and described as committed, under way or highly likely.</li>'
            '<li>Medium: a plausible company-level effect that is smaller, later or less certain. Low: limited or contained.</li>'
            '<li>Not assessed: the source doesn\'t give enough to judge. A dollar figure alone doesn\'t make an item High.</li></ul></details>')


# Form 8-K item names, from the SEC's Form 8-K instructions. EDGAR lists each filing's items, so this label is a
# fact about the filing, not a judgment by Claude. 9.01 (exhibits) accompanies most 8-Ks and is shown only when alone.
EIGHT_K_ITEMS = {
    "1.01": "Material agreement entered", "1.02": "Material agreement terminated", "1.03": "Bankruptcy or receivership",
    "1.05": "Cybersecurity incident", "2.01": "Acquisition or disposition completed", "2.02": "Results of operations",
    "2.03": "New financial obligation", "2.04": "Obligation accelerated", "2.05": "Exit or disposal costs",
    "2.06": "Material impairment", "3.01": "Delisting notice", "3.02": "Unregistered sale of equity",
    "3.03": "Change to shareholder rights", "4.01": "Auditor change", "4.02": "Prior financial statements not to be relied on",
    "5.01": "Change in control", "5.02": "Director or officer change", "5.03": "Bylaw or fiscal-year change",
    "5.07": "Shareholder vote results", "7.01": "Regulation FD disclosure", "8.01": "Other events",
    "9.01": "Financial statements and exhibits"}


def eight_k_items(items: str) -> str:
    """'5.02,9.01' -> 'Item 5.02 · Director or officer change'. Empty when EDGAR lists no items."""
    codes = [c.strip() for c in (items or "").split(",") if c.strip()]
    shown = [c for c in codes if c != "9.01"] or codes
    return " · ".join(f"Item {c} {EIGHT_K_ITEMS[c]}" if c in EIGHT_K_ITEMS else f"Item {c}" for c in shown)


def event_list(events: list) -> str:
    """8-K events, newest first, dated by EDGAR's filing date. The label above each headline is the 8-K item from
    EDGAR. Claude's category (one of five fixed choices) isn't shown: it repeated the headline and looked like a fact
    the code had checked. It stays in the Excel export."""
    rows = []
    for e in sorted(events, key=lambda e: e["source"].get("filed", ""), reverse=True):
        meta = _meta([eight_k_items(e["source"].get("items", "")), "Figures to check" if e.get("unsupported_figures") else ""])
        text = f'<div class="row-text">{esc(e["summary"])}</div>'
        rows.append(_row(meta, e["headline"], text, e["source"], f'{_figures_flag(e)}{_wording(e)}{_excerpt_block(e)}', "event"))
    return f'<div class="irt-list">{"".join(rows)}</div>' if rows else ""


# The spending guard skips a ticker without anything having gone wrong, so it isn't shown as failed
SKIP_MESSAGES = {
    "daily": "Today's limit for live analyses is reached. It resets at midnight ET. The saved AAPL and STRL sample works now.",
    "monthly": "The monthly AI budget for this demo is used up.",
}
SKIP_LABELS = {"daily": "skipped, daily limit reached", "monthly": "skipped, monthly AI budget used up"}


def progress_strip(statuses: dict) -> str:
    """statuses: {ticker: (state, detail)}, state in queued / working / done / partial / skipped / failed. One line
    of plain text; a failed or partial ticker is in stronger text, not a colored pill. Skipped isn't a problem."""
    parts = []
    for ticker, (state, detail) in statuses.items():
        strong = " problem" if state in ("failed", "partial") else ""
        parts.append(f'<span class="prog{strong}"><b>{esc(ticker)}</b> {esc(detail or state)}</span>')
    return f'<div class="irt-progress" role="status" aria-live="polite">{"".join(parts)}</div>'


def skeleton(ticker: str, status: str) -> str:
    """Placeholder shaped like one ticker's results: header, metrics panel, chart, evidence bar, finding rows.
    The status line is real text (screen readers announce it); the gray blocks are aria-hidden."""
    def block(h, w="100%", mt=0):
        return f'<div class="sk" style="height:{h}px;width:{w};margin-top:{mt}px"></div>'
    tiles = block(104)   # the metrics panel: one block, like the panel itself
    rows = "".join(block(64, mt=6) for _ in range(6))
    return (f'<div role="status" aria-live="polite" aria-busy="true">'
            f'<p class="sk-status">{esc(ticker)} · {esc(status)}</p>'
            f'<div aria-hidden="true">{block(26, "38%")}{block(14, "24%", 8)}<div style="height:14px"></div>'
            f'{tiles}{block(420, mt=16)}{block(38, mt=16)}{block(20, "30%", 22)}{rows}</div></div>')
