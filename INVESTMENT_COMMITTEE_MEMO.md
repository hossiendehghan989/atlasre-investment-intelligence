# AtlasRE Investment Intelligence — Executive Investment Committee Brief

## Executive position

AtlasRE is a **transparent, deterministic decision-support prototype** for real-estate investment screening. It is built to help a principal or committee challenge assumptions before committing diligence time or capital. It is not an approval system, a valuation opinion, or investment advice.

The current release combines annual acquisition underwriting, monthly debt and development schedules, a multi-tier LP/GP waterfall, seeded correlated risk analysis, source-aware governance gates, a small lease-level foundation, and constrained portfolio diagnostics.

## What the committee sees first

The decision surface is intentionally downside-first. It presents the source status and decision state before base-case returns. It then exposes critical economic flags, governance flags, negative NPV, minimum DSCR, exit-cap break-even, stress cases, expected shortfall, DSCR-breach probability, and portfolio concentration. A verified source package is a prerequisite for an automatic initial-screen pass.

The downloadable screening package includes the executive report, assumptions, lineage, risk summary, stress cases, and monthly development reference schedule. Its model-run fingerprint provides a reproducibility handle for the exact model version, assumption snapshot, and lineage set used in the package.

## Questions the model can answer

A reviewer can change purchase price, NOI, growth, hold period, exit cap, leverage, and hurdle assumptions. The system can then show:

- whether the simplified acquisition case clears configured economic gates;
- how much value depends on the terminal exit cap and NOI path;
- whether debt coverage or LTV is the binding sizing constraint;
- how the outcome behaves under rate, cost, growth, and exit-cap stress;
- what the worst simulated 10% of IRR and NPV outcomes look like;
- which portfolio assets are eligible, capped, rationed, or excluded;
- how much invested capital is exposed to DSCR breach or negative IRR.

These answers remain conditional on the supplied assumptions. They do not establish that the assumptions are true.

## How to present a case to an Investment Committee

Begin with source status and the decision state. If the case is `REVIEW REQUIRED`, say that before showing returns. Walk through critical flags and the minimum DSCR. Review negative NPV, the exit-cap break-even, stress cases, expected shortfall, and any portfolio concentration. Then review base-case IRR and equity multiple. Finish by agreeing on the diligence that could change the decision and record the assumption version and model fingerprint.

A committee should challenge the terminal value, the operating income path, the debt terms, the timing of cash flows, and the evidence supporting market assumptions. A polished output is not evidence of a verified deal.

## Current strengths

The financial engines are small enough to inspect and are covered by adversarial tests. Monthly debt interest, principal, draws, IO periods, amortization, and balloon balances are visible. Development schedules separate costs, draws, capitalized interest, stabilization, and exit. Waterfall distributions reconcile to available cash. Risk simulation is seeded and reports tails rather than only a median. Governance records assumptions, lineage, source status, audit hashes, and a model-run fingerprint.

The optional lease module is a foundation rather than a full rent-roll product. It supports multiple leases, dates, escalations, vacancy assumptions, credit-quality labels, and monthly NOI roll-up. The existing simplified annual-NOI path remains explicit and unchanged.

## Remaining limitations

The repository is an advanced analytical prototype. It does not provide live market data, document extraction, persistent approval records, production identity and access control, complete commercial lease economics, tax or FX modeling, a full construction debt stack, or a multi-period fund optimizer. It must not be used as a substitute for independent model validation or legal, tax, engineering, environmental, insurance, or market diligence.

## Resume-ready description

> Built AtlasRE, a deterministic real-estate investment intelligence prototype with monthly debt and development underwriting, multi-tier LP/GP waterfall economics, seeded correlated risk simulation with expected shortfall, source-aware IC decision gates, reproducibility fingerprints, lease-level NOI foundations, and constrained portfolio risk diagnostics. Designed the system around auditable assumptions, explicit downside, and adversarial tests rather than opaque automation.

## References

[1]: https://github.com/hossiendehghan989/atlasre-investment-intelligence "AtlasRE Investment Intelligence repository"
