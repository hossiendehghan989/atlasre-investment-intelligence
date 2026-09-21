# Using an owner-supplied deal locally

The owner supplies all real deal data, source references, and reviewer details. Run the CLI only on a local machine or private environment. The hosted demo has no authentication and shared hosting; never enter confidential deal data there or upload it to this repository.

## Prepare and run

Copy `docs/templates/deal_template.json` to a local path, remove or preserve its underscore-prefixed descriptions, and replace the illustrative values with owner-supplied values and units. Percentages are decimal fractions: 6% is `0.06`; counters such as `hold_years`, `debt_amortization_years`, and `simulations` must be integers.

```bash
python scripts/screen_deal.py /private/path/deal.json --output /private/path/deal-review
```

The command fails closed for missing fields, unknown fields, non-finite values, negative percentages, non-integer counters, and invalid core-model ranges. It writes the memo, assumptions, risk summary, annual debt schedule, stress cases, lineage, and Excel reconciliation workbook to the output directory.

## Verification gate

The package says **REVIEW REQUIRED** unless both `verified_by` and `source_reference` are non-empty. Supplying `source_status: VERIFIED` alone is not sufficient. The gate does not verify the source document, the valuation, legal matters, or tax treatment; those remain owner and reviewer responsibilities.

## Compare with your own Excel

Open the generated `excel_reconciliation.xlsx` in Excel or LibreOffice and recalculate it. Use its **Reconciliation** sheet to compare the workbook's formula result and the Python model result. Add a `Your figure` column beside the model-output column in your own working copy and a difference formula such as `=YourFigure-ModelOutput`. Record the source, date, unit, and any convention differences next to each comparison.

## Boundaries

The CLI is local screening tooling, not source-document ingestion, valuation, legal or tax diligence, investment approval, accounting, or production underwriting. Review all assumptions, terminal value, debt terms, taxes, capex reserve, TI/LC, refinance, and capital-stack items that matter to your case before using any output.
