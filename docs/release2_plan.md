# Release 2 plan: liquidity stress simulation

**Status: built and audited (October 17, 2026).**
- Step 1: `liquidity_simulation.py`.
- Step 2: the Oracle app panel (`simulation_view.py`).
- Step 3: a scenario Excel download.
- Step 4: [`liquidity_simulation.md`](liquidity_simulation.md), the method document, which is the reference for the model as built.
- OCF–prepayment correlation was added the same day.
- An audit the same day corrected the treatment of excluded cash uses and the wording of results (see "Changes from the original plan").

Release 2 was chosen by Jack on October 17 (option A of four, recorded below). Nothing in this plan changes the checked reviews, their figures or their funding conclusions.

## The question

> If Oracle's operating cash flow over the next twelve months fell anywhere in an assumed range, in what share of simulated trials would its checked August 31 cash, plus that cash flow, end the window below the cash uses the model subtracts, and by how much?

The answer is an **illustrative scenario**, not a forecast, a rating, a probability of default or a funding conclusion. The reviews' "future funding coverage: Unavailable" stays as it is. This sits beside it and shows how sensitive the answer is to stated assumptions.

## Why this release (decision record)

| Option | Verdict |
|---|---|
| **A. Liquidity stress simulation** | **Chosen.** It applies VSB 2008 Module 2 simulation to the product's own question and the checked data. It's one feature Jack can explain end to end: the model, the inputs, the validation and the limits. Credit analysis is a recruiter-relevant skill. |
| B. A fourth company | Later. Mostly repetition of the pilot method, with days of hand-checking. |
| C. Refresh with newer filings | Later, when the next 10-Qs arrive (Oracle's is likely mid-December). Driven by the filing calendar. |
| D. Stock-price Monte Carlo, LP allocation, CAPM in general research | Not now. It's disconnected from the Debt & Liquidity product, a max-return LP is close to investment-advice territory, and CAPM regression is Upcoming (Nov 11–13). |

## Scope: Oracle first

Oracle is the only review with a **dated** principal calendar ([`oracle_principal_calendar.md`](oracle_principal_calendar.md)): $7.317B of note and term-loan principal falls due September 2026–August 2027, with commercial paper Unavailable. Lilly's per-note calendar isn't supported by its filings ([`lly_principal_calendar_check.md`](lly_principal_calendar_check.md)), and Vistra's borrowing base and Parent-accessible cash are Unavailable. Simulating them would mean inventing the obligations side, so they wait until their evidence exists.

## Model as built

The method document has the full input table, exclusions, results and validation. In brief:

```
ending cash = starting cash + OCF excluding prepayments + prepayments
              − capex − dividends − dated note and term-loan principal − commercial paper due
              (+ revolver draw up to $10B, only where the decision assumes it is usable)
```

- **Horizon:** September 1, 2026–August 31, 2027. Cash is tested at the end and at each month end (added October 17): dated principal falls in its calendar month and the other flows are spread evenly, an assumption. Cash on each payment date within a month and OCF seasonality aren't tested.
- **Filing facts:** starting cash ($36.369B, excluding restricted cash) and dated note and term-loan principal ($7.317B).
- **Assumptions:** triangles for OCF excluding prepayments, prepayments and commercial paper, plus an OCF–prepayment correlation (default 0). Their corners are anchored to checked history, which does not establish future bounds or a most-likely value.
- **Decisions:** capex at the TTM rate ($75.66B) or the fiscal 2026 level ($55.663B); dividends ($6.26B); the revolver assumed unusable or usable up to $10B (a hypothetical, since drawable capacity is Unavailable).
- **Excluded because a filing shows the overlap:** operating lease payments, finance-lease interest, interest and taxes (all inside OCF).
- **Measured separately because overlap isn't established:** finance-lease principal, short-term financing related to capex, and purchase and other obligations. Each is subtracted at a stated amount and its effect is shown; none is in the base result.
- **Outputs:** mean, standard deviation, percentiles, the share of trials with ending cash below zero, the average shortfall in those trials, and a histogram. For the month-end path: the share of trials below zero at any month end, the lowest month-end cash (mean and 10th percentile) and the month most often lowest. Seeded, 10,000 trials by default.

## Changes from the original plan

The plan written before the build differed in several places. Where they differ, the built model governs.

| Original plan | As built | Why |
|---|---|---|
| Subtract dated lease and purchase payments ($3.219B operating, $0.620B finance, $5.449B purchase, Sep 2026–May 2027) | Operating leases and finance-lease interest excluded (inside OCF, per Oracle's policy). Finance-lease principal and purchase obligations measured as outside uses. | Operating-lease cash and finance-lease interest are operating cash flows, so subtracting them again would double count. **Correction (audit):** the first build also excluded finance-lease principal and purchase obligations as overlaps. Principal is a financing cash flow, and the purchase-obligation overlap isn't established, so both are now measured. |
| Interest and dividends not modelled | Interest is inside OCF; dividends are a decision ($6.26B) | Dividends are a cash use outside OCF |
| Commercial paper due $0 to $1.468B (the May 31 balance) | $287M–$387M, triangular | The range implied by rounded August 31 10-Q figures replaced the older May balance |
| Capex: TTM versus a lower rate the user sets | TTM versus the fiscal 2026 level, both editable | A checked level as the default |
| "Probability of shortfall" | "Share of trials below zero" | A simulated share under assumptions isn't a probability of default or of a funding gap |
| Triangles "from the checked periods" | Assumptions anchored to the checked periods | History doesn't establish future bounds or a most-likely value |
| Step 3: a scenario sheet added by script to Oracle's checked workbook | A separate scenario workbook from the app panel | Assumptions are not filing facts, and adding a sheet would change the shared fingerprint of all three company workbooks |
| Short-term capex financing not considered | Measured as an outside use (balance undisclosed; cumulative net proceeds as an indicator) | It's a financing cash use outside OCF and capex |

## Validation

The four checks from class (logic, boundary, distribution, stability) run as unit tests, along with correlation, exclusion and wording tests. Results and the test list are in the method document.

## Guardrails

- Every result is labelled "Illustrative scenario from stated assumptions, not a forecast or funding conclusion."
- Percentages are shares of simulated trials, never probabilities of default or funding.
- The assumption basis and the math model are shown before any result, as in class.
- No grade, rating, default probability or recommendation.
- The simulation never changes the funding conclusion, the checked figures or the source gates. Its inputs are read from the saved checked JSON, and it refuses to run if those don't load.
- A cash use is left out only when a filing shows it overlaps a modelled line; otherwise its effect is measured and shown. Unavailable items appear as stated exclusions, never as zeros presented as facts.

## Timing (as it happened)

The plan proposed starting after the October 19 and 21 simulation classes. The model, panel, workbook and correlation were built on October 17, before those classes. The correlation mechanics (a Gaussian copula) are this app's own choice; the course notes cover only the principle. **After the classes:** check the model against what is taught and record any differences.

## Open questions (resolved)

1. **Horizon:** twelve months, September 1, 2026–August 31, 2027.
2. **OCF range basis:** editable triangle, defaults anchored to checked periods.
3. **Correlation:** added, default 0, with a −0.5 / 0 / +0.5 comparison.

Still open: whether Oracle's next 10-Q (likely mid-December) discloses the commercial-paper and capex-financing balances, the finance-lease principal split, or the purchase-obligation split. Any of these would let an outside use move into the base model.
