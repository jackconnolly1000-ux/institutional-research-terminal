"""Historical Lilly coverage from exact duration facts; no forecast or covenant test."""
import hashlib
import json
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

import filing_xbrl as fx
import lly_liquidity as liquidity

SAMPLE = Path(__file__).parent / "samples/lly_interest.json"
CHECKED_INPUTS_SHA256 = "c1557b44e4b357ca3b347f8ee33876aaf873dbefbb4483d42d252520ef337dac"
START, END = "2025-07-01", "2026-06-30"
INTEREST = "us-gaap:InterestExpenseNonoperating"
SEGMENT = [("us-gaap:StatementBusinessSegmentsAxis", "lly:ReportableSegmentMember")]
TAGS = {"revenue": "Revenues", "cost_sales": "CostOfGoodsAndServicesSold",
        "rd": "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
        "sga": "SellingGeneralAndAdministrativeExpense",
        "iprd": "ResearchAndDevelopmentAssetAcquiredOtherThanThroughBusinessCombinationWrittenOff",
        "special": "RestructuringSettlementAndImpairmentProvisions",
        "other_income": "NonoperatingIncomeExpense",
        "pretax": "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"}
EXPENSES = ["cost_sales", "rd", "sga", "iprd", "special"]
PERIODS = [("fy", "annual", "2025-01-01", "2025-12-31", 1),
           ("current", "quarter", "2026-01-01", END, 1),
           ("prior", "quarter", "2025-01-01", "2025-06-30", -1)]
BASIS = ("FY2025 Note 11 explicitly reports interest on borrowings net of capitalized interest. "
         "The interim segment table labels the line interest expense without explicitly stating its "
         "capitalization basis. All three amounts are used as reported, before any interest-income offset. "
         "Capitalized interest is not added or subtracted; its amount and total interest incurred are Unavailable.")
LIMITS = ("Historical accrual-based earnings coverage, not cash interest coverage, a repayment forecast, "
          "a covenant calculation or proof of drawable credit. Operating income is derived, not a reported "
          "Lilly subtotal. Acquired IPR&D and impairment/restructuring charges remain included; no adjusted "
          "earnings addbacks. Interim capitalization basis and future interest are not inferred.")


def statement_table(root):
    """Select the sole consolidated operations table, not rounded MD&A or segment repeats."""
    required = {"us-gaap:" + t for t in TAGS.values()}
    matches = [t for t in root.iter() if t.tag.rsplit("}", 1)[-1] == "table" and
               required <= {f.get("name") for f in t.iter(f"{{{fx.IX}}}nonFraction")}]
    return matches[0] if len(matches) == 1 else None


def statement_copy(root, destination):
    table = statement_table(root)
    if table is None:
        return False
    copy = ET.Element("html")
    resources = ET.SubElement(copy, "resources")
    resources.extend(root.iter(f"{{{fx.XBRLI}}}context"))
    resources.extend(root.iter(f"{{{fx.XBRLI}}}unit"))
    copy.append(table)
    ET.ElementTree(copy).write(destination, encoding="utf-8", xml_declaration=True)
    return True


def calculate(inputs):
    """Validate each period independently; retain a supported numerator or denominator."""
    result = dict(periods={}, interest=None, operating_income=None, value=None, detail="")
    reasons = []
    for role, source, start, end, coefficient in PERIODS:
        facts = {k: inputs.get(role + "_" + k, {}) for k in [*TAGS, "interest"]}
        period = dict(operating_income=None, interest=None, control=None, coefficient=coefficient,
                      period_start=start, period_end=end)
        result["periods"][role] = period

        def valid(key):
            f = facts[key]
            dims = [list(d) for d in SEGMENT] if key == "interest" and source == "quarter" else []
            tag = INTEREST if key == "interest" else "us-gaap:" + TAGS[key]
            return (f.get("value") is not None and f.get("unit") == "iso4217:USD" and
                    (f.get("period_start"), f.get("period_end")) == (start, end) and
                    f.get("accession") == liquidity.SOURCES[source]["accession"] and
                    f.get("source_sha256") == liquidity.SOURCES[source]["sha256"] and
                    str(f.get("entity_identifier") or "").lstrip("0") == "59478" and
                    f.get("tag") == tag and f.get("dimensions") == dims)

        if valid("interest") and facts["interest"]["value"] >= 0:
            period["interest"] = facts["interest"]["value"]
        else:
            reasons.append(role + " interest: missing, negative or incompatible exact-period fact; " + facts["interest"].get("detail", ""))
        missing = [k for k in TAGS if not valid(k)]
        if missing:
            reasons.append(role + " operating income: missing or incompatible " + ", ".join(missing))
            continue
        v = {k: facts[k]["value"] for k in TAGS}
        if any(v[k] < 0 for k in EXPENSES):
            reasons.append(role + " operating income: a negative expense requires presentation review.")
            continue
        op = v["revenue"] - sum(v[k] for k in EXPENSES)
        # The XBRL tag is positive income, negative expense, opposite the printed
        # Other–net (income) expense row. Preserve the filed sign and subtract it.
        period["control"] = v["pretax"] - v["other_income"]
        if op != period["control"]:
            reasons.append(role + " operating income: costs do not reconcile to pretax less nonoperating income (expense).")
        else:
            period["operating_income"] = op
    for field in ["operating_income", "interest"]:
        if all(p[field] is not None for p in result["periods"].values()):
            result[field] = sum(p["coefficient"] * p[field] for p in result["periods"].values())
    if result["interest"] is not None and result["interest"] <= 0:
        reasons.append("TTM reported interest is zero or negative; coverage is Unavailable.")
    if result["operating_income"] is not None and result["interest"] is not None and result["interest"] > 0:
        result["value"] = result["operating_income"] / result["interest"]
    result["detail"] = "; ".join(reasons)
    return result


def build(annual: Path, quarter: Path):
    inputs = {}
    docs = {"annual": Path(annual), "quarter": Path(quarter)}
    with tempfile.TemporaryDirectory() as folder:
        statements = {}
        errors = {}
        for source, path in docs.items():
            try:
                dest = Path(folder) / (source + ".htm")
                if statement_copy(ET.parse(path).getroot(), dest):
                    statements[source] = dest
                else:
                    errors[source] = "A unique consolidated operations table was not established."
            except (OSError, ET.ParseError) as e:
                errors[source] = "Filing could not be read: " + type(e).__name__
        for role, source, start, end, coefficient in PERIODS:
            meta = liquidity.SOURCES[source]
            for key, tag in {**{k: "us-gaap:" + t for k, t in TAGS.items()}, "interest": INTEREST}.items():
                dims = SEGMENT if key == "interest" and source == "quarter" else ()
                path = docs[source] if key == "interest" else statements.get(source)
                fact = dict(value=None, tag=tag, detail=errors.get(source, "Source unavailable"), dimensions=[])
                try:
                    if path:
                        fact = fx.read_duration(path, meta["accession"], tag, start, end, dimensions=dims)
                        if fact["value"] is not None and str(fact.get("entity_identifier") or "").lstrip("0") != "59478":
                            fact.update(value=None, detail="Selected context is not Lilly's CIK.")
                except (OSError, ET.ParseError) as e:
                    fact.update(value=None, detail="Source could not be read: " + type(e).__name__)
                fact.update(label=role + " " + key, role=role, coefficient=coefficient, period_start=start, period_end=end,
                            document=meta["document"], accession=meta["accession"], filed=meta["filed"],
                            form=meta["form"], source_url=meta["source_url"], source_sha256=meta["sha256"],
                            location=("Note 11 p. 77" if source == "annual" else "Note 11 p. 23") if key == "interest" else
                            ("Consolidated operations p. 57" if source == "annual" else "Consolidated operations p. 5"),
                            selection_rule="Exact tag, duration, USD and Lilly CIK; " +
                            ("exact single-segment dimension" if dims else "no dimensions") +
                            ("; consolidated operations table only" if key != "interest" else ""))
                inputs[role + "_" + key] = fact
    return dict(ticker="LLY", period_start=START, period_end=END, checked_as_of="2026-10-15",
                basis=BASIS, limitations=LIMITS, inputs=inputs, calculation=calculate(inputs), tag=None,
                formula="Derived TTM operating income / TTM reported interest expense on borrowings",
                operating_formula="Revenue - cost of sales - R&D - SG&A - acquired IPR&D - impairment/restructuring/special charges",
                ttm_formula="FY2025 + H1 2026 - H1 2025")


def load():
    try:
        r = json.loads(SAMPLE.read_text())
        if (hashlib.sha256(json.dumps(r["inputs"], sort_keys=True, separators=(",", ":")).encode()).hexdigest() == CHECKED_INPUTS_SHA256 and
                r["basis"] == BASIS and r["limitations"] == LIMITS and
                (r["period_start"], r["period_end"]) == (START, END) and r["calculation"] == calculate(r["inputs"])):
            return r
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def for_snapshot(snapshot):
    if snapshot.get("ticker") != "LLY":
        return None
    anchor = snapshot.get("metrics", {}).get("cash", {})
    if (anchor.get("period_end"), anchor.get("accession")) != (END, liquidity.SOURCES["quarter"]["accession"]):
        return None
    return load()
