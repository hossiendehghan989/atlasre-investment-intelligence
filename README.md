# AtlasRE Investment Intelligence

AtlasRE is a **deterministic real-estate investment committee decision-support prototype**. It is designed to make assumptions, source status, downside, leverage, and governance visible before a human committee commits diligence time or capital. It is not production software, an automated approval system, a valuation opinion, or investment, legal, tax, engineering, or accounting advice.

## Executive summary

The repository combines a transparent Python financial core with a Streamlit decision surface and downloadable screening artifacts. The core supports annual acquisition underwriting, monthly debt schedules, development draw schedules with capitalized interest and stabilization, multi-tier LP/GP waterfall mechanics, deterministic correlated simulation, expected-shortfall analysis, source-aware initial screening, reproducibility fingerprints, and constrained portfolio allocation.

The system is deliberately built for challenge rather than persuasion. It keeps schedules inspectable, retains the distinction between economic performance and evidence quality, and requires unverified source packages to remain in `REVIEW REQUIRED`. Attractive returns do not override a negative NPV, weak debt coverage, or incomplete source verification.

> **Decision posture:** downside and governance precede upside. Every illustrative input remains illustrative until an identified source and reviewer are attached.

## What the committee can challenge

AtlasRE presents the following before base-case return metrics: the decision state, source status, severity-ranked screening flags, unlevered NPV, minimum debt-service coverage ratio (DSCR), break-even exit cap, stress cases, and simulated tail outcomes. The decision package also preserves the assumption register, output lineage, and model-run fingerprint used for the run.

A reviewer can then challenge the purchase price, operating-income path, exit-cap evidence, leverage, debt terms, timing assumptions, and portfolio context. The model states what it calculated; it does not assert that its supplied assumptions are true.

## Implemented capabilities

| Area | Current capability | Deliberate boundary |
| --- | --- | --- |
| Acquisition underwriting | Annual NOI, growth, exit value, unlevered and levered cash flows, IRR, NPV, equity multiple, and annual DSCR | Does not replace an asset-specific operating model or valuation opinion |
| Numerical controls | Finite-input validation, bracket-scanned IRR, explicit zero-rate debt treatment, and auditable failure modes | Does not resolve non-conventional cash-flow economics automatically |
| Debt | Monthly interest, IO, amortization, draws, balloon payoff, DSCR observations, LTV and DSCR sizing | Does not model a complete debt stack, hedge book, refinance, or loan-document covenants |
| Development | Land, hard cost, soft cost, contingency, monthly draws, capitalized interest, NOI ramp, stabilization, and terminal value | Does not model contract-level budgets, change orders, or cost-to-complete controls |
| Waterfall | Return of capital, preferred return, ordered hurdles, tier-specific promotes, and distribution reconciliation | Does not replace negotiated legal waterfall language, tax distributions, clawbacks, or escrow terms |
| Risk | Named stress cases, seeded correlated simulation, percentile tails, expected shortfall, NPV-loss probability, and DSCR-breach probability | Does not claim calibrated market probabilities or live-data validation |
| Lease foundation | Validated multi-tenant rent roll, escalations, vacancy and rollover assumptions, credit flags, expiry counts, monthly rent/NOI roll-up, and an opt-in bridge to core annual NOI | Does not yet model TI/LC, recoveries, capex, granular downtime, or complete commercial lease economics |
| Governance | Versioned assumptions, stable assumption IDs, lineage records, a tamper-evident audit primitive, and model-run fingerprinting | Does not provide an immutable server-side approval ledger, role-based access control, or persistent retention |
| IC workflow | Severity-ranked flags, source-aware decision state, deal comparison, Markdown memo, and downloadable support files | Does not approve, transmit, or execute a transaction |
| Portfolio | Capital rationing, DSCR eligibility, concentration limits, HHI, and downside-exposure diagnostics | Does not solve a multi-period fund optimization problem |

## Quickstart

```bash
python -m pip install -r requirements.txt
python -m pytest -q
streamlit run dashboard.py
python generate_committee_report.py
```

The report generator writes a screening package to `artifacts/`. The dashboard offers the same package as a ZIP download. Calculations are deterministic for explicit inputs; the simulation uses a fixed seed unless the caller changes it. Human-facing documents may include a timestamp, but a reproducibility fingerprint should be stable for the same model version, assumption snapshot, and lineage.

## Repository structure

```text
atlasre-investment-intelligence/
├── dashboard.py                         # Streamlit decision surface
├── generate_committee_report.py         # Markdown/CSV/JSON/ZIP screening-package generator
├── README.md                            # User and reviewer guide
├── ATLASRE_ARCHITECTURE.md               # Architecture, controls, gaps, and roadmap
├── INVESTMENT_COMMITTEE_MEMO.md          # Executive IC briefing guide
├── CHANGELOG.md                          # Release history
├── data/
│   └── market_inputs.csv                 # Illustrative normalized market inputs
├── src/
│   ├── atlasre.py                        # Core acquisition underwriting and market scoring
│   ├── advanced_underwriting.py          # Development screen, stress tests, and simulation
│   ├── debt.py                           # Monthly debt schedules and constraint sizing
│   ├── institutional.py                  # Monthly development schedule and LP/GP waterfall
│   ├── lease.py                          # Modular lease-level rent-roll foundation
│   ├── governance.py                     # Assumptions, lineage, audit primitive, and fingerprints
│   ├── ic_workflow.py                    # Source-aware screening, comparison, and memo logic
│   ├── committee_analytics.py            # Sensitivities and committee metrics
│   └── portfolio.py                      # Constrained allocation and portfolio-risk diagnostics
└── tests/                                # Financial, governance, IC, lease, and adversarial tests
```

## Why this stands out

AtlasRE does not use a polished interface to hide weak assumptions. Important outputs are tied to schedules, assumptions, source status, and lineage rather than displayed as isolated headline values. Debt sizing identifies whether LTV or DSCR is binding. Waterfall distributions reconcile to available cash. Simulation tails are seeded and repeatable. Governance status remains distinct from economic performance. Portfolio allocation records both eligibility and exclusion reasons.

The project is intentionally conservative about what it claims. An annual NOI input is not represented as a complete lease forecast. A seeded Monte Carlo run is not represented as a forecast of market outcomes. A hash fingerprint is not represented as a persistent audit database. These distinctions are essential to institutional credibility.

## Limitations and production gaps

AtlasRE is an analytical prototype. It does not provide live market data, document ingestion, OCR, complete commercial lease economics, database-backed persistence, immutable server-side approvals, production RBAC, tax or FX treatment, accounting outputs, construction-to-permanent debt, mezzanine or preferred-equity stacks, refinance modeling, or a multi-period portfolio optimizer.

A real deployment would require source-controlled data ingestion, independent model validation, document and calculation reconciliation, persistent governance controls, formal authorization, monitoring, legal and compliance review, and firm-specific investment policies. No output should be treated as a recommendation without those controls.

## How to present a case to an Investment Committee

Start with the **source status** and **decision state**. Then show governance and critical flags, minimum DSCR, negative NPV, break-even exit cap, stress cases, expected shortfall, and DSCR-breach probability. Only after the downside is understood should the committee review levered IRR, equity multiple, and upside sensitivity.

Ask the committee which assumptions are verified, which outputs depend most on terminal value, whether the debt terms are evidenced, and what diligence could reverse the initial view. Close by recording the assumption version and model-run fingerprint. Treat the package as a challenge document, never as a substitute for investment judgment.

## Testing and release state

The Phase 0 baseline recorded **37 passing tests**. The current `v0.10` elevation adds eight adversarial tests for lease rollover, all-expired rent rolls, negative lease growth, the opt-in lease bridge, canonical fingerprint stability, fingerprint sensitivity, unverified-package gates, and lease-artifact lineage. The hardened suite contains **45 passing tests**.

See [ATLASRE_ARCHITECTURE.md](ATLASRE_ARCHITECTURE.md) for the control model, current gaps, and highest-ROI roadmap. See [INVESTMENT_COMMITTEE_MEMO.md](INVESTMENT_COMMITTEE_MEMO.md) for the executive presentation frame.

## References

[1]: https://github.com/hossiendehghan989/atlasre-investment-intelligence "AtlasRE Investment Intelligence repository"
