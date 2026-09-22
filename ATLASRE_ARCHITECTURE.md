# AtlasRE Investment Intelligence — Architecture and Controls

**Author:** Hossein Dehghan · **Project type:** personal engineering prototype

## Executive position

I built AtlasRE as a **deterministic analytical prototype for real-estate screening**. The architecture keeps financial calculations in small, inspectable Python modules and uses Streamlit as a decision surface. Governance and source status are model inputs, not visual annotations.

The system is designed to answer a narrow question: **given explicit assumptions, what does the model calculate, how fragile is the result, which constraints bind, and what must be verified before a human decision?** That focus reflects how I approach decision-support work: understand the system, make assumptions explicit, build the simplest useful solution, and measure the result. The project does not claim production readiness, replace diligence, approve investments, or provide investment advice.

## Current architecture

```text
Illustrative, supplied, or reviewed inputs
                 |
                 v
Assumption register + source status + version + supersession
                 |
                 v
Deterministic financial engines
  ├─ acquisition underwriting and IRR / NPV
  ├─ monthly debt and constraint sizing
  ├─ monthly development and capitalized interest
  ├─ LP / GP waterfall
  ├─ modular lease-level rent-roll roll-up
  └─ scenarios, stress cases, correlated simulation
                 |
                 v
Governance and reproducibility layer
  ├─ lineage records
  ├─ tamper-evident audit primitives
  └─ model-run fingerprint
                 |
                 v
Decision layer
  ├─ source-aware IC screening
  ├─ downside-first memo and downloadable package
  ├─ side-by-side comparison
  └─ constrained portfolio allocation and risk view
                 |
                 v
Streamlit dashboard + Markdown / CSV / JSON artifacts
```

## Module boundaries

| Module | Responsibility | Deliberate boundary |
| --- | --- | --- |
| `src/atlasre.py` | Acquisition cash flows, annual underwriting, IRR/NPV, and market scoring | Does not ingest documents, construct a lease forecast, or make a decision |
| `src/debt.py` | Monthly debt schedule, draws, IO, amortization, balloon, DSCR, and LTV/DSCR sizing | Does not infer missing loan terms or model a full debt stack |
| `src/advanced_underwriting.py` | Development screen, seeded correlated simulation, stress cases, and risk tails | Does not claim probability calibration from observed market data |
| `src/institutional.py` | Monthly development schedule and multi-tier LP/GP waterfall | Does not replace project-specific legal or financing documents |
| `src/lease.py` | Validated rent roll and monthly contract-rent/vacancy/NOI roll-up | Does not yet model TI/LC, downtime, recoveries, capex, or re-leasing economics |
| `src/governance.py` | Assumptions, lineage, audit primitives, and reproducibility fingerprints | Does not provide persistent approvals, identity, or permissions |
| `src/ic_workflow.py` | Source-aware flags, comparison, decision state, and screening memo | Does not approve or transmit a transaction |
| `src/portfolio.py` | Capital rationing, concentration caps, DSCR gates, and exposure diagnostics | Does not optimize multi-period fund commitments |
| `generate_committee_report.py` | Reproducible Markdown/CSV/JSON/ZIP screening package | Does not certify the supplied data |
| `dashboard.py` | Interactive decision surface built on the model modules | Does not duplicate financial formulas as a second source of truth |

## Control principles

1. **Downside precedes upside.** Source status, governance flags, NPV, DSCR, stress cases, and tail metrics are decision inputs before headline return metrics.
2. **Source status is a gate.** `REVIEW REQUIRED` is not equivalent to `VERIFIED`; an unverified case cannot receive `PASSES INITIAL SCREEN`.
3. **Periodicity is explicit.** Monthly schedules remain monthly. Monthly IRRs are annualized only at the presentation boundary.
4. **Constraints are visible.** Debt sizing states the binding constraint. Portfolio allocation retains eligibility and exclusion reasons.
5. **Outputs are challengeable.** Material outputs carry explicit assumptions, lineage fields, source status, and a deterministic model-run fingerprint.
6. **Illustrative data remains labeled.** Formatting cannot convert an illustrative default into a verified fact.
7. **Invalid states fail loudly.** Non-finite values, malformed schedules, invalid dates, and malformed governance records are rejected or marked invalid.

## Current capabilities versus production gaps

| Capability | Current state | Production gap |
| --- | --- | --- |
| Acquisition underwriting | Deterministic annual model with IRR, NPV, leverage, exit value, and DSCR | Independent validation, accounting, tax, and asset-level operating-model integration |
| Debt | Monthly IO/amortization/draw/balloon schedule and LTV/DSCR sizing | Full debt stack, covenants, hedging, refinance, and term-sheet ingestion |
| Development | Monthly draws, contingency, capitalized interest, stabilization, and exit | Contract-level budgets, change orders, schedule risk, and cost-to-complete controls |
| Waterfall | Return of capital, pref, hurdles, promote, and reconciliation | Legal-document mapping, clawbacks, catch-ups, tax distributions, and escrow terms |
| Lease foundation | Rent roll, escalations, vacancy and rollover assumptions, credit flag, expiry counts, monthly NOI, and opt-in annual-NOI bridge | TI/LC, recoveries, capex, granular downtime, tenant credit evidence, and complete rollover economics |
| Risk | Seeded correlated shocks, stress cases, tails, expected shortfall, and DSCR-breach probability | Calibrated distributions, historical validation, liquidity, and drawdown modeling |
| Governance | Versioned assumptions, lineage, audit hash chain, and fingerprint | Persistent immutable event store, identity, roles, approvals, and retention policy |
| IC workflow | Source-aware flags, comparison, memo, and ZIP package | Human approval workflow, conditions precedent, decision history, and permissions |
| Portfolio | Concentration cap, DSCR gate, capital rationing, HHI, and exposure view | Multi-period optimizer, capital calls, liquidity, covariance, and fund obligations |
| Data | Illustrative CSV and explicit user inputs | Source connectors, document extraction, citations, timestamps, and confidence review |

## Modeling conventions and simplifications

The following choices are part of the current model contract. They are not hidden assumptions and should be reconsidered before using the repository for a live transaction.

| Area | Current convention or simplification |
| --- | --- |
| Operating income | Acquisition underwriting uses one annual NOI input. The input is year-one NOI; growth begins in year two. There is no monthly operating statement in the acquisition engine. |
| Property taxes | Property tax is not modeled as a separate line. Any impact must already be reflected in the supplied NOI. |
| Capital reserves | There is no capex reserve in the acquisition engine. Major repairs and replacement reserves are not forecast. |
| Lease economics | The optional lease foundation models contract rent, escalation, vacancy, rollover assumptions, operating expenses, and NOI roll-up. It does not model TI/LC, recoveries, downtime detail, capex, renewal probability, or tenant-credit evidence. |
| Transaction costs | Acquisition and selling costs are percentage assumptions applied to purchase price and exit value. Legal, financing, diligence, tax, and other fees are not separately modeled unless represented by an input. |
| Exit | Exit value is final-period NOI divided by an exit cap rate. There is no disposition timing uncertainty, buyer-side financing analysis, or exit-price distribution calibrated to market data. |
| Debt | The acquisition model contains one amortizing loan with monthly amortization. There is no mezzanine, preferred equity, construction-to-permanent facility, hedge, covenant package, refinance, extension, or default model. |
| Development | The development module uses evenly distributed construction draws, a contingency percentage, capitalized interest, a simple NOI ramp, and a single terminal sale. It is not a contractor cost-to-complete model. |
| Taxes and accounting | Income tax, property tax, transfer tax, depreciation, accounting treatment, FX, and cash-tax timing are outside the model. |
| Waterfall | Waterfall logic is a deterministic distribution schedule, not legal advice. It omits negotiated catch-ups, clawbacks, tax distributions, escrow, and document-specific definitions. |
| Risk | Simulation shocks are seeded and reproducible. They are not empirical probability estimates and are not calibrated to a historical dataset. |
| Portfolio | `portfolio_exposure` is a documented naive score-weighted screen. The constrained allocator in `src/portfolio.py` is the intended path when DSCR, concentration, and eligibility constraints are required. |
| Governance | Source status, lineage, and fingerprints are calculated in-process. There is no persistent server-side approval ledger, role system, retention policy, or immutable event store. |
| Data | The bundled market CSV and dashboard defaults are illustrative. The model does not ingest or verify PDFs, spreadsheets, leases, appraisals, bank terms, or third-party sources. |

## Current gaps versus target

The baseline audit identified gaps between the remote baseline and the current local branch. The local branch now includes the lease bridge, source-aware screening, canonical fingerprints, downside metrics, and a shorter internal-review dashboard. These additions do not remove the simplifications listed above.

The remaining gaps are appropriately material rather than cosmetic: persistent approvals, source-controlled ingestion, complete commercial lease economics, validated probability calibration, a full debt stack, and multi-period portfolio constraints. The simpler annual-NOI path remains available and untouched. The lease route stays opt-in, traceable, and source-gated.

## Six-to-ten-week implementation roadmap

| Timing | Outcome | Control objective |
| --- | --- | --- |
| Weeks 1–2 | Persistent model-run and assumption store | Immutable versioning, actor identity, source files, approval states, and reproducible reruns |
| Weeks 2–4 | Commercial lease economics | Rollover, downtime, TI/LC, recoveries, capex, and tenant-level evidence with tests |
| Weeks 4–6 | Debt-stack and development controls | Construction-to-perm, mezz/preferred equity, covenants, refinance, and cost-to-complete |
| Weeks 6–8 | Source-controlled ingestion and validation | Excel/PDF inputs with citations, reviewer queue, stale-data flags, and reconciliations |
| Weeks 8–10 | Portfolio and IC operating workflow | Multi-period allocation, approval conditions, variance monitoring, and audit reporting |

A FastAPI boundary, database, and document layer are plausible future directions. They should not be introduced as cosmetic migrations before the deterministic engines, audit controls, and source lineage are genuinely strengthened.

## How to challenge a model run

A reviewer should first inspect the source status, decision state, governance flags, and model-run fingerprint. Next, inspect the assumption register and lineage for purchase price, NOI, growth, exit cap, leverage, debt terms, and terminal value. Then review minimum DSCR, negative NPV, stress cases, expected shortfall, and portfolio exposure. Only after those checks should the committee discuss base-case IRR and upside. A change in any material assumption requires a new assumption version and a new fingerprint.

## Explicit non-claims

AtlasRE does not claim production readiness, live-data accuracy, investment advice, legal or tax compliance, complete lease underwriting, persistent approval controls, or calibrated market probabilities. Those are future engineering and governance deliverables; they must not be implied through documentation, design, or terminology.

## References

[1]: https://github.com/hossiendehghan989/atlasre-investment-intelligence "AtlasRE Investment Intelligence repository"
