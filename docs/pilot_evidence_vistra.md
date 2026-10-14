# Pilot evidence: Vistra (VST)

Evidence for the third debt and liquidity pilot (see `debt_liquidity_plan.md`): filing values with sources and checks, hand calculations labeled as such, decided classifications, and open gaps. Checked values are the pilot's expected answers; Unavailable items and open gaps are not. Checked Oct 14, 2026. The saved debt and liquidity pilot uses the checked cash, borrowing and current-position values; other sections retain their own status.

**How it was checked:** each amount was read from the filing's HTML text and matched to the inline XBRL fact on that row (tag, period, dimensions, unit), then compared with SEC companyfacts where companyfacts has the tag. Page numbers are the filing's printed page footers, found by splitting the document at its page breaks. Raw downloads are kept outside the repo in `Stock Project/data/raw/` (`xbrl/VST_*`, `sec/VST/`).

**Labels used below:** *Fact* = a reported amount, with its location. *Calculation* = a hand calculation from reported amounts. *Classification* = a first-release decision recorded here (Oct 14, 2026), not a filing statement. *Unavailable* / *Open* = not established.

**Why Vistra is a limit case:** the basic framework (one debt line, one interest line) does not fit. Vistra reports several borrowing-like balance-sheet lines besides long-term debt, project-level debt that the filing says is non-recourse to Vistra Operations, an affiliate collateral financing arrangement, and an "interest expense and related charges" line that includes interest rate swap gains and losses and a debt extinguishment loss. The classifications below are specific to Vistra.

## Filings

| Filing | Period | Filed | Accession | Link |
|---|---|---|---|---|
| 10-Q (balance-sheet date for the pilot) | 2026-06-30 | 2026-08-10 | 0001692819-26-000019 | https://www.sec.gov/Archives/edgar/data/1692819/000169281926000019/vistra-20260630.htm |
| 10-K | 2025-12-31 | 2026-02-27 | 0001692819-26-000006 | https://www.sec.gov/Archives/edgar/data/1692819/000169281926000006/vistra-20251231.htm |

Companyfacts: https://data.sec.gov/api/xbrl/companyfacts/CIK0001692819.json (CIK 1692819).

## Cash and current position at June 30, 2026 (10-Q, USD millions)

| Item | Amount | Location | Tag | Kind |
|---|---|---|---|---|
| Cash and cash equivalents | 435 | Condensed consolidated balance sheet, p. 2 | `CashAndCashEquivalentsAtCarryingValue` | Fact |
| Restricted cash, current | 41 | Balance sheet, p. 2 | `RestrictedCashCurrent` | Fact |
| Restricted cash, noncurrent | 5 | Balance sheet, p. 2 | `RestrictedCashNoncurrent` | Fact |
| Cash, cash equivalents and restricted cash | 481 | Cash flow statement, p. 5 | `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | Fact; 435 + 41 + 5 = 481 (calculation) |
| Total current assets | 10,276 | Balance sheet, p. 2 | `AssetsCurrent` | Fact |
| Total current liabilities | 10,557 | Balance sheet, p. 2 | `LiabilitiesCurrent` | Fact |

Cash for the plan's definition is 435; restricted cash is reported on separate lines and is not included.

## Baseline gross borrowing at June 30, 2026 (classification)

| Component | Amount | Location | Tag | Kind |
|---|---|---|---|---|
| Long-term debt due currently | 1,876 | Balance sheet, p. 2 | `LongTermDebtAndCapitalLeaseObligationsCurrent` | Fact |
| Long-term debt, less amounts due currently | 17,719 | Balance sheet, p. 2 | `LongTermDebtAndCapitalLeaseObligations` | Fact |
| Long-term debt including amounts due currently (carrying amount) | 19,595 | Note 12: Debt, Credit Facilities, and Financings, debt summary, p. 20 | `LongTermDebt` / `LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities` | Fact; equals 1,876 + 17,719 (calculation) |
| Short-term borrowings | 0 ("—"; 1,800 at Dec 31, 2025) | Balance sheet, p. 2; Note 12, p. 20 | `ShortTermBorrowings` | Fact |
| Accounts receivable financing | 300 (1,225 at Dec 31, 2025) | Balance sheet, p. 2; Note 12, pp. 20 and 27 | `vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed` (extension; not in companyfacts) | Fact. Note 12 (p. 27): "outstanding borrowings under the Receivables Facility totaled $300 million", supported by $1.609 billion of gross receivables; Vistra "records interest expense on amounts advanced". |
| **Baseline gross borrowing** | **19,895** | | none | Calculation: 19,595 + 0 + 300 |

- **Carrying amount vs principal (Note 12, p. 20):** principal before premiums, discounts and issuance costs is 19,764 (Vistra Operations debt 18,131 + project-level debt 1,633), less 169 = 19,595 carrying. The baseline uses carrying amounts.
- **Project-level debt, shown as a subset of the 19,595, not added again:** 1,633 principal (Note 12, p. 20; `DebtInstrumentCarryingAmount` with `LongtermDebtTypeAxis = ProjectLevelDebtMember`). It consists of BCOP bridge loans 261 and construction/term loans 503, the Vistra Zero Term Loan B 697, and the Texas Energy Fund loan 172; 261 + 503 + 697 + 172 = 1,633 (calculation; credit facilities table, p. 22). **Recourse is reported by the filing, not assumed here:** for each of the three, the filing says the obligations are secured by that project group's assets "but are otherwise non-recourse to Vistra Operations and its other subsidiaries" (BCOP p. 24; Vistra Zero and TxEF p. 25). The 1,633 is principal: it sits in the block labeled "before unamortized premiums, discounts and issuance costs" (p. 20), so it is not exactly the carrying amount inside the 19,595.
- **Repurchase facility:** no outstanding borrowings at June 30, 2026 (125 at Dec 31, 2025) (Note 12, p. 28). Nothing to add.
- **Leases are not in the baseline** (see Leases).

### Borrowing source audit (Oct 14, 2026)

Checked in the 10-Q's inline XBRL (accession 0001692819-26-000019) and in SEC companyfacts.

| Component | Amount | Inline XBRL fact | Context | Unit / scale / decimals | In companyfacts |
|---|---|---|---|---|---|
| Long-term debt due currently | 1,876 | `us-gaap:LongTermDebtAndCapitalLeaseObligationsCurrent` (balance sheet, p. 2) | c-8: instant 2026-06-30, no dimensions | iso4217:USD / 6 / -6 | Yes, 10-Q, fy 2026, fp Q2 |
| Long-term debt, less amounts due currently | 17,719 | `us-gaap:LongTermDebtAndCapitalLeaseObligations` (balance sheet, p. 2) | c-8 | same | Yes |
| Short-term borrowings | 0 (printed "—") | `us-gaap:ShortTermBorrowings`, format `ixt:fixed-zero` (balance sheet, p. 2) | c-8 | same | Yes, value 0: a reported zero, not a missing fact |
| Accounts receivable financing | 300 | `vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed` (balance sheet, p. 2) | c-8, no dimensions | iso4217:USD / 6 / -6 | **No.** It is a Vistra extension element; companyfacts carries only `dei`, `us-gaap` and `ffd` for Vistra. |
| (same, Note 12 text, p. 27: "outstanding borrowings under the Receivables Facility totaled $300 million") | 300 | same extension element | c-722: instant 2026-06-30, `us-gaap:DebtInstrumentAxis = vistra:AccountsReceivableSecuritizationProgramMember` | USD / 6 | No |

**Debt reconciliation without leases (Note 12, p. 20; calculations from the printed table):**
- Vistra Operations debt 18,131 + project-level debt 1,633 = 19,764 principal; less 169 unamortized premiums, discounts and issuance costs = 19,595.
- 1,876 + 17,719 = 19,595, which is the table's "Long-term debt including amounts due currently" (`us-gaap:LongTermDebt` and `LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities`, c-8).
- Note 12's itemized debt lists senior notes, credit facilities, project-level loans, revenue bonds, equipment financing agreements (46) and other (4); there is no lease line. The balance-sheet tag names include "CapitalLeaseObligations", but the itemization shows debt only. The 10-K (p. 122) places lease liabilities in other current liabilities and other noncurrent liabilities and deferred credits.

**Result:** the three `us-gaap` components come from companyfacts; the 300 comes from the filing's own inline XBRL. Given a document mapped to checked accession 0001692819-26-000019, `xbrl.baseline_gross_debt` calculates 1,876 + 17,719 + 0 + 300 = **19,895M** at June 30, 2026 and keeps the extension fact's context c-8 and document name in its inputs. Without that document it returns Unavailable, keeps the three companyfacts components for review, and never treats the missing 300 as zero. This result is not shown in the app.

**Remaining uncertainty:**
- At Dec 31, 2025 the balance-sheet line was 1,225 while the Receivables Facility's outstanding borrowings were "$1.1 billion" (p. 27) and the repurchase facility had 125 outstanding (p. 28). 1,100 + 125 = 1,225 (calculation) suggests the balance-sheet line includes both facilities; the filing does not say so explicitly. At June 30, 2026 the repurchase facility had no borrowings, so the line and the Receivables Facility agree at 300.
- **Element definition (read Oct 14, 2026)** in the filing's schema `vistra-20260630.xsd` and label file `vistra-20260630_lab.xml` (same accession): `vistra:AccountsReceivableSecuritizationProgramAmountsBorrowed` is a monetary item (`xbrli:monetaryItemType`), `periodType="instant"`, `balance="credit"` (a liability-type amount), not abstract. Standard label "Accounts Receivable Securitization Program, Amounts Borrowed"; the documentation label repeats that text and adds no definition; terse and verbose labels "Accounts receivable financing". This establishes that the fact is a point-in-time borrowed amount under the receivables securitization program, presented as the balance-sheet line. It does not say whether the line also includes the repurchase facility (see the Dec 31, 2025 note above).
- **Filing-level reader (Oct 14, 2026):** `filing_xbrl.read_instant` reads this fact from the saved 10-Q: 300M from context c-8 (no dimensions, USD, scale 6, decimals -6), where the balance-sheet and Note 12 table facts agree; the dimensioned Note 12 text fact (c-722) is not selected. Tested on a trimmed copy of the filing (`tests/fixtures/VST_2026Q2_ixbrl.htm`) and, when saved locally, the full document. `baseline_gross_debt("VST", filing_documents={accession: document})` uses this reader only after the three standard components select the same checked accession. The caller must obtain and pair the real filing document with that accession; the document itself does not contain its accession.

## Shown separately, not in baseline borrowing (classifications)

**Forward repurchase obligation: 613, current (Fact; balance sheet p. 2; Note 12, p. 28).** The June 30 10-Q explains it in its debt note (Note 12, "Forward Repurchase Obligation", p. 28):
- It arises from the purchase of the 15% noncontrolling interest in Vistra Vision from Nuveen and Avenue (agreements dated Sept 18, 2024; closed Dec 31, 2024). Avenue was paid in full at closing; Nuveen is paid in installments through Dec 31, 2026.
- The remaining payments are guaranteed by Vistra Operations and certain subsidiaries.
- In June 2026, Vistra paid $38 million ($19 million principal, $19 million interest).
- "A final principal and interest payment totaling $631 million is due to Nuveen on December 31, 2026."
- The 613 is the present value of the remaining payments discounted at 6% (632 at Dec 31, 2025).
- **Classification:** a current obligation from the minority-interest purchase, shown separately; not conventional borrowing and not in the 19,895.

**Margin deposits financing with affiliate: 438, noncurrent liability (Fact; balance sheet p. 2), with a matching current asset "Margin deposits posted under affiliate financing agreement" of 438 (balance sheet p. 2).** Note 11: Collateral Financing Agreement with Affiliate (p. 19):
- In 2023 a Delaware trust formed by the company (the Trust, not consolidated) sold 450,000 pre-capitalized trust securities (P-Caps), redeemable May 17, 2028, for $450 million, and invested the proceeds in Treasuries.
- At Vistra Operations' direction, those eligible assets can be delivered to subsidiaries to meet posting obligations with counterparties or pledged for a letter of credit program.
- The fair value of eligible assets held by counterparties, $438 million at June 30, 2026 ($444 million at Dec 31, 2025), is reported as both the asset and the liability.
- **Classification:** shown separately with its matching asset; not added to baseline borrowing, because no rule for affiliate collateral financing has been decided.

**Near-term category:** the 613 Nuveen obligation (above) stays in its own near-term category, separate from both baseline borrowing and the obligations note below.

**Not borrowing:** Series A and Series B preferred stock, 2,476 in equity (balance sheet p. 3). Letters of credit, surety bonds and the collateral bond are under Commitments.

## Leases (USD millions)

| Item | Amount | Date | Location | Tag | Kind |
|---|---|---|---|---|---|
| Lease liabilities at June 30, 2026 | **Unavailable** | 2026-06-30 | | | The 10-Q reports finance lease right-of-use assets (192 gross, 40 accumulated amortization; Note on property, plant and equipment, p. 16) but no lease liability amounts were found in it. |
| Operating lease liabilities, current / noncurrent | 13 / 92 (total 105) | 2025-12-31 | 10-K lease note, p. 122 (current in "other current liabilities"; noncurrent in "other noncurrent liabilities and deferred credits") | `OperatingLeaseLiabilityCurrent` / `Noncurrent` / `OperatingLeaseLiability` | Fact, older date |
| Finance lease liabilities, current / noncurrent | 4 / 218 (total 222) | 2025-12-31 | 10-K lease note, p. 122 (same balance-sheet lines) | `FinanceLeaseLiabilityCurrent` / `Noncurrent` / `FinanceLeaseLiability` | Fact, older date |
| Total lease liabilities | 327 | 2025-12-31 | 10-K, pp. 122-123 (maturity table: 648 payments less 321 imputed interest) | | Fact, older date |

Lease liabilities are not in baseline borrowing. The Dec 31, 2025 amounts may be shown only with their own date.

## Interest expense for operating-income interest coverage

Vistra's statement of operations (p. 1) shows "Interest expense and related charges" (312 for Q2 2026, 575 for the six months). Its components are in Note 12 (p. 28) and, for 2025, the 10-K (p. 121). **The coverage denominator is the separately reported "Interest expense" component, not the mixed total.**

| Component (USD millions) | FY2025 | H1 2025 | H1 2026 | Q2 2026 |
|---|---|---|---|---|
| Interest expense | 1,107 | 547 | 557 | 272 |
| Unrealized mark-to-market net (gains) losses on interest rate swaps | 67 | 74 | (7) | 9 |
| Amortization of debt issuance costs, discounts, and premiums | 46 | 22 | 21 | 12 |
| Debt extinguishment (gain) loss | — | — | 35 | 35 |
| Capitalized interest | (125) | (56) | (82) | (40) |
| Other | 84 | 35 | 51 | 24 |
| **Total interest expense and related charges** | **1,179** | **622** | **575** | **312** |
| Source | 10-K p. 121 | 10-Q p. 28 (comparative) | 10-Q p. 28 | 10-Q p. 28 |

- Each column adds to its total (calculation).
- **Tags:** the "Interest expense" component is tagged `vistra:PostEmergenceInterestPaidAndAccrued`, a **Vistra extension element** (defined in each filing's own schema, for example `vistra-20260630.xsd`), with no dimensions. The total is `us-gaap:InterestExpenseNonoperating`. Companyfacts carries only standard taxonomies (for Vistra: `dei`, `us-gaap`, `ffd`), which is why the component is absent there.
- **H1 2025 checked against the prior 10-Q:** the 10-Q for June 30, 2025 (filed 2025-08-08, accession 0001692819-25-000085, p. 30) reports the same component as 547 for the six months, with the same extension tag, no dimensions. It matches the 2026 10-Q's comparative column.
- **TTM interest to June 30, 2026 (hand-checked calculation):** 1,107 + 557 - 547 = **1,117**. All three inputs are the same component, and each was matched to its printed table.

**Inline XBRL contexts checked for the component (tag `vistra:PostEmergenceInterestPaidAndAccrued`, unit iso4217:USD, scale 6, decimals -6, no dimensions):**

| Filing (accession) | Context | Period | Value | Printed location |
|---|---|---|---|---|
| 10-K 2025 (0001692819-26-000006) | c-1 | 2025-01-01 to 2025-12-31 | 1,107 | p. 121 |
| 10-Q Q2 2026 (0001692819-26-000019) | c-1 | 2026-01-01 to 2026-06-30 | 557 | p. 28 |
| 10-Q Q2 2026 (0001692819-26-000019) | c-7 | 2025-01-01 to 2025-06-30 | 547 | p. 28 (comparative) |
| 10-Q Q2 2025 (0001692819-25-000085) | c-1 | 2025-01-01 to 2025-06-30 | 547 | p. 30 |

**Extraction finding:** the inputs can be extracted from the filings' inline XBRL with verified context (period, no dimensions), unit, scale and accession, and they match the printed tables. Companyfacts omitting the tag is an implementation constraint, not a reason to call the ratio permanently Unavailable. Not yet done: reading the extension element's definition and label in the filer's schema and label files, and building and testing an extractor. Until that extractor passes these checks, the app shows no Vistra coverage ratio.

**Operating income inputs (us-gaap:OperatingIncomeLoss, no dimensions; all also in companyfacts):**

| Period | Amount | Location |
|---|---|---|
| FY2025 | 1,906 | 10-K statement of operations, p. 79 |
| H1 2026 | 2,052 | 10-Q statement of operations, p. 1 |
| H1 2025 | 395 | 10-Q statement of operations, p. 1 (comparative); same in the 2025 Q2 10-Q |

- TTM operating income to June 30, 2026 (calculation): 1,906 + 2,052 - 395 = **3,563**.
- Operating-income interest coverage (hand calculation, not for display yet): 3,563 / 1,117 = **3.19x**, labeled "Operating income / reported interest expense (before capitalized interest)".
- The 10-K also tags a parent-only operating loss (-114, `ConsolidatedEntitiesAxis = ParentMember`); it is not used.
- **Basis:** the component is shown **before capitalized interest**, which is a separate line (82 in H1 2026; 125 in FY2025). It excludes swap mark-to-market, amortization of debt costs, extinguishment losses and "Other". It is before interest income, which the statement does not net against it. Label: "Operating income / reported interest expense (before capitalized interest)".
- **Uncertainty:**
  1. Vistra says it "records interest expense on amounts advanced" under the receivables facility (p. 27), and the forward repurchase obligation carries interest ($19 million paid in June 2026, p. 28). The filings do not say whether those amounts are in the "Interest expense" component or in "Other".
  2. What "Other" (51 in H1 2026) contains is not stated.
  3. The app's coverage for Vistra waits on an inline XBRL extractor (see the extraction finding above).

## Obligations and commitments outside baseline debt

None of these is added to borrowing, lease liabilities, each other or any ratio. The first-release note shows each separately with its date.

**Recognized nondebt liability**

| Item | Amount | Date | Location | Kind and status |
|---|---|---|---|---|
| Asset retirement obligations | 197 current + 4,072 noncurrent = 4,269 | 2026-06-30 | Balance sheet, p. 2 (facts); total is a calculation. Note 15: Asset Retirement Obligations, p. 38 | Recognized liability, not borrowing. Per Note 15 they "primarily relate to nuclear generation plant decommissioning, land reclamation related to lignite mining, remediation or closure of coal ash basins, and generation plant disposal costs". The balance is an estimate of future retirement costs, not an amount payable now; only the 197 is classified as current. Note 15's detail beyond its opening was not reviewed. |

**Near-term obligation (own category):** the 613 Nuveen forward repurchase obligation, with its 631 final payment due Dec 31, 2026 (see above).

**Future commitment: Helix Fund (10-Q Note 7: Equity Method Investment, p. 15; MD&A Liquidity, p. 69, paragraph beginning "Additionally, as of June 30, 2026"; referenced in Note 16, p. 39)**

| Part | Amount | What the filing says | Funding at June 30, 2026 |
|---|---|---|---|
| Initial commitment | up to $500 million | "an initial $500 million commitment" under the limited partnership agreement entered into in June 2026 | MD&A p. 69: the $500 million initial commitment "remains callable by the fund's general partner" as of June 30, 2026; the timing and amount of capital calls are set by the general partner. **Amount funded to date: not separately disclosed** in the sections checked (no funded or called amount, no tagged fact), so it stays unverified. |
| Additional commitment | up to $500 million | "subject to the Helix Fund meeting certain commercial power supply milestones for our existing generation assets or, at the Company's election, regardless of whether such milestones are achieved" | MD&A p. 69: contingent on the milestones, "which has not occurred as of June 30, 2026". Note 7 adds that Vistra may also elect to make it regardless of the milestones. |

**Credit support and security (separate disclosures, not borrowing, not added together; 10-Q Note 16: Commitments and Contingencies, p. 39)**

| Item | Amount | What it is |
|---|---|---|
| Letters of credit outstanding | $3.587 billion | Issued "to support commodity risk management and collateral requirements" and other purposes. The filing's breakdown by purpose: $3.006 billion commodity risk management and collateral (including $843 million of collateral postings with ISOs/RTOs), $307 million battery and solar projects, $110 million EPA, $86 million PUCT retail requirements, $18 million executory contracts and insurance, $60 million other. By facility (Note 12): $1,092 million under the revolving credit facility (p. 22), $1.759 billion under the LOC facilities (p. 25), $736 million under the alternative LOC facilities (p. 25); these sum to $3.587 billion (calculation), so they are parts of the same total, not additions. |
| Surety bonds outstanding | $979 million, including $81 million with ISOs/RTOs | Financial performance assurance for subsidiaries' obligations; Vistra must reimburse any surety payment. |
| Reclamation collateral bond (Railroad Commission of Texas) | up to $975 million | A collateral bond supporting Luminant's mining reclamation obligations; "effectively a first lien on all of Vistra Operations' assets" that lets the RCT be paid up to $975 million before other first-lien lenders in a liquidation. A limit, not an amount drawn. |

**Overlap the filing identifies:** within the letters of credit, the $843 million of ISO/RTO collateral postings is part of the $3.006 billion purpose line; the facility amounts are parts of the $3.587 billion total. Both ISO/RTO amounts (letters of credit $843 million and surety bonds $81 million) relate to ISOs/RTOs, but the filing does not say they cover the same obligations. The filing does not state any overlap between the letters of credit, the surety bonds and the reclamation bond, or how the reclamation obligations covered by the bond relate to the recognized asset retirement obligations. Note 11 says the P-Caps eligible assets can be "pledged as collateral support for a letter of credit program"; the amount so pledged is not stated.

**Future commitments at an older date**

| Item | Amount | Date | Location | Status |
|---|---|---|---|---|
| Long-term purchase commitments: long-term service and maintenance contracts 3,075; coal transportation agreements 90; pipeline transportation and storage reservation fees 1,818; water contracts 77 | 5,060 (calculation) | 2025-12-31 | 10-K commitments table, p. 140 (tags `ContractualObligation` by category) | No June 30, 2026 update was found in the 10-Q; a June 30 amount is **Unavailable**. Shown only with its Dec 31, 2025 date. |

**Sections checked:**
- **10-Q (read in full):** balance sheet (pp. 2-3), statement of operations (p. 1), cash flow statement (pp. 4-5); Note 7 Helix Fund (p. 15); property, plant and equipment (p. 16); Note 11 (p. 19); Note 12 Debt, Credit Facilities, and Financings (pp. 20-28); Note 16 Commitments and Contingencies, p. 39 (letters of credit, surety bonds, collateral bond, litigation introduction).
- **10-Q MD&A:** Liquidity, p. 69 (Helix Fund paragraph).
- **10-Q (opening only):** Note 15 Asset Retirement Obligations (p. 38).
- **10-K:** statement of operations (p. 79); lease policy (p. 90); interest expense and related charges (p. 121); leases (pp. 122-123); commitments table (p. 140).
- **10-Q Q2 2025:** interest expense and related charges table (p. 30) and statement of operations facts.
- **Not fully reviewed:** litigation and regulatory proceedings (10-Q Note 16, pp. 40-43; read only through the start of the Winter Storm Uri matter on p. 40), the rest of Note 15, Note 13 Derivatives, the 10-K's full commitments, contingencies and guarantees text, and the 10-K litigation note. Legal matters there are not quantified in this file.
## Financing filings since the balance sheet

**App status (Oct 14, 2026):** `reviewed_financing.py` joins ten manually screened Vistra filings (six 8-Ks and S-3ASR, 424B5, FWP, 424B2) to the subsequent-filing index only when accession, form and filed date match the live EDGAR list and the balance-sheet anchor is June 30, 2026. The six 8-Ks also require the event date to match. The June 30 8-K reports an event before the balance sheet; July 14 is a power capacity auction, not borrowing; August 7 is an earnings release with June 30 liquidity and a Helix investment commitment. The July 16 receivables 8-K and its Exhibits 4.1/10.1, September 11 pricing FWP, September 14 final 424B2 prospectus, September 24 issuance 8-K and Exhibit 4.2, and October 2 facility 8-K and Exhibit 10.1 support the later financing rows. The S-3ASR and preliminary 424B5 do not by themselves establish issuance. The four offering documents support the one September 24 completed issuance, not four debt events. The indenture permits interest deferral up to 10 consecutive years per deferral period; that term is displayed with the issuance. The $1.48 billion net proceeds and preferred-stock redemption remain the prospectus's estimate and intention. Any new or mismatched indexed candidate remains **Not checked**; an incomplete index stays incomplete. These later events do not change June 30 debt or cash.

The complete EDGAR filing list (submissions JSON, 1,000 most recent filings back to 2017-04-27) was retrieved Oct 14, 2026 at 3:08 PM laptop time; the newest filing in it was dated October 8, 2026. Forms screened by content from June 30, 2026 through October 14, 2026: 8-K (6, with exhibits where relevant), 424B5, 424B2, FWP, S-3ASR. No 8-K/A. June 30 balance-sheet amounts stay dated June 30; nothing below changes them.

| Event date | Filed | Form, items | Accession | What happened | Kind of amount |
|---|---|---|---|---|---|
| 2026-06-24 | 2026-06-30 | 8-K, 1.01, 2.03, 9.01 | [0001140361-26-026944](https://www.sec.gov/Archives/edgar/data/1692819/000114036126026944/) | Revolving credit commitments raised from $3.44 billion to $5.50 billion; guarantors released; covenant changes. Commodity-linked facility amended. | Facility capacity. **Not post-balance-sheet:** the event predates June 30; the 10-Q's credit facilities table (p. 22) already shows the $5,500 limit. |
| 2026-07-10 | 2026-07-16 | 8-K, 1.01, 2.03, 9.01 | [0001140361-26-028619](https://www.sec.gov/Archives/edgar/data/1692819/000114036126028619/) | Receivables facility commitment raised from $1.1 billion to $1.25 billion and extended to July 9, 2027; repurchase facility extended to July 9, 2027 | Facility capacity and term; not an outstanding balance |
| 2026-07-14 | 2026-07-14 | 8-K, 8.01 | [0001140361-26-028454](https://www.sec.gov/Archives/edgar/data/1692819/000114036126028454/) | PJM capacity auction results | Not financing |
| 2026-08-07 | 2026-08-07 | 8-K, 2.02, 9.01 (EX-99.1) | [0001692819-26-000017](https://www.sec.gov/Archives/edgar/data/1692819/000169281926000017/) | Q2 2026 earnings release; restates June 30 liquidity ($4,408 million revolver and $1,452 million commodity-linked availability) | Facility capacity as of June 30; no later financing |
| 2026-09-08 to 2026-09-14 | 2026-09-09 (S-3ASR), 09-10 (424B5, preliminary), 09-11 (FWP), 09-14 (424B2, final) | S-3ASR, 424B5, FWP, 424B2 | 0001140361-26-035954, -036130, -036245, -036415 | Shelf registration and offering documents for the notes below | Offering documents |
| 2026-09-24 | 2026-09-24 | 8-K, 1.01, 8.01, 9.01 | [0001140361-26-037577](https://www.sec.gov/Archives/edgar/data/1692819/000114036126037577/) | Vistra Operations completed an offering of $1.5 billion of junior subordinated notes due 2057: $850 million at 7.000% (Series A) and $650 million at 7.250% (Series B), guaranteed by Vistra | **New debt issued after the balance sheet.** Per the 424B2 "Use of Proceeds", net proceeds of about $1.48 billion are intended for general corporate purposes, including funding the redemption of some or all of the Series A and Series B preferred stock at their October and December 2026 reset dates. **Redemption is an intended use; no filing checked confirms it occurred.** |
| 2026-09-30 | 2026-10-02 | 8-K, 1.01, 2.03, 9.01 | [0001140361-26-038468](https://www.sec.gov/Archives/edgar/data/1692819/000114036126038468/) | Commodity-linked revolving credit facility maturity extended from Sept 30, 2026 to Sept 29, 2027 | Change of terms; no amount |

## Open gaps

1. Lease liabilities at June 30, 2026 are Unavailable; only Dec 31, 2025 amounts are established.
1a. The saved pilot displays and exports the 19,895M baseline, built from companyfacts and the trimmed real-filing fixture. Live analysis still does not fetch or pass the checked filing document for this calculation.
2. Interest basis: whether receivables-facility interest and the Nuveen obligation's interest are inside the "Interest expense" component or in "Other", and what "Other" contains, are not stated.
3. Interest extraction: the component is the Vistra extension tag `vistra:PostEmergenceInterestPaidAndAccrued`. Its contexts are verified by hand above. Still needed before any display: read the element's definition and label in the filer's schema, and build and test an inline XBRL extractor that reproduces the four checked facts with their provenance.
4. Helix Fund: amount funded to date not separately disclosed (callable status and milestone status are stated on p. 69).
5. Purchase commitments only at Dec 31, 2025; no June 30 update found.
6. Overlap among letters of credit, surety bonds and the reclamation bond, and between the reclamation bond and the recognized asset retirement obligations, is not stated; the P-Caps amount pledged for letters of credit is not stated.
7. Whether the Series A and B preferred stock redemptions occurred (intended at the October and December 2026 reset dates).
8. Not fully reviewed: litigation and regulatory proceedings (10-Q pp. 40-43), the rest of Note 15 (asset retirement obligations), Note 13 (derivatives), and the 10-K's full commitments, contingencies, guarantees and litigation text.
9. Possible additions to the obligations note from the sections not yet reviewed (gap 8). The items listed above are the decided first-release scope; this gap does not reopen them.
10. Vistra-specific limits to state in the app's README "Known limits": borrowing-like lines beyond long-term debt, non-recourse project debt, affiliate collateral financing, a mixed interest line whose borrowing component uses an extension tag.
