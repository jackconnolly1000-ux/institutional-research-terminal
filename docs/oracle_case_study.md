# Oracle case study: funding disclosed near-term obligations

**Question:** What do the checked filings establish about Oracle's ability to fund its disclosed near-term obligations?

**Short answer:** They establish what Oracle had and what it owed on stated dates. They don't establish that it can fund those obligations. At August 31, 2026, Oracle held $36.369B of cash and cash equivalents. It also had $7.625B of current borrowing and $9.288B of lease and purchase payments disclosed for September 2026–May 2027. Cash rose in the June–August quarter, but only because $19.909B of net equity proceeds and $11.363B of specified customer prepayments arrived while cash capital spending ($28.499B) exceeded operating cash flow ($23.103B). The $10B revolver was undrawn at May 31, but no reviewed filing shows how much could be drawn later. **Future funding coverage: Unavailable.**

This case study uses only evidence already checked and saved in the app (`samples/`, `docs/`). It adds no figure, metric or forecast. Each review's numbers come from the app models listed under "Where each figure lives".

## Reporting dates

| Item | Date or period | Source |
|---|---|---|
| Latest balance sheet | August 31, 2026 (end of Q1 fiscal 2027) | 10-Q filed September 11, 2026 |
| Quarter cash flows | June 1–August 31, 2026 | Same 10-Q |
| TTM cash flows and interest | September 1, 2025–August 31, 2026 (FY2026 + Q1 FY2027 − Q1 FY2026) | FY2026 10-K and Q1 10-Q |
| Debt principal schedule | As of May 31, 2026 (historical; not rolled forward) | 10-K filed June 22, 2026 |
| Revolver agreement | Dated March 6, 2026; original maturity March 6, 2031 | Exhibit 10.17, 10-Q filed March 11, 2026 |
| Later filings screened | August 31–October 15, 2026 (SEC submissions index) | Two 8-Ks, filed Sep 10 and Sep 14 |
| Review checks | Balance-sheet facts Oct 14; cash analysis and revolver audit Oct 15; interpretation Oct 16, 2026 | `pilot_evidence_oracle.md`, `oracle_liquidity_reconciliation.md`, `oracle_revolver_reconciliation.md` |

Oracle's fiscal year ends May 31, so "Remainder FY2027" means September 1, 2026–May 31, 2027.

## Filing sources

- [10-Q for the quarter ended Aug 31, 2026](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.htm), filed Sep 11, 2026, accession 0001193125-26-389274. Balance sheet p. 1; cash flows p. 5; cash note p. 6; Note 1 pp. 6–7 (prepayments); Note 5 p. 11 (borrowings); Note 6 pp. 12–13 (leases, purchase obligations); MD&A liquidity pp. 32–35.
- [10-K for fiscal 2026](https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm), filed Jun 22, 2026, accession 0001193125-26-277521. Note 6 pp. 83–85 (principal schedule, revolver, covenant).
- [Revolving credit agreement, Exhibit 10.17](https://www.sec.gov/Archives/edgar/data/1341439/000119312526101045/orcl-ex10_17.htm), filed Mar 11, 2026, accession 0001193125-26-101045. §§1.01, 2.01, 2.06, 2.21, 4.02, 6.02(c).
- [8-K filed Sep 10, 2026](https://www.sec.gov/Archives/edgar/data/1341439/000119312526387905/orcl-20260910.htm) and [Exhibit 99.1](https://www.sec.gov/Archives/edgar/data/1341439/000119312526387905/orcl-ex99_1.htm), accession 0001193125-26-387905: quarterly results and dividends; no new borrowing established.
- [8-K filed Sep 14, 2026](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389753/d20034d8k.htm) and [Exhibit 99.1](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389753/d20034dex991.htm), accession 0001193125-26-389753: cancellation of an insider trading plan; no financing event.
- [SEC submissions index](https://data.sec.gov/submissions/CIK0001341439.json), saved Oct 15, 2026 (SHA-256 `bed0ec89…`): no other financing candidate after August 31 through October 15.

## Essential figures

USD. Each figure keeps its own date and basis. **None of these are added together into a "liquidity" or "coverage" total.**

### 1. Cash (a balance at a date)

| Figure | Amount | Date | Location |
|---|---:|---|---|
| Cash and cash equivalents, excluding restricted cash | $36.369B | Aug 31, 2026 | 10-Q balance sheet p. 1 |
| Restricted cash (excluded from the repayment pool) | $2.565B | Aug 31, 2026 | 10-Q cash note p. 6 |
| Cash including restricted, start → end of quarter | $31.289B → $38.934B (+$7.645B) | May 31 → Aug 31, 2026 | 10-Q p. 1, pp. 5–6 |

August cash is one shared pool. It isn't reserved for any payment, and the filings don't say how much of it will be available on any future date.

### 2. Historical cash generation (flows already reflected in cash)

| Figure | Amount | Period | Location |
|---|---:|---|---|
| Reported operating cash flow (OCF) | $23.103B | Jun–Aug 2026 | 10-Q p. 5 |
| Cash capital expenditures | $28.499B | Jun–Aug 2026 | 10-Q p. 5 |
| OCF less cash capex | −$5.396B | Jun–Aug 2026 | Calculation |
| TTM OCF / capital spending / free cash flow | $46.94B / $75.66B / −$28.72B | Sep 2025–Aug 2026 | 10-K and 10-Q cash-flow statements |
| Historical interest coverage (reported operating income / reported interest expense) | $23.057B / $5.104B = 4.52x | Sep 2025–Aug 2026 | `oracle_interest_coverage.md` |

These are historical flows. They don't predict future OCF. The 4.52x ratio is earnings coverage on Oracle's reported interest line. It isn't the credit agreement's covenant ratio, and it doesn't show repayment capacity.

### 3. Customer prepayments (inside OCF, not a separate source)

| Figure | Amount | Period | Location |
|---|---:|---|---|
| Customer prepayments with a significant financing component | $11.363B (49.2% of quarter OCF) | Jun–Aug 2026 | 10-Q p. 5; Note 1 pp. 6–7 |
| OCF excluding those prepayments | $11.740B | Jun–Aug 2026 | Calculation |
| OCF excluding prepayments, less cash capex | −$16.759B | Jun–Aug 2026 | Calculation |

The prepayments are part of the $23.103B and are already in August cash, so they can't be counted again. They come with future obligations to provide service to those customers. They are neither debt proceeds nor free cash, and whether they will recur isn't established.

### 4. Equity proceeds (a completed financing, already in cash)

| Figure | Amount | Period | Location |
|---|---:|---|---|
| ATM common-stock proceeds, net | $19.909B | Jun–Aug 2026 | 10-Q p. 5; 8-K Ex. 99.1 (Sep 10) |
| Cash increase without the equity proceeds | −$12.264B | Jun–Aug 2026 | Calculation |
| Cash increase without the equity proceeds or the prepayments | −$23.627B | Jun–Aug 2026 | Calculation |

The $20B gross ATM program was fully used, so no remaining equity capacity is established. The two "without" lines hold every other flow fixed. They describe the past quarter only; they aren't runway estimates or forecasts.

### 5. Committed versus drawable credit

| Figure | Amount | Date | Location |
|---|---:|---|---|
| Revolver commitment | $10.000B | Agreement Mar 6, 2026; original maturity Mar 6, 2031 | Ex. 10.17 §§2.01, 2.06 |
| Revolver drawn | $0 | May 31, 2026 | 10-K Note 6 pp. 84–85 |
| Undrawn commitment | $10.000B | May 31, 2026 | Calculation (commitment − drawn) |
| Drawn, undrawn or drawable at Aug 31 or later | **Unavailable** | — | 10-Q Note 5 p. 11 doesn't update the revolver |
| Contractual minimum interest coverage | 3.0x, contract-defined | Agreement | Ex. 10.17 §6.02(c) |
| Covenant headroom | **Unavailable** | — | Ratio not disclosed |
| $12B increase option | Not committed; not counted | Agreement | Ex. 10.17 |

A *commitment* is the most the lenders agreed to lend. An *undrawn commitment* is that amount minus borrowings at a date. *Drawable* credit is what Oracle could actually borrow on a given day. That depends on §4.02 draw conditions (accurate representations, no default) and the covenant, and no reviewed filing establishes it for any date. Commercial-paper capacity isn't added to the revolver.

### 6. Disclosed near-term obligations

| Obligation | Amount | Period or date | Basis | Location |
|---|---:|---|---|---|
| Current borrowing (notes payable and other borrowings, current) | $7.625B | At Aug 31, 2026 | Carrying amount, not a dated principal schedule | 10-Q p. 1 |
| Operating lease payments | $3.219B | Sep 1, 2026–May 31, 2027 | Undiscounted, includes interest | 10-Q Note 6 pp. 12–13 |
| Finance lease payments | $620M | Sep 1, 2026–May 31, 2027 | Undiscounted, includes interest | Same |
| Purchase and other obligations | $5.449B | Sep 1, 2026–May 31, 2027 | Unrecorded commitments | Same |
| Debt principal, fiscal 2027 bucket | $7.210B | Jun 1, 2026–May 31, 2027, **as of May 31** | Historical; three of its months had already passed by Aug 31 | 10-K Note 6 pp. 83–85 |
| Q1 debt repayments | $4.202B | Jun–Aug 2026 | Senior notes, term loans and other repayments, grouped | 10-Q p. 5 |
| Unpaid capital expenditures | $6.247B | At Aug 31, 2026 | Noncash disclosure; payment dates Unavailable | 10-Q p. 5 |
| Operating leases not yet commenced | $288B | At Aug 31, 2026 | Commitment; payment timing Unavailable | 10-Q Note 6 p. 13 |

The $4.202B can't be subtracted from the $7.210B bucket. The 10-Q groups the repayments by type, and MD&A describes about $3.1B of scheduled debt repayment plus $1.1B of commercial-paper repayment, while the cash-flow commercial-paper row is zero. Purchase obligations may overlap unpaid capex and leases. For both reasons, no near-term total is presented.

## Supported conclusion

The checked filings support this statement, and no stronger one:

> In the quarter ended August 31, 2026, Oracle's cash capital spending exceeded its operating cash flow. Its cash balance still rose, because net equity proceeds of $19.909B and specified customer prepayments of $11.363B (part of reported OCF) contributed. At August 31 it held $36.369B of unrestricted cash against $7.625B of current borrowing and $9.288B of lease and purchase payments disclosed for September 2026–May 2027, with $288B of leases not yet commenced and no dated payment schedule for them. The $10B revolver was an undrawn commitment at May 31; whether any of it was drawable at August 31 or later is not established. The dated cash balance doesn't establish that future debt and infrastructure payments are covered.

The filings don't support:
- adding cash, the revolver, OCF and prepayments into one "liquidity" figure;
- treating the quarter's equity proceeds or prepayments as recurring;
- a cash runway, surplus or shortfall for any payment date;
- treating the revolver commitment or undrawn amount as drawable credit;
- treating the May 31 principal schedule as the August 31 schedule;
- reading 4.52x as covenant compliance or repayment capacity.

## Decisive unknowns and the evidence that would resolve them

| Unknown | Why it decides the answer | Evidence that would resolve it |
|---|---|---|
| Remaining debt principal by date after Aug 31, 2026 | Current borrowing ($7.625B) is the largest single near-term item, but carrying value has no dates. | A post-August maturity table, or each note's stated maturity (10-K Note 6 and the note indentures and prospectuses), reconciled to the Q1 repayments and the commercial-paper presentation. |
| Revolver drawn and drawable amount at Aug 31 and later | Decides whether the $10B is usable. | A later 10-Q or 10-K stating revolver borrowings and covenant compliance, or an 8-K amending, drawing on or terminating the facility. |
| Covenant headroom | A draw requires covenant compliance. | A disclosed contract-defined ratio (EBITDA and cash interest as §1.01 defines them), or a compliance statement for a stated date. |
| Payment timing for the $288B of uncommenced leases | Determines when these become cash payments. | Commencement disclosures and lease maturity tables in later filings, as each lease starts. |
| Overlap among purchase obligations, unpaid capex and leases | Prevents double counting in any near-term total. | Filing language that allocates or reconciles these commitments. |
| Commercial-paper presentation (zero cash-flow row versus about $1.1B in MD&A) | Affects how much debt was repaid in Q1. | The next 10-Q or 10-K's debt note and cash-flow presentation. |
| Future OCF, prepayment recurrence and future equity raises | These would be the future funding sources. | Can't come from filed historical statements. The app keeps them Unavailable and doesn't forecast. |

## Five-minute walkthrough: live app and Oracle Excel

App: https://sec-filing-research-terminal.streamlit.app/. Opening it makes no live data request and needs no sign-in.

| Time | Where | What to read | What it shows |
|---|---|---|---|
| 0:00–0:30 | App, company selector | Choose **Oracle (ORCL)**. Read the header: balance sheet Aug 31, 2026; facts checked 2026-10-14. | The review is frozen at one date. |
| 0:30–1:30 | **Funding conclusion for ORCL** (just below the four headline figures) | Its four rows: Near-term obligations, Resources and access, Competing cash uses, Decisive unknowns. | The answer to the question, with links to the 10-Q, 10-K and credit agreement. |
| 1:30–2:15 | **What funded Oracle's cash balance?** and **How much came from customer prepayments?** | The six-bar quarter chart: OCF excluding prepayments, prepayments, equity proceeds, capex, debt repayments, other. | Cash rose because of equity proceeds and prepayments, not because OCF covered capex. |
| 2:15–3:00 | **What payments are actually dated?**, then **How much financing capacity is established?** | The Remainder FY2027 row, then the three revolver dates (Mar 6, May 31, Aug 31), each "drawable capacity Unavailable". | Dated lease and purchase payments, and committed versus drawable credit. |
| 3:00–3:30 | Scroll down to **When was borrowing scheduled to be repaid?** | The fiscal 2027 bar and the note that it is the May 31 schedule. | The near-term debt principal is historical and not rolled forward. |
| 3:30–5:00 | Click **Download ORCL review and evidence** (`Oracle_Liquidity_2026-08-31.xlsx`). Open **Funding conclusion**, then **Repayment review** rows 5–18, then **Data**. | Funding conclusion repeats the app's rows and lists all ten tabs. Repayment review lists each resource with "Available for future payments?" and each Remainder FY2027 obligation with "Confirmed funds at due date: Unavailable". In Data, find a value's filing, accession, tag and source URL. | Every figure is a formula linked to a reported input, and unknowns read "Unavailable" instead of being estimated. |

## Where each figure lives

| Evidence | App model | Saved file | Reconciliation |
|---|---|---|---|
| Cash, borrowing, ratios, TTM flows | `liquidity_pilot.py`, `cash_generation.py` | `samples/liquidity_pilots.json` | `pilot_evidence_oracle.md`, `ratio_reconciliation.md` |
| Quarter cash bridge, prepayments, equity, dated payments | `oracle_liquidity.py` | `samples/oracle_liquidity.json` | `oracle_liquidity_reconciliation.md` |
| May 31 principal schedule, later 8-Ks | `oracle_financing.py` | `samples/oracle_financing.json` | `oracle_maturity_reconciliation.md` |
| Revolver audit | `oracle_revolver.py` | `samples/oracle_revolver.json` | `oracle_revolver_reconciliation.md` |
| Interest coverage | `oracle_interest.py` | `samples/oracle_interest.json` | `oracle_interest_coverage.md` |
| Funding conclusion | `funding_conclusions.py` | `samples/` (fingerprinted) | `funding_conclusions.md` |
| Primary workbook | `oracle_liquidity.workbook_bytes` | `samples/oracle_liquidity.xlsx` (SHA-256 checked against its manifest before download) | `excel_parity.md` |

## First-time reader obstacles

Observed on October 17, 2026 on the deployed app at desktop width and in the saved Oracle workbook. Each is a reading problem with the existing evidence, not a missing number.

1. **Two near-term debt figures sit far apart and use different windows.** "What payments are actually dated?" (about 3,500 px down the page) gives lease and purchase payments for September 2026–May 2027 at Aug 31. Debt principal appears about 4,000 px further down, under "When was borrowing scheduled to be repaid?", as a fiscal 2027 bucket ($7.210B) for June 2026–May 2027 as of May 31. Current borrowing ($7.625B) is a third, carrying-value figure in the funding conclusion. A reader looking for "what is due soon" has to find and reconcile all three on their own.
2. **The page is long, and its "Unavailable" labels look alike.** The Oracle review runs about 9,000 px with 20 question headings. Seven collapsed rows read "funding coverage Unavailable" and three read "drawable capacity Unavailable". A first-time reader can't tell from the summary line whether a value is Unavailable because the filing doesn't disclose it or because the review hasn't checked it, and can easily stop reading before the revolver and debt-schedule sections.
3. **Following a number to its filing takes several steps in Excel.** Workbook formulas point to the Data sheet, and the source URLs there are plain text, not clickable links (known problem 9). Checking one figure in Excel means following the formula to Data, copying the URL into a browser and finding the page from the location column. The app's links are clickable.

## Limits of this case study

- It covers one company at one balance-sheet date, with the financing screen ending October 15, 2026. It doesn't claim a fresh SEC search.
- It doesn't download from the live site. The walkthrough's workbook is the repository file the app serves, checked against its SHA-256 manifest.
- It isn't investment advice and doesn't rank or rate Oracle.
