# AtlasRE Investment Intelligence — Executive Investment Committee Brief

## Executive position

AtlasRE is a **transparent, deterministic decision-support prototype** for real-estate investment screening. It is built to help a principal or committee challenge assumptions before committing diligence time or capital. It is not an approval system, a valuation opinion, or investment advice.

The current core combines annual acquisition underwriting, monthly debt and development schedules, a multi-tier LP/GP waterfall, seeded correlated risk analysis, source-aware governance gates, a modular lease-level rent-roll foundation, and constrained portfolio diagnostics. The system is intentionally clearer about what it does not model than a polished but opaque tool would be.

## The committee sees downside and governance first

The decision surface begins with the source status and the screening decision. It then shows critical economic flags, governance flags, unlevered NPV, minimum DSCR, break-even exit cap, stress cases, expected shortfall, and DSCR-breach probability. Base-case IRR and equity multiple appear only after those downside questions are visible.

A verified source package is a prerequisite for an automatic initial-screen pass. A strong return cannot cure an incomplete source package, and a dashboard display cannot turn an illustrative input into verified evidence.

## What the model can answer

A reviewer can change purchase price, annual NOI, NOI growth, hold period, exit cap, leverage, debt terms, and hurdle assumptions. The system can then show whether the simplified acquisition case clears configured economic gates, how much value depends on the terminal exit cap and operating-income path, whether debt coverage or LTV is the binding sizing constraint, and how the result behaves under rate, cost, growth, and exit-cap stress.

It can also show the worst simulated ten percent of IRR and NPV outcomes, DSCR-breach probability, source-aware screening flags, and whether a portfolio asset is eligible, capped, rationed, or excluded. These outputs remain conditional on supplied assumptions. They do not establish that those assumptions are true.

## How to present a case to an Investment Committee

Begin with source status and decision state. If the case is `REVIEW REQUIRED`, state that before showing returns. Walk through governance and critical flags, minimum DSCR, negative NPV, break-even exit cap, stress cases, expected shortfall, and portfolio concentration. Only then review base-case IRR and equity multiple.

The discussion should challenge terminal value, the operating-income path, debt terms, timing of cash flows, and the quality of evidence supporting market assumptions. Close by agreeing on the next diligence actions, recording the assumption version, and preserving the model-run fingerprint. A polished output is not evidence of a verified deal.

## Current strengths

The financial engines are small enough to inspect and are covered by adversarial tests. Monthly debt interest, principal, draws, IO periods, amortization, and balloon balances are visible. Development schedules separate costs, draws, capitalized interest, stabilization, and exit. Waterfall distributions reconcile to available cash. Risk simulation is seeded and reports tails rather than only a median. Governance records assumptions, lineage, source status, audit hashes, and a model-run fingerprint.

The lease module is deliberately a foundation, not a complete rent-roll product. It supports multiple leases, dates, escalations, vacancy assumptions, credit-quality labels, and monthly NOI roll-up. The existing simplified annual-NOI path remains explicit until an optional lease-derived path is selected and evidenced.

## Remaining limitations

The repository is an advanced analytical prototype. It does not provide live market data, document extraction, persistent approval records, production identity and access control, complete commercial lease economics, tax or FX modeling, a complete construction debt stack, or a multi-period fund optimizer. It must not be used as a substitute for independent model validation or legal, tax, engineering, environmental, insurance, or market diligence.

## Resume-ready description

> Built AtlasRE, a deterministic real-estate investment intelligence prototype with auditable acquisition and monthly development underwriting, debt sizing, multi-tier LP/GP waterfall economics, seeded correlated risk simulation with expected shortfall, source-aware IC decision gates, reproducibility fingerprints, lease-level NOI foundations, and constrained portfolio-risk diagnostics. Designed the system for adversarial review by prioritizing evidence quality, downside visibility, and explicit model boundaries over opaque automation.

## References

[1]: https://github.com/hossiendehghan989/atlasre-investment-intelligence "AtlasRE Investment Intelligence repository"
