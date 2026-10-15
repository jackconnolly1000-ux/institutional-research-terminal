# Oracle liquidity and repayment analysis

Checked October 15, 2026. Saved review for the quarter June 1–August 31, 2026, not a cash forecast.
Implementation: `oracle_liquidity.py`, `oracle_liquidity_view.py`; saved input review and a separate
formula-based Excel workbook in `samples/oracle_liquidity.*`. The existing company-review workbook,
debt maturity schedule, other pilots and saved research remain available.

## Sources checked

- [10-Q, August 31, 2026](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.htm),
  accession `0001193125-26-389274`, filed September 11. Cash flows p. 5, cash and prepayments Note 1
  pp. 6–7, lease and purchase commitments Note 6 pp. 12–13, ATM equity Note 7 pp. 13–14, MD&A pp. 33–35.
- [10-K, May 31, 2026](https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm),
  accession `0001193125-26-277521`, filed June 22. Historical borrowing maturities and credit disclosure,
  Note 6 pp. 83–85. Its principal table remains historical; see `oracle_maturity_reconciliation.md`.
- [March 6, 2026 credit agreement](https://www.sec.gov/Archives/edgar/data/1341439/000119312526101045/orcl-ex10_17.htm),
  Ex. 10.17 to the February 28 10-Q, accession `0001193125-26-101045`, filed March 11.
  The exhibit was not in the uploaded archive; downloaded from the official link in the saved 10-K.
  Reviewed definitions §1.01, advances §2.01, extensions §2.06, draw conditions §4.02,
  financial covenant §6.02(c), and related termination/default provisions.
- Later saved 8-Ks `0001193125-26-387905` (event and filed September 10) and
  `0001193125-26-389753` (event September 12, filed September 14), including their Ex. 99.1.
  The former reports the same quarter equity program and dividends. The latter cancels an insider's
  sale plan. Neither establishes later corporate borrowing. Exact links and findings are retained in
  `oracle_financing.FILINGS` and the workbook About sheet. No complete later inventory was rebuilt.

## Quarter cash reconciliation

USD millions, as printed in the cash-flow statement. Positive amounts add cash, negative amounts use cash.

| Line | Amount |
|---|---:|
| Opening cash including restricted cash, May 31 | 31,289 |
| Reported OCF | 23,103 |
| Investment purchases | (306) |
| Sales and maturities of investments | 225 |
| Cash capex | (28,499) |
| ATM common-stock proceeds, net | 19,909 |
| Employee stock programs, net | 41 |
| Dividends to stockholders | (1,565) |
| Commercial-paper repayments, cash-flow row | 0 |
| Net capex-financing cash flow | (830) |
| Senior notes, term loans and other repayments | (4,202) |
| Other financing, net | (242) |
| Exchange-rate effect | 11 |
| Cash increase | 7,645 |
| Ending cash including restricted cash, August 31 | 38,934 |
| Less: derived ending restricted cash | (2,565) |
| Balance-sheet cash and equivalents, August 31 | 36,369 |

Detailed investing flows equal reported net investing **(28,580)**. Financing flows equal reported
net financing **13,111**. OCF + investing + financing + FX equals **7,645**, which reconciles opening
and ending cash. Ending restricted cash is the difference between the exact rounded-million totals,
not the rounded $2.6B text disclosure. Removing it is a balance exclusion, not another cash use.

The grouped repayment line is counted once. MD&A describes about $3.1B scheduled debt and $1.1B CP
repayment, while the cash-flow CP line shows zero. Classification is unresolved; no extra $1.1B is
deducted and no repayment is assigned to the old maturity buckets. The dividend row's tag name
mentions common stock, but the printed line says payments to stockholders; its printed scope is retained.
Unpaid capex **6,247** is a separate noncash disclosure, not an addition to cash capex.

## Funding contributions and bounded historical calculations

The disclosed customer-prepayment contribution is **11,363**, already inside OCF; its share of OCF
is **49.2%**. The extension is
`orcl:IncreaseDecreaseInDeferredRevenuesFromCustomerPrepaymentsWithSignificantFinancingComponent`.

| Calculation | USD millions |
|---|---:|
| OCF less specified prepayment contribution: 23,103 − 11,363 | 11,740 |
| Reported OCF less cash capex: 23,103 − 28,499 | (5,396) |
| OCF less specified prepayments and capex: 11,740 − 28,499 | (16,759) |
| Cash increase less ATM proceeds: 7,645 − 19,909 | (12,264) |
| Cash increase less ATM and specified prepayments | (23,627) |

These exclusions keep every other actual cash flow fixed. They do not estimate behavioral offsets,
recurring OCF, future capex, financing access or cash runway. The OCF remainder still includes working
capital and other items. Customer prepayments fund future performance obligations and entail service
costs. The $20B gross ATM program was fully utilized; the net proceeds are already in August cash and
are not unused capacity or an additional September inflow. Interest and operating-lease payments
already reflected in OCF are not deducted again.

## Dated commitments at August 31

USD millions. Fiscal years end May 31; remainder FY2027 is September 1, 2026–May 31, 2027.
Lease amounts are undiscounted payments including interest. Columns are not added together.

| Period | Operating leases | Finance leases | Purchase and other |
|---|---:|---:|---:|
| Remainder FY2027 | 3,219 | 620 | 5,449 |
| FY2028 | 4,135 | 852 | 6,176 |
| FY2029 | 4,097 | 923 | 3,863 |
| FY2030 | 4,109 | 947 | 4,318 |
| FY2031 | 4,089 | 971 | 6,768 |
| FY2032 | 4,030 | 996 | 954 |
| Thereafter, combined | 24,371 | 9,886 | 6,622 |
| Total | 48,050 | 15,195 | 34,150 |

Operating payments **48,050 − 13,429** imputed interest = **34,621** recognized liability.
Finance payments **15,195 − 6,010** imputed interest = **9,185** recognized liability.
Each of the three payment columns reconciles independently to its reported total.

Some standard tag names say next twelve months or first anniversary. The printed table explicitly
labels those rows fiscal 2028; source-specific mapping uses that heading, not an inferred rolling year.
The $288B of operating leases not yet commenced is outside this table. Expected commencement in
FY2027–2029 and terms of 15–19 years do not establish annual payment amounts. Annual timing remains
Unavailable. Overlap among purchase obligations, unpaid capex and leases is not established, so no
aggregate funding requirement is inferred.

## Facility interpretation

The original commitment is **$10B**, with a five-year term from March 6, 2026, subject to earlier
termination and agreement terms. Extensions require lender consent and conditions; they are not assumed.
Draws require representations and no default. The minimum contractual coverage is **3.0x**.
Contract EBITDA includes specified addbacks and exclusions. Net cash interest uses contract definitions,
including finance-lease interest and specified swap costs, less cash interest income.

The May 31 10-K reports zero drawn and compliance then. August drawings, drawable capacity and covenant
headroom are Unavailable. Generic operating-income/interest coverage does not establish compliance.
Commercial-paper program capacity is not added to revolver capacity as independent available liquidity.

**Repayment conclusion:** the quarter's spending exceeded OCF and identified prepayments and equity
contributed funding. A future repayment surplus or shortfall cannot be established without remaining
debt payment dates, current drawable credit and future operating cash generation. Missing inputs are
not zero and historical cash is not compared with a mismatched future maturity period.

## Tag checks and reproducibility

The quarter's `orcl-20260831.xsd` embeds its labels and documentation; there is no separate `_lab.xml`
in this accession. Read the schema and embedded labels for all three extensions used here: prepayments,
net capex-financing flows, and operating leases not yet commenced. They are monetary items; the first
two are duration/debit and the lease commitment is instant/credit. Documentation repeats the labels
and adds no timing or availability definition. Source:
[schema with embedded linkbases](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.xsd).

`tests/fixtures/make_oracle_liquidity_fixture.py` retains all 75 real occurrences of the selected tags,
their contexts and units from the saved full 10-Q. No facts are edited. `build_oracle_liquidity.py`
reads exact undimensioned USD facts, checks Oracle CIK, signs, dates and independent reconciliations,
then writes the saved JSON. Cash and the three payment schedules fail independently on missing or
inconsistent inputs.

The separate workbook uses Artifact Tool at build time. Streamlit serves the checked bytes, with no
new deployment dependency or network call. A manifest binds both JSON and workbook hashes; stale
evidence is Unavailable. Formulas retain full dollars, fiscal due dates, source metadata and native
editable chart bindings. Missing numeric inputs propagate as unavailable rather than zero.

Rebuild from the repo using `.venv/bin/python tests/fixtures/make_oracle_liquidity_fixture.py`, then
`.venv/bin/python tests/offline/build_oracle_liquidity.py`. For the Excel file, copy
`tests/offline/build_oracle_liquidity.mjs` and `tests/offline/workbook_style.mjs` to a temporary directory, symlink that directory's
`node_modules` to `CODEX_PRIMARY_RUNTIME_NODE_MODULES`, and run it with `CODEX_PRIMARY_RUNTIME_NODE`,
passing the absolute repo path. This requires the Codex artifact runtime only for rebuilding, not deployment.
