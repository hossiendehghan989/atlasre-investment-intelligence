# AtlasRE Investment Intelligence — Architecture and Controls

## Executive position

AtlasRE is a **deterministic analytical prototype for real-estate investment committee screening**. The architecture keeps financial calculations in small, inspectable Python modules and uses Streamlit as the decision surface. Governance and source status are treated as model inputs rather than presentation metadata.

The system is designed to answer a narrow question well: *given explicit assumptions, what does the model say, how fragile is the result, what constraints bind, and what must be verified before a human decision?* It is not a production investment platform and does not claim to replace diligence, approval, or independent model validation.

## Current architecture

```text
Illustrative or reviewed inputs
            |
            v
Assumption register + source status + version
            |
            v
Deterministic financial engines
  ├─ acquisition underwriting and IRR/NPV
  ├─ monthly debt and constraint sizing
  ├─ monthly development and capitalized interest
  ├─ LP/GP waterfall
  ├─ optional lease-level rent-roll roll-up
  └─ scenarios, stress, correlated simulation
            |
            v
Governance layer
  ├─ lineage records
  ├─ model-run fingerprint
  └─ tamper-evident audit primitives
            |
            v
Decision layer
  ├─ source-aware IC screening
  ├─ downside-first memo/package
  ├─ side-by-side comparison
  └─ constrained portfolio allocation and risk view
            |
            v
Streamlit dashboard + CSV/JSON/Markdown artifacts
```

## Module boundaries

| Module | Responsibility | Deliberate boundary |
| --- | --- | --- |
| `src/atlasre.py` | Acquisition cash flows, debt-linked annual underwriting, IRR/NPV, market scoring | Does not ingest documents or make approval decisions |
| `src/debt.py` | Monthly debt schedule, draws, IO, amortization, balloon and DSCR/LTV sizing | Does not infer missing loan terms |
| `src/advanced_underwriting.py` | Development screen, seeded correlated simulation, stress and tail metrics | Does not claim probability calibration from live markets |
| `src/institutional.py` | Monthly development and multi-tier waterfall | Does not replace project-specific legal waterfall language |
| `src/lease.py` | Validated rent-roll foundation and monthly rent/NOI roll-up | Does not silently override simplified underwriting |
| `src/governance.py` | Assumptions, lineage, audit chain, reproducibility fingerprint | Does not provide persistent server-side approvals |
| `src/ic_workflow.py` | Source-aware flags, comparison, decision states, screening memo | Does not approve or transmit a transaction |
| `src/portfolio.py` | Capital rationing, concentration, DSCR gates, exposure diagnostics | Does not optimize a multi-period fund portfolio |
| `generate_committee_report.py` | Reproducible Markdown/CSV/JSON/ZIP screening package | Does not certify source data |
| `dashboard.py` | Streamlit interaction and visual decision surface | Does not contain financial formulas as a second source of truth |

## Control principles

1. **Downside precedes upside.** Critical flags, source status, DSCR, NPV, stress cases, and tail risk appear before attractive base-case return metrics.
2. **Source status is a gate.** `REVIEW REQUIRED` is not equivalent to `VERIFIED`; an unverified deal cannot automatically pass the initial screen.
3. **Periodicity is explicit.** Monthly schedules remain monthly. Reported monthly IRRs are annualized only at the presentation boundary.
4. **Constraints are visible.** Debt sizing identifies its binding constraint. Portfolio allocation retains eligibility and exclusion reasons.
5. **Outputs are challengeable.** Important outputs carry lineage fields, assumption versions, and a deterministic model-run fingerprint.
6. **Illustrative data is labeled.** The system does not convert an illustrative default into a verified fact through formatting.
7. **Invalid states fail loudly.** Non-finite values, malformed schedules, invalid dates, and malformed governance records are rejected or explicitly marked invalid.

## Current capabilities versus production gaps

| Capability | Current state | Production gap |
| --- | --- | --- |
| Acquisition underwriting | Deterministic annual model with IRR, NPV, leverage, exit value and DSCR | Independent validation, accounting and tax treatment |
| Debt | Monthly IO/amortization/draw/balloon schedule and LTV/DSCR sizing | Full debt stack, covenants, hedging, refinance, term-sheet ingestion |
| Development | Monthly draws, contingency, capitalized interest, stabilization and exit | Contract-level budget, change orders, schedule risk, cost-to-complete controls |
| Waterfall | Multi-tier return of capital, pref, hurdles, promote and reconciliation | Legal-document mapping, tax distributions, clawbacks, catch-ups and escrow terms |
| Lease-level foundation | Rent roll, escalations, vacancy, credit flag and monthly NOI proxy | Rollover economics, downtime, TI/LC, rent-free, recoveries, tenant credit and capex |
| Risk | Seeded correlated shocks, tails, expected shortfall, stress and DSCR breach probability | Calibrated distributions, historical validation, liquidity and drawdown modeling |
| Governance | Versioned assumptions, lineage, audit hash chain and fingerprint | Persistent immutable event store, identity, roles, approvals and retention policy |
| IC workflow | Source-aware flags, comparison, screening memo and ZIP package | Human approval workflow, conditions precedent, decision history and permissions |
| Portfolio | Concentration cap, DSCR gate, capital rationing, HHI and exposure view | Multi-period optimizer, liquidity, capital calls, covariance and fund obligations |
| Data | Illustrative CSV and explicit user inputs | Source connectors, document extraction, citations, timestamps and confidence review |

## Six-to-ten-week highest-ROI roadmap

| Timing | Outcome | Control objective |
| --- | --- | --- |
| Weeks 1–2 | Persistent model-run and assumption store | Immutable versioning, actor identity, source files, approval states and reproducible reruns |
| Weeks 2–4 | Commercial lease economics | Rollover, downtime, TI/LC, recoveries, capex and tenant-level evidence with tests |
| Weeks 4–6 | Real debt-stack and development controls | Construction-to-perm, mezz/preferred equity, covenants, refinance and cost-to-complete |
| Weeks 6–8 | Source-controlled ingestion and validation | Excel/PDF inputs with citations, reviewer queue, stale-data flags and reconciliation |
| Weeks 8–10 | Portfolio and IC operating workflow | Multi-period capital allocation, approval conditions, variance monitoring and audit reporting |

A FastAPI boundary, database, and document layer are plausible future directions, but they are not prerequisites for improving the deterministic engines and should not be introduced as cosmetic migrations.

## Phase 0 current gaps note

The baseline audit found that the financial core and tests were ahead of several user-facing artifacts. The dashboard footer still carried a v0.3 label, the report generator omitted newer tail and governance outputs, and the dashboard referenced the development function without importing it. The executive documentation also described the project historically rather than as the current v0.9 analytical prototype. This release corrects those mismatches and adds a small lease-level foundation without changing the simplified path.

## How to challenge a model run

A reviewer should first inspect source status and the model-run fingerprint. Next, review the assumption register and lineage for purchase price, NOI, growth, exit cap, leverage, debt terms, and terminal value. Then examine minimum DSCR, negative NPV, stress cases, expected shortfall, and portfolio exposure. Only after those checks should the committee discuss base-case IRR and upside. Any change in a material assumption requires a new version and a new fingerprint.

## Explicit non-claims

AtlasRE does not claim production readiness, live-data accuracy, investment advice, legal or tax compliance, complete lease underwriting, persistent approval controls, or a calibrated market probability model. Those are engineering and governance deliverables for a later system, not features to imply through documentation.

## References

[1]: https://github.com/hossiendehghan989/atlasre-investment-intelligence "AtlasRE Investment Intelligence repository"
