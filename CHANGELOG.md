# Changelog

## v0.9 — Executive and lease-level elevation

This release moves AtlasRE from an advanced analytical prototype toward a more executive-ready Investment Committee decision-support artifact without changing the Streamlit stack or weakening the deterministic financial core.

### Added

- Optional lease-level foundation for multi-tenant rent rolls.
- Monthly contract-rent, vacancy, effective-rent, operating-expense, and NOI roll-up.
- Lease expiry counts and credit-quality flags.
- Downloadable screening package containing Markdown, CSV, and JSON artifacts.
- Model-run fingerprint and source-aware decision status in the executive package.
- Expected-shortfall and governance sections in the generated IC report.
- Adversarial tests for lease validation and screening-package contents.

### Strengthened

- Dashboard decision surface now leads with source status, downside metrics, governance flags, and package download.
- Dashboard footer and documentation now reflect the actual release state.
- Architecture documentation distinguishes current capabilities from production gaps.
- Executive memo now explains how a skeptical committee should challenge a model run.
- Fixed the dashboard runtime import for the development feasibility path.

### Validation

- 37 tests passing.
- Python compilation passing.
- Streamlit startup smoke test passing.
- `git diff --check` passing.

### Explicit limitations

This remains a deterministic analytical prototype. It is not production-ready, not an automated approval system, and not investment advice. Persistent governance, live data, complete lease economics, full debt stacks, and multi-period portfolio optimization remain future work.
