# Baseline audit

**Audit date:** 2026-09-19  
**Repository:** `https://github.com/hossiendehghan989/atlasre-investment-intelligence`  
**Working copy:** local clone

## 1. Local versus remote state

Work is being performed from the **local copy**, not directly from the remote checkout. The local working tree was clean before this audit and was on local branch `main` at:

- **Local HEAD:** `bf8f05137860c76829e26ec46a33a3c0054e0e7a` (`style: replace generated dashboard copy`)
- **Remote `origin/main` supplied in the task:** an abbreviated hash that differed from the live reference.
- **Remote `origin/main` verified live with `git ls-remote`:** `eed2d47b4e164795c08d06e15204547f1ceed348` (`feat: elevate ic package and add lease foundation`). The full live reference is used for all comparisons.
- **Remote history:** 11 commits total. This is a same-day 11-commit history, not a one-commit history.
- **Divergence:** local is 3 commits ahead of `origin/main` and 0 commits behind it.

The remote baseline was independently checked in a temporary worktree at `origin/main`: **37 passed**. The current local copy passes **45 tests**.

## 2. Local-only commits and file differences

The three local-only commits are:

| Commit | Message |
| --- | --- |
| `ef92393` | `feat: harden IC governance and lease underwriting` |
| `88c63b9` | `style: refine IC screening dashboard` |
| `bf8f051` | `style: replace generated dashboard copy` |

Compared with `origin/main`, the local copy has these file differences:

| Change | File |
| --- | --- |
| Modified | `ATLASRE_ARCHITECTURE.md` |
| Modified | `CHANGELOG.md` |
| Modified | `INVESTMENT_COMMITTEE_MEMO.md` |
| Modified | `README.md` |
| Modified | `dashboard.py` |
| Modified | `generate_committee_report.py` |
| Modified | `src/governance.py` |
| Modified | `src/ic_workflow.py` |
| Modified | `src/lease.py` |
| Added | `tests/test_elevation_hardening.py` |
| Modified | `tests/test_screening_package.py` |

The local-only test changes are one new test module, `tests/test_elevation_hardening.py`, and updates to `tests/test_screening_package.py`. The local suite contains 13 test modules and passes 45 tests.

## 3. Issue-by-issue verification against the local copy

| Prompt issue | Local status | Evidence and audit conclusion |
| --- | --- | --- |
| `market_score` counts risk twice | **Still present** | `score` already applies `(1 - risk) * risk_weight`, then `risk_adjusted_score` multiplies the resulting score by `(1 - risk)` again. `rank_markets` consumes this value directly. Correctness fix required. |
| Year-1 NOI convention | **Still present and undocumented** | `underwrite_deal` builds NOI with `annual_noi * (1 + annual_noi_growth) ** year` for years `1..hold_years`, so year 1 includes one full growth step. The convention is not an explicit model parameter and is not clearly stated in the core model documentation. |
| `equity_multiple` uses only positive levered flows | **Still present** | The return value uses `sum(max(flow, 0) for flow in levered_flows) / equity`, which hides negative interim equity flows. Correctness fix and tests required. |
| `portfolio_exposure` is not aligned with constrained allocation | **Still present** | The function applies only an equity-fits-capital filter and then allocates proportionally to non-negative risk-adjusted score. It does not use DSCR eligibility, concentration caps, or the allocator in `src/portfolio.py`. This must either be aligned or explicitly labeled as a naive legacy screen; alignment is preferable. |
| Independent IRR/NPV/debt cross-checks | **Missing** | No `numpy-financial` or equivalent independent cross-check tests are present. Existing tests check selected invariants but do not independently recompute fixed cases for IRR, NPV, and debt schedules. |
| Readability / long one-line functions | **Still present** | `underwrite_deal` contains a long one-line return dictionary; `scenario_matrix` and several other functions remain compressed. No lint configuration or repository lint command is present. |
| LICENSE | **Missing** | No `LICENSE` file exists in the repository. |
| `pyproject.toml` / pinned tooling | **Missing or incomplete** | The repository has `requirements.txt` with lower bounds, but no `pyproject.toml`, linter configuration, or pinned sensible versions for a release workflow. |
| GitHub Actions CI | **Missing** | No `.github/workflows` files exist. |
| Dashboard screenshots under `docs/images/` | **Missing** | No `docs/images/` directory or committed screenshots exist. A dashboard smoke test had previously been run, but the requested committed screenshots are not present. |
| `docs/case_study.md` | **Missing** | No case-study document exists. |
| Modeling conventions in architecture | **Incomplete** | The architecture describes capabilities and gaps but does not yet provide a single upfront inventory of all simplifications such as annual NOI timing, property tax, capex reserve, TI/LC, refinance, and related exclusions. |
| Optional property tax and capex reserve | **Not assessed for implementation** | This remains optional and should be attempted only after all required fixes, tests, docs, CI, and lint work are complete and green. |

## 4. Baseline decision

The `review-fixes` branch was created from the **current local state** at `bf8f051`, not from remote `origin/main`, and currently contains the audit commit `75226cb`. The remote 37-test baseline is preserved as a reference point; the local 45-test suite and local lease/governance/dashboard work must not be discarded.

No implementation changes were made before this audit file. The next step is to implement the requested fixes in small, separate commits.

## Status after review-fixes implementation

| Issue | Status | Evidence |
| --- | --- | --- |
| Portfolio unallocated capital repeated per row | Fixed | Explicit `UNALLOCATED` summary row and allocation reconciliation tests |
| Verified source without evidence printed as verified | Fixed | Package propagates reviewer and source reference; tests cover both evidence states |
| Development project IRR definition mismatch | Fixed | Project IRR is now unlevered; independent `numpy-financial` regression test added |
| NaN, infinity, negative-rate, and fractional-counter validation | Fixed for reviewed public inputs | Shared validation helpers and parametrized boundary tests added |
| Dashboard/package path dependence | Fixed | Paths resolve from `__file__` and the dashboard uses the repository root |
| Reproducible dependency installation | Fixed | `requires-python`, bounded requirements, lock file, and CI lock installation added |
| Live market ingestion, authentication/RBAC, immutable approvals | Open / not applicable to this prototype | Explicitly documented as production limitations |
| Screenshot regeneration | Open until final dashboard capture | Existing committed screenshots require final visual verification after the last code changes |
