"""Release 2, steps 2–3: the Oracle stress scenario in the app, with editable assumptions and an Excel record.

The model is liquidity_simulation.py. This view shows the math model and the assumption basis before any result
(as in class), runs the four decisions side by side, tests month-end cash for the decision shown, measures the cash
uses the model leaves out, shows a stability check, and offers the scenario as its own workbook. It is kept out of the checked evidence workbooks on purpose:
assumptions are not filing facts. Results are shares of simulated trials, never probabilities of default.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
from io import BytesIO
from zoneinfo import ZoneInfo

import liquidity_simulation as ls

B = 1_000_000_000
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SHARE = "Share of trials below zero"
USD = " (USD, displayed in millions)"   # stored in dollars, shown in $ millions


def _billions(st, label, value, key, help=None):
    return st.number_input(label, value=round(value / B, 3), step=0.5, format="%.3f", key=key, help=help,
                           persist_state="session") * B


def assumptions(st, inputs, decisions):
    """Editable inputs, defaulting to the checked basis. Returns (inputs, decisions, trials, seed) or None."""
    st.markdown("**Assumptions** · USD billions · defaults are anchored to checked historical figures, which do not "
                "establish future values")
    c1, c2, c3 = st.columns(3)
    t = inputs.ocf_ex_prepayments
    low = _billions(c1, "OCF excl. prepayments, assumed low", t.low, "sim_ocf_low")
    mode = _billions(c2, "Assumed most likely", t.mode, "sim_ocf_mode")
    high = _billions(c3, "Assumed high", t.high, "sim_ocf_high")
    st.caption(t.basis)
    c4, c5 = st.columns(2)
    prepay = _billions(c4, "Prepayments, assumed high (low and most likely are $0)", inputs.prepayments.high,
                       "sim_prepay", help=inputs.prepayments.basis)
    dividends = _billions(c5, "Dividends over the year (a decision)", decisions[0].dividends, "sim_div",
                          help="Default: Jun–Aug 2026 dividends of $1.565B, times four.")
    c6, c7 = st.columns(2)
    capex_a = _billions(c6, "Capex, decision A", decisions[0].capex, "sim_capex_a", help="Default: TTM cash capex.")
    capex_b = _billions(c7, "Capex, decision B", decisions[2].capex, "sim_capex_b", help="Default: fiscal 2026 cash capex.")
    rho = st.slider("Correlation, OCF excl. prepayments and prepayments", -0.9, 0.9, inputs.correlation, 0.1,
                    format="%.1f", key="sim_rho", persist_state="session")
    st.caption(ls.CORRELATION_BASIS)
    c8, c9 = st.columns(2)
    trials = c8.selectbox("Trials", [10_000, 50_000], key="sim_trials", persist_state="session")
    seed = int(c9.number_input("Seed", value=ls.DEFAULT_SEED, step=1, key="sim_seed", persist_state="session"))
    try:
        edited = replace(inputs, ocf_ex_prepayments=ls.Triangular(low, mode, high, t.basis),
                         prepayments=ls.Triangular(0, 0, max(prepay, 0), inputs.prepayments.basis),
                         correlation=float(rho))
    except ValueError:
        st.warning("The OCF range needs low ≤ most likely ≤ high. Nothing was run.")
        return None
    choices = [ls.Decision(f"{name}{', revolver assumed usable' if rev else ''}", capex, dividends, rev)
               for name, capex in (("Decision A", capex_a), ("Decision B", capex_b)) for rev in (False, True)]
    return edited, choices, trials, seed


def results_table(st, results):
    import pandas as pd
    rows = [{"Decision": r["decision"], "Capex ($B)": round(d.capex / B, 2),
             "Mean ending cash ($B)": round(r["mean"] / B, 2), "10th percentile ($B)": round(r["p10"] / B, 2),
             SHARE: r["share_below_zero"] * 100,
             "Average shortfall in those trials ($B)": round(r["mean_shortfall"] / B, 2)}
            for r, d in results]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                 column_config={SHARE: st.column_config.NumberColumn(format="%.1f%%")})
    st.caption("Shares are of simulated trials under the assumptions above. They are not probabilities of default "
               "or of a funding gap.")


def monthly_table(st, end, path):
    """The decision shown, tested once at the end of the window and again at every month end."""
    import pandas as pd
    rows = [{"Cash at": "Aug 31, 2027", SHARE: end["share_below_zero"] * 100,
             "Mean ($B)": round(end["mean"] / B, 2), "10th percentile ($B)": round(end["p10"] / B, 2)},
            {"Cash at": "Lowest month end", SHARE: path["share_below_zero_any_month"] * 100,
             "Mean ($B)": round(path["lowest_mean"] / B, 2), "10th percentile ($B)": round(path["lowest_p10"] / B, 2)}]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                 column_config={SHARE: st.column_config.NumberColumn(format="%.1f%%")})
    dated = ", ".join(f"{m} ${a / B:.3f}B" for m, a in zip(ls.MONTHS, path["principal_by_month"]) if a)
    where = (f"The month with the lowest cash before any revolver draw is {path['lowest_month']} in "
             f"{path['lowest_month_share']:.1%} of trials.")
    if path["lowest_month"] == ls.MONTHS[-1] and path["lowest_month_share"] == 1:
        why = (" The year's flows are a net outflow in every trial, so cash falls every month, and the" if
               path["share_net_outflow"] == 1 else " The")
        where += f"{why} two tests agree on these assumptions."
    st.caption(f"Lowest month end: each trial's lowest of the twelve month ends, Sep 2026–Aug 2027; below zero means "
               f"below zero in any month. {where}")
    st.caption(_dollars(f"Dated principal by month: {dated}. {ls.MONTHLY_BASIS}"))


def correlation_table(st, comparison, revolver):
    """The same decision and seed at three correlations: each input keeps its triangle, so only the spread moves."""
    import pandas as pd
    rows = [{"Correlation setting": r["correlation"], "Realized correlation": r["realized_correlation"],
             "Mean ending cash ($B)": round(r["mean"] / B, 2), "Std dev ($B)": round(r["sd"] / B, 2),
             "10th percentile ($B)": round(r["p10"] / B, 2), SHARE: r["share_below_zero"] * 100}
            for r in comparison]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                 column_config={"Correlation setting": st.column_config.NumberColumn(format="%.1f"),
                                "Realized correlation": st.column_config.NumberColumn(format="%+.2f"),
                                SHARE: st.column_config.NumberColumn(format="%.1f%%")})
    note = ("Without the revolver, ending cash is a sum of the inputs, so the mean stays put and only the spread "
            "changes.")
    if revolver:
        note = ("With the revolver, a draw fills only shortfalls and stops at \\$10B, so a wider spread can also move "
                "the mean.")
    st.caption(f"Same decision, seed and trials at each setting. {note}")


def outside_uses(st, effects, uses, decision):
    """The base result beside each use the model leaves out, then the uses excluded because they are inside OCF."""
    import pandas as pd
    rows = [{"Scenario": e["scenario"], "Added use ($B)": round(e["added_uses"] / B, 3),
             "Mean ending cash ($B)": round(e["mean"] / B, 2), SHARE: e["share_below_zero"] * 100}
            for e in effects]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                 column_config={SHARE: st.column_config.NumberColumn(format="%.1f%%")})
    measured = "\n".join(f"- **{u.name}** (${u.amount / B:.3f}B). {u.why_outside} {u.amount_basis}" for u in uses)
    excluded = "\n".join(f"- **{name}:** {status}. {proof}" for name, status, proof in ls.EXCLUDED)
    unmeasured = "\n".join(f"- **{name}:** {note}" for name, note in ls.UNQUANTIFIED)
    st.markdown(_dollars(f"{decision.name}, same seed and trials. Each amount is subtracted once over the window; "
                         "none is in the base result above.\n\n" + measured))
    st.markdown(_dollars("**Left out because a filing shows they are inside a modelled line**\n\n" + excluded))
    st.markdown(_dollars("**Left out with no measurable amount**\n\n" + unmeasured))


def _dollars(text):
    """Streamlit's Markdown treats text between dollar signs as math."""
    return text.replace("$", "\\$")


def histogram(st, result):
    import plotly.graph_objects as go
    import theme as T
    from charts import CHART_CONFIG
    fig = go.Figure(go.Histogram(x=result["ending_cash"] / B, nbinsx=60, marker_color=T.FLOW_OUT,
                                 hovertemplate="%{x:.1f}B: %{y} trials<extra></extra>"))
    fig.add_vline(x=0, line_color=T.TEXT_STRONG, line_width=1)
    fig.add_annotation(x=0, y=1, yref="paper", text="zero", showarrow=False, yanchor="bottom",
                       font=dict(color=T.TEXT_MUTED, size=11))
    fig.update_layout(height=280, margin=dict(l=56, r=12, t=24, b=40), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", bargap=0.04, showlegend=False,
                      font=dict(color=T.TEXT, size=11),
                      xaxis=dict(title="Ending cash, USD billions", gridcolor=T.BORDER, zerolinecolor=T.BORDER),
                      yaxis=dict(title="Trials", gridcolor=T.BORDER))
    st.plotly_chart(fig, width="stretch", theme=None, config=CHART_CONFIG)


SHARE_NOTE = ("Shares of trials below zero describe the simulated trials under the stated assumptions. They are not "
              "probabilities of default or of a funding gap.")


def workbook(inputs, results, trials, seed, comparison=None, outside=None, uses=None, monthly=None) -> bytes:
    """The scenario on screen as its own record: inputs (each marked filing fact, derived, assumption or hypothetical)
    with sources, seed, trials, results, the correlation comparison for the decision shown, the effect of each use
    the model leaves out and the month-end path, for every decision. Arial 10."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    wb = Workbook()
    ws = wb.active
    ws.title = "Scenario"
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
            ("Dated note and term-loan principal due", "Filing fact", *fixed(inputs.principal_due),
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
    rho_row = ws.max_row
    ws.append([])
    ws.append([ls.TIMING_LIMIT])
    ws.append([SHARE_NOTE])
    ws.append(["Cash uses the model leaves out, and why, are on the Uses not modelled sheet; their effect on each "
               "decision is on Outside-use effects. Capex and dividends are decisions, shown on Results. Month-end "
               "cash is on Monthly path and Monthly path by month."])
    ws.append([ls.MONTHLY_BASIS])
    res = wb.create_sheet("Results")
    res.append(["Decision", "Capex" + USD, "Dividends" + USD, "Revolver assumed usable", "Mean ending cash" + USD,
                "Std dev" + USD, "10th percentile" + USD, "Median" + USD, "90th percentile" + USD,
                SHARE, "Average shortfall in trials below zero" + USD])
    for r, d in results:
        res.append([r["decision"], d.capex, d.dividends, "Yes" if d.revolver else "No", r["mean"], r["sd"], r["p10"],
                    r["p50"], r["p90"], r["share_below_zero"], r["mean_shortfall"]])
    if comparison:
        cor = wb.create_sheet("Correlation")
        cor.append(["Decision", "Correlation setting", "Realized correlation", "Mean ending cash" + USD,
                    "Std dev" + USD, "10th percentile" + USD, SHARE])
        for r in comparison:
            cor.append([r["decision"], r["correlation"], r["realized_correlation"], r["mean"], r["sd"], r["p10"],
                        r["share_below_zero"]])
    if monthly:
        mon = wb.create_sheet("Monthly path")
        mon.append(["Decision", "Revolver assumed usable", "Share of trials below zero at Aug 31, 2027",
                    "Share of trials below zero at any month end", "Mean ending cash" + USD,
                    "Mean lowest month-end cash" + USD, "10th percentile of lowest month-end cash" + USD,
                    "Month most often lowest (before any revolver draw)", "Share of trials lowest in that month",
                    "Share of trials with a net outflow over the year"])
        for d, end, path in monthly:
            mon.append([d.name, "Yes" if d.revolver else "No", end["share_below_zero"],
                        path["share_below_zero_any_month"], end["mean"], path["lowest_mean"], path["lowest_p10"],
                        path["lowest_month"], path["lowest_month_share"], path["share_net_outflow"]])
        by = wb.create_sheet("Monthly path by month")
        by.append(["Decision", "Month", "Month end", "Dated note and term-loan principal" + USD,
                   "Mean month-end cash" + USD, "10th percentile month-end cash" + USD,
                   "Share of trials below zero at this month end"])
        for d, _, path in monthly:
            for k, month in enumerate(ls.MONTHS):
                by.append([d.name, month, date.fromisoformat(ls.MONTH_ENDS[k]), float(path["principal_by_month"][k]),
                           float(path["month_mean"][k]), float(path["month_p10"][k]),
                           float(path["month_share_below_zero"][k])])
    if outside:
        eff = wb.create_sheet("Outside-use effects")
        eff.append(["Decision", "Scenario", "Added use" + USD, "Mean ending cash" + USD, "10th percentile" + USD,
                    SHARE, "Average shortfall in trials below zero" + USD])
        for decision, effects in outside:
            for e in effects:
                eff.append([decision.name, e["scenario"], e["added_uses"], e["mean"], e["p10"],
                            e["share_below_zero"], e["mean_shortfall"]])
    if uses is not None:
        notes = wb.create_sheet("Uses not modelled")
        notes.append(["Cash use", "Treatment", "Amount used to measure effect" + USD, "Amount basis", "Reason",
                      "Source"])
        for u in uses:
            notes.append([u.name, "Outside the base model; effect measured", u.amount, u.amount_basis,
                          u.why_outside, u.source])
        for name, status, proof in ls.EXCLUDED:
            notes.append([name, f"Excluded: {status[0].lower()}{status[1:]}", None, "", proof, ""])
        for name, note in ls.UNQUANTIFIED:
            notes.append([name, "Not modelled; no measurable amount", None, "", note, ""])
    money_fmt = '#,##0,,;(#,##0,,);"-"'
    # Non-USD cells by sheet: column numbers (or the correlation row on Scenario) and their format.
    ratio = {"Results": {10: "0.0%"}, "Correlation": {2: "+0.0;-0.0;0.0", 3: "+0.00;-0.00;0.00", 7: "0.0%"},
             "Outside-use effects": {6: "0.0%"}, "Monthly path": {3: "0.0%", 4: "0.0%", 9: "0.0%", 10: "0.0%"},
             "Monthly path by month": {7: "0.0%"}}
    for sheet in wb:
        for row in sheet.iter_rows():
            for cell in row:
                cell.font = Font(name="Arial", size=10, bold=cell.row in ((1, 5) if sheet.title == "Scenario" else (1,)))
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                if isinstance(cell.value, float | int) and not isinstance(cell.value, bool):
                    if sheet.title == "Scenario" and cell.row == rho_row:
                        cell.number_format = "+0.0;-0.0;0.0"
                    else:
                        cell.number_format = ratio.get(sheet.title, {}).get(cell.column, money_fmt)
                elif isinstance(cell.value, date):
                    cell.number_format = "yyyy-mm-dd"
        sheet.freeze_panes = None if sheet.title == "Scenario" else "A2"
        for col in "ABCDEFGHIJK":
            sheet.column_dimensions[col].width = 22
    wb["Scenario"].column_dimensions["A"].width = 34
    wb["Scenario"].column_dimensions["F"].width = 70
    if uses is not None:
        for col, width in (("A", 30), ("B", 26), ("D", 50), ("E", 60), ("F", 40)):
            wb["Uses not modelled"].column_dimensions[col].width = width
    out = BytesIO()
    wb.save(out)
    return out.getvalue()


VIEWS = ("Checked review", "Stress scenario (illustrative)")


def available(snapshot) -> bool:
    """Oracle only: Lilly and Vistra have no dated principal calendar, so their obligations side would be invented."""
    return snapshot.get("ticker") == "ORCL"


def render(st, snapshot) -> None:
    """The scenario as its own view, framed (ui.py, .st-key-scenario_view) so it never reads as checked facts."""
    from ui import notice
    if not available(snapshot):
        return
    inputs = ls.oracle_inputs()
    uses = ls.oracle_uses_outside_model()
    if inputs is None or uses is None:
        st.markdown(notice("Stress scenario Unavailable", "The checked Oracle evidence it reads did not load. "
                           "No assumed figures are substituted.", "caution"), unsafe_allow_html=True)
        return
    with st.container(key="scenario_view"):
        st.markdown(notice(ls.LABEL, "Oracle, September 2026 to August 2027. The figures below come from simulated "
                           "trials, not from checked filing facts. The checked review's funding conclusion is "
                           "unchanged: future funding coverage remains Unavailable.", "caution"), unsafe_allow_html=True)
        st.markdown(_dollars(
            "**Question:** if operating cash flow fell anywhere in the assumed range below, in what share of "
            "simulated trials would August 31 cash plus that cash flow end the twelve months below the cash uses "
            "the model subtracts, or go below zero at a month end on the way?\n\n"
            f"**Model, per trial:** ending cash = ${inputs.starting_cash / B:.3f}B cash + OCF excluding prepayments "
            f"+ prepayments − capex − dividends − ${inputs.principal_due / B:.3f}B dated debt principal − commercial "
            "paper due (+ a revolver draw up to $10B, only where the decision assumes it is usable; drawable credit "
            "is Unavailable in the filings). The month-end path subtracts each dated principal payment in its "
            "calendar month and spreads the other flows evenly.\n\n"
            "**Filing facts:** the starting cash (10-Q balance sheet, August 31, 2026) and the note and term-loan "
            "principal due in the window (Oracle's August 31 principal calendar). **Assumptions:** the OCF, "
            "prepayment and commercial-paper triangles and the correlation; their defaults are anchored to checked "
            "history, which does not set future bounds. **Decisions:** capex, dividends and the revolver."))
        st.caption(ls.TIMING_LIMIT)
        chosen = assumptions(st, inputs, ls.oracle_decisions())
        if chosen is None:
            return
        edited, decisions, trials, seed = chosen
        results = [(ls.simulate(edited, d, trials, seed), d) for d in decisions]
        st.markdown("**Results by decision**")
        results_table(st, results)
        pick = st.radio("Show the distribution for", [d.name for d in decisions], horizontal=True, key="sim_pick",
                        persist_state="session")
        histogram(st, next(r for r, d in results if d.name == pick))
        shown = next(d for d in decisions if d.name == pick)
        monthly = [(d, r, ls.monthly_path(edited, d, trials, seed)) for r, d in results]
        st.markdown(f"**Cash at each month end** · {shown.name}")
        monthly_table(st, *next((r, m) for d, r, m in monthly if d.name == pick))
        comparison = ls.compare_correlations(edited, shown, trials, seed)
        st.markdown(f"**How correlation changes the spread** · {shown.name}")
        correlation_table(st, comparison, shown.revolver)
        outside = [(d, ls.outside_use_effects(edited, uses, d, trials, seed)) for d in decisions]
        st.markdown(f"**Cash uses outside the model** · {shown.name}")
        outside_uses(st, next(e for d, e in outside if d.name == pick), uses, shown)
        check = ls.simulate(edited, decisions[0], trials * 5, seed + 1)
        drift = abs(check["share_below_zero"] - results[0][0]["share_below_zero"])
        st.caption(f"Stability check: rerunning decision A with {trials * 5:,} trials and a new seed changes the "
                   f"share of trials below zero by {drift:.1%}. The logic, boundary, distribution and stability "
                   "checks from class also run as automated tests.")
        st.caption("Also not modelled: new borrowing or equity.")
        st.download_button("Download this scenario (Excel)",
                           workbook(edited, results, trials, seed, comparison, outside, uses, monthly),
                           file_name=f"Oracle_Stress_Scenario_seed{seed}.xlsx", mime=XLSX, key="sim_download")
