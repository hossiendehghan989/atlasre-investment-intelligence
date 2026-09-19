# AtlasRE Investment Intelligence

## A transparent decision-support system for global real-estate investing

AtlasRE is a portfolio project designed around the real questions faced by a real-estate investment and development firm: **Which opportunity deserves attention? What assumptions drive its return? How fragile is the thesis? How should an investment committee compare markets and deals?**

The project is intentionally aligned with the public strategy of global real-estate investment platforms that combine REIT exposure, luxury development, general investments, advisory, and brokerage. It is not affiliated with Tamleek, does not use private company data, and does not provide investment advice. Its purpose is to demonstrate the author's ability to convert finance and real-estate reasoning into a tested analytical product.

## Why this project stands out

Most real-estate portfolio projects stop at a property-value calculator. AtlasRE goes further by connecting four layers:

1. **Underwriting:** NOI growth, entry yield, exit capitalization, debt, equity, IRR, NPV, and equity multiple.
2. **Scenario analysis:** downside, base, and upside combinations across growth and exit-cap assumptions.
3. **Market intelligence:** risk-adjusted market ranking across growth, employment, rents, liquidity, and risk.
4. **Portfolio thinking:** capital allocation across eligible opportunities using risk-adjusted scores.

The result is not a black-box prediction. It is an auditable investment committee workflow in which every important output can be traced to an explicit assumption.

## Core model

For each opportunity, the engine forecasts NOI through the hold period:

```text
NOI_t = NOI_0 × (1 + growth)^t
```

The terminal value is estimated through the exit capitalization method:

```text
Exit Value = Forward NOI / Exit Cap Rate
```

The cash-flow engine then accounts for acquisition costs, selling costs, debt, annual debt service, and equity contributions. It reports both levered and unlevered returns because leverage can improve equity returns while increasing refinancing and downside risk.

## What the dashboard shows

The Streamlit dashboard contains two decision surfaces. The underwriting view allows an investment committee member to change purchase price, NOI, growth, hold period, exit cap, and leverage. It immediately shows entry cap, levered IRR, unlevered IRR, equity multiple, exit value, and a full sensitivity matrix.

The market view ranks illustrative global markets using a transparent weighted score. The sample inputs are placeholders and are visibly labeled as such. This is deliberate: the project demonstrates the methodology without presenting invented market statistics as facts.

## Example underwriting assumptions

| Input | Illustrative value |
| --- | ---: |
| Purchase price | $10,000,000 |
| Annual NOI | $650,000 |
| Hold period | 5 years |
| NOI growth | 3.0% |
| Exit cap rate | 6.0% |
| Leverage | 50.0% |

These values are defaults for demonstration and must be replaced with verified asset-level information before any real decision.

## Engineering quality

The repository includes a modular Python engine, a Streamlit interface, automated tests, input validation, and a clear separation between assumptions and calculations. The test suite covers cash-flow structure, scenario behavior, market-risk ranking, and capital-allocation constraints.

## Quick start

```bash
git clone https://github.com/hossiendehghan989/atlasre-investment-intelligence.git
cd atlasre-investment-intelligence
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
streamlit run dashboard.py
```

## Project structure

```text
.
├── dashboard.py
├── data/market_inputs.csv
├── requirements.txt
├── src/atlasre.py
└── tests/test_atlasre.py
```

## Resume-ready description

> Built **AtlasRE Investment Intelligence**, a transparent real-estate underwriting and market-ranking platform that models NOI growth, exit capitalization, leverage, IRR, NPV, equity multiples, downside/base/upside scenarios, and risk-adjusted global-market allocation. Delivered a tested Streamlit investment-committee dashboard using Python, pandas, SciPy, and reproducible analytical assumptions.

## Why it is relevant to global real-estate leadership

The project is built around strategic questions rather than a generic coding exercise. It demonstrates an understanding of selective asset acquisition, stakeholder value, cross-market comparison, investment advisory, and the relationship between development assumptions and returns. It also reflects the legal and governance reality of property transactions by keeping assumptions explicit and separating analytical output from an investment decision.

## Limitations

This is a research and portfolio prototype. The default market data is illustrative, not a live market feed. The valuation is not a full development feasibility model and does not include taxes, construction draws, operating-expense detail, waterfall structures, preferred returns, FX exposure, refinancing, or legal diligence. The system must not be used as a substitute for verified financial, legal, tax, engineering, or market analysis.

## License

MIT License.

## Advanced underwriting layer

The project now includes a second underwriting layer for development and risk review. The development module models land, hard costs, soft costs, contingency, construction debt, capitalized interest, stabilized NOI, exit value, preferred return, and sponsor promote. This is closer to the questions asked during development screening than a simple buy-and-hold calculator.

The risk module runs reproducible Monte Carlo simulations over NOI growth, exit cap rate, and purchase price. It reports median, P10, and P90 levered IRR, the probability that IRR falls below a hurdle rate, and the probability of negative NPV. A named stress-test table also covers no growth, exit-cap expansion, cost inflation, and a combined downside case.

The dashboard presents these outputs in separate Underwriting, Risk & Scenarios, Development, and Markets tabs. The purpose is to make downside visible before a committee discusses upside.

## Investment discipline

The project does not present an attractive base case as a conclusion. It presents the assumptions that create the base case, shows how results change when those assumptions move, and separates operating performance from leverage. In a real workflow, verified rent rolls, operating statements, construction budgets, debt terms, title and legal diligence, tax treatment, market comparables, and FX assumptions would replace the illustrative inputs.

## Executive note

[`INVESTMENT_COMMITTEE_MEMO.md`](INVESTMENT_COMMITTEE_MEMO.md) explains the business purpose and how the prototype could be extended inside a real investment organization. It is deliberately written as a concise investment-committee brief rather than a technical showcase.

## Committee screening outputs

The underwriting engine now amortizes debt monthly, reports the remaining balance at exit, and calculates minimum DSCR across the hold period. A committee summary applies explicit initial-screen flags for return below hurdle, thin debt coverage, and negative unlevered NPV. A break-even exit-cap solver shows the terminal capitalization rate required to meet the selected hurdle.

The dashboard also includes a one-way exit-cap sensitivity table. This is a more useful committee artifact than a single base-case IRR because it makes the terminal-value dependency visible and gives reviewers a precise assumption to challenge.

## Institutional underwriting upgrade

The latest version adds a monthly development model with land, hard-cost, soft-cost, and contingency draws; construction-period debt draws; capitalized interest; stabilization ramp; sale proceeds; and debt repayment at exit. It also sizes acquisition debt from the binding LTV and DSCR constraints, rather than selecting leverage as an isolated input.

The LP/GP distribution module applies return of capital, a preferred return, and a sponsor promote. The assumption register labels every supplied input as requiring review until a source is attached. This keeps an illustrative model from being mistaken for verified diligence.

Run the committee report generator with:

```bash
python generate_committee_report.py
```

It produces a Markdown investment-committee review, stress-case CSV, and monthly development-model CSV under `artifacts/`. The report is intentionally written as a screening document: it states what the model says, what it does not say, and which diligence steps must happen before an approval decision.


## Institutional platform upgrade (v0.3)

The repository now includes a governance and portfolio layer designed around the original brief. The Streamlit decision surface adds an IC workflow, version-ready assumption register, output lineage download, downside-first risk review, and portfolio allocation with concentration and DSCR flags. `src/governance.py` provides source/status labeling, machine-readable lineage records, and a tamper-evident hash-chain audit primitive. `src/portfolio.py` provides explicit capital-allocation constraints and portfolio snapshot metrics.

The target operating model, high-level schema, agent boundaries, recommended stack, controls, and 8–12 week roadmap are documented in [`ATLASRE_ARCHITECTURE.md`](ATLASRE_ARCHITECTURE.md). This is intentionally an evolution of the existing Python/Streamlit core rather than a replacement: deterministic financial calculations remain the source of truth while future AI agents are constrained to cited, reviewable outputs.


## Institutional hardening (v0.4)

The latest increment adds a dedicated monthly debt engine with interest-only periods, balloon maturity, monthly DSCR observations, and binding LTV/DSCR sizing; a deterministic IC workflow with side-by-side deal comparison, severity-ranked flags, and downloadable downside-first screening memos; stable versioned assumption IDs; and an active-set portfolio allocator that re-allocates around concentration caps while excluding assets below the minimum DSCR gate. The regression suite now contains 18 tests covering these behaviors.

The system still does not claim live data ingestion, OCR, semantic search, AI agents, or persistent role-based approvals. Those are explicit remaining gaps, not mocked features.


## Reference-grade model upgrade (v0.5)

The financial core now includes a multi-tier LP/GP waterfall with return-of-capital, preferred return, ordered hurdles, tier-specific promote, and distribution checks. The monthly development model explicitly records lender fees, peak debt, capitalized interest, construction/stabilization timing, and annualizes monthly IRRs before reporting them. The uncertainty engine uses deterministic correlated shocks across growth, exit cap, purchase price, and debt rate, and reports P05/P10/median/P90/P95 IRR, negative-NPV probability, hurdle failure, and DSCR breach probability. Stress cases now include a rate shock and expose minimum DSCR.

These upgrades are deliberately deterministic. They do not pretend to be a live data platform, a lease-level model, or an AI system. All assumptions remain explicit and challengeable.


## Numerical and governance hardening (v0.6)

The underwriting core now validates finite inputs, transaction-cost bounds, growth limits, debt terms, and normalized market factors. IRR solving uses a deterministic scanned bracket and handles negative/high-return cases without noisy overflow warnings. Zero-rate amortization is supported explicitly. Debt schedules reject malformed draws and NOI vectors, and portfolio allocation rejects non-finite inputs while preserving deterministic ordering.

Governance records now have typed lineage and audit contracts. Malformed audit events return a failed verification rather than raising an opaque key error; lineage records require explicit inputs and a positive assumption version. The adversarial suite covers zero-rate debt, invalid assumptions, malformed audit events, verified assumption snapshots, deterministic allocation, and market-factor validation.

The repository currently passes **27 tests**. It remains a deterministic analytical prototype: live data ingestion, persistent approvals, lease-level modeling, and production storage are intentionally not claimed.


## Decision and reproducibility hardening (v0.7)

IC screening is now source-aware: a case marked `REVIEW REQUIRED` cannot pass automatically even if its modeled returns clear the economic thresholds. Flags are classified as `CRITICAL`, `HIGH`, `GOVERNANCE`, or `INFO`, and the decision state is explicitly one of `PASSES INITIAL SCREEN`, `REVIEW REQUIRED`, or `REJECT / REWORK`. Side-by-side comparisons expose critical and review-flag counts rather than only a free-text summary.

Risk summaries now include expected shortfall for the worst 10% of IRR and NPV outcomes, in addition to percentile tails and DSCR-breach probability. Governance includes a deterministic model-run fingerprint over the model version, assumption snapshot, and lineage records, creating a reproducibility handle without pretending to provide persistent storage.


## Portfolio risk view (v0.8)

Portfolio review now reports financed exposure, not only weighted return. The allocator exposes capital eligibility, DSCR eligibility, constraint reason, DSCR-breach exposure, negative-IRR exposure, concentration HHI, and maximum asset weight. This keeps capital rationing and portfolio risk visible when an asset is excluded or capped. The test suite now passes **32 tests**.
