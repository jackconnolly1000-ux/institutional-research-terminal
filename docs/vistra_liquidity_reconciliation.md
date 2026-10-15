# Vistra liquidity and repayment review

Checked October 15, 2026. Amounts below are USD millions unless stated otherwise.
This is a saved filing review. It does not forecast cash or determine contractual compliance.

## Source documents

| Source | Period / event | Filed | Accession | Checked sections |
|---|---|---|---|---|
| [10-Q](https://www.sec.gov/Archives/edgar/data/1692819/000169281926000019/vistra-20260630.htm) | June 30, 2026 | Aug 10, 2026 | 0001692819-26-000019 | Cash flows pp.4–5; balance sheet p.2; acquisitions p.9; Helix p.15 and p.69; Note12 pp.20–28; credit support p.39; liquidity pp.67–70 |
| [10-K](https://www.sec.gov/Archives/edgar/data/1692819/000169281926000006/vistra-20251231.htm) | Dec 31, 2025 | Feb 27, 2026 | 0001692819-26-000006 | Debt and maturities pp.113–115; distribution language p.116 and Schedule I pp.159–160 |
| [Corporate credit amendment, Ex.10.1](https://www.sec.gov/Archives/edgar/data/1692819/000114036126026944/ef20077059_ex10-1.htm) | June 24, 2026 | June 30, 2026 | 0001140361-26-026944 | Clean agreement Annex B: Compliance Period definition, §§7.1–7.2, 9.13, 10.9; June commodity amendment Ex.10.2 also read |
| [Receivables amendment, Ex.4.1](https://www.sec.gov/Archives/edgar/data/1692819/000114036126028619/ef20077984_ex4-1.htm) | July 10, 2026 | July 16, 2026 | 0001140361-26-028619 | §§2.1–2.5 and purchaser Schedule VI; repurchase amendment Ex.10.1 §2 also read |
| [Commodity-linked amendment, Ex.10.1](https://www.sec.gov/Archives/edgar/data/1692819/000114036126038468/ef20083016_ex10-1.htm) | Sept 30, 2026 | **Oct 5, 2026** | 0001140361-26-038468 | Amendment commitment schedule, §§1.1, 2.1, 5.2, 7.1–7.2 and 10.9 |
| [Final prospectus](https://www.sec.gov/Archives/edgar/data/1692819/000114036126036415/ny20081693x3_424b2.htm) and [issuance 8-K](https://www.sec.gov/Archives/edgar/data/1692819/000114036126037577/ef20082680_8k.htm) | Sept 24 issuance | Sept 14 / Sept 24 | …-036415 / …-037577 | Use of proceeds and terms; supplemental indenture Ex.4.2 also read |

The saved primary financing documents and relevant exhibits are retained outside the repo.
The SEC submissions index was retrieved October 15: six 8-Ks and four offering-form candidates
since June 30, matching the ten accession-specific records in `reviewed_financing.py`.
No later financing candidate appeared in that retrieved index. This does not classify future
filings; new or mismatched index rows remain Not checked.

**Date correction:** the …-038468 filing index and submissions JSON state October 5 as the
filing date. Its acceptance timestamp is October 2 at 20:12:47. The older review used the
acceptance date. Event date remains September 30.

## Cash sources and uses: January 1–June 30, 2026

| Cash source / use | Amount |
|---|---:|
| Opening cash including restricted cash | 822 |
| Reported operating cash flow | 2,222 |
| Capital expenditures including nuclear fuel and LTSA prepayments | (1,572) |
| **Operating cash flow less capital spending** | **650** |
| Debt issuance cash proceeds | 6,422 |
| Corporate revolver borrowings | 400 |
| Commodity-linked borrowings, reported zero | 0 |
| Debt repayments / repurchases | (3,859) |
| Revolver repayments | (780) |
| Commodity-linked repayments | (1,420) |
| Net receivables financing repayments | (925) |
| **Net debt cash flow** | **(162)** |
| Stock repurchases | (709) |
| Common dividends | (154) |
| Preferred dividends | (96) |
| **Buybacks and dividends** | **(959)** |
| Other investing, derived from the components below | 293 |
| Debt issuance costs | (72) |
| Share compensation tax withholding | (69) |
| Nuveen principal paid | (19) |
| Other financing | (3) |
| **Cash change including restricted cash** | **(341)** |
| **Ending cash including restricted cash** | **481** |

Bold subtotals are calculations and are not added again to their component rows.
Other investing = Lotus adjustment 6 + trust-security sales 3,036 − trust purchases 3,037
+ environmental allowance sales 128 − allowance purchases 201 + insurance 234 + asset sales 50
+ other investing 77 = 293. Detailed investing equals reported −1,279; detailed financing equals
reported −1,284. 2,222 − 1,279 − 1,284 = −341; 822 − 341 = 481.

Ending cash 481 = balance-sheet cash 435 + restricted current 41 + restricted noncurrent 5.
The restricted 46 is a balance exclusion, not another cash outflow.
650 − 959 = −309 after capex, buybacks and dividends, before other investing and financing.
This is historical arithmetic. OCF includes working capital and margin movements, and the
filing states seasonality toward the second half. No recurring OCF or annualized H1 forecast
is inferred. Nuveen's 19 interest paid in June is not deducted again from OCF; the 19 principal
cash-flow line is separate. Nuclear trust-security sale proceeds are not gross available
corporate cash. Debt issuance is financing, not operating cash generation.

## Repayment dates and commitments

| June 30 amount / term | Amount | Date / status |
|---|---:|---|
| Pulaski bridge principal | 261 | Dec 3, 2026; Vistra guarantees repayment |
| Pulaski construction balance | 297 | December 2026; conversion requires commercial operation and other conditions |
| 5.050% senior notes principal | 500 | Dec 30, 2026 |
| Nuveen final principal **and interest** | 631 | Dec 31, 2026; same obligation as 613 carrying amount |
| 3.700% senior notes principal | 800 | Jan 30, 2027 |
| 5.000% senior notes principal | 1,300 | July 31, 2027 |
| Cogentrix expected cash consideration | approximately 2,300 | Late-2026 closing expectation; conditions/adjustments apply. Exact date and completed closing Unavailable |
| Helix initial commitment | 500 | Callable at June 30; timing and funded-to-date Unavailable |
| Helix additional commitment | up to 500 | Milestones unmet at June 30; elective funding also allowed |

The chart compares selected outstanding balances, not a complete debt-service schedule.
Senior-note coupons are additional. No sum combines these amounts with carrying balances,
the full annual maturity schedule, project debt a second time, or conditional Helix funding.
Cogentrix also contemplates estimated debt assumption and share consideration; these are not
added to its expected cash payment.

Historical December 31, 2025 debt principal schedule: 2026 1,201; 2027 3,435; 2028 786;
2029 2,362; 2030 2,853; thereafter 6,559. Total 17,196 − 153 costs = 17,043 carrying debt.
The schedule is **not rolled forward** after April refinancing and other first-half debt activity.
A complete remaining June debt-service schedule is Unavailable in this review.

## Resources, constraints and recourse

- June liquidity: 435 cash + 4,408 revolver availability + 1,452 commodity-linked availability
  = **6,295**, matching MD&A p.68. This is not cash all located at Parent.
- Revolver: limit 5,500 − drawings 0 − LCs 1,092 = **4,408**. General corporate purposes include
  permitted acquisitions/investments/restricted payments under §9.13, subject to conditions.
- Commodity-linked: 1,750 commitment, 0 drawings and 1,452 available under the weekly hedge-based
  borrowing base. A declining base can require repayment. General corporate uses are also allowed;
  this facility is not characterized as restricted solely to commodity margin.
- Revolver §§7.1–7.2 require no default, specified representations and borrowing notice. §10.9 caps
  contract-defined total net leverage at 5.50x during a Compliance Period. The >35% usage trigger
  excludes specified LCs, including undrawn LCs. Undrawn LCs reduce available capacity without
  automatically being trigger usage. No contractual headroom or current compliance is calculated.
- September commodity amendment keeps 1,750 commitments and changes maturity to Sept 29, 2027.
  It does not establish a new cash inflow, current borrowing base or current availability.
- Receivables July purchase limit 1,250 and repo limit 125 are capacities under their own
  structures. Eligible receivables, draw conditions, current balances and repo lender discretion
  prevent treating the limits as freely drawable cash. Repo uses the receivables subordinated
  note, so an independent extra collateral pool is not assumed.
- Project principal 261 bridge + 503 BCOP construction/term + 697 Vistra Zero + 172 TxEF = **1,633**.
  BCOP's 503 = 297 construction + 206 **combined** term balance. The 206 is repeated in three tagged
  prose contexts; it is selected once, not added three times. Term loans amortize from conversion
  over 20 years and have a Dec 2029 final maturity; no 206 balloon is invented.
- Project 1,633 + Operations 18,131 = 19,764 principal − 169 costs = 19,595 long-term carrying
  debt. Add 300 receivables and reported-zero short-term borrowing = **19,895** baseline debt.
  Project debt is already included. BCOP/Zero/TxEF unused capacity is zero in the June table.
  The 583 TxEF development agreement is not free remaining capacity. Project security/recourse
  applies; the Vistra bridge guarantee is identified as an exception.
- LCs: 1,092 revolver + 1,759 other LOC facilities + 736 alternative facilities = **3,587**.
  Other LOC facilities are uncommitted credit support, not cash. Note12 also states 13 of BCOP
  debt-service reserve LCs while its facility table shows zero project LCs. Scope/overlap is
  unresolved; no additional aggregate is inferred. Surety/reclamation support is not added.
- Posted margin 1,436 and affiliate-financed eligible assets 438 are already posted. They are
  not added to cash. Restrictions, release timing and project/parent transfer amounts are Unavailable.
- Annual permission to distribute Vistra Operations net assets and 1,625 of actual 2025 subsidiary
  dividends do not prove future transfers or locate June cash. Current Parent-accessible cash
  remains Unavailable. Downgrade-dependent distribution restrictions remain relevant.

## Later financing

July extensions are changes of capacity/term. The September FWP, prospectus and issuance 8-K
describe **one** 1,500 junior-note issuance on Sept24, not multiple inflows. The 1,480 net proceeds
are a prospectus estimate, and preferred redemptions are intended uses, not verified completed
uses. The indenture's interest deferral right is subject to its terms, not an assumed cash saving.
No September proceeds or October renewal capacity is added to June balances.

## Implementation and reproducibility

`filing_xbrl` retains undimensioned selection by default. New optional exact dimensions are used
only by the filing-specific Vistra rules, with exact period, USD, entity CIK, scale, sign and
duplicate/context checks. No different tag, dimension or period is substituted. Extension
elements and labels were read in `vistra-20260630.xsd` and `_lab.xml`: the new cash-flow extension
facts are monetary durations; facility balances, Nuveen and affiliate assets are monetary
instants. Helix commitment facts are durations for June 1–30; those are disclosure periods,
not capital-call dates. The Cogentrix tagged context is Dec31,2025, not its future payment date.

Run from the repo:

```bash
.venv/bin/python tests/fixtures/make_vistra_liquidity_fixture.py
.venv/bin/python tests/offline/build_vistra_liquidity.py
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python tests/offline/check_liquidity_app.py
```

The fixture keeps all occurrences of selected tags, real contexts and units unchanged from
the saved filing. Full-document comparison also runs when the raw documents exist locally.
Build the workbook with `tests/offline/build_vistra_liquidity.mjs` from a temporary directory
using the Codex spreadsheet runtime and its `node_modules` symlink. The app only serves the
saved workbook when review/workbook SHA256 hashes match its manifest. Native editable charts,
formulas, real dates and source provenance are retained; deployment needs no new dependency.

Workbook recalculation checks include every cash control, annual carrying reconciliation,
revolver and LC totals, and debt reconciliation. Missing, zero and changed capex inputs are
tested before restoring source values. Current drawable fields stay explicitly Unavailable.
Excel desktop execution is not claimed; the artifact engine and exported file are checked.
