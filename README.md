# AtlasRE Investment Intelligence

AtlasRE is a **deterministic real-estate investment committee decision-support prototype**. It is designed to make assumptions, downside, leverage, governance status, and portfolio constraints visible before a human committee spends time on a deal. It is not production software, an automated approval system, or investment, legal, tax, engineering, or valuation advice.

## Executive summary

The repository contains a transparent Python financial core with a Streamlit decision surface. It supports annual acquisition underwriting, monthly debt schedules, development draws, capitalized interest, stabilization, multi-tier LP/GP distributions, deterministic correlated simulation, expected-shortfall reporting, source-aware IC gates, reproducibility fingerprints, and constrained portfolio allocation.

The newest layer adds a **lease-level foundation**. A validated rent roll can be rolled into monthly contract rent, explicit vacancy, operating expenses, effective rent, NOI, and lease-expiry counts. This path is deliberately optional and does not silently replace the existing simplified annual-NOI path.

## What a committee can challenge

The dashboard and generated screening package place downside and governance before upside. They expose negative NPV, minimum DSCR, exit-cap break-even, source status, economic flags, governance flags, tail IRR, expected shortfall, DSCR-breach probability, portfolio exposure, and a model-run fingerprint. The generated package contains the report plus assumptions, lineage, stress cases, risk summary, and monthly development support files.

All defaults are illustrative until a source and reviewer are attached. A deal marked `REVIEW REQUIRED` cannot automatically reach `PASSES INITIAL SCREEN`.

## Implemented capabilities

| Area | Current capability |
| --- | --- |
| Acquisition underwriting | Entry cap, annual NOI growth, exit value, unlevered and levered cash flows, NPV, IRR, equity multiple |
| Numerical controls | Finite-input validation, bracket-scanned IRR, zero-rate debt handling, explicit failure modes |
| Debt | Monthly interest, IO, amortization, draws, balloon payoff, DSCR observations, LTV/DSCR sizing |
| Development | Land, hard cost, soft cost, contingency, monthly draws, capitalized interest, stabilization, exit value |
| Waterfall | Return of capital, preferred return, ordered hurdles, tier-specific promote, distribution reconciliation |
| Risk | Scenario grids, stress cases, seeded correlated simulation, percentile tails, expected shortfall, covenant-breach probability |
| Lease foundation | Multi-tenant rent roll, escalations, vacancy, credit flag, rollover/expiry counts, monthly NOI roll-up |
| Governance | Versioned assumptions, source status, lineage records, audit hash chain, model-run fingerprint |
| IC workflow | Severity-ranked flags, source-aware status, side-by-side comparison, downside-first memo and package |
| Portfolio | Concentration caps, DSCR gates, capital rationing, allocation reasons, HHI, downside exposure |

## Quickstart

```bash
python -m pip install -r requirements.txt
python -m pytest -q
streamlit run dashboard.py
python generate_committee_report.py
```

The report generator writes a screening package to `artifacts/`. The dashboard generates the same package as a downloadable ZIP. The package is deterministic except for timestamps that may appear in human-facing documents; model calculations use explicit inputs and a fixed simulation seed unless a caller changes it.

## Repository structure

```text
atlasre-investment-intelligence/
├── dashboard.py                         # Streamlit decision surface
├── generate_committee_report.py         # Executive screening-package generator
├── INVESTMENT_COMMITTEE_MEMO.md         # Executive project brief
├── ATLASRE_ARCHITECTURE.md               # Architecture, controls, gaps, roadmap
├── src/
│   ├── atlasre.py                        # Core acquisition underwriting
│   ├── advanced_underwriting.py          # Development, simulation, stress testing
│   ├── debt.py                           # Monthly debt schedules and sizing
│   ├── institutional.py                  # Monthly development and waterfall
│   ├── lease.py                          # Optional lease-level foundation
│   ├── governance.py                     # Assumptions, lineage, audit, fingerprints
│   ├── ic_workflow.py                    # Source-aware screening and memo logic
│   ├── committee_analytics.py            # Sensitivity and committee metrics
│   └── portfolio.py                      # Constrained allocation and portfolio risk
├── tests/                                # Financial, governance, IC, lease, and adversarial tests
└── data/market_inputs.csv                # Illustrative normalized market inputs
```

## Why this stands out

AtlasRE does not use a polished interface to hide weak assumptions. Its primary design decision is that a material output must remain challengeable. The engines expose schedules rather than only summary values. Debt constraints identify whether LTV or DSCR is binding. Waterfall distributions reconcile to available cash. Simulation tails are reproducible. Governance status is separate from economic performance. Portfolio allocation reports why capital was excluded or rationed.

The repository is intentionally conservative about claims. It does not pretend that an annual NOI input is a lease-level forecast, that a seeded Monte Carlo run is a market forecast, or that a hash fingerprint is a persistent audit database.

## Limitations and production gaps

The project is an analytical prototype. It does not provide live market data, document ingestion, OCR, a lease-level model with all commercial lease economics, database-backed persistence, immutable server-side approvals, production RBAC, tax or FX treatment, accounting outputs, construction-to-permanent debt, mezzanine or preferred-equity stacks, refinance modeling, or a multi-period portfolio optimizer. The lease module is a foundation, not a complete rent-roll underwriting system.

Any real deployment would require source-controlled data ingestion, model validation independent of the author, legal and compliance review, persistent governance controls, monitoring, and firm-specific investment policies. No output should be treated as a recommendation without those controls.

## Testing and release state

The current suite passes **37 tests** covering financial calculations, monthly debt, waterfall balancing, risk tails, malformed inputs, zero-rate debt, audit tampering, source-aware IC gates, deterministic allocation, lease roll-up, and screening-package generation. Streamlit startup and Python compilation are checked before release.

Current release line: **v0.9 analytical prototype**.

## How to present this to an Investment Committee

Start with the source status and the decision state. Then show critical and governance flags, minimum DSCR, negative NPV, expected shortfall, and stress cases. Only after the downside is understood should the committee review base-case IRR, equity multiple, and upside sensitivities. Ask which assumptions are verified, which outputs are most exposed to terminal value, and what diligence would change the decision. Treat the package as a challenge document, not as a substitute for judgment.

## References

[1]: https://github.com/hossiendehghan989/atlasre-investment-intelligence "AtlasRE Investment Intelligence repository"
