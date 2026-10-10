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
from datetime import date, datetime, timedelta

from bs4 import BeautifulSoup, NavigableString

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
    return filings_from_columns(submissions["filings"]["recent"], cik)


def older_pages(submissions: dict) -> list[dict]:
    """EDGAR's older filing pages: [{"name", "filingFrom", "filingTo", ...}]. Frequent filers (banks) can have
    last year's 10-K only there; JPM fills a page about every month."""
    return list(submissions["filings"].get("files", []))


def filings_from_columns(r: dict, cik: str) -> list[Filing]:
    """One page of EDGAR filings (column lists: form, filingDate, ...) as Filing objects."""
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


def select_with_older_pages(submissions: dict, cik: str, today: date, fetch_json, max_pages: int = 4) -> Selection:
    """select_filings, reading EDGAR's older filing pages when the prior 10-K isn't in the recent list.
    Only pages dated 9 to 15 months before the current 10-K are fetched (10-Ks come about a year apart),
    newest first. fetch_json(url) -> dict is passed in, so this stays network-free in tests."""
    filings = filings_from_submissions(submissions, cik)
    selection = select_filings(filings, today)
    if selection.annual_prior is not None or selection.annual_current is None:
        return selection
    filed = datetime.strptime(selection.annual_current.filed, "%Y-%m-%d").date()
    lo, hi = filed.replace(year=filed.year - 1) - timedelta(days=92), filed - timedelta(days=270)
    pages = [p for p in older_pages(submissions) if p.get("filingFrom", "") <= hi.isoformat() and p.get("filingTo", "9") >= lo.isoformat()]
    for page in sorted(pages, key=lambda p: p.get("filingTo", ""), reverse=True)[:max_pages]:
        filings += filings_from_columns(fetch_json(f"https://data.sec.gov/submissions/{page['name']}"), cik)
        selection = select_filings(filings, today)
        if selection.annual_prior is not None:
            selection.notes = [n for n in selection.notes if "Only one 10-K" not in n]
            break
    return selection


# --- Text --------------------------------------------------------------------------------------

BLOCK_TAGS = ["p", "div", "li", "tr", "td", "th", "table", "br", "h1", "h2", "h3", "h4", "h5", "h6"]


def html_to_text(html: bytes) -> str:
    """Visible text of a filing: a line break between block elements (so paragraphs survive), and
    nothing between inline pieces (so a heading styled letter by letter reads "Item", not "I tem")."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(BLOCK_TAGS):
        tag.insert_before(NavigableString("\n"))
        tag.append(NavigableString("\n"))
    lines = (re.sub(r"[^\S\n]+", " ", line).strip() for line in soup.get_text(separator="").split("\n"))
    return "\n".join(line for line in lines if line)


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

MIN_SECTION_CHARS = 200

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
    elif len(body) < MIN_SECTION_CHARS:
        # e.g. JPM's 10-K Item 1A only points to its annual report exhibit
        return Section("missing", start=start.pos, end=end_m.pos,
                       note=f"Item {item.upper()} heading found but the section is {len(body)} characters long "
                            "(likely incorporated by reference from another document); not extracted.")
    refs = form == "10-Q" and item == "1a" and bool(EARLIER_10Q_REF.search(body)) and "incorporated" in body.lower()
    return Section(status, body, start.pos, end_m.pos, note, references_earlier_10q=refs)


# --- Paragraphs --------------------------------------------------------------------------------
MIN_PARAGRAPH_WORDS = 10
MAX_TITLE_WORDS = 30
_PAGE_FURNITURE = re.compile(r"^(\d{1,3}|table of contents|.*\|\s*\d{4} form 10-k\s*\|\s*\d+|\d{1,3}\s+table of contents"
                             r"|(part\s+i{1,2}\s+)?item\s*1a|part\s+i{1,2})$", re.I)   # a lone "PART I" is a running header
_RUNNING_HEADER = re.compile(r"^(\d{1,3}\s+)?(part\s+i\s+)?item\s*1a\s+(?=[a-z])", re.I)


def split_paragraphs(section_text: str) -> list[str]:
    """Paragraphs of a section. Page numbers, footers and running headers are dropped, a line that
    continues a sentence across a page break is joined to the one before, and subheadings
    (short lines with no ending punctuation) are skipped."""
    out = []
    for line in (ln.strip() for ln in section_text.split("\n")):
        if not line or _PAGE_FURNITURE.match(line):
            continue
        header = _RUNNING_HEADER.match(line)
        if header:
            line = line[header.end():]
        if out and (line[0].islower() or line[0] in ",;)"):
            out[-1] += " " + line
        else:
            out.append(line)
    out = [p for p in out if not (len(p.split()) < 15 and p.rstrip()[-1:] not in ".:;?!")]   # subheadings
    # A risk factor's title is often its own one-sentence paragraph. Join it to the text that follows, so a
    # title reworded from last year is compared together with its body instead of standing alone.
    joined = []
    for i, p in enumerate(out):
        if joined and joined[-1][1]:
            joined[-1] = (joined[-1][0] + " " + p, False)
            continue
        is_title = (len(p.split()) <= MAX_TITLE_WORDS and len(re.findall(r"[.!?](?=\s|$)", p)) == 1
                    and p.rstrip()[-1:] in ".!?" and i + 1 < len(out) and out[i + 1][:1].isupper())
        joined.append((p, is_title))
    return [p for p, _ in joined if len(p.split()) >= MIN_PARAGRAPH_WORDS]
