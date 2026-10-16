# Lilly financing inventory and contractual maturities

Checked through October 15, 2026. The material addition is an eight-series **initial issuance schedule** from May's $9B offering. It is not a complete June or October outstanding-principal schedule. Drawable bank capacity and future funding coverage remain **Unavailable**.

## Inventory comparison

[SEC submissions](https://data.sec.gov/submissions/CIK0000059478.json) retrieved for this review contains 1,001 filing rows, latest October 15, 2026 and oldest December 16, 2021. Its two older pages end before 2026; no 2026 row is omitted by using the recent page. Snapshot SHA256: `c271d2468744874b2c34fa4beec68b10d9dc9547910833d521ddbc22031c9269`.

All 2026 form rows were screened. Periodic reports and amendments, 8-Ks, shelf/prospectus/pricing forms and debt delisting were prioritized. Ownership filings are not treated as issuer borrowing. After June 30 the index lists the saved August 5 10-Q and August 5 earnings 8-K; no later periodic report/amendment, 424B2 or FWP is listed through the cutoff. The latest ownership filing does not update credit availability. This conclusion is dated; it is not a promise of future completeness.

The original saved set had the FY2025 10-K, June 2026 10-Q and August 5 8-K/exhibit. Missing relevant documents were retrieved and retained with URLs, accession numbers and SHA256 fingerprints in `lly_financing.py` and the saved audit JSON:

| Document | Filed / accession | Use |
| --- | --- | --- |
| [Completed offering 8-K](https://www.sec.gov/Archives/edgar/data/59478/000119312526232707/d148580d8k.htm) | May 20, 2026 · 0001193125-26-232707 | Item 8.01 confirms completion and initial principal; Item 9.01 identifies exhibits. |
| [Final prospectus](https://www.sec.gov/Archives/edgar/data/59478/000119312526213175/d81251d424b2.htm) | May 8, 2026 · 0001193125-26-213175 | Cover, Description of Notes, Use of Proceeds; corroborates dates and rates. |
| [Preliminary prospectus](https://www.sec.gov/Archives/edgar/data/59478/000119312526207625/d81251d424b2.htm) and [pricing FWP](https://www.sec.gov/Archives/edgar/data/59478/000119312526209416/d110421dfwp.htm) | May 6, 2026 · …-207625 / …-209416 | Offering history; later completed terms control the selected schedule. |
| [Underwriting agreement, Ex. 1.1](https://www.sec.gov/Archives/edgar/data/59478/000119312526232707/d148580dex11.htm) | May 20, 2026 · …-232707 | Corroborating issue documentation; not unused financing. |
| [Fixed certificate and note forms, Ex. 4.3](https://www.sec.gov/Archives/edgar/data/59478/000119312526232707/d148580dex43.htm) | May 20, 2026 · …-232707 | Clauses (iii)–(v): initial limits, stated maturities and rates; note forms: redemption terms. |
| [Floating certificate and note forms, Ex. 4.4](https://www.sec.gov/Archives/edgar/data/59478/000119312526232707/d148580dex44.htm) | May 20, 2026 · …-232707 | Initial limits, stated dates, SOFR margins and note-specific conditions. |
| [Incorporated 1991 indenture](https://www.sec.gov/Archives/edgar/data/59478/000005947813000010/exhibit41-indenturedatedfe.htm) | March 1, 2013 · 0000059478-13-000010 | General note terms, including §1.11 legal holidays. This is not a bank credit agreement. |
| [March 2026 10-Q](https://www.sec.gov/Archives/edgar/data/59478/000005947826000045/lly-20260331.htm) | April 30, 2026 · 0000059478-26-000045 | Historical unused facilities and exhibit screening. |
| [September 2025 10-Q](https://www.sec.gov/Archives/edgar/data/59478/000005947825000254/lly-20250930.htm) | October 30, 2025 · 0000059478-25-000254 | Note 7 describes the August **2025** renewal and extension. |
| [Shelf registration](https://www.sec.gov/Archives/edgar/data/59478/000119312525029608/d933321ds3asr.htm) | February 19, 2025 · 0001193125-25-029608 | Debt/indenture and exhibit references; no verified drawable bank amount. |
| [Form 25](https://www.sec.gov/Archives/edgar/data/59478/000087666126000494/primary_doc.xml) | June 2, 2026 · 0000876661-26-000494 | Delisting of the 1.625% notes due 2026, not a cash repayment allocation. |

The May filing indexes were checked against their document/exhibit lists. The annual, March and June reports and shelf references were searched for bank credit agreements and renewals. No relevant current bank agreement or August 2026 renewal was identified in that review. This is a retrieval finding, not a claim that such agreements cannot exist.

## May issue: documented dates

Principal in USD millions. The completed offering confirms issuance on May 20, 2026; the certificates are filed forms corroborated by the final prospectus.

| Series | Initial principal | Stated maturity | Contract rate |
| --- | ---: | --- | --- |
| Floating 2028 | 750 | May 20, 2028 | Compounded SOFR + 0.350% |
| Floating 2029 | 500 | May 20, 2029 | Compounded SOFR + 0.460% |
| Fixed 2029 | 750 | May 20, 2029 | 4.150% |
| Fixed 2031 | 1,500 | May 20, 2031 | 4.375% |
| Fixed 2033 | 1,250 | May 20, 2033 | 4.650% |
| Fixed 2036 | 1,500 | May 20, 2036 | 4.850% |
| Fixed 2056 | 1,750 | May 20, 2056 | 5.600% |
| Fixed 2066 | 1,000 | May 20, 2066 | 5.700% |
| Initial issue total | **9,000** | | |

**Do not add the 9,000 to June debt or cash.** It is already reflected in the June balance sheet and H1 proceeds. Initial face principal differs from net cash proceeds and from carrying values. Later redemptions, changes in series balances and actual balances at future payment dates have not been established. This schedule adds supported contractual dates without pretending to reconstruct the full June repayment calendar.

Dates are stated contractual maturities. Business-day provisions, optional redemption and default acceleration can affect actual payment. No calendar-adjusted settlement forecast, future floating interest amount or interest-inclusive funding requirement is calculated.

### Coupon conflict

The 8-K interest paragraph describes 4.650% for the fixed 2029 notes, contradicting its series title. The final prospectus and Exhibit 4.3 clauses (i)/(v) and note form consistently specify **4.150%**. The selected rate follows the corroborated contract terms. The conflicting 8-K sentence remains flagged rather than silently treated as an amendment.

### Acquisition-related special redemption

Specified series had a 101% acquisition-failure redemption condition. The documents say that condition ceases upon consummation. The saved June 10-Q Note 4 reports Centessa acquired June 24, 2026. Accordingly, this review does not manufacture a future 101% payment from the former acquisition-failure clause. Other contractual redemption/default provisions remain; no exercise is assumed.

## Credit conclusion unchanged

The September 2025 report says the 364-day facility was renewed and increased to $6B in August **2025**, and the multiyear facility increased to $4B with expiry December 2029. The annual report supplies August 2026 expiry for the 364-day facility. The older renewal is not evidence of renewal in August 2026.

March and June 2026 unused facilities are dated disclosures. No post-expiry renewal, current usage, contract draw conditions, permitted uses or covenant headroom was established by the retrieved evidence. Unused commitment is not demonstrated drawable cash. The note indenture does not supply revolver conditions. No new drawable amount or repayment coverage is calculated.

## Implementation and checks

`lly_financing.py` binds the manual contract audit to exact saved-source fingerprints and the exact index snapshot. `load()` refuses an edited/stale sample; the app restricts it to the checked June Lilly snapshot. The Lilly workbook links each initial amount, maturity and rate to Data, reconciles the eight amounts to the completed offering's 9,000, and propagates missing principal into Unavailable. Its download manifest includes the financing JSON. Existing metrics, cash build, catalysts, other-company reviews and exports are preserved.
