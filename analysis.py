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

import sec_data

MODEL = "claude-sonnet-5"
MAX_OUTPUT_TOKENS = 16000      # Jack's call, Oct 10. Non-streaming: the SDK refuses above ~21,333 (10-minute rule)
REQUEST_TOKEN_BUDGET = 60_000  # whole request: prompt + tool schema + evidence + MAX_OUTPUT_TOKENS
TOOL_NAME = "record_filing_findings"

IMPACTS = ["HIGH", "MEDIUM", "LOW", "NOT_ASSESSED"]
TRENDS = ["NEW", "ESCALATED", "UNCHANGED", "NOT_COMPARED"]
CATEGORIES = ["DEMAND", "PRICING_MARGINS", "COSTS_SUPPLY_CHAIN", "CAPEX_CAPACITY", "CAPITAL_ALLOCATION",
              "COMPETITION", "REGULATORY_LEGAL", "FINANCING_LIQUIDITY", "OPERATIONS", "LEADERSHIP_GOVERNANCE", "OTHER"]
EVENT_CATEGORIES = ["LEADERSHIP", "M&A / CONTRACT", "FINANCIAL", "COMPLIANCE", "OPERATIONAL"]
MAX_FINDINGS = 5               # per list; keeps the answer inside MAX_OUTPUT_TOKENS


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

    @property
    def sendable(self) -> bool:
        return bool(self.id) and self.status in ("found", "no_material_changes") and bool(self.text)

    def coverage(self) -> dict:
        return {"id": self.id, "role": self.role, "status": self.status, "note": self.note, **self.filing,
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
    """Whether annual trend labels can be assigned, with both reporting periods."""
    by_id = {s.id: s for s in sources if s.id}
    cur, prior = by_id.get("R_CUR"), by_id.get("R_PRIOR")
    labels = {"current": cur.filing.get("label") if cur else None, "prior": prior.filing.get("label") if prior else None}
    if cur and prior and cur.status == "found" and prior.status == "found":
        # "New" means absent from the prior 10-K, which can only be checked if all of it was sent
        partial = 0 < len(prior.sent_text) < len(prior.text)
        share = f"{len(prior.sent_text) / len(prior.text):.0%}" if partial else "100%"
        return {"status": "available", **labels, "reason": "", "prior_partial": partial, "prior_share_sent": share}
    missing = [s for s in sources if s.role.startswith("Risk factors") and s.status != "found"]
    status = "failed" if any(s.status == "failed" for s in missing) else "missing"
    reason = " ".join(f"{s.role}: {s.status.replace('_', ' ')}. {s.note}".strip() for s in missing)
    return {"status": status, **labels, "reason": reason}


# --- Request -----------------------------------------------------------------------------------

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
    risk = dict(finding, trend={"type": "string", "enum": TRENDS})
    return {
        "name": TOOL_NAME,
        "description": "Record findings from the SEC filing sources provided.",
        "input_schema": {
            "type": "object",
            "properties": {
                "catalysts": {"type": "array", "maxItems": MAX_FINDINGS,
                              "items": {"type": "object", "properties": finding, "required": finding_req}},
                "risks": {"type": "array", "maxItems": MAX_FINDINGS,
                          "items": {"type": "object", "properties": risk, "required": finding_req + ["trend"]}},
                "events": {"type": "array", "maxItems": max(1, len(k8_ids)), "items": {"type": "object", "properties": {
                    "source_id": {"type": "string", "enum": k8_ids},
                    "category": {"type": "string", "enum": EVENT_CATEGORIES},
                    "headline": text("At most 14 words."), "summary": text("At most 35 words."),
                    "quote": text("Words copied exactly from that 8-K, at most 40 words.")},
                    "required": ["source_id", "category", "headline", "summary", "quote"]}},
                "questions": {"type": "array", "maxItems": 3, "items": {"type": "object", "properties": {
                    "question": text("A specific question for management, at most 35 words."),
                    "source_id": {"type": "string", "enum": ids}}, "required": ["question", "source_id"]}},
            },
            "required": ["catalysts", "risks", "events", "questions"],
        },
    }


def build_prompt(ticker: str, company: str, sources: list[Source], comparison: dict) -> str:
    blocks = []
    for s in sources:
        if not s.sendable:
            continue
        cut = (f" Only the first {len(s.sent_text):,} of {len(s.text):,} characters are included; the rest was "
               "omitted to fit the request budget." if len(s.sent_text) < len(s.text) else "")
        status = " The filing states there were no material changes." if s.status == "no_material_changes" else ""
        blocks.append(f"[{s.id}] {s.role}: {s.filing.get('label', '')}.{status}{cut}\n{s.sent_text}")
    if comparison["status"] == "available":
        comp = (f"Annual comparison: R_CUR ({comparison['current']}) against R_PRIOR ({comparison['prior']}). "
                "Set trend only for risks whose source_id is R_CUR: NEW = no corresponding risk in R_PRIOR; "
                "ESCALATED = in R_PRIOR, but the current text describes a larger, nearer or more certain effect; "
                "UNCHANGED = substantively the same. Use NOT_COMPARED for risks from any other source.")
    else:
        comp = "No annual comparison is available. Set trend to NOT_COMPARED for every risk."
    return f"""You are summarizing SEC filings for {company} ({ticker}) for an equity research record.
Write plainly and precisely. No promotional or dramatic adjectives, no investment recommendations.

Use only the sources below. Each finding is based on one source: set source_id to its ID, and copy
quote word for word from that source. Up to {MAX_FINDINGS} catalysts and {MAX_FINDINGS} risks, the most significant first.

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
Questions: 3 specific questions for management, each tied to one source.

SOURCES

{chr(10).join(chr(10) + b for b in blocks)}
"""


def _trim(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
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
        shares = water_fill({s.id: len(s.text) for s in sendable}, allowance)
        for s in sendable:
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


def _check_finding(item, kind, sources_by_id, comparison) -> tuple[dict | None, str]:
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
    out = dict(item)
    if kind == "risks":
        allowed = comparison["status"] == "available" and src.id == "R_CUR"
        if item.get("trend") not in TRENDS or (not allowed and item["trend"] != "NOT_COMPARED"):
            out["trend_note"] = f"Model returned {item.get('trend')!r}; set to NOT_COMPARED (no annual comparison for this source)."
            out["trend"] = "NOT_COMPARED"
        elif item["trend"] == "NEW" and comparison.get("prior_partial"):
            out["trend_note"] = (f"Model returned 'NEW', but only {comparison['prior_share_sent']} of the prior 10-K's "
                                 "risk factors were sent, so absence can't be confirmed; set to NOT_COMPARED.")
            out["trend"] = "NOT_COMPARED"
        elif item["trend"] != "NOT_COMPARED" and comparison.get("prior_partial"):
            out["trend_partial"] = True
    out["source"] = src.filing | {"id": src.id, "role": src.role}
    out["excerpt"] = match_excerpt(item["quote"], src.sent_text)
    if out["excerpt"]["status"] == "not_matched":
        elsewhere = [s.id for s in sources_by_id.values() if s.id != src.id
                     and match_excerpt(item["quote"], s.sent_text)["status"] == "matched"]
        out["excerpt"]["found_in"] = elsewhere
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
                excerpt=match_excerpt(item["quote"], src.sent_text)), ""


def _check_question(item, sources_by_id) -> tuple[dict | None, str]:
    if not isinstance(item, dict) or not isinstance(item.get("question"), str) or not item["question"].strip():
        return None, "missing question"
    src = sources_by_id.get(item.get("source_id"))
    return dict(item, source=(src.filing | {"id": src.id, "role": src.role}) if src else {}), ""


def check_response(stop_reason: str | None, tool_input, sources: list[Source]) -> dict:
    """Section-by-section result. Section status:
    complete (items present) | empty (complete answer, genuinely no items) | partial (cut-off answer, some items) |
    missing (cut-off answer, nothing for this section) | invalid (wrong type in a complete answer) |
    no_input (nothing was sent that this section could use, e.g. no 8-Ks)."""
    status = response_status(stop_reason, tool_input)
    by_id = {s.id: s for s in sources if s.sendable}
    comparison = comparison_status(sources)
    data = tool_input if isinstance(tool_input, dict) else {}
    sections = {}
    for name in ("catalysts", "risks", "events", "questions"):
        raw = data.get(name)
        if name == "events" and not any(i.startswith("K8_") for i in by_id):
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
            if name in ("catalysts", "risks"):
                ok, why = _check_finding(it, name, by_id, comparison)
            elif name == "events":
                ok, why = _check_event(it, by_id)
            else:
                ok, why = _check_question(it, by_id)
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
            "sections": {n: {"status": "failed", "items": [], "dropped": []} for n in ("catalysts", "risks", "events", "questions")}}


def is_cacheable(checked: dict) -> bool:
    """Only a complete answer whose every section is usable may be cached."""
    return checked["response_status"] == "complete" and all(
        s["status"] in ("complete", "empty", "no_input") for s in checked["sections"].values())


def request_fingerprint(prompt: str, tool: dict) -> str:
    """Stable text for st.cache_data to key the Claude call on."""
    return json.dumps({"model": MODEL, "max_tokens": MAX_OUTPUT_TOKENS, "prompt": prompt, "tool": tool}, sort_keys=True)
