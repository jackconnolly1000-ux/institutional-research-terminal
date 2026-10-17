"""Release 2, steps 2–3: the Oracle stress scenario in the app, with editable assumptions and an Excel record.

The model is liquidity_simulation.py. This view shows the math model and the assumption basis before any result
(as in class), runs the four decisions side by side, tests month-end cash for the decision shown, measures the cash
uses the model leaves out, shows a stability check, and offers the scenario as its own workbook. It is kept out of the checked evidence workbooks on purpose:
assumptions are not filing facts. Results are shares of simulated trials, never probabilities of default.
"""
from __future__ import annotations

from dataclasses import replace

import liquidity_simulation as ls
from scenario_export import SHARE_NOTE

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
    rows = [{"Scenario": e["scenario"], "Sensitivity amount ($B)": round(e["added_uses"] / B, 3),
             "Mean ending cash ($B)": round(e["mean"] / B, 2), SHARE: e["share_below_zero"] * 100}
            for e in effects]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                 column_config={SHARE: st.column_config.NumberColumn(format="%.1f%%")})
    measured = "\n".join(f"- **{u.name}.** {u.amount_basis} {u.why_outside}" for u in uses)
    excluded = "\n".join(f"- **{name}:** {status}. {proof}" for name, status, proof in ls.EXCLUDED)
    unmeasured = "\n".join(f"- **{name}:** {note}" for name, note in ls.UNQUANTIFIED)
    st.markdown(_dollars(f"{decision.name}, same seed and trials. {ls.SENSITIVITY_NOTE}\n\n" + measured))
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


def workbook(inputs, results, trials, seed, comparison=None, outside=None, uses=None, monthly=None) -> bytes:
    """Record the current run with the source documentation and layout authored offline."""
    import scenario_export
    return scenario_export.workbook(inputs, results, trials, seed, comparison, outside, uses, monthly)


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
            "**Checked inputs:** reported starting cash (10-Q balance sheet, August 31, 2026) and derived note and term-loan "
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
        st.markdown(f"**Sensitivity: cash uses outside the model** · {shown.name}")
        outside_uses(st, next(e for d, e in outside if d.name == pick), uses, shown)
        check = ls.simulate(edited, decisions[0], trials * 5, seed + 1)
        drift = abs(check["share_below_zero"] - results[0][0]["share_below_zero"])
        st.caption(f"Stability check: rerunning decision A with {trials * 5:,} trials and a new seed changes the "
                   f"share of trials below zero by {drift:.1%}. The logic, boundary, distribution and stability "
                   "checks from class also run as automated tests.")
        st.caption("Also not modelled: new borrowing or equity.")
        try:
            content = workbook(edited, results, trials, seed, comparison, outside, uses, monthly)
        except (OSError, ValueError, KeyError):
            st.caption("Scenario workbook Unavailable: its verified layout could not be loaded.")
        else:
            st.download_button("Download this scenario (Excel)", content,
                               file_name=f"Oracle_Stress_Scenario_seed{seed}.xlsx", mime=XLSX, key="sim_download")
