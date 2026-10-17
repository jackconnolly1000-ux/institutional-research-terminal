# Oracle liquidity stress scenario: method, results and how to explain it

Built October 17, 2026 (Release 2, [`release2_plan.md`](release2_plan.md)); audited the same day (see "Audit, October 17" below). Code: `liquidity_simulation.py` (model) and `simulation_view.py` (app panel and Excel record). Tests: `tests/test_liquidity_simulation.py`, `tests/test_simulation_view.py`.

> **Illustrative scenario from stated assumptions, not a forecast or funding conclusion.** The checked Oracle review still says future funding coverage is Unavailable. This scenario shows how the answer depends on assumptions the filings can't settle. Every percentage below is a **share of simulated trials under those assumptions**. None is a probability of default or of a funding gap.

## Where it is

On Oracle's page, a **View** switch under the company selector chooses between **Checked review** (the default) and **Stress scenario (illustrative)**. The scenario is its own view, not a section of the review, so assumed figures never sit in the same flow as checked filing facts. It's framed with a dashed caution-colored border and opens with a caution banner saying it isn't a forecast, isn't built from checked facts and doesn't change the funding conclusion. Edits to the assumptions survive switching back to the review, and the view choice survives switching company. The checked review ends with a one-line pointer to the scenario view. (Until October 17 it was a collapsed expander near the bottom of the review, which was easy to miss and looked like the checked sections around it.) It appears only for Oracle. Oracle's August 31 principal calendar ([`oracle_principal_calendar.md`](oracle_principal_calendar.md)) dates its note and term-loan principal; Lilly and Vistra don't have a dated principal calendar, so their obligations side would have to be invented.

## The model (uncertain inputs → business logic → outputs)

Per trial, over September 1, 2026–August 31, 2027:

```
ending cash = starting cash + OCF excluding prepayments + prepayments
              − capex − dividends − dated debt principal − commercial paper due
              (+ revolver draw up to $10B, only in decisions that assume it is usable)
```

| Kind | Input | Default | Source / basis |
|---|---|---|---|
| Filing fact | Starting cash | $36.369B | 10-Q balance sheet, Aug 31, 2026; excludes $2.565B restricted cash |
| Filing fact | Dated note and term-loan principal | $7.317B | [Principal calendar](oracle_principal_calendar.md): due Sep 2026–Aug 2027 |
| Assumption (triangular) | OCF excluding prepayments | $31.977B / $35.577B / $46.960B | Corners set at fiscal 2026 OCF, TTM OCF less the specified prepayments, and Jun–Aug 2026 excluding prepayments times four. These are checked historical figures. They don't establish that future OCF stays inside them, or that the TTM figure is most likely. |
| Assumption (triangular) | Specified customer prepayments | $0 / $0 / $11.363B | From none (as in Q1 FY2026) to one more quarter like Jun–Aug 2026; most likely none. Recurrence isn't established. |
| Derived range, assumed shape | Commercial paper due | $287M / $337M / $387M | The August balance is Unavailable. The low and high are implied by rounded 10-Q figures; the midpoint as most likely, and repayment within the year, are assumptions. |
| Decision | Capex | A: $75.66B (TTM) · B: $55.663B (fiscal 2026) | Management chooses this; it isn't an uncertainty |
| Decision | Dividends | $6.26B | Jun–Aug 2026 dividends of $1.565B (common and preferred), times four |
| Decision (hypothetical) | Revolver usable | No / yes, up to $10B | The commitment is a filing fact; the drawable amount is Unavailable |
| Assumption | Correlation, OCF excluding prepayments vs prepayments | 0 (independent) | No filing establishes it; editable from −0.9 to +0.9 |

Every default is editable in the app. Trials default to 10,000 with seed 2026, and the same inputs and seed reproduce the results exactly.

**What it tests, and what it doesn't.** Cash is tested at the end of the window (August 31, 2027) and, since the month-end path below was added, at every month end from September 2026 to August 2027. It doesn't test cash on each payment date within a month, and it doesn't model OCF seasonality or when capex and dividends fall within the year.

## Month-end cash path (added October 17, 2026)

**What it asks:** does cash go below zero at any month end on the way, not only at the end?

**How each trial is stepped** (`monthly_path` in `liquidity_simulation.py`, the same draws as the ending-cash result for the same seed):

```
month-end cash (month m of 12) = starting cash + (OCF + prepayments − capex − dividends) × m / 12
                                 − dated principal paid through month m − commercial paper (from September)
                                 (+ a revolver draw that fills a month-end gap, where assumed usable)
```

| Item | Timing | Kind |
|---|---|---|
| Note and term-loan principal | In the month the principal calendar dates each payment: $0.141B term-loan installments in Sep, Dec 2026 and Mar, Jun 2027; the 2.80% notes ($2.250B) on April 1, 2027; the term-loan remainder ($4.504B) on August 16, 2027 | Filing fact (dates read from `oracle_principal.json`, never re-derived) |
| OCF, prepayments, capex, dividends | One twelfth each month | Assumption. The filings give no timing within the year. |
| Commercial paper ($0.287B–$0.387B) | All in September 2026 | Assumption. Maturity dates aren't disclosed, so the earliest month is used. |
| Revolver (hypothetical) | A draw fills a month-end gap, up to $10B, and is repaid as cash recovers | Hypothetical, as in the base model; interest on a draw isn't modelled |

Because month twelve covers the full year, the last month-end equals the ending cash of the same trial; a test checks this for every trial.

**Outputs, beside the ending-cash result:** the share of trials below zero at any month end, the mean and 10th percentile of each trial's lowest month-end cash, and the month where cash before any revolver draw is lowest most often. The month is read before any draw, because a draw holds cash at zero for several months, which would tie.

**Default results (10,000 trials, seed 2026):**

| Decision | Share below zero at Aug 31, 2027 | Share below zero at any month end | Mean lowest month-end cash | Month most often lowest |
|---|---:|---:|---:|---|
| A: TTM capex | 99.5% | 99.5% | −$11.23B | Aug 2027 (100% of trials) |
| A, revolver usable | 62.6% | 62.6% | −$2.40B | Aug 2027 (100%) |
| B: FY2026 capex | 0.2% | 0.2% | $8.76B | Aug 2027 (100%) |
| B, revolver usable | 0.0% | 0.0% | $8.76B | Aug 2027 (100%) |

**Reading it:** at the defaults the two tests agree. In every trial the year's flows are a net outflow (capex and dividends exceed even the highest assumed OCF plus prepayments), so cash falls every month and the largest payment, the term-loan remainder, falls in the last month. Under decision A, mean month-end cash first goes below zero in June 2027. The same holds with the three outside uses added. So, under the even-spread assumption, the ending-cash test doesn't hide an earlier month-end gap for these decisions. The monthly test would differ where the year's flows are positive and a large maturity comes early, as in the hand-checked test: $1B of cash, $12B of OCF and $4B due in October give −$1B at the end of October and +$9B at the end of August.

**What it still doesn't test:** evenly spread monthly flows don't establish liquidity on actual payment dates. That includes cash on a payment date within a month (the April 1 maturity is netted against all of April's assumed flows), OCF seasonality, quarterly dividend and capex timing, and when the finance-lease, capex-financing and purchase-obligation uses would fall (they're spread evenly when added).

## Cash uses the model leaves out

A use is left out of the base model for one of two reasons. Either a filing shows it's already inside a modelled line, or it is measured separately with its effect disclosed. An overlap is never assumed.

**Left out because a filing shows the overlap:**

| Use | Where it already is | Proof |
|---|---|---|
| Operating lease payments | Inside OCF | Oracle's policy: operating lease cash flows are operating cash flows (10-K fiscal 2026, Note 1) |
| Finance-lease interest | Inside OCF | Oracle's policy: the interest component is an operating cash flow (same note) |
| Interest on borrowing, income taxes | Inside OCF | US GAAP classifies cash interest and taxes as operating (ASC 230). Historical OCF reflects historical interest, not interest on debt raised since. |
| Restricted cash ($2.565B) | Not in starting cash | A balance choice, not a cash use |

**Measured separately as sensitivities (overlap not established).** Each is subtracted at a stated **sensitivity amount**, with the same seed, so its effect is visible. None is in the base results. **These amounts are not established balances or payments due in the window.** In the month-end path they are spread evenly by month.

| Use | Sensitivity amount | Why it's outside the base model | What the amount is, and what it over- or understates |
|---|---:|---|---|
| Finance-lease payments (principal proxy) | $0.620B | Oracle classifies the principal component as a **financing** cash flow (10-K Note 1), so it's in neither OCF nor capex | Not principal. It's the undiscounted Sep 2026–May 2027 finance-lease **payments** (10-Q Note 6), which include interest already inside OCF, so it overstates principal and counts that interest twice. The principal for the window isn't disclosed. Jun–Aug 2027 is Unavailable and not included. |
| Short-term capex financing (cumulative proceeds proxy) | $3.937B | A separate financing line, so repaying it isn't in cash capex or OCF | **Not an outstanding balance and not a payment due.** It's cumulative net proceeds: $1.422B (FY2025) + $3.345B (FY2026) − $0.830B (Jun–Aug 2026). The balance, terms and due dates aren't disclosed ([`pilot_evidence_oracle.md`](pilot_evidence_oracle.md)), so the amount due in the window could be lower, higher, or nil if it is rolled. |
| Purchase and other obligations | $5.449B | Primarily cloud-infrastructure components (likely capex when paid) and data-center power (likely in OCF). The filing doesn't split them, so overlap with the capex decision and OCF is possible but not established. | The disclosed amount due Sep 2026–May 2027 (10-Q Note 6). It may double count purchases already in the capex decision. Jun–Aug 2027 sits inside fiscal 2028's $6.176B and is Unavailable, so a quarter is missing. |

**Overlap between them.** The three can overlap each other and the modelled lines, so the "All three together (may overlap)" row can count the same cash twice. Missing June–August 2027 amounts push the other way. The combined row is a sensitivity bound, not an estimate of cash due.

**Effect at the defaults (10,000 trials, seed 2026), as the share of trials below zero:**

| Decision | Base | + finance-lease payments | + capex financing proxy | + purchase obligations | All three (may overlap) |
|---|---:|---:|---:|---:|---:|
| A: TTM capex | 99.5% | 99.7% | 100.0% | 100.0% | 100.0% |
| A, revolver usable | 62.6% | 67.7% | 88.1% | 93.6% | 99.5% |
| B: FY2026 capex | 0.2% | 0.7% | 13.0% | 23.4% | 62.6% |
| B, revolver usable | 0.0% | 0.0% | 0.0% | 0.0% | 0.2% |

With all three subtracted, decision B's mean ending cash falls from $8.76B to −$1.24B. The base result for decision B is sensitive to these unresolved items. Because the amounts are proxies that may overlap or miss months, this shows sensitivity, not a measured shortfall.

**Left out with no measurable amount:** the $288B of leases not yet commenced (their payments would enter OCF after commencement and aren't in the historical OCF the triangle is anchored to; annual amounts are Unavailable); the lessor-borrowing guarantee of up to $3.3B (status at August 31 not stated); "other financing activities, net" ($0.242B in Jun–Aug 2026, composition not stated, may include finance-lease principal); June–August 2027 lease and purchase payments; and share repurchases or acquisitions (none in the quarter; they would be decisions). Also excluded: new borrowing or equity.

## Default results, base model (10,000 trials, seed 2026)

| Decision | Mean ending cash | 10th percentile | Share of trials below zero | Average shortfall in those trials |
|---|---:|---:|---:|---:|
| A: TTM capex | −$11.23B | −$16.63B | 99.5% | $11.30B |
| A, revolver usable | −$2.40B | −$6.63B | 62.6% | $3.84B |
| B: FY2026 capex | $8.76B | $3.37B | 0.2% | $0.30B |
| B, revolver usable | $8.76B | $3.37B | 0.0% | $0 |

**Reading it:**
- At the TTM capex rate, checked cash plus the assumed range of operating cash flow doesn't cover the uses the model subtracts in almost every trial. Even the whole revolver lifts ending cash above zero in only about a third of trials, because the mean gap ($11.2B) is larger than the $10B commitment. That's consistent with Oracle raising $19.9B of equity in Jun–Aug 2026.
- At the fiscal 2026 capex level, ending cash stays above zero in almost every trial of the **base** model. That reading isn't robust: with the three measured outside uses, 62.6% of trials end below zero.
- Capex is the decision that moves the result most, and the unresolved uses matter about as much as the OCF range does.

These results describe the assumptions, not what will happen. They moved slightly on October 17 (decision A from 99.4% to 99.5%) when OCF and prepayments began to be drawn through the correlation step below. The random stream changed; the model didn't.

## Correlation between OCF and prepayments (added October 17, 2026)

**What it asks:** if prepayment-heavy quarters also tend to be strong (or weak) quarters for the rest of operating cash flow, how does the picture change?

**The course rule it applies:** correlation changes how inputs move together. It doesn't change each input's own distribution, so the mean of a sum stays the same while its spread changes.

**How the draws are tied together (a Gaussian copula):**
1. Draw two independent standard normal scores per trial, z1 and z2.
2. Tie the second to the first: z2′ = ρ·z1 + √(1 − ρ²)·z2. The pair now has correlation ρ.
3. Turn each score into a percentile (0 to 1) with the normal CDF.
4. Read each percentile off its own triangle with the triangle's inverse CDF (`Triangular.quantile`), so each input keeps its stated low, most likely and high.

The class covers the principle, not these mechanics; the copula is this app's implementation choice. ρ is the correlation of the normal scores. The dollar draws end up slightly less correlated (+0.48 for a setting of +0.5), and the app shows that realized value.

**Default:** 0. No filing establishes the sign. Strong cloud demand could raise both (positive), while prepaid cash isn't collected again later (negative).

**Comparison (decision A, 10,000 trials, seed 2026):**

| Setting | Realized | Mean ending cash | Std dev | 10th percentile | Share of trials below zero |
|---:|---:|---:|---:|---:|---:|
| −0.5 | −0.48 | −$11.23B | $3.05B | −$15.21B | 100.0% |
| 0 | −0.01 | −$11.23B | $4.17B | −$16.63B | 99.5% |
| +0.5 | +0.48 | −$11.23B | $5.08B | −$17.57B | 98.1% |

The mean doesn't move and the spread does, as the class rule predicts; a test checks this. With the revolver assumed usable, the mean moves too (−$1.94B, −$2.40B, −$2.78B). The draw fills only shortfalls and stops at $10B, so ending cash is no longer a plain sum of the inputs.

All three settings reuse the same seed, so the same underlying normal scores appear in each. The differences come from the correlation, not from new random numbers.

## Validation (the four checks from class, plus the audit)

| Check | Test | Result |
|---|---|---|
| Logic | With every input fixed, the simulation equals a hand calculation | Pass |
| Boundary | The revolver covers a gap up to $10B and no more; zero spending never falls short; every trial lies between the worst and best corners; a reversed triangle is rejected | Pass |
| Distribution | 200,000 draws stay within the range, the mean is within 1% of (low + mode + high) / 3, and the histogram peaks at the mode | Pass |
| Stability | 10,000 and 50,000 trials agree; the same seed reproduces exactly, with or without correlation. The app also shows a live stability check (5× the trials, new seed). | Pass |
| Correlation | The inverse CDF hits each triangle's corners and mode; correlated draws keep each triangle and reach the target within 0.05; without the revolver, −0.5, 0 and +0.5 give the same mean and a rising standard deviation; ±1 or beyond is rejected | Pass |
| Exclusions | Every exclusion cites the filing or standard that shows the overlap; finance-lease principal is not among them; each outside amount is labelled a sensitivity, not a balance or payment due; each outside use traces to the checked evidence; an added use lowers every trial by exactly its amount; the effects table starts from the unchanged base | Pass |
| Month-end path | A hand-checked case ($4B due in October) goes below zero in October while ending cash is +$9B, and a $1B revolver draw fills it; dated principal falls in its calendar month and sums to $7.317B; the last month equals ending cash for every trial; seeds reproduce; the path never shows fewer trials below zero than the ending test; commercial paper is due in September | Pass |
| Wording | No result is named a probability; the timing limit and the assumption basis are stated in the panel and the workbook | Pass |

## The Excel record

**"Download this scenario (Excel)"** saves whatever is on screen. It's Arial 10, with numbers stored as numbers.

| Sheet | Contents |
|---|---|
| Scenario | Label, horizon, seed and trials. Each input with its **kind** (filing fact, assumption, derived range, hypothetical), low, most likely, high and basis. The timing limit and the share-of-trials note. |
| Results | One row per decision: mean, standard deviation, percentiles, share of trials below zero and the average shortfall in those trials |
| Correlation | −0.5, 0 and +0.5 for the decision shown |
| Monthly path | One row per decision: share below zero at August 31, 2027 and at any month end, mean ending cash, mean and 10th percentile of the lowest month-end cash, the month most often lowest and its share, and the share of trials with a net outflow over the year |
| Monthly path by month | Every decision × twelve month ends: dated principal, mean and 10th percentile month-end cash, share of trials below zero at that month end |
| Outside-use effects | Every decision × (base, each outside use, all three) |
| Uses not modelled | Each left-out use, its treatment (measured, excluded with proof, or not quantified), amount, basis, reason and source |

It is deliberately separate from Oracle's checked evidence workbook: assumptions are not filing facts, and the checked workbook's fingerprints stay unchanged.

## Audit, October 17, 2026

Findings, all fixed in the same pull request:
1. **Finance-lease principal was wrongly excluded as double counting.** (Measured since as "finance-lease payments (principal proxy)"; the payments include interest.) Oracle's 10-K policy puts the principal component in financing cash flows, so it's outside OCF. It's now measured as an outside use.
2. **Purchase obligations were excluded as "overlapping capex" without proof.** The filing doesn't split them, so overlap isn't established. They're now measured as an outside use.
3. **Short-term capex financing was not considered.** It's a separate financing line with an undisclosed balance. It's now measured, using cumulative net proceeds as an indicator.
4. **Results were labelled "shortfall probability".** They're now "share of trials below zero", with a note that they aren't probabilities of default.
5. **Historical anchors were described as if they set the range.** The basis text now says they're assumptions anchored to history.
6. **The end-of-window limit wasn't stated.** It now appears in the panel, the workbook and this document. (Later the same day the month-end path was added; the limit now states what that path does and doesn't test.)
7. **Stale principal wording elsewhere.** Two Oracle review texts and the combined workbook's About sheet still said August 31 principal was not established. They now point to the principal calendar; the combined workbook was patched in one cell (`tests/offline/patch_combined_principal_note.py`) and its manifest rebound.

## Five-minute interview walkthrough

1. **The problem (30 s).** The checked review can date $7.3B of note and term-loan principal due in twelve months, but it can't say whether Oracle can fund it. Drawable credit and future cash flow aren't in the filings, so the app reports coverage as Unavailable.
2. **Why simulation (30 s).** When an answer depends on an uncertain input, show the whole distribution instead of guessing one number. That's the Module 2 idea: uncertain inputs, business logic, then outputs.
3. **The model (90 s).** Walk through the formula. Say which inputs are filing facts (cash, dated principal), which are assumptions (the triangles, anchored to history but not established by it) and which are decisions (capex, dividends, the revolver). Then explain the exclusions: operating leases and interest are already in OCF per Oracle's own policy, while finance-lease payments, capex financing and purchase obligations aren't shown to overlap, so their effect is measured as a sensitivity. Their amounts are proxies, not balances due (finance-lease payments include interest; the capex-financing figure is cumulative proceeds).
4. **The result (60 s).** At the TTM capex pace, 99% of trials end below zero, and even the full revolver lifts only about a third above it. At the fiscal 2026 level the base model looks comfortable, but adding the unresolved uses moves 63% of trials below zero. The honest conclusion is that the answer depends on items the filings don't settle.
   The month-end path checks the timing question: with dated principal in its calendar month and the other flows spread evenly, cash falls every month at the defaults, so the lowest point is August 2027 and the two tests agree.
5. **Why trust it (60 s).** The checks run as automated tests, the runs are seeded, every percentage is a share of simulated trials, and it never changes the checked conclusion.

**Likely interview question:** *"Why triangular distributions?"* There are only a few checked periods. A low, most likely and high anchored to those periods is a transparent way to state an assumption, and anyone can see and change it. It doesn't claim the history sets the bounds. A fitted normal distribution would imply more precision than three observations support.

## Limits

- The OCF triangle is an assumption anchored to three checked periods. The high corner annualizes a single quarter. History doesn't set future bounds.
- Cash is tested at month ends, not on each payment date within a month. OCF, prepayments, capex and dividends are spread evenly by month (an assumption), so OCF seasonality isn't modelled. Commercial paper is assumed due in September 2026.
- Three outside uses are measured at stated amounts, not modelled as uncertain; several more have no measurable amount (see above).
- The OCF–prepayment correlation is an assumption with no filing evidence. Its default of 0 is a neutral choice, not a finding. Commercial paper is drawn independently.
- Capex and dividends are held at the decision values, with no timing within the year.
- The commercial paper range is implied, not reported.
- Oracle only. Lilly and Vistra need dated obligations first.
