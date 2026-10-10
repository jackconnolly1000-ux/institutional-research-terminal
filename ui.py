"""Page styling and HTML components for the Institutional Research Terminal:
CSS built from theme.py tokens, skeleton loaders, a run-progress strip, metric tiles, and
catalyst / risk / 8-K cards.

Every piece of AI or filing text goes through esc() before it reaches HTML. Filings and model
output can contain "<", "&" or "$", and unsafe_allow_html=True renders whatever it's given.
"""
from __future__ import annotations

import html

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
.irt-tile .src {{ color: var(--text-muted); font-size: 0.7rem; margin-top: 4px; line-height: 1.35; }}  /* wraps: periods and sources are never clipped */

/* 8-K timeline */
.irt-event {{ display: grid; grid-template-columns: 96px 1fr; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--border); }}
.irt-event:last-child {{ border-bottom: none; }}
.irt-event .date {{ color: var(--text-muted); font-variant-numeric: tabular-nums; font-size: 0.85rem; padding-top: 2px; }}
.irt-event details {{ margin-top: 2px; }}

/* Evidence list */
.irt-evidence {{ margin: 6px 0 4px 0; }}
.irt-evidence summary {{ color: var(--text-muted); font-size: 0.85rem; cursor: pointer; }}
.irt-evidence ul {{ list-style: none; padding: 0; margin: 8px 0; }}
.irt-evidence li {{ padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 0.85rem; color: var(--text); }}
.irt-evidence .sid {{ display: inline-block; min-width: 64px; color: var(--text-muted); font-variant-numeric: tabular-nums; }}
.irt-card a, .irt-evidence a {{ color: var(--accent-text, #7aa2ff); }}
.irt-state.tone-caution {{ color: var(--tone-text); }}

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


def company_header(ticker: str, name: str, industry: str) -> str:
    return (f'<div class="irt-company"><span class="tk">{esc(ticker)}</span><span class="nm">{esc(name)}</span>'
            f'<span class="meta">{esc(industry)}</span></div>')


def format_metric(value, unit: str) -> str:
    """Display text for a numeric market-data value; None shows as an em dash."""
    if value is None:
        return "—"
    if unit == "fraction":
        return f"{value * 100:.2f}%"
    if unit == "multiple":
        return f"{value:.1f}x"
    for size, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if abs(value) >= size:
            return f"${value / size:,.2f}{suffix}"
    return f"${value:,.2f}"


def metric_tiles(groups: list) -> str:
    """groups: [(group label, [(label, value, source), ...]), ...]"""
    out = []
    for group_label, tiles in groups:
        cells = "".join(
            f'<div class="irt-tile"><div class="lbl">{esc(lbl)}</div><div class="val">{esc(val)}</div>'
            f'<div class="src">{esc(src)}</div></div>' for lbl, val, src in tiles)
        out.append(f'<section><div class="irt-group-label">{esc(group_label)}</div><div class="irt-tiles">{cells}</div></section>')
    return f'<div class="irt-metrics">{"".join(out)}</div>'


def notice(title: str, body: str, tone: str = "neutral") -> str:
    return (f'<div class="irt-card tone-{tone}" role="status"><div class="irt-card-title">{esc(title)}</div>'
            f'<p class="irt-card-body">{esc(body)}</p></div>')


IMPACT_NOTE = ("Impact is an AI assessment of magnitude relative to the company, timing and certainty. "
               "A stated dollar figure alone doesn't make an item High.")


def trend_note(comparison: dict) -> str:
    if comparison["status"] == "available":
        partial = (f" Only {comparison['prior_share_sent']} of the prior section fit the request budget, so "
                   "'New' labels are withheld." if comparison.get("prior_partial") else "")
        return (f"Annual trend compares Item 1A of the {comparison['current']} with the {comparison['prior']}.{partial} "
                "Trend labels and impact are AI assessments.")
    return f"Comparison unavailable. {comparison['reason']}"


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
_STATUS_TONE = {"found": "positive", "no_material_changes": "neutral", "not_applicable": "neutral",
                "missing": "caution", "failed": "negative", "none_in_window": "neutral"}


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
        rows.append(f'<li><span class="sid">{esc(c["id"] or "–")}</span> {esc(c["role"])} {chip(_STATUS_LABEL.get(c["status"], c["status"]), _STATUS_TONE.get(c["status"], "neutral"))}'
                    f'<div class="irt-note" style="margin:2px 0 0 0">{link}{esc(cut)}</div>{note}</li>')
    tokens = (f'<p class="irt-note">Request: {budget["input_tokens"]:,} input tokens ({budget["count"]}) plus up to '
              f'{budget["output_reserve"]:,} output tokens, within a {budget["limit"]:,}-token budget.</p>' if budget else "")
    return (f'<details class="irt-evidence"><summary>Evidence: {esc(" · ".join(summary))}</summary>'
            f'<ul>{"".join(rows)}</ul>{tokens}</details>')


def section_state(sec: dict, name: str) -> str:
    """A message for every section status except a complete list, so missing output never reads as "none found"."""
    status, dropped = sec["status"], len(sec.get("dropped", []))
    msg = {
        "empty": f"Claude reviewed the sources and reported no {name}.",
        "partial": "Claude's answer was cut off; this list may be incomplete.",
        "missing": "Not available: Claude's answer ended before this section.",
        "invalid": f"Claude's answer for this section didn't pass validation ({dropped} item{'s' * (dropped != 1)} rejected).",
        "no_input": f"No 8-Ks filed in the last {sec_data.EIGHT_K_WINDOW_DAYS} days, so there was nothing to review.",
        "failed": "Not available: the analysis didn't run.",
    }.get(status, "")
    if status == "complete" and dropped:
        msg = f"{dropped} item{'s' * (dropped != 1)} rejected by validation and not shown."
    tone = "neutral" if status in ("empty", "no_input", "complete") else "caution"
    return f'<p class="irt-note irt-state tone-{tone}">{esc(msg)}</p>' if msg else ""


def _excerpt(item: dict) -> str:
    """Source filing, link, quote and whether the quote's words appear in that filing."""
    src, ex = item.get("source", {}), item.get("excerpt", {})
    label = {"matched": ("Excerpt matched", "positive"),
             "not_matched": ("Excerpt not matched in the cited source", "caution"),
             "too_short": ("Excerpt too short to check", "neutral"),
             "no_quote": ("No excerpt given", "neutral")}.get(ex.get("status"), ("Excerpt not checked", "neutral"))
    elsewhere = (f' Found instead in {", ".join(ex["found_in"])}.' if ex.get("found_in") else "")
    link = (f'<a href="{esc(src["url"])}" target="_blank" rel="noopener">{esc(src.get("label", "filing"))}</a>'
            if src.get("url") else esc(src.get("label", "")))
    return (f'<details><summary>Source and excerpt</summary>'
            f'<p class="irt-card-body">{esc(src.get("role", ""))}: {link}</p>'
            f'<blockquote>{esc(item.get("quote", ""))}</blockquote>'
            f'<div class="irt-chips">{chip(label[0], label[1])}</div>'
            f'<p class="irt-note" style="margin:6px 0 0 0">A match means these words appear in the filing; it does not '
            f'check the interpretation above.{esc(elsewhere)}</p></details>')


def finding_card(item: dict, kind: str) -> str:
    impact = item["impact"]
    tones = T.CATALYST_IMPACT_TONE if kind == "catalyst" else T.IMPACT_TONE
    tone = tones.get(impact, "neutral")
    impact_text = "Not assessed" if impact == "NOT_ASSESSED" else f"{impact.title()} impact"
    chips = chip(f"{impact_text} · AI assessment", tone)
    if kind == "risk":
        trend_tone, trend_label = T.TREND_CHIP[item["trend"]]
        chips += chip(trend_label + (" (partial prior text)" if item.get("trend_partial") else ""), trend_tone)
    chips += chip(item["category"].replace("_", " ").title(), "neutral")
    detail = (f'<details><summary>Detail and impact basis</summary><p class="irt-card-body">{esc(item["detail"])}</p>'
              f'<p class="irt-note" style="margin:6px 0 0 0">Impact basis (AI): {esc(item["impact_basis"])}</p></details>')
    return (f'<div class="irt-card tone-{tone}"><div class="irt-card-title">{esc(item["headline"])}</div>'
            f'<div class="irt-chips">{chips}</div><p class="irt-card-body">{esc(item["summary"])}</p>'
            f'<p class="irt-card-body"><strong>Potential implication:</strong> {esc(item["implication"])}</p>'
            f'{detail}{_excerpt(item)}</div>')


def event_rows(events: list) -> str:
    """8-K events as a newest-first list, dated by the 8-K's filing date from EDGAR."""
    rows = []
    for e in sorted(events, key=lambda e: e["source"].get("filed", ""), reverse=True):
        rows.append(f'<div class="irt-event"><div class="date">{esc(e["source"].get("filed", ""))}</div><div>'
                    f'<p class="irt-card-body" style="margin:0">{chip(e["category"], "info")}&nbsp; <strong>{esc(e["headline"])}</strong> '
                    f'{esc(e["summary"])}</p>{_excerpt(e)}</div></div>')
    return f'<div class="irt-card">{"".join(rows)}</div>'


def progress_strip(statuses: dict) -> str:
    """statuses: {ticker: (state, detail)}, state in queued / working / done / partial / failed."""
    style = {"queued": ("neutral", "○"), "working": ("info", "●"), "done": ("positive", "✓"),
             "partial": ("caution", "!"), "failed": ("negative", "✕")}
    chips = []
    for ticker, (state, detail) in statuses.items():
        tone, mark = style[state]
        chips.append(chip(f"{mark} {ticker}" + (f" · {detail}" if detail else ""), tone))
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
