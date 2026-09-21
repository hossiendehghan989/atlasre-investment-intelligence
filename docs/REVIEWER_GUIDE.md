# Reviewer guide for the ILLUSTRATIVE case

This guide explains how to check the default acquisition case independently. AtlasRE is screening decision support, not a valuation opinion or approval workflow. The workbook, package, and screenshots use **ILLUSTRATIVE** inputs and remain subject to source-document reconciliation.

Start with the [project overview](OVERVIEW.md), then use the [review request](REVIEW_REQUEST.md) to define scope and the [structured checklist](review/REVIEW_CHECKLIST.md) to record findings. No independent review is claimed by this repository.

## Start with the control sheet

Open `excel_reconciliation.xlsx` in Excel or LibreOffice and allow the workbook to recalculate. Read the **Control** sheet first. It identifies the model version, source status, and run fingerprint. Then open **Inputs**. The values in that sheet are the complete core acquisition input set: price, year-one NOI, hold period, NOI growth, exit cap, discount rate, transaction costs, leverage, debt rate, amortization period, and IRR hurdle.

A reviewer should first confirm that the source status is appropriate. The default case is `REVIEW REQUIRED`. It must not be treated as source-backed merely because the workbook calculates. Next, check the year-one NOI, exit cap, discount rate, leverage, debt rate, and the distinction between the discount rate and the IRR hurdle. Those assumptions drive the headline outputs.

## Formula map

| Review item | Python source of truth | Workbook check |
| --- | --- | --- |
| Input validation, acquisition cost, initial debt and equity | `src.atlasre.validate_deal` and `src.atlasre.underwrite_deal` | **Inputs** cells B4:B15 |
| Annual NOI and terminal value | `src.atlasre.underwrite_deal` | **Annual NOI** formulas in columns B:E; year one is the supplied NOI and growth begins in year two |
| Monthly debt balance, interest and principal | `src.atlasre.underwrite_deal` | **Debt Schedule** columns C:I use `PMT`, `IPMT`, and `PPMT` |
| Annual debt service and DSCR | `src.atlasre.underwrite_deal` | **Annual NOI** columns F:G aggregate the monthly schedule |
| Levered and unlevered cash flows | `src.atlasre.underwrite_deal` | **Cash Flows** columns B:C |
| IRR, NPV and equity multiple | `src.atlasre._irr`, `src.atlasre._npv`, and `src.atlasre.underwrite_deal` | **Cash Flows** cells B11:B14 use `IRR`, `NPV`, and `SUMIF` formulas |
| Formula-versus-model variance | `src.reconciliation.build_reconciliation_workbook` | **Reconciliation** columns B:D and status column F |
| Seeded tail-risk summary | `src.advanced_underwriting.monte_carlo_underwriting` and `risk_summary` | `risk_summary.json`; it is intentionally not an Excel probability model |
| Screening gates and memo | `src.ic_workflow.screen_case` and `generate_ic_memo` | `investment_committee_report.md` and the dashboard review note |

## Modeling conventions

The core model treats supplied annual NOI as **year-one NOI**. It grows NOI from year two onward. Exit value equals final-year NOI divided by exit cap rate, and selling cost is a percentage of exit value. Acquisition cost is a percentage of purchase price. Debt is one monthly amortizing loan; the outstanding balance at the end of the hold is deducted from final-year levered cash flow. Unlevered NPV includes the period-zero acquisition cash flow. Equity multiple divides all positive levered distributions by all negative levered contributions.

The package uses a seeded Monte Carlo simulation with seed 42. The random input generation, clipping bounds, simulation count, and first-root IRR convention are deterministic. The default report and dashboard review-file download both use 5,000 simulations. A regression test compares the dashboard-equivalent risk summary with the CLI package's serialized `risk_summary.json` for the default case.

## Known gaps

The workbook reconciles the simplified acquisition model only. It does not ingest or validate rent rolls, operating statements, comparable transactions, debt term sheets, property taxes, capex reserves, TI/LC, tenant credit, refinancing, hedges, legal terms, tax, FX, or a capital stack. The debt worksheet uses standard spreadsheet functions, while the Python model deliberately selects the first economically reachable IRR root. Conventional cash-flow streams should reconcile closely; unusual multi-root streams require explicit reviewer judgment.

## Reproduce the headline figures in ten minutes

1. Create a virtual environment and install the exact locked dependencies: `python -m pip install -r requirements.lock`.
2. Run `python generate_committee_report.py` from the repository root. It writes the default **ILLUSTRATIVE** package into `artifacts/`.
3. Open `artifacts/excel_reconciliation.xlsx` in Excel or LibreOffice and recalculate. Confirm that the **Reconciliation** difference column is within the tolerance shown for each row.
4. Compare the workbook's model-output column with `artifacts/investment_committee_report.md`. For the default inputs, the report shows 11.97% levered IRR, 9.32% unlevered IRR, 1.70x equity multiple, $12,193,012 exit value, and approximately -$278,827 unlevered NPV.
5. Inspect `artifacts/risk_summary.json` and `artifacts/annual_debt_schedule.csv`. The report's downside statistics and debt-at-exit disclosure should match those artifacts.
6. Confirm the model version and fingerprint in the report, workbook Control sheet, and `README_ILLUSTRATIVE.md` match. A changed input or model version should change the fingerprint.

The repository test `tests/test_reconciliation_workbook.py` checks the workbook structure and independently re-evaluates the formula inputs with Python and NumPy Financial. The full suite also includes IRR, NPV, and debt-schedule cross-checks.
