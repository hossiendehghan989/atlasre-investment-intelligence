# Changelog

## review-fixes — correctness, testing, and repository controls

This branch contains the local work already present before the review, followed by the review fixes listed below. The branch is based on the local `review-fixes` state and targets the remote `main` branch.

### Review fixes in this branch

- Removed the second risk multiplier from `market_score`; `rank_markets` now receives one consistent composite score.
- Made year-one NOI equal to the supplied input and applied growth from year two onward.
- Changed equity multiple to total positive distributions divided by total negative equity cash flows, including interim contributions.
- Labeled `portfolio_exposure` as a naive score-weighted screen and pointed constrained use cases to `src/portfolio.py`.
- Added independent `numpy-financial` IRR, direct-discount NPV, and closed-form debt schedule checks.
- Added Ruff configuration, safe lint fixes, and readability refactors for model construction.
- Added MIT license, test-only requirements, GitHub Actions CI, screenshots, and the illustrative case study.
- Added an explicit modeling-conventions and simplifications inventory to the architecture document.

### Validation at the time of this entry

The local suite contains 51 passing tests. Ruff passes with `ruff check .`. The dashboard was run headlessly and three screenshots were captured under `docs/images/`.

### Pre-existing local work

The branch also contains earlier local changes for the lease foundation, source-aware governance, IC package generation, reproducibility fingerprints, and dashboard copy. Those commits are retained unchanged and are listed in `docs/baseline_audit.md`.

## v0.10 — IC controls, reproducibility, and lease bridge

This release preserved the deterministic financial core and added source-aware screening, lease support, reproducibility records, and downside reporting.

### Added

- Explicit lease rollover vacancy and replacement-rent assumptions in the modular rent-roll engine.
- Optional rent-roll-to-core-underwriting bridge that derives annual NOI without mutating the original simplified case.
- Annual lease summary artifact and lease lineage in the screening package when the optional lease route is used.
- Canonical model-run fingerprinting that is stable across DataFrame row/column and lineage presentation order.
- Top-level dashboard display of model-run fingerprint, expected shortfall, negative-NPV probability, and DSCR-breach probability.
- Eight adversarial tests covering lease rollover, all-expired leases, negative growth, lease-path isolation, fingerprint stability, fingerprint sensitivity, source gating, and lease-package lineage.

### Strengthened

- The generated IC package now follows a clearer executive structure: thesis, downside and governance flags, key assumptions, economic results, risk tails, lease evidence, reference schedules, next diligence steps, and model fingerprint.
- The package preserves monthly development, stress, risk, governance, and lease support artifacts.
- The dashboard gives the IC workflow its first tab and decision surface, with downside and source status preceding base-case metrics.
- Assumption registers retain stable IDs, versions, source status, supersession fields, and caller-controlled effective dates rather than volatile implicit timestamps.
- Documentation now reflects the optional lease bridge, the `v0.10` release line, the 37-test Phase 0 baseline, and the 45-test hardened suite.

### Validation

- 45 tests passing at the time of the release.
- Python compilation passing.
- `git diff --check` passing.
- IC screening package generation passing.
- Streamlit startup smoke test pending final release verification.

### Explicit limitations

AtlasRE remains a deterministic analytical prototype. It is not production-ready, an automated approval system, or investment advice. Persistent governance, live and source-controlled data, complete lease economics, full debt stacks, independent model validation, and multi-period portfolio optimization remain future work.

## v0.9 — Lease-level support and screening package

This release added a modular lease foundation and downloadable screening artifacts without changing the Streamlit stack.

### Added

- Optional lease-level foundation for multi-tenant rent rolls.
- Monthly contract-rent, vacancy, effective-rent, operating-expense, and NOI roll-up.
- Lease expiry counts and credit-quality flags.
- Downloadable screening package containing Markdown, CSV, and JSON artifacts.
- Model-run fingerprint and source-aware decision status in the executive package.
- Expected-shortfall and governance sections in the generated IC report.
- Adversarial tests for lease validation and screening-package contents.

### Explicit limitations

This remains a deterministic analytical prototype. It is not production-ready, not an automated approval system, and not investment advice. Persistent governance, live data, complete lease economics, full debt stacks, and multi-period portfolio optimization remain future work.
