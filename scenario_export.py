"""A saved simulation record, hydrated into an Artifact Tool-authored template.

The app runs Python only. Layout and styles are authored by tests/offline/organize_exports.mjs;
the standard-library hydration below writes the current run into its reserved cells. Results are
snapshots, not editable Excel Monte Carlo formulas. No network or paid calls.
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo
import hashlib
import json
from pathlib import Path
from io import BytesIO
import zipfile
import xml.etree.ElementTree as ET
import liquidity_simulation as ls

SHARE = "Share of trials below zero"
USD = " (USD, displayed in millions)"
SHARE_NOTE = ("Shares of trials below zero describe simulated trials under stated assumptions, not probabilities "
              "of default or of a funding gap.")

ROOT = Path(__file__).parent
TEMPLATE = ROOT / "samples/scenario_template.xlsx"
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ET.register_namespace("x", NS)


def source_rows(inputs):
    """Retain original filing provenance beside the historical observations used as anchors."""
    import oracle_principal
    q = json.loads((ROOT / "samples/oracle_liquidity.json").read_text())["inputs"]
    snap = next(s for s in json.loads((ROOT / "samples/liquidity_pilots.json").read_text())["snapshots"] if s["ticker"] == "ORCL")
    rows = [["Input", "Kind", "Value (USD, displayed in millions)", "Period start", "Period end", "Form", "Filed", "Accession", "Source URL", "Tag / calculation", "Context", "Location / limit"]]
    def append(label, f):
        rows.append([label, "Reported fact", f["value"], f.get("period_start"), f.get("period_end") or f.get("period"),
                     f.get("form"), f.get("filed"), f.get("accession"), f.get("source_url"), f.get("tag"), f.get("context_id"), f.get("location") or f.get("selection_rule")])
    for key in ("closing_cash", "ocf", "prepay", "capex", "dividends", "capex_financing", "finance_0", "purchase_0"):
        append(q[key]["label"], q[key])
    for key in ("operating_cash_flow", "capital_spending"):
        for f in snap["metrics"][key]["inputs"]:
            append(key + ": " + f.get("role", "source"), f)
    cal = oracle_principal.load()
    if cal is None:
        raise ValueError("Checked principal calendar Unavailable")
    for row in cal["next_twelve_months"]["rows"]:
        rows.append([row["label"], "Derived checked calendar", row["amount"], None, row["date"], "10-K / 10-Q", None,
                     cal["annual"]["accession"], cal["annual"]["source_url"], "Calendar date; contractual amortization where applicable", None,
                     "Principal only; no commercial paper or interest. Loan extension/prepayment may change dates. See checked calendar."])
    # The source is the same contract reviewed by the checked capacity audit; a commitment is not drawable cash.
    rev = json.loads((ROOT / "samples/oracle_revolver.json").read_text())
    s = rev["sources"]["agreement"]
    rows.append(["Revolver commitment", "Reported contract; usability assumed", inputs.revolver_commitment, None,
                 s.get("period"), s["form"], s["filed"], s["accession"], s["source_url"], None, None,
                 "Drawable capacity Unavailable. Only the scenario assumes a draw up to the commitment."])
    for label, value, period in (("Capex financing net proceeds FY2025", 1_422_000_000, "2025-05-31"),
                                 ("Capex financing net proceeds FY2026", 3_345_000_000, "2026-05-31")):
        rows.append([label, "Reported historical flow", value, None, period, "10-K", cal["annual"]["filed"],
                     cal["annual"]["accession"], cal["annual"]["source_url"], None, None,
                     "Cash-flow statement p. 68. Historical net proceeds are not an outstanding balance or payment due."])
    for row in rows[1:]:
        for col in (3, 4, 6):
            if row[col] and len(row[col]) == 10:
                row[col] = date.fromisoformat(row[col])
    return rows


def _column(index):
    name = ""
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def chart_cache(cache, values):
    """Artifact Tool exports range bindings without point caches; seed them for other readers."""
    ns = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
    for child in list(cache):
        if child.tag in (f'{{{ns}}}ptCount', f'{{{ns}}}pt'):
            cache.remove(child)
    ET.SubElement(cache, f'{{{ns}}}ptCount', val=str(len(values)))
    for k, value in enumerate(values):
        point = ET.SubElement(cache, f'{{{ns}}}pt', idx=str(k))
        ET.SubElement(point, f'{{{ns}}}v').text = str(value)


def workbook(*args, **kwargs):
    """Hydrate reserved template cells without altering its styles or native features."""
    payload = tables(*args, **kwargs)
    content = TEMPLATE.read_bytes()
    meta = json.loads(TEMPLATE.with_suffix(".manifest.json").read_text())
    if hashlib.sha256(content).hexdigest() != meta["sha256"]:
        raise ValueError("Scenario layout changed; rebuild and verify its template")
    src = zipfile.ZipFile(BytesIO(content))
    replacement = {}
    book = ET.fromstring(src.read("xl/workbook.xml"))
    sheet_list = book.find(f"{{{NS}}}sheets")
    for entry in list(sheet_list):
        if entry.get("name") not in payload:
            sheet_list.remove(entry)
    replacement["xl/workbook.xml"] = ET.tostring(book, encoding="utf-8", xml_declaration=True)
    for name, layout in meta["sheets"].items():
        rows = payload.get(name, [[name + ": not requested in this record"]])
        if len(rows) > layout["rows"] or max(map(len, rows)) > layout["cols"]:
            raise ValueError("Scenario record exceeds the verified template: " + name)
        path = layout["path"]
        sheet = ET.fromstring(src.read(path))
        cells = {c.attrib["r"]: c for c in sheet.findall(f".//{{{NS}}}sheetData/{{{NS}}}row/{{{NS}}}c")}
        for c in cells.values():
            c.attrib.pop("t", None)
            for child in list(c):
                c.remove(child)
        for r, row in enumerate(rows, 1):
            for k, value in enumerate(row, 1):
                if value is None:
                    continue
                c = cells[_column(k) + str(r)]
                if isinstance(value, date):
                    c.attrib.pop("t", None)
                    ET.SubElement(c, f"{{{NS}}}v").text = str((value - date(1899, 12, 30)).days)
                elif isinstance(value, dict) and "formula" in value:
                    ET.SubElement(c, f"{{{NS}}}f").text = value["formula"].removeprefix("=")
                    ET.SubElement(c, f"{{{NS}}}v").text = repr(float(value["value"]))
                elif isinstance(value, (int, float)):
                    ET.SubElement(c, f"{{{NS}}}v").text = repr(float(value))
                else:
                    c.set("t", "inlineStr")
                    ET.SubElement(ET.SubElement(c, f"{{{NS}}}is"), f"{{{NS}}}t").text = str(value)
        # The authoring runtime does not export native hyperlink actions. Preserve full URL text
        # and attach the exact same URL, using standard OpenXML relationships.
        links = [(f"{_column(k)}{r}", value) for r, row in enumerate(rows, 1)
                 for k, value in enumerate(row, 1) if isinstance(value, str) and value.startswith("https://")]
        if links:
            package_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
            rels = ET.Element("Relationships", xmlns=package_ns)
            block = ET.Element(f"{{{NS}}}hyperlinks")
            for i, (ref, url) in enumerate(links):
                rid = f"rIdSource{i}"
                ET.SubElement(block, f"{{{NS}}}hyperlink", {"ref": ref, f"{{{REL}}}id": rid})
                ET.SubElement(rels, "Relationship", Id=rid, Type=REL + "/hyperlink", Target=url, TargetMode="External")
            position = next((i for i, child in enumerate(sheet) if child.tag == f"{{{NS}}}pageMargins"), len(sheet))
            sheet.insert(position, block)
            rp = path.replace("worksheets/", "worksheets/_rels/") + ".rels"
            replacement[rp] = ET.tostring(rels, encoding="utf-8", xml_declaration=True)
        replacement[path] = ET.tostring(sheet, encoding="utf-8", xml_declaration=True)
    if kwargs.get("monthly") or (len(args) > 7 and args[7]):
        monthly = kwargs.get("monthly") or args[7]
        comparison = kwargs.get("comparison") or (args[4] if len(args) > 4 else None)
        chosen = comparison[0]["decision"] if comparison else monthly[0][0].name
        index, (_, _, path_values) = next((k, row) for k, row in enumerate(monthly) if row[0].name == chosen)
        first, last = 2 + index * 12, 13 + index * 12
        chart_path = meta["monthly_chart"]["path"]
        chart = ET.fromstring(src.read(chart_path))
        cns = "http://schemas.openxmlformats.org/drawingml/2006/chart"
        ans = "http://schemas.openxmlformats.org/drawingml/2006/main"
        series = chart.findall(f".//{{{cns}}}ser")
        for ser, col, values in zip(series, ("F", "H", "I", "J"),
                                    (path_values["month_p10"], path_values["month_p50"], path_values["month_p90"], [0.] * 12)):
            cat = ser.find(f"{{{cns}}}cat/{{{cns}}}strRef")
            if cat is not None:
                cat.find(f"{{{cns}}}f").text = f"'Monthly path by month'!$B${first}:$B${last}"
                chart_cache(cat.find(f"{{{cns}}}strCache"), ls.MONTHS)
            value_ref = ser.find(f"{{{cns}}}val/{{{cns}}}numRef")
            value_ref.find(f"{{{cns}}}f").text = f"'Monthly path by month'!${col}${first}:${col}${last}"
            cache = value_ref.find(f"{{{cns}}}numCache")
            chart_cache(cache, [float(v) for v in values])
        title = chart.find(f".//{{{cns}}}title//{{{ans}}}t")
        if title is not None:
            title.text = "Simulated month-end cash: " + chosen + ". p10 / median / p90; zero reference"
        replacement[chart_path] = ET.tostring(chart, encoding="utf-8", xml_declaration=True)
    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dest:
        for info in src.infolist():
            dest.writestr(info, replacement.get(info.filename, src.read(info.filename)))
        for name in replacement.keys() - set(src.namelist()):
            dest.writestr(name, replacement[name])
    return out.getvalue()

def tables(inputs, results, trials, seed, comparison=None, outside=None, uses=None, monthly=None) -> dict:
    """The scenario on screen as its own record: inputs (each marked filing fact, derived, assumption or hypothetical)
    with sources, seed, trials, results, the correlation comparison for the decision shown, the effect of each use
    the model leaves out and the month-end path, for every decision. Arial 10."""
    wb = {}
    def add(name):
        wb[name] = []
        return wb[name]
    ws = add("Scenario")
    stamp = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M ET")
    ws.append(["Oracle liquidity stress scenario"])
    ws.append([ls.LABEL])
    ws.append([f"Horizon {ls.HORIZON[0]} to {ls.HORIZON[1]}. Created {stamp}. Seed {seed}, {trials:,} trials; "
               "rerunning with the same inputs and seed reproduces these results."])
    ws.append([])
    ws.append(["Input", "Kind", "Low" + USD, "Most likely" + USD, "High" + USD, "Basis / source"])
    t, p, c = inputs.ocf_ex_prepayments, inputs.prepayments, inputs.commercial_paper_due

    def fixed(value):
        return value, value, value

    rows = [("Starting cash", "Filing fact", *fixed(inputs.starting_cash), inputs.sources["starting_cash"]),
            ("Dated note and term-loan principal due", "Derived checked calendar", *fixed(inputs.principal_due),
             inputs.sources["principal_due"]),
            ("OCF excluding prepayments", "Assumption", t.low, t.mode, t.high, t.basis),
            ("Specified customer prepayments", "Assumption", p.low, p.mode, p.high, p.basis),
            ("Commercial paper due", "Derived range; assumed shape", c.low, c.mode, c.high, c.basis),
            ("Revolver commitment", "Filing fact; usable amount hypothetical", *fixed(inputs.revolver_commitment),
             inputs.sources["revolver_commitment"]),
            ("OCF–prepayment correlation (ratio, not USD)", "Assumption", *fixed(inputs.correlation),
             ls.CORRELATION_BASIS)]
    for row in rows:
        ws.append(list(row))
    rho_row = len(ws)
    res = add("Results")
    res.append(["Decision", "Capex" + USD, "Dividends" + USD, "Revolver assumed usable", "Mean ending cash" + USD,
                "Std dev" + USD, "10th percentile" + USD, "Median" + USD, "90th percentile" + USD,
                SHARE, "Average shortfall in trials below zero" + USD])
    for r, d in results:
        res.append([r["decision"], d.capex, d.dividends, "Yes" if d.revolver else "No", r["mean"], r["sd"], r["p10"],
                    r["p50"], r["p90"], r["share_below_zero"], r["mean_shortfall"]])
    if comparison:
        cor = add("Correlation")
        cor.append(["Decision", "Correlation setting", "Realized correlation", "Mean ending cash" + USD,
                    "Std dev" + USD, "10th percentile" + USD, SHARE])
        for r in comparison:
            cor.append([r["decision"], r["correlation"], r["realized_correlation"], r["mean"], r["sd"], r["p10"],
                        r["share_below_zero"]])
    if monthly:
        mon = add("Monthly path")
        mon.append(["Decision", "Revolver assumed usable", "Share of trials below zero at Aug 31, 2027",
                    "Share of trials below zero at any month end", "Mean ending cash" + USD,
                    "Mean lowest month-end cash" + USD, "10th percentile of lowest month-end cash" + USD,
                    "Month most often lowest (before any revolver draw)", "Share of trials lowest in that month",
                    "Share of trials with a net outflow over the year"])
        for d, end, path in monthly:
            mon.append([d.name, "Yes" if d.revolver else "No", end["share_below_zero"],
                        path["share_below_zero_any_month"], end["mean"], path["lowest_mean"], path["lowest_p10"],
                        path["lowest_month"], path["lowest_month_share"], path["share_net_outflow"]])
        by = add("Monthly path by month")
        by.append(["Decision", "Month", "Month end", "Dated note and term-loan principal" + USD,
                   "Mean month-end cash" + USD, "10th percentile month-end cash" + USD,
                   "Share of trials below zero at this month end", "Median month-end cash" + USD,
                   "90th percentile month-end cash" + USD, "Zero reference" + USD])
        for d, _, path in monthly:
            for k, month in enumerate(ls.MONTHS):
                by.append([d.name, month, date.fromisoformat(ls.MONTH_ENDS[k]), float(path["principal_by_month"][k]),
                           float(path["month_mean"][k]), float(path["month_p10"][k]),
                           float(path["month_share_below_zero"][k]),float(path["month_p50"][k]),
                           float(path["month_p90"][k]),0.0])
    if outside:
        eff = add("Outside-use effects")
        eff.append(["Decision", "Scenario", "Sensitivity amount" + USD, "Mean ending cash" + USD, "10th percentile" + USD,
                    SHARE, "Average shortfall in trials below zero" + USD])
        for decision, effects in outside:
            for e in effects:
                eff.append([decision.name, e["scenario"], e["added_uses"], e["mean"], e["p10"],
                            e["share_below_zero"], e["mean_shortfall"]])
    if uses is not None:
        notes = add("Uses not modelled")
        notes.append(["Cash use", "Treatment", "Sensitivity amount used" + USD, "Amount basis", "Reason",
                      "Source"])
        for u in uses:
            notes.append([u.name, "Outside the base model; sensitivity measured", u.amount, u.amount_basis,
                          u.why_outside, u.source])
        for name, status, proof in ls.EXCLUDED:
            notes.append([name, f"Excluded: {status[0].lower()}{status[1:]}", None, "", proof, ""])
        for name, note in ls.UNQUANTIFIED:
            notes.append([name, "Not modelled; no measurable amount", None, "", note, ""])
    wb["Data"] = source_rows(inputs)
    # Deterministic arithmetic remains traceable in Excel. Monte Carlo statistics stay saved
    # results, since rerunning them requires the app's seeded model.
    data = wb["Data"]
    commitment = next(r for r, row in enumerate(data, 1) if row[0] == "Revolver commitment")
    principal = [r for r, row in enumerate(data, 1) if row[1] == "Derived checked calendar"]
    for r, formula in ((6, "='Data'!C2"), (7, f"=SUM('Data'!C{principal[0]}:C{principal[-1]})"),
                       (11, f"='Data'!C{commitment}")):
        for col in (2, 3, 4):
            ws[r - 1][col] = {"formula": formula, "value": ws[r - 1][col]}
    if uses is not None:
        a = next(r for r, row in enumerate(data, 1) if row[0] == "Capex financing net proceeds FY2025")
        b = next(r for r, row in enumerate(data, 1) if row[0] == "Capex financing net proceeds FY2026")
        for r, formula in ((2, "='Data'!C8"), (3, f"='Data'!C{a}+'Data'!C{b}+'Data'!C7"), (4, "='Data'!C9")):
            wb["Uses not modelled"][r - 1][2] = {"formula": formula, "value": wb["Uses not modelled"][r - 1][2]}
    wb["About"] = [
        ["Item", "Description"],
        ["Record", "Oracle illustrative stress scenario, September 1, 2026–August 31, 2027. Not investment advice."],
        ["Meaning", ls.LABEL + " Future funding coverage remains Unavailable."],
        ["Reproduction", f"Seed {seed}; {trials:,} trials. Change assumptions in the app and download again. Editing this workbook does not rerun Monte Carlo; outputs are saved simulation results."],
        ["Units", "Amounts are stored in whole USD and displayed in millions; shares are fractions formatted as percentages. Dates are real dates."],
        ["Colors", "Blue numeric text: recorded inputs. Green: links to another sheet. Black: formulas or saved simulation outputs. No cells are editable model controls."],
        ["Fact versus assumption", "Data records reported facts and derived evidence separately. Scenario records the chosen distributions. Capex/dividends are decisions; revolver usability is hypothetical."],
        ["Timing", ls.TIMING_LIMIT],
        ["Monthly allocation", ls.MONTHLY_BASIS],
        ["Sensitivity", ls.SENSITIVITY_NOTE],
        ["Shares", SHARE_NOTE],
        ["Percentiles", "Monthly percentiles summarize trials at each month end; they are not individual cash paths or confidence intervals for Oracle."],
        ["Sheets", "Results: four decisions. Monthly path: timing summary. Monthly path by month: monthly results. Correlation and Outside-use effects: sensitivities. Scenario: chosen inputs. Uses not modelled: omissions. Data: evidence. About: method and limits."],
        ["Method", "https://github.com/jackconnolly1000-ux/sec-filing-research-terminal/blob/main/docs/liquidity_simulation.md"],
    ]
    order = ["Results", "Monthly path", "Monthly path by month", "Correlation", "Outside-use effects", "Scenario", "Uses not modelled", "Data", "About"]
    return {name: wb[name] for name in order if name in wb}
