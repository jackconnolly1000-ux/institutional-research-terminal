# Release 2 plan: liquidity stress simulation

**Status: step 1 built (October 17, 2026): `liquidity_simulation.py` and `tests/test_liquidity_simulation.py`. Steps 2–4 are planned.** Release 2 was chosen by Jack on October 17 (option A of four, recorded below). Nothing in this plan changes the checked reviews, their figures or their funding conclusions.

## The question

> If Oracle's operating cash flow over the next twelve months varied within a stated range, how often would its checked August 31 cash plus that cash flow fall short of the obligations the filings actually date, and by how much?

The answer is an **illustrative scenario**, not a forecast, a rating or a funding conclusion. The reviews' "future funding coverage: Unavailable" stays as it is. This sits beside it and shows how sensitive the answer is to one uncertainty, using stated assumptions.

## Why this release (decision record)

| Option | Verdict |
|---|---|
| **A. Liquidity stress simulation** | **Chosen.** It applies VSB 2008 Module 2 simulation, which is covered (with more on Oct 19 and 21), to the product's own question and the checked data. It's one feature Jack can explain end to end: the model, the inputs, the validation and the limits. Credit analysis is a recruiter-relevant skill. |
| B. A fourth company | Later. Mostly repetition of the pilot method, with days of hand-checking. |
| C. Refresh with newer filings | Later, when the next 10-Qs arrive (Oracle's is likely mid-December). Driven by the filing calendar. |
| D. Stock-price Monte Carlo, LP allocation, CAPM in general research | Not now. It's disconnected from the Debt & Liquidity product, a max-return LP is close to investment-advice territory, and CAPM regression is Upcoming (Nov 11–13). |

## Scope: Oracle first

Oracle is the only review with a **dated** principal calendar ([`oracle_principal_calendar.md`](oracle_principal_calendar.md)). Lilly's per-note calendar isn't supported by its filings ([`lly_principal_calendar_check.md`](lly_principal_calendar_check.md)), and Vistra's borrowing base and Parent-accessible cash are Unavailable. Simulating them would mean inventing the obligations side, so they wait until their evidence exists.

## Model (course structure: uncertain inputs → business logic → outputs)

**Decision owner:** a credit analyst reviewing Oracle's next twelve months (September 1, 2026–August 31, 2027).

**Fixed inputs, from checked evidence** (each keeps its source and date):

| Input | Value | Source |
|---|---|---|
| Starting cash (excludes $2.565B restricted cash) | $36.369B at Aug 31, 2026 | 10-Q balance sheet |
| Dated note and term-loan principal, Sep 2026–Aug 2027 | $7.317B | `oracle_principal.json` |
| Dated lease and purchase payments, Sep 2026–May 2027 | $3.219B operating, $0.620B finance, $5.449B purchase/other | 10-Q Note 6 |

The lease and purchase payments cover only nine of the twelve months. Their June–August 2027 amounts are Unavailable and will be stated as a gap, not filled.

**Uncertain inputs** (one draw per trial, triangular distributions, as in class):

| Input | Range basis | Why it's uncertain |
|---|---|---|
| Operating cash flow, excluding specified prepayments | Minimum, most likely and maximum from the checked periods (TTM $46.94B; the quarter's $11.74B excluding prepayments). The basis is shown in the app and editable. | Recurrence isn't established. |
| Specified customer prepayments | $0 to the last quarter's run rate | Recurrence isn't established; Q1 FY2026 had none. |
| Commercial paper due | $0 to $1.468B (the May 31 balance) | The August balance and dates are Unavailable. |

**Decisions compared** (the course requires at least two):
1. Capital spending at the checked TTM rate versus a lower rate the user sets. Capex is a management decision, not an uncertainty.
2. The revolver either assumed unavailable, or available up to its $10B commitment. That is a **hypothetical**, because drawable capacity is Unavailable.

**Not modelled:** interest and dividends (stated as excluded), new borrowing or equity, the $288B of uncommenced leases (no payment dates), and unpaid capex timing.

**Outputs per scenario:**
- probability that ending cash falls below zero;
- mean, standard deviation and 10th percentile of ending cash;
- the size of the shortfall when one occurs;
- a histogram.

All results come from seeded trials (10,000 by default).

## Validation (the four checks from class, as tests)

1. **Logic:** fixed inputs (minimum = most likely = maximum) reproduce a hand calculation exactly.
2. **Boundary:** the minimum and maximum draws, zero capex and the revolver toggle behave as expected.
3. **Distribution:** sampled inputs match their stated minimum, mode and maximum, and their theoretical mean.
4. **Stability:** 10,000 versus 50,000 trials agree within a stated tolerance; the same seed gives identical output.

## Guardrails

- Every result is labelled "Illustrative scenario from stated assumptions, not a forecast or funding conclusion."
- The assumption basis is shown before any result, and the math model is shown before running, as in class.
- No grade, rating, default probability or recommendation.
- The simulation never changes the funding conclusion, the checked figures or the source gates. Its inputs are read from the saved checked JSON, and it refuses to run if those don't load.
- Unavailable items appear as toggles or stated exclusions, never as zeros presented as facts.

## Delivery steps (one PR each)

1. **Model and tests.** `liquidity_simulation.py`: pure Python, no Streamlit, seeded, with the four validation checks as unit tests.
2. **App section.** An Oracle-only expander, "Stress scenario (illustrative)", with editable assumptions, the two decisions side by side, outputs and a histogram. Checked at desktop and 390 px.
3. **Excel record.** A scenario sheet with its inputs, seed, trial count and summary outputs, labelled illustrative. It's added by script, like the other post-build blocks.
4. **Docs and case study.** A method doc, the case-study update and an interview walkthrough.

## Timing

- **Plan now; start building after the Oct 19 and 21 simulation classes,** so the release only uses methods Jack has covered.
- Group Project 2 is due Oct 26 and Exam 2 is on Nov 2. Steps 1–2 fit after Oct 21, and steps 3–4 after the exam.
- Revisit the input ranges when Oracle's next 10-Q arrives (likely mid-December).

## Open questions for Jack

1. Horizon: twelve months (proposed) or Oracle's fiscal year to May 31, 2027?
2. OCF range basis: proposed from the checked periods above. Or should it be a user-entered triangle only, with the checked values as defaults?
3. Include correlation between OCF and prepayments (covered in class) in step 2, or defer it?

## Step 1 as built (October 17, 2026)

`liquidity_simulation.py` is pure Python with no Streamlit, seeded through numpy's `default_rng`. Its inputs are read from the saved checked JSON, and it refuses to run if any of it doesn't load. Every result carries the scenario label.

**Correction to the model above:** dated lease and purchase payments are *not* subtracted.
- Operating lease payments are already inside operating cash flow.
- Finance-lease interest is too, and the principal split isn't disclosed.
- Purchase obligations overlap capex.

Subtracting them again would count the same cash twice. The cash uses outside OCF and capex are what's modelled: dated debt principal ($7.317B), commercial paper ($287M–$387M, triangular), and dividends, which are a decision (Q1 FY2027's $1.565B times four, $6.26B).

**Defaults for the open questions (all editable in step 2):**
1. **Horizon:** twelve months, Sep 1, 2026–Aug 31, 2027.
2. **OCF excluding prepayments, triangular:**
   - low $31.977B (fiscal 2026 OCF);
   - most likely $35.577B (TTM OCF less the specified prepayments);
   - high $46.960B (Jun–Aug 2026 excluding prepayments, times four; an optimistic bound).
   - Prepayments are triangular from $0 to $11.363B, with a mode of $0.
3. **Correlation:** not modelled in step 1. It could be added in step 2 as covered in class.

**Decisions compared:** capex at the TTM rate ($75.66B) or the fiscal 2026 level ($55.663B), each with the revolver assumed unusable or usable up to $10B (a hypothetical).

**Default results (10,000 trials, seed 2026; illustrative):**

| Decision | Mean ending cash | 10th percentile | Probability of shortfall |
|---|---:|---:|---:|
| TTM capex | −$11.2B | −$16.6B | 99% |
| TTM capex, revolver usable | −$2.4B | −$6.6B | 63% |
| FY2026 capex | $8.8B | $3.4B | under 1% |
| FY2026 capex, revolver usable | $8.8B | $3.4B | under 1% |

Read: at the TTM capex rate, the stated range of operating cash flow and the checked cash don't cover the dated cash uses without outside funding, even with the full revolver. That is consistent with Oracle raising $19.9B of equity in Jun–Aug 2026. At the fiscal 2026 capex level they do in almost every trial. This describes the assumptions, not what will happen.

**Validation (all pass):**
- **Logic:** fixed inputs equal the hand calculation.
- **Boundary:** the revolver covers a gap up to $10B and no more; zero spending never falls short; every trial lies between the worst and best corners; a reversed triangle is rejected.
- **Distribution:** 200,000 draws stay within the range, with the mean within 1% and the histogram peak at the mode.
- **Stability:** 10,000 and 50,000 trials agree, and the same seed reproduces exactly.
