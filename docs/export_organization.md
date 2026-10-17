# Excel organization and scope

The individual LLY, ORCL and VST downloads remain the primary records. Their analytical sheets,
figures, formula caches, charts, hyperlinks and source distinctions are preserved. Faint vertical
separators define columns; existing outlines define calculation blocks. Equivalent core sheets
already share names. Company-specific detail names remain different because their contents differ:
Lilly combines cash and repayment in Repayment review; Oracle separates those into Repayment review
and Cash analysis; Vistra's Cash review includes the financing-cost reconciliation.

The optional combined download contains only Debt and liquidity, Liquidity inputs and About.
The full Oracle maturity and financing detail belongs in its individual workbook. Company dates,
fiscal calendars and definitions differ; the summary is not a peer ranking.

## Scenario record

The separate Oracle scenario workbook opens on Results. Its monthly, correlation and outside-use
sensitivity tables retain the current run. Scenario records the chosen distributions and controls;
Data retains historical filing inputs, exact periods, forms, filed dates, accessions and clickable
filing URLs. The checked principal calendar is classified as derived rather than a reported subtotal.
About explains units, colors, reproduction, omissions and the payment-date limit.

Results are saved Monte Carlo statistics. Editing this workbook does not rerun the model; change
assumptions in the app and download again. Deterministic input links and the cumulative-proceeds
sensitivity arithmetic remain Excel formulas. Proceeds are not an outstanding balance or a payment due.

## Reproduction

Copy `tests/offline/organize_exports.mjs` and `workbook_style.mjs` into an OS temporary directory
with the Codex Artifact Tool runtime available. Run the copied script with the repository path and
an output directory. It authors the combined workbook, scenario template and border overlays, and
renders the changed sheets. Then run:

```
PYTHONPATH=. python tests/offline/apply_export_layout.py OUTPUT_DIRECTORY
```

The border overlay changes only style references in the existing company files. The original
formulas, cached results, charts, native links and all other ZIP parts are retained. This avoids a
date-handling error encountered when round-tripping the original Oracle file through the authoring
runtime. Source/style gates and workbook hashes are rebound after the patch.

The app hydrates current run values into the Artifact Tool-authored `scenario_template.xlsx` using
standard-library OpenXML handling in `scenario_export.py`; it needs no Node runtime on Streamlit.
The template is fingerprinted. Source URLs receive native hyperlinks to their own displayed text.

Native desktop Excel is unavailable in the cloud editing environment. Formula caches, independent
arithmetic, artifact-runtime recalculation and reopened XML/workbook structure are checked here;
native Excel recalculation is not claimed.
