"""Claude analysis of SEC evidence: what gets sent, how it fits a token budget, and how the answer is checked.

No Streamlit and no network calls here. app.py makes the API calls and passes results in, so tests
call these exact functions.

Two things are tracked separately and never merged:
- input coverage: which sources were found, failed, not applicable, or cut to fit the budget
- response completeness: whether Claude's answer was complete, cut off, refused, or malformed
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import compare
import sec_data

MODEL = "claude-sonnet-5"
MAX_OUTPUT_TOKENS = 12000      # sized so a worst-case call fits the $0.25/day cap (budget.py); real answers used 4,867-6,765
REQUEST_TOKEN_BUDGET = 76_000  # whole request: prompt + tool schema + evidence + MAX_OUTPUT_TOKENS (64K input)
TOOL_NAME = "record_filing_findings"

IMPACTS = ["HIGH", "MEDIUM", "LOW", "NOT_ASSESSED"]
# Trend is set by code from the paragraph a risk cites (compare.py), never by the model
TRENDS = ["NEW", "CHANGED", "REMOVED", "QUARTERLY_UPDATE", "NOT_COMPARED"]
CATEGORIES = ["DEMAND", "PRICING_MARGINS", "COSTS_SUPPLY_CHAIN", "CAPEX_CAPACITY", "CAPITAL_ALLOCATION",
              "COMPETITION", "REGULATORY_LEGAL", "FINANCING_LIQUIDITY", "OPERATIONS", "LEADERSHIP_GOVERNANCE", "OTHER"]
EVENT_CATEGORIES = ["LEADERSHIP", "M&A / CONTRACT", "FINANCIAL", "COMPLIANCE", "OPERATIONAL"]
MAX_FINDINGS = 5               # per list; keeps the answer inside MAX_OUTPUT_TOKENS
MAX_OTHER_RISKS = 3            # risks from management's discussion, not compared to last year
FINDING_SECTIONS = ("catalysts", "risks", "other_risks")
SECTIONS = FINDING_SECTIONS + ("events",)


# --- Evidence ----------------------------------------------------------------------------------

@dataclass
class Source:
    """One block of evidence, or a placeholder explaining why a block is absent."""
    id: str                 # R_CUR, R_PRIOR, QU1.., MDA, K8_1..  ("" for placeholders)
    role: str               # what it is, in words
    status: str             # found | no_material_changes | not_applicable | missing | failed | none_in_window
    filing: dict = field(default_factory=dict)   # form, filed, period, accession, url, index_url, label
    text: str = ""          # full extracted text
    sent_text: str = ""     # what was sent after the token budget
    note: str = ""
    compared: bool = False  # annual risk factors compared in code: sent as R_CMP, not directly
    extra: dict = field(default_factory=dict)    # R_CMP: paragraph labels, counts, unchanged and removed lists

    @property
    def sendable(self) -> bool:
        return bool(self.id) and self.status in ("found", "no_material_changes") and bool(self.text) and not self.compared

    def coverage(self) -> dict:
        return {"id": self.id, "role": self.role, "status": self.status, "note": self.note, "compared": self.compared, **self.filing,
                "chars": len(self.text), "sent_chars": len(self.sent_text),
                "omitted_chars": len(self.text) - len(self.sent_text) if self.sendable else 0}


def _filing_meta(f: sec_data.Filing) -> dict:
    return {"form": f.form, "filed": f.filed, "period": f.period, "accession": f.accession,
            "url": f.url, "index_url": f.index_url, "label": f.label}


def build_sources(selection: sec_data.Selection, texts: dict) -> list[Source]:
    """texts maps accession -> filing text (str), or an Exception if the download failed.
    Returns every source with a status, including placeholders for what is missing or not applicable."""
    out = []

    def section_source(sid, role, filing, item):
        if filing is None:
            return None
        meta = _filing_meta(filing)
        got = texts.get(filing.accession)
        if isinstance(got, Exception) or got is None:
            return Source(sid, role, "failed", meta, note=f"Download failed: {got}" if got else "Not downloaded.")
        sec = sec_data.find_section(got, item, filing.form)
        note = sec.note + (" Incorporates an earlier 10-Q by reference; earlier 10-Qs since the 10-K are included."
                           if sec.references_earlier_10q else "")
        return Source(sid, role, sec.status, meta, text=sec.text if sec.usable else "", note=note)

    cur = selection.annual_current
    out.append(section_source("R_CUR", "Risk factors, latest annual report", cur, "1a")
               or Source("", "Risk factors, latest annual report", "missing", note=" ".join(selection.notes)))
    out.append(section_source("R_PRIOR", "Risk factors, prior annual report", selection.annual_prior, "1a")
               or Source("", "Risk factors, prior annual report", "missing", note=" ".join(selection.notes)))
    r_cur, r_prior = out[0], out[1]
    if r_cur.status == "found" and r_prior.status == "found":
        comp = compare.compare_sections(sec_data.split_paragraphs(r_cur.text), sec_data.split_paragraphs(r_prior.text))
        for s in (r_cur, r_prior):
            s.compared = True
            s.note = (s.note + " Compared paragraph by paragraph in code; only new, changed and removed "
                      "paragraphs are sent (R_CMP).").strip()
        out.append(Source("R_CMP", "Risk factors: changes since the prior 10-K", "found", dict(r_cur.filing),
                          text=compare.render_for_prompt(comp), extra={
                              "labels": compare.paragraph_labels(comp), "counts": comp.counts(),
                              "unchanged": [compare.first_sentence(p.text) for p in comp.paragraphs if p.label == "UNCHANGED"],
                              "removed": [compare.first_sentence(p.text) for p in comp.removed],
                              "prior_filing": dict(r_prior.filing)}))
    if selection.quarterly_updates:
        for i, q in enumerate(selection.quarterly_updates, 1):
            out.append(section_source(f"QU{i}", "Risk factor updates, quarterly report", q, "1a"))
    else:
        out.append(Source("", "Risk factor updates, quarterly report", "not_applicable",
                          note="No 10-Q filed since the latest 10-K."))
    m = selection.mdna_source
    out.append(section_source("MDA", "Management's discussion and analysis", m, "7" if m and m.form == "10-K" else "2")
               or Source("", "Management's discussion and analysis", "missing", note="No 10-K or 10-Q found."))
    if selection.eight_ks:
        for i, k in enumerate(selection.eight_ks, 1):
            got = texts.get(k.accession)
            meta = _filing_meta(k) | {"items": k.items}
            if isinstance(got, Exception) or got is None:
                out.append(Source(f"K8_{i}", "Current report (8-K)", "failed", meta, note=f"Download failed: {got}"))
            else:
                out.append(Source(f"K8_{i}", "Current report (8-K)", "found", meta, text=got))
    else:
        out.append(Source("", "Current reports (8-K)", "none_in_window",
                          note=f"No 8-K filed in the last {sec_data.EIGHT_K_WINDOW_DAYS} days."))
    return out


def comparison_status(sources: list[Source]) -> dict:
    """Whether the annual comparison ran, with both reporting periods and the code's paragraph counts."""
    by_id = {s.id: s for s in sources if s.id}
    cur, prior, cmp_ = by_id.get("R_CUR"), by_id.get("R_PRIOR"), by_id.get("R_CMP")
    labels = {"current": cur.filing.get("label") if cur else None, "prior": prior.filing.get("label") if prior else None}
    if cmp_:
        x = cmp_.extra
        return {"status": "available", **labels, "reason": "", "counts": x["counts"], "unchanged": x["unchanged"],
                "removed": x["removed"], "prior_url": x["prior_filing"].get("url")}
    missing = [s for s in sources if s.role.startswith("Risk factors") and s.status != "found"]
    status = "failed" if any(s.status == "failed" for s in missing) else "missing"
    reason = " ".join(f"{s.role}: {s.status.replace('_', ' ')}. {s.note}".strip() for s in missing)
    return {"status": status, **labels, "reason": reason}


# --- Request -----------------------------------------------------------------------------------

def risk_source_ids(sources: list[Source]) -> list[str]:
    """Risks come only from risk-factor sources: the code comparison (or the current 10-K section when no
    comparison ran) and the 10-Q updates."""
    return [s.id for s in sources if s.sendable and (s.id in ("R_CMP", "R_CUR") or s.id.startswith("QU"))]


def tool_schema(sources: list[Source]) -> dict:
    ids = [s.id for s in sources if s.sendable]
    k8_ids = [i for i in ids if i.startswith("K8_")] or ["NONE"]
    text = lambda d: {"type": "string", "description": d}
    finding = {
        "headline": text("The finding as a short factual statement, at most 14 words. Not a topic label."),
        "summary": text("What the filing says, at most 35 words, with figures and periods when given."),
        "implication": text("The potential implication for the business, at most 30 words. Hedged, not a prediction."),
        "detail": text("Supporting explanation, at most 60 words."),
        "category": {"type": "string", "enum": CATEGORIES},
        "impact": {"type": "string", "enum": IMPACTS},
        "impact_basis": text("One sentence: magnitude relative to the company, timing, and certainty."),
        "source_id": {"type": "string", "enum": ids},
        "quote": text("Words copied exactly from that source, at most 40 words. '...' between non-adjacent fragments, in order."),
    }
    finding_req = list(finding)
    # Optional: every other source a figure in the finding comes from (Jack's rule, Oct 10)
    finding["other_source_ids"] = {"type": "array", "items": {"type": "string", "enum": ids},
                                   "description": "Other sources that figures in this finding come from. Empty if all come from source_id."}
    risk = dict(finding, source_id={"type": "string", "enum": risk_source_ids(sources) or ["NONE"]},
                paragraph_id=text("For a finding from R_CMP: the [P#] or [R#] ID of the paragraph it is based on. Otherwise empty."))
    return {
        "name": TOOL_NAME,
        "description": "Record findings from the SEC filing sources provided.",
        "input_schema": {
            "type": "object",
            "properties": {
                "catalysts": {"type": "array", "maxItems": MAX_FINDINGS,
                              "items": {"type": "object", "properties": finding, "required": finding_req}},
                "risks": {"type": "array", "maxItems": MAX_FINDINGS,
                          "items": {"type": "object", "properties": risk, "required": finding_req}},
                "other_risks": {"type": "array", "maxItems": MAX_OTHER_RISKS, "items": {"type": "object",
                                "properties": dict(finding, source_id={"type": "string", "enum": ["MDA"] if "MDA" in ids else ["NONE"]}),
                                "required": finding_req}},
                "events": {"type": "array", "maxItems": max(1, len(k8_ids)), "items": {"type": "object", "properties": {
                    "source_id": {"type": "string", "enum": k8_ids},
                    "category": {"type": "string", "enum": EVENT_CATEGORIES},
                    "headline": text("At most 14 words."), "summary": text("At most 35 words."),
                    "quote": text("Words copied exactly from that 8-K, at most 40 words.")},
                    "required": ["source_id", "category", "headline", "summary", "quote"]}},
            },
            "required": ["catalysts", "risks", "other_risks", "events"],
        },
    }


BANNED_WORDS = ["powerful", "robust", "seamless", "cutting-edge", "next-gen", "leverage (as a verb)", "unlock", "elevate",
                "comprehensive", "insights", "intelligent", "AI-powered", "institutional-grade", "game-changing",
                "surged", "plunged", "skyrocketed", "soared", "crashed", "buy", "undervalued", "target price"]


def build_prompt(ticker: str, company: str, sources: list[Source], comparison: dict) -> str:
    blocks = []
    for s in sources:
        if not s.sendable:
            continue
        cut = (f" Only part of this block fits the request budget ({len(s.sent_text):,} of {len(s.text):,} characters); "
               "the rest was omitted." if len(s.sent_text) < len(s.text) else "")
        status = " The filing states there were no material changes." if s.status == "no_material_changes" else ""
        label = s.filing.get("label", "")
        if s.id == "R_CMP":
            label = f"{comparison['current']}, compared with the {comparison['prior']}"
        blocks.append(f"[{s.id}] {s.role}: {label}.{status}{cut}\n{s.sent_text}")
    if comparison["status"] == "available":
        comp = ("R_CMP lists only the risk-factor paragraphs that code found to be new, changed or removed since the prior "
                "10-K; unchanged paragraphs are not sent. The labels are set by code. For a risk from R_CMP, set "
                "paragraph_id to the [P#] or [R#] it is based on and describe what changed. Quote only current text, "
                "never the removed words; for a removed paragraph, quote its opening sentence. NEW means the code found "
                "no close match in the prior 10-K's text, which can also mean heavy rewording: do not call it a new risk.")
    else:
        comp = "No annual comparison is available, so describe risks without saying whether they are new or changed."
    return f"""You are summarizing SEC filings for {company} ({ticker}) for an equity research record.
Write plainly and precisely. Give every figure with its period. Do not use these words: {", ".join(BANNED_WORDS)}.
Do not describe movements as surging, plunging, soaring or crashing; state the numbers instead. No investment recommendations.

Use only the sources below. Each finding is based on one source: set source_id to its ID, and copy
quote word for word from that source. Up to {MAX_FINDINGS} catalysts and {MAX_FINDINGS} risks, the most significant first.
"risks" come only from risk-factor sources (R_CMP, R_CUR, QU). A risk that appears only in management's discussion
goes in "other_risks" (up to {MAX_OTHER_RISKS}, source_id MDA). Never cite a source that reports no material changes
as evidence for a finding. When a finding uses a figure, cite the source where that figure appears: source_id for the
main source, and other_source_ids for every other source a figure comes from.

{comp}

Impact is your assessment and is shown to readers as an AI assessment.
- Judge magnitude relative to this company (share of revenue, operating income, cash or assets when the
  source gives figures), how soon it could matter, and how certain it is.
- A dollar figure or percentage on its own does not make an item HIGH.
- HIGH: likely to change company-level revenue, margins, cash flow or liquidity materially within about
  two years, and described as committed, under way or highly likely.
- MEDIUM: a plausible company-level effect that is smaller, later or less certain.
- LOW: a limited or contained effect.
- NOT_ASSESSED: the source does not give enough to judge.
State the reason in impact_basis.

QU sources are risk-factor updates in 10-Qs filed since the 10-K. A source marked "no material changes"
contains nothing to extract. Events: at most one per 8-K source, only material events; skip an 8-K with none.

SOURCES

{chr(10).join(chr(10) + b for b in blocks)}
"""


CMP_SHARE = 0.6   # the comparison may use up to 60% of the evidence allowance before other sources are trimmed


def _trim(text: str, limit: int, at_entries: bool = False) -> str:
    """Cut to `limit` characters at a sentence end, or for R_CMP at a paragraph entry, never mid-entry."""
    if len(text) <= limit:
        return text
    if at_entries:
        stop = text.rfind("\n[", 0, limit)
        return text[:stop] if stop > 0 else ""
    cut = text[:limit]
    stop = cut.rfind(". ")
    return cut[:stop + 1] if stop > limit * 0.8 else cut


def water_fill(sizes: dict, total: int) -> dict:
    """Split `total` characters across sources: each gets an equal share, and any share a small
    source doesn't need is passed to the larger ones."""
    alloc, left, budget = {}, dict(sizes), max(0, total)
    while left:
        share = budget // len(left)
        small = {k: v for k, v in left.items() if v <= share}
        if not small:
            alloc.update({k: share for k in left})
            break
        for k, v in small.items():
            alloc[k] = v
            budget -= v
            del left[k]
    return alloc


def fit_to_budget(ticker: str, company: str, sources: list[Source], count_tokens, budget: int = REQUEST_TOKEN_BUDGET) -> dict:
    """Set each source's sent_text so the whole request fits `budget` tokens, measured with
    count_tokens(prompt, tool) -> int (the Anthropic token-counting endpoint in the app).
    Returns {"prompt", "tool", "input_tokens", "count_calls", "budget"}; omissions are recorded on each source."""
    comparison = comparison_status(sources)
    tool = tool_schema(sources)
    sendable = [s for s in sources if s.sendable]
    input_budget = budget - MAX_OUTPUT_TOKENS
    for s in sendable:
        s.sent_text = s.text
    prompt = build_prompt(ticker, company, sources, comparison)
    tokens, calls = count_tokens(prompt, tool), 1
    if tokens <= input_budget:
        return {"prompt": prompt, "tool": tool, "input_tokens": tokens, "count_calls": calls, "budget": budget}

    for s in sendable:
        s.sent_text = ""
    base = count_tokens(build_prompt(ticker, company, sources, comparison), tool)
    calls += 1
    evidence_chars = sum(len(s.text) for s in sendable)
    chars_per_token = evidence_chars / max(1, tokens - base)
    allowance = int((input_budget - base) * chars_per_token)
    for _ in range(4):
        rest, left = [s for s in sendable if s.id != "R_CMP"], allowance
        for s in sendable:
            if s.id == "R_CMP":
                s.sent_text = _trim(s.text, min(len(s.text), int(allowance * CMP_SHARE) if rest else allowance), at_entries=True)
                left -= len(s.sent_text)
        shares = water_fill({s.id: len(s.text) for s in rest}, left)
        for s in rest:
            s.sent_text = _trim(s.text, shares[s.id])
        prompt = build_prompt(ticker, company, sources, comparison)
        tokens = count_tokens(prompt, tool)
        calls += 1
        if tokens <= input_budget:
            break
        allowance = int(allowance * input_budget / tokens * 0.97)
    else:
        raise ValueError(f"Could not fit the request in {budget:,} tokens ({tokens:,} input tokens after trimming).")
    return {"prompt": prompt, "tool": tool, "input_tokens": tokens, "count_calls": calls, "budget": budget}


# --- Excerpt matching --------------------------------------------------------------------------
# Documented normalization, applied to both the quote and the source before comparing:
NORMALIZATION_RULES = [
    "curly quotes and apostrophes become straight ones",
    "en and em dashes and the minus sign become hyphens",
    "non-breaking and zero-width spaces become spaces; runs of whitespace become one space",
    "the ellipsis character becomes '...', which separates fragments",
    "upper and lower case are treated as the same",
    "punctuation and quote marks at the very start or end of a fragment are ignored",
]
_TRANSLATE = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-", "−": "-",
                            " ": " ", " ": " ", "​": " ", "…": "..."})
MIN_EXCERPT_WORDS = 6


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.translate(_TRANSLATE)).strip().lower()


def excerpt_fragments(quote: str) -> list[str]:
    parts = re.split(r"\s*(?:\[\s*\.\.\.\s*\]|\.\s?\.\s?\.)\s*", normalize(quote))
    return [p.strip(" \"'.,;:") for p in parts if p.strip(" \"'.,;:")]


def match_excerpt(quote: str, source_text: str) -> dict:
    """Do the quote's fragments appear, in order, in the source? Matching proves the words are in the
    filing; it does not show that the finding's interpretation of them is right."""
    frags = excerpt_fragments(quote or "")
    if not frags:
        return {"status": "no_quote", "fragments": 0, "matched": 0}
    if sum(len(f.split()) for f in frags) < MIN_EXCERPT_WORDS:
        return {"status": "too_short", "fragments": len(frags), "matched": 0}
    hay, pos, matched = normalize(source_text), 0, 0
    for f in frags:
        i = hay.find(f, pos)
        if i < 0:
            break
        pos, matched = i + len(f), matched + 1
    status = "matched" if matched == len(frags) else "not_matched"
    return {"status": status, "fragments": len(frags), "matched": matched}


# --- Response checks ---------------------------------------------------------------------------

def response_status(stop_reason: str | None, tool_input) -> str:
    if stop_reason == "max_tokens":
        return "incomplete"
    if stop_reason == "refusal":
        return "refused"
    if stop_reason == "tool_use" and isinstance(tool_input, dict):
        return "complete"
    return "no_output"


# Section 1 words of the quality standard. "leverage" is flagged only outside its financial senses.
_BANNED_RE = re.compile(r"\b(powerful|robust|seamless|cutting-edge|next-gen|unlock\w*|elevat(?:e|es|ing)|comprehensive|insights?|"
                        r"intelligent|ai-powered|institutional-grade|game-changing|surg(?:e|ed|ing)|plung\w*|skyrocket\w*|"
                        r"soar\w*|crash\w*|undervalued|target price|leverag(?:e|es|ed|ing))\b", re.I)
_FINANCIAL_LEVERAGE = re.compile(r"leverage (ratio|covenant|level)|(operating|financial|net|gross|debt) leverage|"
                                 r"leverage (of|at|to) \d|\d(\.\d+)?x\b", re.I)   # any ratio like 2.00x nearby


_NEW_RISK_CLAIM = re.compile(r"\bnew(?:ly)?\s+(?:added\s+|disclosed\s+|introduced\s+)?risks?(?:\s+factors?)?\b|"
                             r"\bnewly\s+(?:added|disclosed|introduced|cited)\b", re.I)

# --- Figures: does every figure in a finding appear in the source it cites? ------------------------
# Formats are normalized before comparing: $14.7M = 14.7 million = $14,700 thousand; 15% = 15.0% = 15 percent.
# A figure counts as found when it equals a source figure within the rounding of the less precise one.
# Unscaled source numbers also count in thousands and millions, because filing tables say "(in millions)" once
# in a header. Dates, years, form names and item numbers are not figures. A miss is flagged, not rejected:
# some figures are fair calculations (a percent change).
_MONTHS = "january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec"
_NOT_FIGURES = re.compile(
    rf"\b(?:{_MONTHS})\.?\s+\d{{1,2}}(?!\d)(?:st|nd|rd|th)?(?:,\s*\d{{4}})?|\b(?:{_MONTHS})\.?\s+\d{{4}}|\b(?:q[1-4]|h[12])\s*(?:fy)?'?\d{{0,4}}\b|"
    r"\b(?:fy|fiscal(?:\s+year)?)\s*'?\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b|"
    r"\b(?:form\s+)?(?:10-k|10-q|8-k|20-f|6-k|s-\d|def\s*14a)\b|\b(?:item|section|rule|note|part|article|chapter|tier|level)\s+\d+[a-z]?(?:\.\d+)?\b|"
    r"\b\d+(?:st|nd|rd|th)\b|\b(?:covid|ex)-\d+\b", re.I)
_FIGURE = re.compile(r"(?P<usd>\$\s?)?(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
                     r"(?P<unit>%|percent\b|per\s+cent\b|basis\s+points?\b|bps\b|x\b|trillion\b|billion\b|million\b|"
                     r"thousand\b|bn\b|mm\b|[tbmk]\b)?", re.I)
_SCALE = {"trillion": 1e12, "t": 1e12, "billion": 1e9, "bn": 1e9, "b": 1e9, "million": 1e6, "mm": 1e6, "m": 1e6,
          "thousand": 1e3, "k": 1e3}


def _figures(text: str) -> list[tuple]:
    """(kind, value, tolerance, as written) for each figure. kind: percent, bps, multiple or amount."""
    text = _NOT_FIGURES.sub(" ", text)
    out = []
    for m in _FIGURE.finditer(text):
        raw, unit = m.group("num"), (m.group("unit") or "").lower().replace(" ", "")
        value = float(raw.replace(",", ""))
        decimals = len(raw.split(".")[1]) if "." in raw else 0
        if unit in ("%", "percent", "percent"):
            kind, scale = "percent", 1
        elif unit in ("basispoint", "basispoints", "bps"):
            kind, scale = "bps", 1
        elif unit == "x":
            kind, scale = "multiple", 1
        else:
            kind, scale = "amount", _SCALE.get(unit, 1)
            if not m.group("usd") and scale == 1 and (value < 13 and decimals == 0 or 1900 <= value <= 2100 and decimals == 0):
                continue   # counts like "3 segments", and years, aren't checked
        out.append((kind, value * scale, 0.5 * 10 ** -decimals * scale, m.group(0).strip()))
    return out


def unsupported_figures(item: dict, source_texts: list[str]) -> list[str]:
    """Figures in the finding's headline, summary or detail that don't appear in its cited source."""
    have = []
    for kind, value, tol, _ in (f for t in source_texts for f in _figures(t)):
        have.append((kind, value, tol))
        if kind == "amount" and tol == 0.5 and value >= 1000:      # unscaled table number: maybe in thousands or millions
            have += [(kind, value * 1e3, tol * 1e3), (kind, value * 1e6, tol * 1e6)]
    missing = []
    for key in ("headline", "summary", "detail"):
        for kind, value, tol, written in _figures(item.get(key) or ""):
            if not any(k == kind and abs(v - value) <= max(t, tol) + 1e-9 * abs(value) for k, v, t in have):
                if written not in missing:
                    missing.append(written)
    return missing


def wording_flags(item: dict) -> list[str]:
    """Banned words in an AI-written finding. Marked for the reader, not deleted: the text stays as Claude wrote it."""
    flags = []
    for key in ("headline", "summary", "implication", "detail", "impact_basis"):
        text = item.get(key) or ""
        for m in _BANNED_RE.finditer(text):
            if m.group(0).lower().startswith("leverag") and _FINANCIAL_LEVERAGE.search(text[max(0, m.start() - 40):m.end() + 40]):
                continue
            flags.append(f"{key}: {m.group(0)}")
        for m in _NEW_RISK_CLAIM.finditer(text):
            flags.append(f"{key}: '{m.group(0)}' (the code found only no close match in the prior 10-K's text)")
    return flags


def _excerpt_haystack(src: Source, item: dict, all_by_id: dict) -> str:
    """Where a quote must appear. R_CMP findings quote the 10-K itself: the current section, or the prior
    one for a removed paragraph."""
    if src.id != "R_CMP":
        return src.sent_text
    label = src.extra["labels"].get(item.get("paragraph_id", ""), ("", ""))[0]
    return all_by_id["R_PRIOR" if label == "REMOVED" else "R_CUR"].text


def _check_finding(item, kind, sources_by_id, all_by_id) -> tuple[dict | None, str]:
    if not isinstance(item, dict):
        return None, "not an object"
    needed = ["headline", "summary", "implication", "detail", "impact_basis", "quote"]
    blank = [k for k in needed if not isinstance(item.get(k), str) or not item[k].strip()]
    if blank:
        return None, f"missing {', '.join(blank)}"
    if item.get("category") not in CATEGORIES:
        return None, f"unknown category {item.get('category')!r}"
    if item.get("impact") not in IMPACTS:
        return None, f"unknown impact {item.get('impact')!r}"
    src = sources_by_id.get(item.get("source_id"))
    if src is None:
        return None, f"unknown source {item.get('source_id')!r}"
    if src.status == "no_material_changes":
        return None, f"cites {src.id}, which reports no material changes and so can't support a finding"
    others = item.get("other_source_ids") or []
    if not isinstance(others, list) or any(o not in sources_by_id for o in others):
        return None, f"unknown source in other_source_ids {others!r}"
    if any(sources_by_id[o].status == "no_material_changes" for o in others):
        return None, "other_source_ids include a source that reports no material changes"
    if kind == "other_risks" and src.id != "MDA":
        return None, f"other risk cites {src.id}; this group is for management's discussion (MDA) only"
    out = dict(item)
    if kind == "risks":
        if not (src.id in ("R_CMP", "R_CUR") or src.id.startswith("QU")):
            return None, f"risk cites {src.id}, which is not a risk-factor source"
        if src.id == "R_CMP":
            pid = item.get("paragraph_id") or ""
            if pid not in src.extra["labels"]:
                return None, f"unknown paragraph {pid!r} in R_CMP"
            out["trend"], out["trend_reason"] = src.extra["labels"][pid]
        else:
            out["trend"], out["trend_reason"] = ("QUARTERLY_UPDATE" if src.id.startswith("QU") else "NOT_COMPARED"), ""
    out["source"] = src.filing | {"id": src.id, "role": src.role}
    if src.id == "R_CMP" and out.get("trend") == "REMOVED":
        out["source"] = src.extra["prior_filing"] | {"id": src.id, "role": src.role}
    out["excerpt"] = match_excerpt(item["quote"], _excerpt_haystack(src, item, all_by_id))
    if out["excerpt"]["status"] == "not_matched":
        elsewhere = [s.id for s in sources_by_id.values() if s.id != src.id
                     and match_excerpt(item["quote"], s.sent_text)["status"] == "matched"]
        out["excerpt"]["found_in"] = elsewhere
    out["wording_flags"] = wording_flags(out)
    seen = ([src.sent_text] + ([all_by_id["R_CUR"].text, all_by_id["R_PRIOR"].text] if src.id == "R_CMP" else [])
            + [sources_by_id[o].sent_text for o in others])
    out["other_sources"] = [sources_by_id[o].filing | {"id": o, "role": sources_by_id[o].role} for o in others if o != src.id]
    out["unsupported_figures"] = unsupported_figures(out, seen)
    return out, ""


def _check_event(item, sources_by_id) -> tuple[dict | None, str]:
    if not isinstance(item, dict):
        return None, "not an object"
    blank = [k for k in ("headline", "summary", "quote") if not isinstance(item.get(k), str) or not item[k].strip()]
    if blank:
        return None, f"missing {', '.join(blank)}"
    if item.get("category") not in EVENT_CATEGORIES:
        return None, f"unknown category {item.get('category')!r}"
    src = sources_by_id.get(item.get("source_id"))
    if src is None or not src.id.startswith("K8_"):
        return None, f"unknown 8-K source {item.get('source_id')!r}"
    return dict(item, source=src.filing | {"id": src.id, "role": src.role},
                excerpt=match_excerpt(item["quote"], src.sent_text), wording_flags=wording_flags(item),
                unsupported_figures=unsupported_figures(item, [src.sent_text])), ""


def check_response(stop_reason: str | None, tool_input, sources: list[Source]) -> dict:
    """Section-by-section result. Section status:
    complete (items present) | empty (complete answer, genuinely no items) | partial (cut-off answer, some items) |
    missing (cut-off answer, nothing for this section) | invalid (wrong type in a complete answer) |
    no_input (nothing was sent that this section could use, e.g. no 8-Ks)."""
    status = response_status(stop_reason, tool_input)
    by_id = {s.id: s for s in sources if s.sendable}
    all_by_id = {s.id: s for s in sources if s.id}
    comparison = comparison_status(sources)
    data = tool_input if isinstance(tool_input, dict) else {}
    sections = {}
    for name in SECTIONS:
        raw = data.get(name)
        if ((name == "events" and not any(i.startswith("K8_") for i in by_id)) or (name == "risks" and not risk_source_ids(sources))
                or (name == "other_risks" and "MDA" not in by_id)):
            sections[name] = {"status": "no_input", "items": [], "dropped": []}
            continue
        if raw is None:
            sections[name] = {"status": "missing", "items": [], "dropped": []}
            continue
        if not isinstance(raw, list):
            sections[name] = {"status": "invalid" if status == "complete" else "missing", "items": [], "dropped": []}
            continue
        items, dropped = [], []
        for i, it in enumerate(raw):
            if name in FINDING_SECTIONS:
                ok, why = _check_finding(it, name, by_id, all_by_id)
            else:
                ok, why = _check_event(it, by_id)
            (items.append(ok) if ok else dropped.append({"index": i, "reason": why}))
        if status == "complete":
            sec_status = "complete" if items else ("empty" if not dropped else "invalid")
        else:
            sec_status = "partial" if items else "missing"
        sections[name] = {"status": sec_status, "items": items, "dropped": dropped}
    return {"response_status": status, "stop_reason": stop_reason, "comparison": comparison, "sections": sections}


def failed_result(sources: list[Source], reason: str) -> dict:
    """The analysis couldn't run (API error, budget couldn't be met). Every section says so;
    none of them reads as an empty result."""
    return {"response_status": "failed", "stop_reason": None, "error": reason, "comparison": comparison_status(sources),
            "sections": {n: {"status": "failed", "items": [], "dropped": []} for n in SECTIONS}}


def is_cacheable(checked: dict) -> bool:
    """Only a complete answer whose every section is usable may be cached."""
    return checked["response_status"] == "complete" and all(
        s["status"] in ("complete", "empty", "no_input") for s in checked["sections"].values())


def request_fingerprint(prompt: str, tool: dict) -> str:
    """Stable text for st.cache_data to key the Claude call on."""
    return json.dumps({"model": MODEL, "max_tokens": MAX_OUTPUT_TOKENS, "prompt": prompt, "tool": tool}, sort_keys=True)
