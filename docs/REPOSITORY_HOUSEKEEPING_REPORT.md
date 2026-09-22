# Repository housekeeping report

**Scope:** This report records the neutral organization pass on `chore/repo-tidy`, created from `main` commit `840e1700eda181d4abf6b3b9edff16c346c3677b`. The pass intentionally changes no underwriting economics, screening logic, default values, or committed `docs/sample_output/` artifacts.

## Source modules and dependency flow

The repository has thirteen Python modules under `src/`. `validation` and `atlasre` are the foundation layers. Domain modules build on those layers, while committee and reconciliation modules compose the outputs for review.

| Module | Responsibility | Direct internal dependencies |
| --- | --- | --- |
| `__init__.py` | Declares the AtlasRE package. | None |
| `advanced_underwriting.py` | Runs development feasibility, seeded simulation, risk summaries, and stress tests. | `atlasre` |
| `atlasre.py` | Implements core acquisition underwriting, IRR/NPV helpers, market scoring, and simple exposure screens. | `validation` |
| `committee_analytics.py` | Produces sensitivities, break-even analysis, and committee summaries. | `atlasre`, `validation` |
| `debt.py` | Builds deterministic debt schedules and constrained debt sizing. | `validation` |
| `governance.py` | Manages assumptions, lineage, audit records, and model fingerprints. | `validation` |
| `ic_workflow.py` | Applies screening gates and produces comparisons, flags, and committee memoranda. | `atlasre`, `committee_analytics`, `governance`, `presentation` |
| `institutional.py` | Builds monthly development models, debt sizing, waterfalls, and assumption-quality views. | `atlasre`, `validation` |
| `lease.py` | Builds lease roll-ups and opt-in lease-derived acquisition underwriting. | `atlasre`, `validation` |
| `portfolio.py` | Allocates capital and summarizes portfolio exposure and risk. | `validation` |
| `presentation.py` | Formats dashboard and report metrics without exposing non-finite values. | None |
| `reconciliation.py` | Generates formula-based Excel reconciliation workbooks. | `atlasre`, `governance` |
| `validation.py` | Provides reusable fail-closed numeric and integer validation helpers. | None |

The cleanup added a package docstring and short docstrings to the previously undocumented input dataclasses. It consolidated AtlasRE's private finite-number check into `validation.coerced_finite`, preserving the original coercion and error contract. It also reduced repeated unavailable-metric tests in `presentation.py` to one private helper. No second validation module was added.

## Test organization and preservation

The test suite was reorganized from **19 files to 11 files**. The test count remains **131**, the number of named test functions remains **93**, and the number of `assert` statements remains **229**. Every original test function remains present. History-shaped files were folded into the most relevant component or package test module, with section comments retaining the former topic grouping.

| Original file | What it tested | Source modules covered | Current location |
| --- | --- | --- | --- |
| `test_adversarial_edges.py` | Cross-module invalid-input and determinism edges. | `atlasre`, `debt`, `governance`, `portfolio` | `test_validation.py` |
| `test_adversarial_remediations.py` | Package overwrite, escaping, source-evidence, and workbook remediations. | Package generator, `ic_workflow`, `reconciliation` | `test_screening_package.py` |
| `test_advanced_underwriting.py` | Development feasibility, simulation, risk summary, and stress tests. | `advanced_underwriting`, `atlasre` | `test_advanced_underwriting.py` |
| `test_atlasre.py` | Core acquisition cash flows, scenarios, market score, and simple exposure. | `atlasre` | `test_atlasre.py` |
| `test_committee_analytics.py` | Debt-service analytics, sensitivities, and break-even calculations. | `committee_analytics`, `atlasre` | `test_committee_analytics.py` |
| `test_debt_ic.py` | Debt scheduling and committee memo/comparison behavior. | `debt`, `ic_workflow`, `atlasre` | `test_ic_workflow.py` |
| `test_elevation_hardening.py` | Lease rollover hardening plus lease-path package traceability. | `lease`, `governance`, package generator | `test_lease.py` |
| `test_governance_portfolio.py` | Audit-chain, assumption-register, and allocation behavior. | `governance`, `portfolio` | `test_portfolio.py` |
| `test_ic_governance_edges.py` | Evidence gates, screen statuses, and deal-comparison edges. | `ic_workflow`, `atlasre` | `test_ic_workflow.py` |
| `test_independent_crosschecks.py` | Independent IRR, NPV, cash-flow, and amortization cross-checks. | `atlasre`, `debt` | `test_atlasre.py` |
| `test_institutional.py` | Monthly development, debt sizing, waterfall, and assumption-quality behavior. | `institutional` | `test_institutional.py` |
| `test_lease.py` | Contract rent, vacancy, expiry, and lease-input validation. | `lease` | `test_lease.py` |
| `test_portfolio_risk.py` | Portfolio risk views and Arrow-safe unallocated summaries. | `portfolio` | `test_portfolio.py` |
| `test_presentation.py` | Percentage conversion and unavailable-value formatting. | `presentation`, `atlasre` | `test_presentation.py` |
| `test_reconciliation_workbook.py` | Workbook formulas, outputs, recalculation, and long-hold schedules. | `reconciliation`, `atlasre` | `test_reconciliation_workbook.py` |
| `test_reference_grade_models.py` | Reference-grade development, waterfall, simulation, and stress cases. | `advanced_underwriting`, `institutional`, `atlasre` | `test_advanced_underwriting.py` |
| `test_review_kit.py` | Dashboard, CLI, package, validation, and display regressions. | Package generator, CLI, `atlasre`, `advanced_underwriting`, `presentation` | `test_screening_package.py` |
| `test_screening_package.py` | Package contents, ZIP output, default risk figures, and source verification. | Package generator, `advanced_underwriting`, `atlasre` | `test_screening_package.py` |
| `test_validation_audit.py` | Cross-module fail-closed numeric and integer validation. | `atlasre`, `committee_analytics`, `debt`, `governance`, `institutional`, `lease`, `portfolio` | `test_validation.py` |

## Documentation organization

The new [documentation index](README.md) identifies the purpose, intended audience, and status of every Markdown document below `docs/`. No file was archived or deleted. The current docs remain focused on operating, review, or illustrative-artifact purposes; the two historical documents are now visibly labeled so they cannot be mistaken for live guidance.

| File | Purpose | Current and non-redundant? |
| --- | --- | --- |
| `DEMO_SCRIPT.md` | Two-minute illustrative walkthrough. | Yes; current demo aid. |
| `IMPLEMENTATION_REPORT.md` | Evidence from the earlier review-fixes implementation. | Yes; historical record, now labeled. |
| `OVERVIEW.md` | Purpose, boundaries, and evaluation path. | Yes; current orientation. |
| `README.md` | Documentation directory index. | Yes; current navigation aid. |
| `REVIEWER_GUIDE.md` | Formula and reconciliation guidance. | Yes; current reviewer guide. |
| `REVIEW_REQUEST.md` | Scope for an independent finance review. | Yes; current reviewer request. |
| `SECURITY_AND_DATA.md` | Local data-handling boundaries. | Yes; current owner guidance. |
| `USING_A_REAL_DEAL.md` | Owner-supplied deal workflow. | Yes; current owner guide. |
| `baseline_audit.md` | Earlier baseline comparison and remediation trail. | Yes; historical record, now labeled. |
| `case_study.md` | Reproducible illustrative case and cross-checks. | Yes; current illustrative example. |
| `review/REVIEW_CHECKLIST.md` | Structured review-findings worksheet. | Yes; current review companion. |
| `sample_output/README_ILLUSTRATIVE.md` | Description of committed sample artifacts. | Yes; current committed artifact guide. |
| `sample_output/investment_committee_memo.md` | Generated illustrative memorandum artifact. | Yes; current committed artifact. |
| `sample_output/investment_committee_report.md` | Generated illustrative screening report artifact. | Yes; current committed artifact. |

All **39 local inline links** in `README.md` and the recursive `docs/` Markdown tree resolve. `docs/sample_output/` was not modified.

## Root files, configuration, and formatting

`ATLASRE_ARCHITECTURE.md` remains at the repository root because it is the GitHub-facing, comprehensive system-and-controls orientation. It is not redundant with `docs/OVERVIEW.md`, which is a short product and reviewer orientation. `INVESTMENT_COMMITTEE_MEMO.md` also remains at root because it is a GitHub-facing executive brief. It is distinct from `docs/case_study.md`, which documents one specific illustrative input case and its numerical checks.

`pyproject.toml`, `pytest.ini`, `requirements.txt`, `requirements.lock`, and `requirements-test.txt` now carry short purpose comments where needed. The runtime ranges are compatible with the exact lock, and the lock and test manifest now agree on the existing `ruff==0.16.8` tool version. A fresh environment installed solely from `requirements.lock` passed formatting, lint, and all tests.

`ruff format` reformatted 28 files in `src/`, `tests/`, and `scripts/` in its own commit. The command now reports that all 27 checked files are formatted.

## Commit and validation record

| Commit | Purpose | Validation |
| --- | --- | --- |
| `8bb1939` | Formatted source, tests, and scripts. | `ruff format --check`, `ruff check .`, and 131 tests passed. |
| `091ab79` | Centralized shared validation and presentation helpers; added missing docstrings. | `ruff check .`, 131 tests, and headline-output check passed. |
| `d650256` | Consolidated and renamed tests by component. | 131 tests, 93 named tests, and 229 assertions preserved. |
| `3d3637b` | Added the documentation index and historical labels. | Markdown link validation, `ruff check .`, and 131 tests passed. |
| `2bc1aec` | Clarified and aligned dependency manifests. | Fresh locked environment passed formatting, lint, and 131 tests. |

The branch has not yet been pushed or merged while this report is being prepared. The final PR URL, CI run URL, merge-commit hash, and final run output will be added after remote validation and merge.

## Headline-output preservation

The default case was checked with `DealInputs(10_000_000, 650_000, hold_years=5, leverage=0.5)`. Its required headline outputs are unchanged: **Levered IRR `11.97%`**, **Unlevered IRR `9.32%`**, **Exit value `$12,193,012`**, and **decision `REJECT / REWORK`**. A separate baseline-revision comparison follows before pull-request creation.

## Deliberately not changed

The pass did not alter financial formulas, model defaults, screening policy, tests, test assertions, package artifacts, or `docs/sample_output/`. The two root orientation documents were not moved because each has a distinct GitHub-facing purpose. Historical documents were retained rather than archived because they contain unique audit evidence and are now explicitly marked as historical.

## References

[1]: https://github.com/hossiendehghan989/atlasre-investment-intelligence "AtlasRE Investment Intelligence repository"
