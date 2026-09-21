# Independent finance review request

## Scope

Please review the transparent, early-stage screening model for one acquisition case. The review should assess whether the stated formulas, modeling conventions, downside flags, source-status gate, and Excel reconciliation are internally coherent and sufficiently clear for an analyst to inspect.

## Out of scope

This request does not ask you to supply a deal, validate source documents, provide a valuation opinion, approve an investment, or attest to legal, tax, accounting, engineering, market, or investment-advice conclusions. All bundled inputs are **ILLUSTRATIVE**; the owner will supply any real case separately and locally.

## Time needed

The requested review is 30–60 minutes. Please use the [overview](OVERVIEW.md), [reviewer guide](REVIEWER_GUIDE.md), generated workbook, and [checklist](review/REVIEW_CHECKLIST.md).

## Where the formulas live

The core annual acquisition model is in `src/atlasre.py`, especially `underwrite_deal`, `_irr`, and `_npv`. Seeded downside calculations are in `src/advanced_underwriting.py`, especially `monte_carlo_underwriting` and `risk_summary`. Review-package assembly is in `generate_committee_report.py`; workbook formulas and reconciliation are in `src/reconciliation.py`; source gating is in `src/ic_workflow.py`.

## Conventions to inspect

Annual NOI is year-one NOI; growth begins in year two. Exit value is final-year NOI divided by exit cap rate, less selling cost. Acquisition cost is a percentage of price. Debt is one monthly amortizing loan and remaining debt is deducted at exit. Equity multiple divides positive levered distributions by negative levered contributions. Monte Carlo shocks are seeded and are not calibrated market probabilities.

## Known gaps

The prototype does not ingest source documents and does not model a complete operating statement, property taxes, capex reserve, TI/LC, tenant credit, refinance, hedges, legal terms, tax, FX, or a complete capital stack. The workbook must be recalculated in Excel or LibreOffice. The hosted demo has no authentication and is not a place for confidential data.

## Most useful feedback

Please identify a specific formula, convention, missing practitioner control, unclear disclosure, or reproducibility problem; state whether it is a blocker, material, minor, or informational; and point to the relevant file, function, sheet, or row. Please distinguish a modeling disagreement from an input or source-document limitation. No review has yet been claimed by this repository.
