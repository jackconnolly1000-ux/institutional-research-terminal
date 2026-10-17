# Lilly principal calendar: why it stays Unavailable

Checked October 17, 2026, against the saved Lilly filings, using the method that dated Oracle's principal ([`oracle_principal_calendar.md`](oracle_principal_calendar.md)). **Result: a dated, instrument-level principal calendar at June 30, 2026 is not supported by the saved evidence.** The Lilly review keeps "remaining principal dates" as a decisive unknown. Nothing in the app, the workbook or the numbers changes.

## What was checked

| Source | What it gives | Why it isn't enough |
|---|---|---|
| [10-K for 2025](https://www.sec.gov/Archives/edgar/data/59478/000005947826000013/lly-20251231.htm), Note 11, p. 76 (accession 0000059478-26-000013) | Debt at December 31, 2025 by **due-year bucket** at carrying value: e.g. notes due 2026 $1,632M, 2027 $2,516M, 2028 $3,256M, then ranges (2031–2040 $11,582M, 2041–2050, 2051–2060, 2061–2070), with "other long-term debt and adjustments" of −$339M. | No individual notes, no exact maturity dates, and amounts are carrying values, not principal. Stated-rate ranges (e.g. 0.420%–4.500%) show euro and other currency series inside a bucket, so USD amounts move with exchange rates. |
| 10-K inline XBRL | 20 `DebtInstrumentCarryingAmount` facts: the same 10 due-year bucket members (`lly:NotesDue2025Member` … `lly:NotesDue20612070Member`) at Dec 31, 2024 and Dec 31, 2025. No member is an individual note. | No `DebtInstrumentMaturityDate` and no 10-K maturity-bucket tags (Oracle had both). |
| [10-Q for June 30, 2026](https://www.sec.gov/Archives/edgar/data/59478/000005947826000081/lly-20260630.htm) (accession 0000059478-26-000081) | Balance sheet: $7,050M short-term borrowings and current maturities. Fair-value note: $5,284M commercial paper and $49,624M long-term debt including the current portion, both at carrying value. Cash flows (H1 2026): $8,941M of long-term debt issued and $1,623M repaid. May issuance details. | No borrowing note and no maturity table. The repayment line doesn't say which series were repaid. |
| [May 2026 issuance](https://www.sec.gov/Archives/edgar/data/59478/000119312526232707/d148580d8k.htm) (8-K, accession 0001193125-26-232707), already audited in [`lly_financing_audit.md`](lly_financing_audit.md) | Eight new series with initial principal, stated maturity and rate ($9.0B). | Covers only the new series, not the existing debt. |

## The observation that is not adopted

H1 2026 long-term debt repayments ($1,623M) are within $9M of the December 31 "notes due 2026" bucket ($1,632M). That is **consistent with** the 2026 notes having matured by June 30. But:
- the bucket is a carrying value in USD, which may include euro notes affected by exchange rates;
- the 10-Q doesn't name the repaid series;
- a note due in the second half of 2026 could still be outstanding.

Under the Oracle rule (*don't subtract repayments unless the evidence identifies what they repaid*), the 2026 bucket isn't marked repaid and no June 30 calendar is built.

## What would resolve it

1. **The next 10-K** (for 2026, likely filed February 2027), if its debt note keeps the due-year table. A per-note table with dates would allow an Oracle-style calendar.
2. **Each existing series' prospectus supplement or indenture exhibit**, which gives stated principal and maturity per note, reconciled to the 10-K buckets (including currency translation). This is a large manual audit: dozens of series across many filings.
3. **A Lilly 10-Q or 8-K naming 2026 redemptions or maturities.**

Until one of these is reviewed, Lilly's review shows the due-year carrying amounts and the May issuance schedule, each on its own date and basis. Future funding coverage stays Unavailable.
