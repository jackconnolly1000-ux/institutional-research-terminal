# Pilot cash-flow reconciliation

Checked October 14, 2026 against the uploaded, saved full filings. All values below are USD millions.
The cash-flow statement row labels and their inline XBRL facts agree. These are the independently read expected
values, not outputs copied from the calculation function.

| Company | Reported period | Operating cash flow | Reported capital spending | Source |
|---|---|---:|---:|---|
| LLY | FY2025 | 16,813 | 7,841 | 10-K, 2025-12-31; accession 0000059478-26-000013 |
| LLY | H1 2026 | 16,023 | 5,259 | 10-Q, 2026-06-30; accession 0000059478-26-000081 |
| LLY | H1 2025 comparative | 4,753 | 3,207 | Same 2026 10-Q |
| ORCL | FY2026, 2025-06-01 to 2026-05-31 | 31,977 | 55,663 | 10-K, 2026-05-31; accession 0001193125-26-277521 |
| ORCL | Q1 FY2027, 2026-06-01 to 2026-08-31 | 23,103 | 28,499 | 10-Q, 2026-08-31; accession 0001193125-26-389274 |
| ORCL | Q1 FY2026 comparative, 2025-06-01 to 2025-08-31 | 8,140 | 8,502 | Same 2026 10-Q |
| VST | FY2025 | 4,070 | 2,752 | 10-K, 2025-12-31; accession 0001692819-26-000006 |
| VST | H1 2026 | 2,222 | 1,572 | 10-Q, 2026-06-30; accession 0001692819-26-000019 |
| VST | H1 2025 comparative | 1,171 | 1,458 | Same 2026 10-Q; also agrees with 2025 Q2 10-Q |

## Hand calculations

Each TTM amount is fiscal year + current year to date − prior year to date. Overlapping periods are not summed.

| Company | TTM through | Operating cash flow | Reported capital spending | FCF = OCF − spending | OCF / debt | FCF / debt |
|---|---|---|---|---|---:|---:|
| LLY | 2026-06-30 | 16,813 + 16,023 − 4,753 = **28,083** | 7,841 + 5,259 − 3,207 = **9,893** | **18,190** | 51.1% | 33.1% |
| ORCL | 2026-08-31 | 31,977 + 23,103 − 8,140 = **46,940** | 55,663 + 28,499 − 8,502 = **75,660** | **−28,720** | 37.5% | −22.9% |
| VST | 2026-06-30 | 4,070 + 2,222 − 1,171 = **5,121** | 2,752 + 1,572 − 1,458 = **2,866** | **2,255** | 25.7% | 11.3% |

Denominators are checked period-end baseline borrowing: LLY 54,908; ORCL 125,337; VST 19,895.
Ratios are historical flows divided by period-end debt, not repayment forecasts or measures of cash available for
all obligations. FCF here excludes acquisitions, dividends and other cash uses. Dates differ; these pilots are not peers.

## Definitions and selection

- All three OCF rows use `us-gaap:NetCashProvidedByUsedInOperatingActivities`.
- **LLY:** the filed row is "Purchases of property and equipment", tagged
  `us-gaap:PaymentsToAcquireOtherPropertyPlantAndEquipment`. The generic `xbrl.ttm_metrics` FCF still has no fallback
  to this tag. The saved company review uses this specifically checked presentation through `cash_generation.build`.
- **ORCL:** "Capital expenditures", `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`. OCF includes $11.4B of
  customer prepayments with a significant financing component received in Q1 FY2027 (10-Q p. 7; MD&A pp. 33–34).
  The review states this next to OCF and FCF. It makes no recurring-cash-flow adjustment. Capex-financing cash flows
  are not added to the cash capital-expenditure line.
- **VST:** "Capital expenditures, including nuclear fuel purchases and LTSA prepayments", same standard capex tag.
  This includes long-term service agreement prepayments, rather than only purchases of PP&E. The review states that basis.
- `filing_xbrl.read_duration` requires the exact tag, start and end, undimensioned USD context, and agreeing facts
  within a single context. It applies scale/sign and preserves context, decimals and the entity identifier.
  Wrong periods, units, dimensions, conflicting values and ambiguous contexts give Unavailable. `cash_generation`
  also checks the selected entity against the pilot CIK. The caller pairs documents with their known accessions;
  an inline document does not itself establish its accession.
- This is a frozen six-document mapping, not a general cash-flow method for unreviewed filings. The six trimmed
  fixtures preserve all facts for the chosen tags, plus their contexts and units. Full originals remain outside git.

## Sources and reproduction

- [LLY FY2025 10-K](https://www.sec.gov/Archives/edgar/data/59478/000005947826000013/lly-20251231.htm)
  and [June 2026 10-Q](https://www.sec.gov/Archives/edgar/data/59478/000005947826000081/lly-20260630.htm).
- [ORCL FY2026 10-K](https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm)
  and [August 2026 10-Q](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.htm).
- [VST FY2025 10-K](https://www.sec.gov/Archives/edgar/data/1692819/000169281926000006/vistra-20251231.htm)
  and [June 2026 10-Q](https://www.sec.gov/Archives/edgar/data/1692819/000169281926000019/vistra-20260630.htm).

From the repository: `tests/fixtures/make_cashflow_fixtures.py` rebuilds the small fixtures from the raw files;
`tests/offline/build_liquidity_pilot.py` rebuilds the saved review; `tests/test_cash_generation.py` checks the
independent values above and, when all six full files are saved, agreement with those full documents.

The Excel export uses formulas linked to each reported period's input, retaining the annual and quarterly source
links separately. Selected obligations are manually checked disclosures from the existing pilot evidence files;
they do not enter debt or flow ratios. Interest coverage, maturities and a full obligations review remain open.
