# Implementation evidence report

## Scope completed

The `review-fixes` branch now includes a faster deterministic review-package pipeline, formula-based Excel reconciliation, dashboard package progress feedback, refreshed screenshots, committed **ILLUSTRATIVE** sample outputs, reviewer and demo materials, and Streamlit Community Cloud deployment guidance. The work did not modify `main` or merge pull request #1.

The default visual case is explicitly **ILLUSTRATIVE** and remains `REVIEW REQUIRED`. The refreshed dashboard values come from the current code run: 11.97% levered IRR, 9.32% unlevered IRR, 1.70x equity multiple, $12,193,012 exit value, and approximately -$278,827 unlevered NPV. Earlier dashboard screenshots showing 13.21% levered IRR and $12,558,802 exit value were stale; this is documented in `CHANGELOG.md`.

## Package performance

The pre-change default `python generate_committee_report.py` run took **86.66 seconds**. The final default run took **1.95 seconds**, a measured **44.4x** reduction. The dashboard configuration used by **Prepare review files** runs 1,000 seeded simulations and took **0.73 seconds** in a direct measurement.

The default CLI package still uses 5,000 simulations with seed 42. The optimization did not lower that count. It batches the shared rate-grid calculation across simulations and uses the existing scalar root solver only to refine each scenario's first identified root. The regression suite locks the prior default risk-summary values, preserving the seeded default result contract.

| Profile observation | Before | After |
| --- | ---: | ---: |
| Wall-clock time for default package | 86.66 s | 1.95 s |
| `_npv` calls in cumulative profile | 5,143,693 | 62,487 |
| Main source of time | Per-scenario scalar IRR grid scan | Root refinement after vectorized grid evaluation |

## Excel reconciliation evidence

The package now includes `excel_reconciliation.xlsx`. Its Input, Annual NOI, Debt Schedule, Cash Flows, Reconciliation, and Lineage sheets contain live spreadsheet formulas and a static Python output column. The workbook uses `IRR`, `NPV`, `PMT`, `IPMT`, and `PPMT` formulas.

A headless LibreOffice recalculation of the default workbook returned `PASS` for all eight reconciliation rows. Entry cap, exit value, unlevered NPV, and equity multiple differences were zero at displayed precision. The remaining debt difference was $0.000000028; minimum DSCR, unlevered IRR, and levered IRR differences were below 0.00000001, within the documented tolerances.

## Validation evidence

| Check | Measured result |
| --- | --- |
| Local regression suite | 102 passed in 9.39 seconds |
| Ruff | `ruff check .` passed |
| GitHub Actions CI | Passed in 33 seconds on the pushed branch [2] |
| Fresh-clone dependency install | 31.41 seconds |
| Fresh-clone test suite | 102 passed in 9.47 seconds |
| Fresh-clone dashboard health endpoint | 0.53 seconds |
| Fresh-clone first visible dashboard render | 3.72 seconds |
| Fresh-clone default package | 2.14 seconds |

The clean-room check cloned `review-fixes`, created a new virtual environment, installed `requirements.lock`, ran the test suite, started `dashboard.py`, waited for the health endpoint, rendered the dashboard in Chromium, and generated the default package.

## Commits on the review branch

| Commit | Purpose |
| --- | --- |
| `9859c92` | Vectorized the seeded Monte Carlo rate-grid work and added default-output regression coverage. |
| `ab93b7b` | Added the Excel reconciliation workbook and workbook tests. |
| `491df42` | Added the annual debt-schedule package export. |
| `46799ed` | Added dashboard package progress feedback, stale-input handling, memo preview, and refreshed screenshots. |
| `b80884d` | Added labeled package artifacts, sample-output generator, sample files, and LibreOffice reconciliation validation. |
| `8d7b697` | Added reviewer, demo, and deployment documentation. |

## Deliberately not done

No deployment URL was added because no deployment exists yet; the previous placeholder was removed. The app was not deployed because deployment was explicitly reserved for the repository owner. The package does not claim to replace Excel, ARGUS, source documents, financial-model review, legal or tax diligence, or committee judgment. No real deals, clients, testimonials, benchmark claims, awards, or live market data were introduced.

The default CLI simulation count was not reduced. The dashboard's already-separated 1,000-simulation package mode is labeled in the interface; the default CLI package remains 5,000 seeded simulations. The model still has its documented simplifications, including no complete operating statement, tax, capex, refinance, full capital stack, or source-document ingestion model.

## References

[1]: https://github.com/hossiendehghan989/atlasre-investment-intelligence/pull/1 "Pull request #1"
[2]: https://github.com/hossiendehghan989/atlasre-investment-intelligence/actions/runs/35472519577 "GitHub Actions CI run 35472519577"
