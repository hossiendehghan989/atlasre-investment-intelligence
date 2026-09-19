# Changelog

## v0.10 — IC hardening, canonical reproducibility, and lease bridge

This release advances AtlasRE from an advanced analytical prototype toward a more defensible Investment Committee screening artifact. It preserves the deterministic financial core and the original simplified annual-NOI path while making downside, governance, and reproducibility materially more visible.

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

- 45 tests passing.
- Python compilation passing.
- `git diff --check` passing.
- IC screening package generation passing.
- Streamlit startup smoke test pending final release verification.

### Explicit limitations

AtlasRE remains a deterministic analytical prototype. It is not production-ready, an automated approval system, or investment advice. Persistent governance, live and source-controlled data, complete lease economics, full debt stacks, independent model validation, and multi-period portfolio optimization remain future work.

## v0.9 — Executive and lease-level elevation

This release moved AtlasRE from an advanced analytical prototype toward a more executive-ready Investment Committee decision-support artifact without changing the Streamlit stack or weakening the deterministic financial core.

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
