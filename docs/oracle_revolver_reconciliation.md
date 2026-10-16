# Oracle revolver availability audit

Checked October 15, 2026, using seven saved documents only. The last saved filing is the
September 14 8-K. This audit does not establish completeness of subsequent filings or current capacity.

## Dated reconciliation

USD millions. Undrawn commitment is contractual headroom before testing a particular borrowing.
It is not cash or a verified drawable amount.

| Evidence date | Commitment | Outstanding advances | Undrawn commitment | Drawable amount |
|---|---:|---:|---:|---|
| March 6, 2026 agreement | 10,000 original | Unavailable | Unavailable | Unavailable: actual borrowing and draw conditions not established |
| May 31, 2026 10-K | 10,000 reported | 0 reported | 10,000 − 0 = 10,000 | Unavailable: no borrowing-specific confirmation of all conditions |
| August 31, 2026 10-Q | Unavailable as of this date | Unavailable | Unavailable | Unavailable: updated commitment, advances and conditions not established |

The 10-K reports debt-covenant compliance at May 31. It does not disclose the contract ratio or
headroom. The old $6B facility was terminated on March 6 and is not added to the replacement $10B.
The August borrowing and repayment lines do not establish revolver usage. May balances and
compliance are not carried forward.

## Contract findings

- **Exposure and LCs:** §1.01 defines Revolving Credit Exposure as outstanding advances. §2.01 limits
  each lender's advances to its commitment. These operative provisions do not create an LC issuance
  subfacility or an LC deduction. Other definitions mention letters of credit, including the broad
  definition of Debt and the exclusion of LC fees from cash interest. Company-wide LC use is not
  disclosed in the saved set and is not assumed zero. No arbitrary LC amount is subtracted.
- **Reductions:** §2.04 permits reducing unused commitments with three business days' notice.
  Partial reductions start at $10M with $1M increments and cannot take commitments below outstanding
  exposure. Terminated commitments cannot be reinstated. §7.01 provides default remedies including
  acceleration and termination. No later reduction amount is established by this saved set.
- **Increase option:** §2.05(d) caps aggregate commitments after an increase at **$12B**. Lender
  consent, documentation and other conditions apply. No exercised increase is established. The
  ceiling is not a $12B commitment or an extra $2B of available cash.
- **Draws:** §2.02 requires borrowing notice by 11 a.m. New York time three business days before
  Term SOFR borrowing or on the borrowing day for Base Rate. §4.02 requires specified representations
  before and after the borrowing and use of proceeds, with stated exceptions/materiality rules, and
  no continuing or resulting Default or Event of Default. No borrowing-specific confirmation is saved.
- **Covenant:** §§1.01 and 6.02(c) require at least **3.0x** contract-defined net interest coverage at
  fiscal quarter-end. Four-quarter EBITDA includes specified cash/noncash adjustments. Cash interest
  includes finance-lease interest and net swap costs, excludes LC fees, and is net of cash interest
  income. Acquisition/pro-forma rules also apply. Generic operating-income coverage cannot substitute.
  §6.01(f)(iii) requires a no-default certificate with financial reports. No separate certificate is
  in the saved documents. Its absence here does not establish a failure to deliver it to lenders.
- **Uses:** §§2.21 and 6.01(g) allow working capital and other general corporate purposes, subject to
  Regulation U/X and sanctions, anti-corruption, anti-bribery and anti-money-laundering restrictions.
  This establishes potential permitted use, not an allocation to any obligation.
- **Maturity:** original maturity is **March 6, 2031**, subject to earlier termination. §2.06 allows
  requesting up to two 365-day extensions, individual lender elections, a greater-than-50% extension
  threshold including replacement commitments, and conditions. Non-extending lenders retain their
  dates. No extension has been established. No funding after the original expiry is assumed.
- **Commercial paper:** the separate program size is neither an extra available cash pool nor an
  automatic contractual reduction of revolver exposure. No combined $20B capacity is calculated.

## Saved later filings

- September 10 8-K and Exhibit 99.1: quarter results, the completed equity sale and dividends. No new
  revolver balance, exercised increase, reduction, extension or drawable amount is established.
- September 14 8-K and Exhibit 99.1, event September 12: insider trading-plan cancellation. No
  corporate revolver update is established.

Neither finding proves that no later financing occurred outside this saved set.

## Sources and reproducibility

- [FY2026 10-K](https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm),
  filed June 22, accession 0001193125-26-277521, Note 6 pp. 84–85.
- [Q1 FY2027 10-Q](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.htm),
  filed September 11, accession 0001193125-26-389274, Note 5 p. 11 and MD&A pp. 33–35.
- [Credit agreement](https://www.sec.gov/Archives/edgar/data/1341439/000119312526101045/orcl-ex10_17.htm),
  dated March 6, filed March 11 as Exhibit 10.17, accession 0001193125-26-101045.
- [September 10 8-K](https://www.sec.gov/Archives/edgar/data/1341439/000119312526387905/orcl-20260910.htm)
  and [Exhibit 99.1](https://www.sec.gov/Archives/edgar/data/1341439/000119312526387905/orcl-ex99_1.htm),
  accession 0001193125-26-387905.
- [September 14 8-K](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389753/d20034d8k.htm)
  and [Exhibit 99.1](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389753/d20034dex991.htm),
  accession 0001193125-26-389753.

`oracle_revolver.py` retains the hand-reviewed terms and exact source fingerprints. Run
`python tests/offline/build_oracle_revolver.py [saved-ORCL-folder]` to reproduce
`samples/oracle_revolver.json`. Missing or changed saved documents require review and stop the build.
Deployment uses this saved audit without network access. An edited/mismatched audit is Unavailable.

The app and existing Oracle workbook consume the same audit through `oracle_repayment.py`.
The workbook adds dated capacity, terms and later-filing rows on Repayment review, plus Data provenance.
The May undrawn amount is an Excel formula with missing-input propagation. The conditional ceiling is
separate. The export manifest also binds this audit. Existing cash, payment and catalyst evidence is
unchanged. Coverage remains Unavailable for every future obligation.

## Evidence still needed

A dated borrowing balance and effective commitment update, any amendments or exercised options,
and the applicable contract definitions/compliance evidence would be needed to establish more than
historical undrawn commitment. Borrowing-date conditions still need their own confirmation. A complete
later-filing inventory is a separate task; adding more arithmetic to this saved set cannot resolve it.
