# Oracle liquidity stress scenario: method, results and how to explain it

Built October 17, 2026 (Release 2, [`release2_plan.md`](release2_plan.md)). Code: `liquidity_simulation.py` (model) and `simulation_view.py` (app panel and Excel record). Tests: `tests/test_liquidity_simulation.py`, `tests/test_simulation_view.py`.

> **Illustrative scenario from stated assumptions, not a forecast or funding conclusion.** The checked Oracle review still says future funding coverage is Unavailable. This scenario shows how the answer depends on assumptions the filings can't settle.

## Where it is

On the Oracle review, the expander **"Stress scenario (illustrative) · Sep 2026–Aug 2027"** sits after the checked review and before its evidence trail. It appears only for Oracle: Lilly and Vistra don't have a dated principal calendar, so their obligations side would have to be invented.

## The model (uncertain inputs → business logic → outputs)

Per trial, over September 1, 2026–August 31, 2027:

```
ending cash = starting cash + OCF excluding prepayments + prepayments
              − capex − dividends − dated debt principal − commercial paper due
              (+ revolver draw up to $10B, only in decisions that assume it is usable)
```

| Kind | Input | Default | Source / basis |
|---|---|---|---|
| Fixed (checked) | Starting cash | $36.369B | 10-Q balance sheet, Aug 31, 2026; excludes $2.565B restricted cash |
| Fixed (checked) | Dated debt principal | $7.317B | [Principal calendar](oracle_principal_calendar.md): notes and term loan due Sep 2026–Aug 2027 |
| Uncertain (triangular) | OCF excluding prepayments | $31.977B / $35.577B / $46.960B | Low: fiscal 2026 OCF. Most likely: TTM OCF less the specified prepayments. High: Jun–Aug 2026 excluding prepayments, times four (optimistic). |
| Uncertain (triangular) | Specified customer prepayments | $0 / $0 / $11.363B | None (as in Q1 FY2026) up to one more quarter like Jun–Aug 2026 |
| Uncertain (triangular) | Commercial paper due | $287M / $337M / $387M | The August balance is Unavailable; this is the range implied by rounded 10-Q figures |
| Decision | Capex | A: $75.66B (TTM) · B: $55.663B (fiscal 2026) | Management chooses this; it isn't an uncertainty |
| Decision | Dividends | $6.26B | Jun–Aug 2026 dividends of $1.565B, times four |
| Decision (hypothetical) | Revolver usable | No / yes, up to $10B | The commitment is checked; the drawable amount is Unavailable |

Every default is editable in the app. Trials default to 10,000 with seed 2026, and the same inputs and seed reproduce the results exactly.

**Deliberately not subtracted:**
- **Lease payments:** operating lease payments and finance-lease interest are already inside OCF, and the finance-lease principal split isn't disclosed.
- **Purchase obligations:** they overlap capex.
- **Interest:** it's inside OCF.

Subtracting these too would count the same cash twice. Also excluded: new borrowing or equity, and the $288B of leases not yet commenced, which have no payment dates.

## Default results (10,000 trials, seed 2026)

| Decision | Mean ending cash | 10th percentile | Shortfall probability | Mean shortfall when short |
|---|---:|---:|---:|---:|
| A: TTM capex | −$11.21B | −$16.59B | 99.4% | $11.29B |
| A, revolver usable | −$2.39B | −$6.59B | 62.7% | $3.82B |
| B: FY2026 capex | $8.79B | $3.41B | 0.1% | $0.22B |
| B, revolver usable | $8.79B | $3.41B | 0.0% | $0 |

**Reading it:**
- At the TTM capex rate, checked cash plus the stated range of operating cash flow doesn't cover the dated uses without outside funding. Even the whole revolver closes the gap in only about a third of trials, because the mean gap ($11.2B) is larger than the $10B commitment. That's consistent with Oracle raising $19.9B of equity in Jun–Aug 2026.
- At the fiscal 2026 capex level, the uses are covered in almost every trial.
- The decision that matters most is capex, not the uncertainty in operating cash flow.

These results describe the assumptions, not what will happen.

## Validation (the four checks from class)

| Check | Test | Result |
|---|---|---|
| Logic | With every input fixed, the simulation equals a hand calculation | Pass |
| Boundary | The revolver covers a gap up to $10B and no more; zero spending never falls short; every trial lies between the worst and best corners; a reversed triangle is rejected | Pass |
| Distribution | 200,000 draws stay within the range, the mean is within 1% of (low + mode + high) / 3, and the histogram peaks at the mode | Pass |
| Stability | 10,000 and 50,000 trials agree; the same seed reproduces exactly. The app also shows a live stability check (5× the trials, new seed). | Pass |

## The Excel record

**"Download this scenario (Excel)"** saves whatever is on screen. The Scenario sheet holds the label, horizon, seed and trials, plus each input with its low, most likely, high and source. The Results sheet has one row per decision: mean, standard deviation, percentiles, shortfall probability and mean shortfall. It's Arial 10, with numbers stored as numbers.

It is deliberately separate from Oracle's checked evidence workbook: assumptions are not filing facts, and the checked workbook's fingerprints stay unchanged.

## Five-minute interview walkthrough

1. **The problem (30 s).** The checked review can date $7.3B of debt principal due in twelve months, but it can't say whether Oracle can fund it. Drawable credit and future cash flow aren't in the filings, so the app reports coverage as Unavailable.
2. **Why simulation (30 s).** When an answer depends on an uncertain input, show the whole distribution instead of guessing one number. That's the Module 2 idea: uncertain inputs, business logic, then outputs.
3. **The model (90 s).** Walk through the formula. Explain which inputs are checked facts, which are uncertain (triangular, with the evidence for each corner) and which are decisions (capex, dividends, the revolver). Then explain why leases and purchase obligations are left out: double counting.
4. **The result (60 s).** Capex at the TTM pace leaves a gap in 99% of trials, and even the full revolver closes it in only about a third. That ties to the real $19.9B equity raise.
5. **Why trust it (60 s).** The four validation checks run as automated tests, the runs are seeded, and every number is labelled illustrative. It never changes the checked conclusion.

**Likely interview question:** *"Why triangular distributions?"* There are only a few checked periods, so min / most likely / max is the honest summary of the evidence. A fitted normal distribution would claim more than the data supports.

## Limits

- The OCF range rests on three checked periods. The high end annualizes a single quarter.
- There's no correlation between OCF and prepayments yet (covered in class; a possible addition).
- Capex and dividends are held at the decision values, with no timing within the year.
- The commercial paper range is implied, not reported.
- Oracle only. Lilly and Vistra need dated obligations first.
