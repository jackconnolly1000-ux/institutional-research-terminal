"""SEC EDGAR evidence for the research terminal: which filings to use, and the text of their sections.

No Streamlit and no network calls here. app.py downloads documents (with caching) and passes the
results in, so tests call these exact functions on saved or synthetic filings.

Comparison basis (decided Oct 10, 2026):
- Annual trend labels compare Item 1A Risk Factors in the latest 10-K with the prior 10-K.
  Both reporting periods are kept and shown.
- Every 10-Q filed after the latest 10-K is read for Part II Item 1A updates, oldest first, so an
  update made in an earlier quarter (and incorporated by reference later) is not lost.
- MD&A comes from the most recent periodic report (10-Q if newer than the 10-K).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

from bs4 import BeautifulSoup

ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
EIGHT_K_WINDOW_DAYS = 180   # 8-Ks older than this aren't "recent events"
EIGHT_K_MAX = 4             # most recent 8-Ks read per ticker
FORM4_WINDOW_DAYS = 90


# --- Filings -----------------------------------------------------------------------------------

@dataclass(frozen=True)
class Filing:
    form: str            # "10-K", "10-Q", "8-K", ...
    filed: str           # filing date, YYYY-MM-DD
    period: str          # reporting period end (EDGAR "reportDate"), "" if EDGAR has none
    accession: str       # 0000320193-25-000079
    document: str        # primary document file name
    cik: str             # no leading zeros
    items: str = ""      # 8-K item numbers, e.g. "2.02,9.01"

    @property
    def url(self) -> str:
        return f"{ARCHIVES}/{self.cik}/{self.accession.replace('-', '')}/{self.document}"

    @property
    def index_url(self) -> str:
        return f"{ARCHIVES}/{self.cik}/{self.accession.replace('-', '')}/{self.accession}-index.htm"

    @property
    def label(self) -> str:
        if not self.period:
            period = ""
        elif self.form.startswith("8-K"):
            period = f" (event date {self.period})"   # an 8-K's reportDate is the date of the event
        else:
            period = f" for the period ended {self.period}"
        return f"{self.form}{period}, filed {self.filed}"


def filings_from_submissions(submissions: dict, cik: str) -> list[Filing]:
    """EDGAR's submissions JSON (data.sec.gov/submissions/CIK##########.json) as Filing objects, newest first."""
    r = submissions["filings"]["recent"]
    n = len(r["form"])
    get = lambda key, i: (r.get(key) or [""] * n)[i] or ""
    return [Filing(form=r["form"][i], filed=r["filingDate"][i], period=get("reportDate", i),
                   accession=r["accessionNumber"][i], document=r["primaryDocument"][i],
                   cik=str(int(cik)), items=get("items", i)) for i in range(n)]


@dataclass
class Selection:
    annual_current: Filing | None
    annual_prior: Filing | None
    quarterly_updates: list[Filing]      # 10-Qs filed after annual_current, oldest first
    mdna_source: Filing | None           # most recent 10-K or 10-Q
    eight_ks: list[Filing]               # newest first
    form4_count: int
    notes: list[str] = field(default_factory=list)

    @property
    def comparison_available(self) -> bool:
        return self.annual_current is not None and self.annual_prior is not None


def _days_between(earlier: str, later: date) -> int:
    return (later - datetime.strptime(earlier, "%Y-%m-%d").date()).days


def select_filings(filings: list[Filing], today: date) -> Selection:
    """Pick the filings the analysis uses. Amended filings (10-K/A, 10-Q/A) are ignored:
    they often contain only a cover page or one exhibit."""
    tenks = [f for f in filings if f.form == "10-K"]
    current, prior = (tenks + [None, None])[:2]
    notes = []
    if current is None:
        notes.append("No 10-K in EDGAR's recent filings list, so there is no annual risk-factor baseline.")
    elif prior is None:
        notes.append("Only one 10-K in EDGAR's recent filings list, so the annual comparison is unavailable.")

    tenqs = [f for f in filings if f.form == "10-Q"]
    updates = sorted([q for q in tenqs if current is None or q.filed > current.filed], key=lambda f: f.filed)
    periodic = [f for f in filings if f.form in ("10-K", "10-Q")]
    eight_ks = [f for f in filings if f.form in ("8-K", "8-K/A") and _days_between(f.filed, today) <= EIGHT_K_WINDOW_DAYS]
    form4 = sum(1 for f in filings if f.form in ("4", "4/A") and _days_between(f.filed, today) <= FORM4_WINDOW_DAYS)
    return Selection(annual_current=current, annual_prior=prior, quarterly_updates=updates,
                     mdna_source=periodic[0] if periodic else None, eight_ks=eight_ks[:EIGHT_K_MAX],
                     form4_count=form4, notes=notes)


# --- Text --------------------------------------------------------------------------------------

def html_to_text(html: bytes) -> str:
    """Visible text of a filing, whitespace collapsed to single spaces."""
    return re.sub(r"\s+", " ", BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True))


# --- Sections ----------------------------------------------------------------------------------
# A filing mentions "Item 1A" in three ways, and only one of them starts the section:
#   table of contents  "Item 1A. Risk Factors 5 Item 1B. Unresolved Staff Comments 17"
#   cross-reference    "see Item 1A of this Form 10-K", "under “Part I, Item 1A. Risk Factors,” other ..."
#   heading            "Item 1A. Risk Factors The Company's business ..."
# "i\s?tem" allows "I tem": some filings style the first letter separately (STRL FY2024 10-K).

ITEM_RE = re.compile(r"\bi\s?tem\s*(\d{1,2}[a-c]?)\b", re.I)
QUOTES = "\"'“”‘’"
_XREF_BEFORE = re.compile(
    r"\b(see|refer to|in|under|including|described in|discussed in|disclosed in|set forth in|and|of|heading|also)"
    r"\s*[" + QUOTES + r"]?\s*(part\s+i{1,2}\s*[,.]?\s*)?[" + QUOTES + r"]?\s*$", re.I)
_XREF_AFTER = re.compile(r"^(of\s+(this|the|our|that)|above|below|herein|in\s+(this|our|the))\b", re.I)
# Table-of-contents titles have no sentence periods ("Unresolved Staff Comments None. 21" is a real section)
_TOC_AFTER = re.compile(r"^[^\d.]{2,150}?\s\d{1,3}\s+(i\s?tem|part|signatures?)\b", re.I)

TITLES = {"1a": ("risk factors",), "7": ("management's discussion", "managements discussion"),
          "2": ("management's discussion", "managements discussion")}
# The headings that can end a section, by form and starting item
SECTION_ENDS = {("10-K", "1a"): {"1b", "1c", "2"}, ("10-K", "7"): {"7a", "8"},
                ("10-Q", "2"): {"3", "4"}, ("10-Q", "1a"): {"2", "3", "4", "5", "6"}}

# The heading's title, so the section body starts after it
# Some filings style letters separately, so a title can come out as "RIS K FACTORS" (MSFT 10-K).
# _loose() allows one stray space inside each word.
def _loose(phrase: str) -> str:
    return r"\s+".join(r"\s?".join(re.escape(ch) for ch in word) for word in phrase.split())


_MDA_TITLE = re.compile(_loose("management's discussion and analysis of financial condition and results of operations")
                        .replace("'", "'?") + r"[\s.:]*", re.I)
TITLE_SKIP = {"1a": re.compile(_loose("risk factors") + r"[\s.:]*", re.I), "7": _MDA_TITLE, "2": _MDA_TITLE}

NO_CHANGES = re.compile(r"\b(no|not been any|not been)\s+(material\s+)?changes?\b", re.I)
NOT_APPLICABLE = re.compile(r"\bnot\s+applicable\b|\bsmaller\s+reporting\s+compan", re.I)
EARLIER_10Q_REF = re.compile(r"form\s+10-q", re.I)


@dataclass
class Mention:
    pos: int          # where "Item" starts
    item: str         # "1a", "7", ...
    kind: str         # "heading", "toc", "xref"
    title_end: int    # where the heading's title ends (for headings)


def _normalize_apostrophes(s: str) -> str:
    return s.replace("’", "'").replace("‘", "'")


def classify_mentions(text: str) -> list[Mention]:
    out = []
    for m in ITEM_RE.finditer(text):
        item = m.group(1).lower()
        after = text[m.end():m.end() + 200]
        sep = re.match(r"[\s.:\-—–]*", after).end()
        rest = after[sep:]
        before = text[max(0, m.start() - 45):m.start()].rstrip()
        if ((before and before[-1] in QUOTES) or _XREF_BEFORE.search(before) or rest[:1] in QUOTES + ","
                or _XREF_AFTER.match(rest) or not rest[:1].isupper()):
            kind = "xref"
        elif _TOC_AFTER.match(rest):
            kind = "toc"
        else:
            kind = "heading"
        out.append(Mention(m.start(), item, kind, m.end() + sep))
    return out


@dataclass
class Section:
    status: str          # found | no_material_changes | not_applicable | missing | failed
    text: str = ""       # section body, heading removed
    start: int = -1
    end: int = -1
    note: str = ""       # how the boundary was found, or why it wasn't
    references_earlier_10q: bool = False

    @property
    def usable(self) -> bool:
        return self.status in ("found", "no_material_changes")


def find_section(text: str, item: str, form: str) -> Section:
    """The body of one Item, from its real heading to the next allowed heading.
    Never substitutes other text: if the heading can't be found, the status is "missing"."""
    item = item.lower()
    titles = TITLES[item]
    mentions = classify_mentions(text)
    starts = []
    for mo in mentions:
        if mo.item == item and mo.kind == "heading":
            title = _normalize_apostrophes(text[mo.title_end:mo.title_end + 60]).lower().replace(" ", "")
            if any(title.startswith(t.replace(" ", "")) for t in titles):
                starts.append(mo)
    if not starts:
        kinds = sorted({mo.kind for mo in mentions if mo.item == item})
        seen = f" (only {', '.join(kinds)} mentions found)" if kinds else ""
        return Section("missing", note=f"No Item {item.upper()} heading found{seen}.")

    start = starts[0]
    allowed = SECTION_ENDS[(form, item)]
    end_m = next((mo for mo in mentions if mo.pos > start.pos and mo.kind == "heading" and mo.item in allowed), None)
    if end_m is None:
        end_m = next((mo for mo in mentions if mo.pos > start.pos and mo.kind == "heading" and mo.item != item), None)
        note = "Section end inferred from the next item heading."
    else:
        note = f"Heading at character {start.pos:,}; ends at Item {end_m.item.upper()}."
    if end_m is None:
        return Section("missing", start=start.pos, note=f"Item {item.upper()} heading found but no heading after it.")

    body_start = start.title_end
    skip = TITLE_SKIP[item].match(_normalize_apostrophes(text[body_start:body_start + 200]))
    if skip:
        body_start += skip.end()
    body = text[body_start:end_m.pos].strip()

    status = "found"
    if len(body) < 1500 and NO_CHANGES.search(body):
        status = "no_material_changes"
    elif len(body) < 800 and NOT_APPLICABLE.search(body):
        status = "not_applicable"
    refs = form == "10-Q" and item == "1a" and bool(EARLIER_10Q_REF.search(body)) and "incorporated" in body.lower()
    return Section(status, body, start.pos, end_m.pos, note, references_earlier_10q=refs)
