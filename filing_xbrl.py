"""Read one fact from a filing's own inline XBRL (the tagged 10-K or 10-Q document itself).

No Streamlit and no network calls here: the caller passes a saved document, so tests run on saved filing data.

Why this exists: SEC companyfacts (xbrl.py) carries only standard taxonomies. A company's own extension elements,
such as Vistra's vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed, appear only in the filing. This
reader takes the filing as the source and checks each fact before trusting it:
- the tag must match exactly, prefix included; another tag is never substituted;
- the context must have the exact requested instant or duration with no dimensions (a dimensioned context reports a part or
  a breakdown, not the line item itself);
- the unit must be iso4217:USD;
- the displayed number is converted with the fact's scale, sign and format (ixt:fixed-zero is a reported zero);
- several facts for the same tag and context must agree.
Anything else returns Unavailable with the reason, never zero.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path

IX = "http://www.xbrl.org/2013/inlineXBRL"
XBRLI = "http://www.xbrl.org/2003/instance"
XBRLDI = "http://xbrl.org/2006/xbrldi"
NS = {"ix": IX, "xbrli": XBRLI, "xbrldi": XBRLDI}
USD = "iso4217:USD"
UNAVAILABLE = "Unavailable"
# Display formats whose text is a number with comma thousands separators and an optional decimal point
NUMBER_FORMATS = {"num-dot-decimal", "numdotdecimal"}
ZERO_FORMATS = {"fixed-zero", "zerodash"}


def _contexts(root: ET.Element) -> dict:
    """{context id: {"instant", "start", "end", "dimensions": [(axis, member), ...]}}."""
    out = {}
    for c in root.iter(f"{{{XBRLI}}}context"):
        period = c.find("xbrli:period", NS)
        dims = [(m.get("dimension"), (m.text or "").strip()) for m in c.iter(f"{{{XBRLDI}}}explicitMember")]
        dims += [(m.get("dimension"), "typed") for m in c.iter(f"{{{XBRLDI}}}typedMember")]
        get = lambda tag: (period.findtext(f"xbrli:{tag}", default=None, namespaces=NS) or "").strip() or None
        out[c.get("id")] = {"instant": get("instant"), "start": get("startDate"), "end": get("endDate"),
                            "dimensions": dims,
                            "entity_identifier": c.findtext("xbrli:entity/xbrli:identifier", namespaces=NS)}
    return out


def _units(root: ET.Element) -> dict:
    """{unit id: measure text}, for single-measure units (a divide unit, such as USD per share, is not money)."""
    out = {}
    for u in root.iter(f"{{{XBRLI}}}unit"):
        measures = [(m.text or "").strip() for m in u.iter(f"{{{XBRLI}}}measure")]
        out[u.get("id")] = measures[0] if len(measures) == 1 and u.find("xbrli:divide", NS) is None else "/".join(measures)
    return out


def _number(fact: ET.Element) -> tuple[Decimal | None, str]:
    """The fact's value in units (scale and sign applied), or (None, why not)."""
    fmt = (fact.get("format") or "").split(":")[-1]
    text = "".join(fact.itertext()).strip()
    if fmt in ZERO_FORMATS:
        shown = Decimal(0)
    elif fmt in NUMBER_FORMATS or fmt == "":
        cleaned = text.replace(",", "")
        if not re.fullmatch(r"\d+(\.\d+)?", cleaned):
            return None, f"its displayed text {text!r} is not a plain number"
        shown = Decimal(cleaned)
    else:
        return None, f"its display format {fact.get('format')!r} is not one this reader handles"
    try:
        value = shown.scaleb(int(fact.get("scale") or 0))
    except (InvalidOperation, ValueError):
        return None, f"its scale {fact.get('scale')!r} is not an integer"
    return (-value if fact.get("sign") == "-" else value), ""


def read_instant(document: str | Path, accession: str, tag: str, instant: str, *, dimensions=()) -> dict:
    """The value of tag (prefix included, e.g. "vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed")
    as a USD instant at instant (YYYY-MM-DD), undimensioned by default, from filing accession.

    The accession is recorded as given: the document itself does not state it, so the caller is responsible for
    pairing them. A filing-specific caller may supply exact expected dimensions; the default
    accepts none. Returns tag, value (int dollars, None when unavailable), period (the instant), context_id,
    dimensions ([] by default), unit, scale, decimals, document (file name), accession, facts_found
    (how many matching facts agreed), note (None or UNAVAILABLE) and detail (why unavailable)."""
    return _read(document, accession, tag, instant, dimensions=dimensions)


def read_duration(document: str | Path, accession: str, tag: str, start: str, end: str, *, dimensions=()) -> dict:
    """One USD fact for the exact start and end dates; never sum quarterly overlaps.

    Uses the instant reader's unit, format, duplicate and conflict checks. The caller supplies the accession
    and is responsible for pairing it with the right source document. A filing-specific caller
    may supply exact expected dimensions; no axis or member is inferred.
    """
    from datetime import date
    if date.fromisoformat(start) > date.fromisoformat(end):
        raise ValueError("Duration starts after it ends")
    return _read(document, accession, tag, end, start=start, dimensions=dimensions)


def _read(document: str | Path, accession: str, tag: str, instant: str, start: str | None = None,
          dimensions=()) -> dict:
    """Shared fact selection and conversion; start distinguishes a duration from an instant."""
    document = Path(document)
    result = {"tag": tag, "value": None, "period": instant, "context_id": None, "dimensions": [], "unit": None,
              "scale": None, "decimals": None, "document": document.name, "accession": accession,
              "facts_found": 0, "note": UNAVAILABLE, "detail": ""}

    if start is not None:
        result.update(start=start, end=instant, entity_identifier=None)

    def unavailable(why):
        return {**result, "detail": why}

    root = ET.parse(document).getroot()
    contexts, units = _contexts(root), _units(root)
    facts = [f for f in root.iter(f"{{{IX}}}nonFraction") if f.get("name") == tag]
    if not facts:
        return unavailable(f"no {tag} fact in {document.name}")

    candidates, other_dates, dimensioned, other_units, durations = [], set(), [], set(), 0
    for f in facts:
        ctx = contexts.get(f.get("contextRef"))
        if ctx is None:
            return unavailable(f"a {tag} fact refers to context {f.get('contextRef')!r}, which the document does "
                               f"not define")
        if start is None:
            if ctx["instant"] is None:
                durations += 1
                continue
            if ctx["instant"] != instant:
                other_dates.add(ctx["instant"])
                continue
        else:
            if ctx["instant"] is not None:
                durations += 1
                continue
            if (ctx["start"], ctx["end"]) != (start, instant):
                other_dates.add(f"{ctx['start']} to {ctx['end']}")
                continue
        # A caller may name an exact, filing-checked dimensional breakdown. Extra or missing
        # axes never match; the default continues to accept only undimensioned facts.
        if sorted(ctx["dimensions"]) != sorted(tuple(d) for d in dimensions):
            dimensioned.append(f.get("contextRef"))
            continue
        unit = units.get(f.get("unitRef"))
        if unit != USD:
            other_units.add(unit or f.get("unitRef"))
            continue
        candidates.append(f)

    if not candidates:
        reasons = []
        if dimensioned:
            reasons.append((f"only dimensioned contexts at {instant} ({', '.join(sorted(set(dimensioned)))}), "
                            "which report a part or breakdown rather than the line item") if not dimensions else
                           f"no contexts with the exact expected dimensions at {instant}; rejected "
                           f"{', '.join(sorted(set(dimensioned)))}")
        if other_units:
            reasons.append(f"units other than {USD} at {instant} ({', '.join(sorted(other_units))})")
        if other_dates:
            kind = "instants" if start is None else "durations"
            reasons.append(f"{kind} at other dates ({', '.join(sorted(other_dates))})")
        if durations:
            reasons.append(f"{durations} duration fact(s), not instants" if start is None
                           else f"{durations} instant fact(s), not durations")
        period = f"instant at {instant}" if start is None else f"duration from {start} to {instant}"
        scope = "undimensioned" if not dimensions else "expected-dimension"
        return unavailable(f"no {scope} {USD} {period} for {tag}; the document has "
                           + "; ".join(reasons))

    values = []
    for f in candidates:
        value, why = _number(f)
        if value is None:
            return unavailable(f"the {tag} fact in context {f.get('contextRef')} cannot be read: {why}")
        values.append((value, f))
    distinct = {v for v, _ in values}
    if len(distinct) > 1:
        shown = ", ".join(f"{v:,.0f} in {f.get('contextRef')}" for v, f in values)
        return unavailable(f"conflicting {tag} facts at {instant}: {shown}")
    value, first = values[0]
    if value != value.to_integral_value():
        return unavailable(f"the {tag} value {value} is not a whole number of dollars")
    ctx_ids = sorted({f.get("contextRef") for _, f in values})
    if len(ctx_ids) > 1:
        return unavailable(f"{tag} facts at {instant} sit in more than one undimensioned context "
                           f"({', '.join(ctx_ids)}); which one is the line item is not established")
    selected = {**result, "value": int(value), "context_id": ctx_ids[0], "unit": USD,
            "dimensions": [list(d) for d in contexts[ctx_ids[0]]["dimensions"]],
            "scale": int(first.get("scale") or 0), "decimals": first.get("decimals"),
            "facts_found": len(values), "note": None}
    if start is not None:
        selected["entity_identifier"] = contexts[ctx_ids[0]]["entity_identifier"]
    return selected
