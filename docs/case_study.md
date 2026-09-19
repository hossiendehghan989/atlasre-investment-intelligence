# Illustrative acquisition case study

> **ILLUSTRATIVE ONLY. This is not a real transaction, a client mandate, or an investment recommendation.**

This example uses fixed inputs so a reviewer can reproduce the model outputs and the independent numerical checks. The figures are deliberately treated as unverified source data by the screening workflow.

## Inputs

| Input | Value |
| --- | ---: |
| Purchase price | $8,500,000 |
| Annual NOI, year 1 | $620,000 |
| Hold period | 5 years |
| NOI growth from year 2 | 2.50% |
| Exit cap rate | 6.50% |
| Leverage | 55.00% |
| Debt rate | 6.25% |
| Acquisition cost | 3.00% |
| Selling cost | 2.00% |
| Discount rate | 10.00% |

The model convention is that the supplied $620,000 is **year-one NOI**. Growth begins in year two. Terminal value is final-year NOI divided by the exit cap rate.

## Model outputs

| Output | Value |
| --- | ---: |
| Entry cap rate | 7.29% |
| Exit value | $10,528,677 |
| Unlevered IRR | 10.31% |
| Levered IRR | 14.15% |
| Unlevered NPV | $110,936 |
| Equity multiple | 1.85x |
| Minimum DSCR | 1.51x |

The equity multiple is total positive distributions divided by total negative equity cash flows. If interim cash flows are negative, those additional contributions remain in the denominator rather than being discarded.

## Screening flags

The case is passed to the workflow with source status `REVIEW REQUIRED`. The economic outputs above do not change that status. The initial screen therefore records one governance flag:

| Severity | Flag | Evidence |
| --- | --- | --- |
| GOVERNANCE | Source package is not verified | `REVIEW REQUIRED` |

The flag means the case should remain in review until the operating statement, rent roll, exit-cap evidence, financing terms, and other supporting material are confirmed. It does not mean the model has proven the transaction is unattractive.

## Independent cross-checks

The levered IRR was recomputed from the returned levered cash-flow vector with `numpy-financial`:

| Check | Model | Independent calculation | Difference |
| --- | ---: | ---: | ---: |
| Levered IRR | 14.149828% | 14.149828% | less than 2e-14 |
| Unlevered NPV | $110,935.66 | $110,935.66 | less than 2e-9 |

The NPV check directly discounts the independently rebuilt unlevered cash flows, including acquisition cost, year-one NOI, subsequent grown NOI, terminal value, and selling costs. The debt test independently applies the monthly payment formula for a 6.25% annual rate and compares the resulting 60-month balance path with the model schedule within a $1e-6 tolerance.

## Reproduction

From the repository root:

```bash
python -m pip install -r requirements-test.txt
python -m pytest -q tests/test_independent_crosschecks.py
```

The case is intentionally small. It demonstrates how the model exposes assumptions, calculations, and a governance flag; it does not demonstrate live data ingestion, document reconciliation, tax treatment, complete lease economics, or an approval workflow.
