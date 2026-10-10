"""Paragraph-level comparison of the current and prior 10-K Risk Factors. Labels come from code, not the model.

Method (thresholds locked Oct 10, 2026 after checks on AAPL, FAST, STRL, MSFT, then WMT, JNJ held out):
1. Candidates: the 5 prior paragraphs sharing the most 5-word sequences with the current paragraph.
2. ratio: difflib word-level similarity to each candidate, and to each candidate joined with the next
   paragraph (filers merge paragraphs). jaccard: overlap of content words with the closest prior paragraph.
3. Labels:
   UNCHANGED  ratio >= 0.97 and the same figures (years ignored, so rolled-forward dates don't count)
   CHANGED    ratio >= 0.97 with different figures ("figures changed"), or ratio >= 0.50 ("edited" /
              "text removed"), or content overlap >= 0.30 ("rewritten")
   NEW        none of the above: no close match in the prior 10-K. This is a text test; a heavily
              rewritten paragraph can land here, so the closest prior paragraph is kept as context.
   REMOVED    a prior paragraph that would be NEW if the comparison ran the other way
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

UNCHANGED_RATIO = 0.97
CHANGED_RATIO = 0.50
REWRITE_JACCARD = 0.30
CONTEXT_JACCARD = 0.20      # NEW paragraphs this close to a prior one get it as context
MINOR_RATIO = 0.90          # an edit this small with <= MINOR_WORDS added words is sent as a one-line diff
MINOR_WORDS = 5
_STOP = set("the a an and or of to in for on by with as is are be been may could our we its it their this that "
            "these those from at which such other any can will not have has including".split())
_YEAR = re.compile(r"^(19|20)\d\d$")


def words(text: str) -> list[str]:
    """Lowercase word tokens. A trailing period is dropped ("sales." = "sales"); decimals like 3.5 stay whole."""
    t = text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"})).lower()
    return [w.rstrip(".") for w in re.findall(r"[a-z0-9$%.]+", t) if w.rstrip(".")]


def _scored(w: list[str]) -> list[str]:
    """Tokens for similarity scoring: years become one placeholder, so a rolled-forward date isn't an edit."""
    return ["<year>" if _YEAR.match(x) else x for x in w]


def _shingles(w: list[str], k: int = 5) -> set:
    return {tuple(w[i:i + k]) for i in range(max(1, len(w) - k + 1))}


def _content(w: list[str]) -> set:
    return {x for x in w if x not in _STOP and len(x) > 2}


def _figures(w: list[str]) -> list[str]:
    return sorted(x for x in w if re.search(r"\d", x) and not _YEAR.match(x.strip(".,%$")))


@dataclass
class Paragraph:
    text: str
    label: str                      # NEW | CHANGED | UNCHANGED | REMOVED
    reason: str = ""                # figures changed | edited | text removed | rewritten | minor edit
    ratio: float = 0.0
    jaccard: float = 0.0
    prior: str = ""                 # matched prior text (CHANGED), or closest prior paragraph (NEW, if close enough)
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


def _diff(prior_w: list[str], cur_w: list[str]) -> tuple[list[str], list[str]]:
    ops = difflib.SequenceMatcher(None, prior_w, cur_w, autojunk=False).get_opcodes()
    added = [" ".join(cur_w[j1:j2]) for t, i1, i2, j1, j2 in ops if t in ("insert", "replace")]
    removed = [" ".join(prior_w[i1:i2]) for t, i1, i2, j1, j2 in ops if t in ("delete", "replace")]
    return added, removed


def _classify(current: list[str], prior: list[str]) -> list[Paragraph]:
    pw = [_scored(words(p)) for p in prior]
    psh = [_shingles(w) for w in pw]
    pc = [_content(w) for w in pw]
    out = []
    for text in current:
        w = _scored(words(text))
        sh, c = _shingles(w), _content(w)
        best_ratio, best = 0.0, None
        for i in sorted(range(len(pw)), key=lambda i: -len(sh & psh[i]))[:5]:
            for idx in ((i,), (i, i + 1)) if i + 1 < len(pw) else ((i,),):
                joined = [x for j in idx for x in pw[j]]
                r = difflib.SequenceMatcher(None, w, joined, autojunk=False).ratio()
                if r > best_ratio:
                    best_ratio, best = r, idx
        jac = [len(c & pc[i]) / max(1, len(c | pc[i])) for i in range(len(pc))]
        closest = max(range(len(pc)), key=jac.__getitem__) if pc else None
        jaccard = jac[closest] if pc else 0.0
        matched = " ".join(prior[i] for i in best) if best else ""
        mw = _scored(words(matched))
        if best_ratio >= UNCHANGED_RATIO and _figures(w) == _figures(mw):
            para = Paragraph(text, "UNCHANGED", ratio=best_ratio, jaccard=jaccard, prior=matched)
        elif best_ratio >= CHANGED_RATIO:
            added, removed = _diff(words(matched), words(text))
            only_numbers = all(re.search(r"\d", x) for x in " ".join(added + removed).split())
            if best_ratio >= UNCHANGED_RATIO or only_numbers:
                reason = "figures changed"
            elif not added:
                reason = "text removed"
            elif best_ratio >= MINOR_RATIO and _figures(w) == _figures(mw) and sum(len(a.split()) for a in added) <= MINOR_WORDS:
                reason = "minor edit"
            else:
                reason = "edited"
            para = Paragraph(text, "CHANGED", reason, best_ratio, jaccard, matched, added, removed)
        elif jaccard >= REWRITE_JACCARD:
            added, removed = _diff(words(prior[closest]), words(text))
            para = Paragraph(text, "CHANGED", "rewritten", best_ratio, jaccard, prior[closest], added, removed)
        else:
            context = prior[closest] if closest is not None and jaccard >= CONTEXT_JACCARD else ""
            para = Paragraph(text, "NEW", ratio=best_ratio, jaccard=jaccard, prior=context)
        out.append(para)
    return out


@dataclass
class Comparison:
    paragraphs: list[Paragraph]     # current paragraphs, in filing order
    removed: list[Paragraph]        # prior paragraphs with no counterpart, in filing order

    def counts(self) -> dict:
        out = {}
        for p in self.paragraphs:
            key = p.label + (f" ({p.reason})" if p.reason else "")
            out[key] = out.get(key, 0) + 1
        out["REMOVED"] = len(self.removed)
        return out


def compare_sections(current: list[str], prior: list[str]) -> Comparison:
    """current and prior are paragraph lists (sec_data.split_paragraphs)."""
    removed = [Paragraph(p.text, "REMOVED", ratio=p.ratio, jaccard=p.jaccard)
               for p in _classify(prior, current) if p.label == "NEW"]
    return Comparison(_classify(current, prior), removed)


def first_sentence(text: str, limit: int = 240) -> str:
    sentence = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    return sentence if len(sentence) <= limit else sentence[:limit].rsplit(" ", 1)[0] + " …"


def render_for_prompt(comp: Comparison) -> str:
    """The comparison as Claude sees it: each changed, new or removed paragraph with a code-assigned ID and label.
    Unchanged paragraphs are not sent. Quotes must come from the current text, never from [-removed-] parts."""
    lines = []
    for n, p in enumerate(comp.paragraphs, 1):
        pid = f"P{n}"
        if p.label == "UNCHANGED":
            continue
        if p.label == "NEW":
            ctx = f"\n   Closest prior paragraph, for context only: {p.prior}" if p.prior else ""
            lines.append(f"[{pid}] NEW (no close match in the prior 10-K): {p.text}{ctx}")
        elif p.reason == "minor edit":
            lines.append(f"[{pid}] CHANGED (minor edit): added: {' | '.join(p.added)} / removed: {' | '.join(p.removed) or '-'}"
                         f" (in the paragraph beginning: {first_sentence(p.text, 90)})")
        else:
            delta = f"added: {' | '.join(p.added) or '-'} / removed: {' | '.join(p.removed) or '-'}"
            lines.append(f"[{pid}] CHANGED ({p.reason}): {p.text}\n   {delta}")
    for n, p in enumerate(comp.removed, 1):
        lines.append(f"[R{n}] REMOVED (in the prior 10-K, no counterpart now): {first_sentence(p.text)}")
    return "\n".join(lines)


def paragraph_labels(comp: Comparison) -> dict:
    """Paragraph ID -> (label, reason), for checking which paragraph a finding cites."""
    out = {f"P{n}": (p.label, p.reason) for n, p in enumerate(comp.paragraphs, 1) if p.label != "UNCHANGED"}
    out.update({f"R{n}": ("REMOVED", "") for n in range(1, len(comp.removed) + 1)})
    return out
