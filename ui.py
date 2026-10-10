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
/* Streamlit's default top padding is about 6rem; the toolbar should sit near the top */
.main .block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; }}
.irt-header {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 14px; margin: 0 0 10px 0; }}
h1.irt-title {{ font-size: 1.3rem; font-weight: 650; color: var(--text-strong); margin: 0; padding: 0; letter-spacing: -0.01em; }}
.irt-header .irt-sub {{ color: var(--text-muted); font-size: 0.85rem; }}
p.irt-subtitle {{ color: var(--text-muted); margin: 2px 0 10px 0; font-size: 0.85rem; }}

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
  padding: 0 8px; border-radius: 999px; color: var(--tone-text); background: var(--tone-bg); max-width: 100%; }}
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
.irt-group-label {{ color: var(--text-muted); font-size: 0.78rem; font-weight: 600; margin-bottom: 6px; }}
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

/* Finding rows: one compact row per finding; expanding needs no rerun (HTML details) */
.irt-list {{ border: 1px solid var(--border); border-radius: 6px; background: var(--surface); margin-bottom: 8px; }}
.irt-row {{ border-top: 1px solid var(--border); }}
.irt-row:first-child {{ border-top: 0; }}
.irt-row > summary {{ display: grid; grid-template-columns: 1fr auto; gap: 12px; padding: 10px 14px; cursor: pointer; list-style: none; }}
.irt-row > summary::-webkit-details-marker {{ display: none; }}
.irt-row > summary:hover {{ background: var(--surface-hover); }}
.irt-row .badges {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 4px; }}
.irt-row .row-head {{ color: var(--text-strong); font-weight: 600; font-size: 0.95rem; line-height: 1.35; }}
.irt-row .row-text {{ color: var(--text); font-size: 0.86rem; line-height: 1.45; margin-top: 3px; }}
.irt-row .impl-label {{ color: var(--text-muted); font-weight: 600; }}
.irt-row .row-src {{ color: var(--text-muted); font-size: 0.75rem; text-align: right; white-space: nowrap; }}
.irt-row .chev {{ display: inline-block; margin-left: 8px; transition: transform .15s; }}
.irt-row[open] .chev {{ transform: rotate(90deg); }}
.irt-row .row-body {{ padding: 0 14px 14px; font-size: 0.86rem; line-height: 1.5; color: var(--text); }}
.irt-row .row-body p {{ margin: 6px 0 0 0; }}
.irt-row blockquote {{ margin: 8px 0 0 0; padding: 6px 10px; border-left: 2px solid var(--border); color: var(--text-muted); }}
.irt-row a {{ color: {T.INFO_TEXT}; }}
.irt-row .phone-only {{ display: none; }}
.irt-criteria {{ font-size: 0.8rem; color: var(--text-muted); margin: 0 0 8px 0; }}
.irt-criteria summary {{ cursor: pointer; }}
.irt-criteria ul {{ margin: 6px 0 0 0; padding-left: 1.1rem; line-height: 1.5; }}
@media (prefers-reduced-motion: reduce) {{ .irt-row .chev {{ transition: none; }} }}
/* Phones: a collapsed row is badges and headline; summary and implication move into the expanded row */
@media (max-width: 640px) {{
  .main .block-container {{ padding-top: 1.2rem; }}
  .irt-row > summary {{ grid-template-columns: 1fr; }}
  .irt-row .row-src {{ text-align: left; white-space: normal; order: -1; }}
  .irt-row .desk-only {{ display: none; }}
  .irt-row .phone-only {{ display: block; }}
  .irt-tiles {{ grid-auto-flow: row; grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}

/* Evidence list */
.irt-evidence {{ margin: 10px 0; }}
.irt-evidence.panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 8px 12px; }}
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
.sk {{ background: var(--surface); animation: sk-pulse 1.6s ease-in-out infinite; border-radius: 6px; }}
@keyframes sk-pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.55; }} }}
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
            f'<ol class="irt-questions">{items}</ol></details>')


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
        label, tone = _STATUS_LABEL.get(c["status"], c["status"]), _STATUS_TONE.get(c["status"], "neutral")
        if c.get("compared"):
            label, tone = "Compared in code, not sent", "neutral"
        elif c["id"] == "R_CMP":
            label = "Changes sent"
        rows.append(f'<li><span class="sid">{esc(c["id"] or "–")}</span> {esc(c["role"])} {chip(label, tone)}'
                    f'<div class="irt-note" style="margin:2px 0 0 0">{link}{esc(cut)}</div>{note}</li>')
    if comparison["status"] == "available" and comparison["removed"]:
        removed = "".join(f"<li>{esc(t)}</li>" for t in comparison["removed"])
        rows.append(f'<li><span class="sid">R#</span> Removed since the prior 10-K ({len(comparison["removed"])}), opening sentences'
                    f'<ol class="irt-questions">{removed}</ol></li>')
    tokens = (f'<p class="irt-note">Request: {budget["input_tokens"]:,} input tokens ({budget["count"]}) plus up to '
              f'{budget["output_reserve"]:,} output tokens, within a {budget["limit"]:,}-token budget.</p>' if budget else "")
    return (f'<details class="irt-evidence panel"><summary>Evidence: {esc(" · ".join(summary))}</summary>'
            f'<ul>{"".join(rows)}</ul>{tokens}</details>')


def section_state(sec: dict, name: str) -> str:
    """A message for every section status except a complete list, so missing output never reads as "none found"."""
    status, dropped = sec["status"], len(sec.get("dropped", []))
    msg = {
        "empty": f"Claude reviewed the sources and reported no {name.replace('_', ' ')}.",
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


def _excerpt_block(item: dict) -> str:
    """Quote, its check, the caveat, and the source links, shown inside an expanded row."""
    src, ex = item.get("source", {}), item.get("excerpt", {})
    label = {"matched": ("Excerpt matched", "positive"),
             "not_matched": ("Excerpt not matched in the cited source", "caution"),
             "too_short": ("Excerpt too short to check", "neutral"),
             "no_quote": ("No excerpt given", "neutral")}.get(ex.get("status"), ("Excerpt not checked", "neutral"))
    elsewhere = f' Found instead in {", ".join(ex["found_in"])}.' if ex.get("found_in") else ""
    link = (f'<a href="{esc(src["url"])}" target="_blank" rel="noopener">{esc(src.get("label", "filing"))}</a>'
            if src.get("url") else esc(src.get("label", "")))
    others = "".join(f'<p class="irt-note" style="margin:2px 0 0 0">Figures also from {esc(o.get("role", ""))}: '
                     f'<a href="{esc(o["url"])}" target="_blank" rel="noopener">{esc(o.get("label", ""))}</a></p>'
                     for o in item.get("other_sources", []) if o.get("url"))
    return (f'<blockquote>{esc(item.get("quote", ""))}</blockquote>'
            f'<div class="irt-chips">{chip(label[0], label[1])}</div>'
            f'<p class="irt-note" style="margin:6px 0 0 0">The quoted words appear in this filing. That does not confirm the '
            f'interpretation above.{esc(elsewhere)}</p>'
            f'<p class="irt-note" style="margin:4px 0 0 0">{esc(src.get("role", ""))}: {link}</p>{others}')


CATEGORY_LABELS = {"DEMAND": "Demand", "PRICING_MARGINS": "Pricing and margins", "COSTS_SUPPLY_CHAIN": "Costs and supply chain",
                   "CAPEX_CAPACITY": "Capital spending and capacity", "CAPITAL_ALLOCATION": "Capital allocation",
                   "COMPETITION": "Competition", "REGULATORY_LEGAL": "Regulatory and legal",
                   "FINANCING_LIQUIDITY": "Financing and liquidity", "OPERATIONS": "Operations",
                   "LEADERSHIP_GOVERNANCE": "Leadership and governance", "OTHER": "Other", "LEADERSHIP": "Leadership",
                   "M&A / CONTRACT": "M&A or contract", "FINANCIAL": "Financial", "COMPLIANCE": "Compliance",
                   "OPERATIONAL": "Operational"}


def _wording(item: dict) -> str:
    flags = item.get("wording_flags") or []
    return (f'<p class="irt-note" style="margin:6px 0 0 0">Wording check: {esc(", ".join(flags))} '
            "(words the quality standard bans; left as Claude wrote them).</p>" if flags else "")


def _figures_flag(item: dict) -> str:
    """Figures in the finding that the code couldn't find in the cited source. Shown on the card, not hidden:
    some are fair calculations (a percent change), others mean the finding rests on another source."""
    missing = item.get("unsupported_figures") or []
    if not missing:
        return ""
    return (f'<div class="irt-chips">{chip("Figures not found in the cited source: " + ", ".join(missing), "caution")}</div>'
            '<p class="irt-note" style="margin:4px 0 0 0">Some may be calculations from the source, such as a percent change. Check them against the filing.</p>')


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


def _impact_chip(item: dict, kind: str) -> str:
    tones = T.CATALYST_IMPACT_TONE if kind == "catalyst" else T.IMPACT_TONE
    label = "Not assessed" if item["impact"] == "NOT_ASSESSED" else f"{item['impact'].title()} impact"
    return chip(f"{label} · AI assessment", tones.get(item["impact"], "neutral"))


def _row(badges: str, headline: str, text_html: str, src: dict, body: str, kind: str) -> str:
    return (f'<details class="irt-row" data-kind="{kind}"><summary><div><div class="badges">{badges}</div>'
            f'<div class="row-head">{esc(headline)}</div><div class="desk-only">{text_html}</div></div>'
            f'<div class="row-src">{esc(source_short(src))}<span class="chev" aria-hidden="true">›</span></div></summary>'
            f'<div class="row-body"><div class="phone-only">{text_html}</div>{body}</div></details>')


def finding_row(item: dict, kind: str) -> str:
    """kind: catalyst, risk (risk-factor change) or other_risk. Collapsed: badges, headline, summary and
    potential implication (desktop). Expanded: detail, impact basis, checks, quote and source links."""
    badges = _impact_chip(item, kind)
    if "trend" in item:
        badges += chip(trend_text(item), T.TREND_CHIP[item["trend"]][0])
    if item.get("unsupported_figures"):
        badges += chip("Figures to check", "caution")
    text = (f'<div class="row-text">{esc(item["summary"])}</div>'
            f'<div class="row-text"><span class="impl-label">Potential implication:</span> {esc(item["implication"])}</div>')
    body = (f'<p>{esc(item["detail"])}</p>'
            f'<p class="irt-note" style="margin:6px 0 0 0">{esc(CATEGORY_LABELS.get(item["category"], item["category"]))} · '
            f'Impact basis (AI assessment): {esc(item["impact_basis"])}</p>'
            f'{_figures_flag(item)}{_wording(item)}{_excerpt_block(item)}')
    return _row(badges, item["headline"], text, item.get("source", {}), body, kind)


def findings_list(items: list, kind: str) -> str:
    return f'<div class="irt-list">{"".join(finding_row(i, kind) for i in items)}</div>' if items else ""


def impact_criteria() -> str:
    return ('<details class="irt-criteria"><summary>How impact is rated (AI assessment)</summary><ul>'
            '<li>High: likely to change company-level revenue, margins, cash flow or liquidity materially within about two years, '
            'and described as committed, under way or highly likely.</li>'
            '<li>Medium: a plausible company-level effect that is smaller, later or less certain. Low: limited or contained.</li>'
            '<li>Not assessed: the source doesn\'t give enough to judge. A dollar figure alone doesn\'t make an item High.</li></ul></details>')


def event_list(events: list) -> str:
    """8-K events, newest first, dated by EDGAR's filing date."""
    rows = []
    for e in sorted(events, key=lambda e: e["source"].get("filed", ""), reverse=True):
        badges = chip(CATEGORY_LABELS.get(e["category"], e["category"]), "info")
        if e.get("unsupported_figures"):
            badges += chip("Figures to check", "caution")
        text = f'<div class="row-text">{esc(e["summary"])}</div>'
        rows.append(_row(badges, e["headline"], text, e["source"], f'{_figures_flag(e)}{_wording(e)}{_excerpt_block(e)}', "event"))
    return f'<div class="irt-list">{"".join(rows)}</div>' if rows else ""


def question_list(questions: list) -> str:
    items = "".join(f'<li>{esc(q["question"])} <span class="irt-note">{esc(source_short(q.get("source", {})))}</span></li>'
                    for q in questions)
    return f"<ol class='irt-questions'>{items}</ol>" if items else ""


def progress_strip(statuses: dict) -> str:
    """statuses: {ticker: (state, detail)}, state in queued / working / done / partial / failed."""
    tones = {"queued": "neutral", "working": "info", "done": "positive", "partial": "caution", "failed": "negative"}
    chips = []
    for ticker, (state, detail) in statuses.items():
        chips.append(chip(f"{ticker} · {detail or state}", tones[state]))
    return f'<div class="irt-progress" role="status" aria-live="polite">{"".join(chips)}</div>'


def skeleton(ticker: str, status: str) -> str:
    """Placeholder shaped like one ticker's results: header, metric tiles, chart, evidence bar, finding rows.
    The status line is real text (screen readers announce it); the gray blocks are aria-hidden."""
    def block(h, w="100%", mt=0):
        return f'<div class="sk" style="height:{h}px;width:{w};margin-top:{mt}px"></div>'
    tiles = '<div class="sk-row" style="grid-template-columns:2fr 3fr 1fr;gap:12px">' + "".join(
        block(78) for _ in range(3)) + "</div>"
    rows = "".join(block(64, mt=6) for _ in range(6))
    return (f'<div role="status" aria-live="polite" aria-busy="true">'
            f'<p class="sk-status">{esc(ticker)} · {esc(status)}</p>'
            f'<div aria-hidden="true">{block(26, "38%")}{block(14, "24%", 8)}<div style="height:14px"></div>'
            f'{tiles}{block(420, mt=16)}{block(38, mt=16)}{block(20, "30%", 22)}{rows}</div></div>')
