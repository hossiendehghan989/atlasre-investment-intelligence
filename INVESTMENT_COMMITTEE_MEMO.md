# AtlasRE — Investment Committee Brief

**Built by Hossein Dehghan** as a personal portfolio project in decision-support engineering.

## What I was trying to build

AtlasRE is a transparent, deterministic prototype for early-stage real-estate screening. I built it to help a principal or reviewer challenge assumptions before spending diligence time or capital. It is not an approval system, a valuation opinion, or investment advice.

The current version combines annual acquisition underwriting, monthly debt and development schedules, a multi-tier LP/GP waterfall, seeded risk analysis, source-aware governance gates, a modular lease-level rent-roll foundation, and constrained portfolio diagnostics. The important design choice is not the number of modules; it is keeping the assumptions and limitations visible.

## Start with downside and evidence

The decision surface starts with source status and the screening decision. It then shows critical economic flags, governance flags, unlevered NPV, minimum DSCR, break-even exit cap, stress cases, expected shortfall, and DSCR-breach probability. Base-case IRR and equity multiple come after those checks.

A verified source package is required for an automatic initial-screen pass. A strong return cannot repair an incomplete source package, and a dashboard cannot turn an illustrative input into evidence.

## What the model can answer

A reviewer can change purchase price, annual NOI, NOI growth, hold period, exit cap, leverage, debt terms, and hurdle assumptions. The system then shows whether the simplified case clears its configured gates, how much value depends on the terminal exit cap and NOI path, whether debt coverage or LTV is the binding sizing constraint, and how the result behaves under rate, cost, growth, and exit-cap stress.

It can also show the worst simulated ten percent of IRR and NPV outcomes, DSCR-breach probability, source-aware screening flags, and whether a portfolio asset is eligible, capped, rationed, or excluded. These results are conditional on the supplied assumptions. They do not prove that those assumptions are true.

## How I would present a case

I would start with source status and decision state. If the case is `REVIEW REQUIRED`, I would say that before showing returns. Then I would walk through governance and critical flags, minimum DSCR, negative NPV, break-even exit cap, stress cases, expected shortfall, and portfolio concentration. Only after that would I discuss base-case IRR and equity multiple.

The useful questions are about terminal value, the operating-income path, debt terms, cash-flow timing, and the evidence behind market assumptions. The next diligence actions should be recorded together with the assumption version and model-run fingerprint. A polished output is not proof of a verified deal.

## What is working well

The financial engines are small enough to inspect and are covered by adversarial tests. Monthly debt interest, principal, draws, IO periods, amortization, and balloon balances are visible. Development schedules separate costs, draws, capitalized interest, stabilization, and exit. Waterfall distributions reconcile to available cash. Risk simulation is seeded and reports tails rather than only a median. Governance records assumptions, lineage, source status, audit hashes, and a model-run fingerprint.

The lease module is deliberately a foundation, not a complete rent-roll product. It supports multiple leases, dates, escalations, vacancy assumptions, credit-quality labels, and monthly NOI roll-up. The simplified annual-NOI path remains explicit until an optional lease-derived path is selected and evidenced.

## What is not finished

The repository does not provide live market data, document extraction, persistent approval records, production identity and access control, complete commercial lease economics, tax or FX modeling, a complete construction debt stack, or a multi-period fund optimizer. It must not replace independent model validation or legal, tax, engineering, environmental, insurance, or market diligence.

## Short description

> I built AtlasRE, a deterministic real-estate screening prototype that makes acquisition cash flows, debt sizing, downside cases, source status, and review artifacts explicit. I designed it around a simple rule: show the evidence and the downside before presenting the headline return.

## References

[1]: https://github.com/hossiendehghan989/atlasre-investment-intelligence "AtlasRE Investment Intelligence repository"
