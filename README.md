# AtlasRE Investment Intelligence

[![CI](https://github.com/hossiendehghan989/atlasre-investment-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/hossiendehghan989/atlasre-investment-intelligence/actions/workflows/ci.yml)

I built AtlasRE as a personal portfolio project to explore a practical question: **when the assumptions are explicit, can an analyst see how an acquisition model reaches its answer, what could break it, and what still needs to be verified?**

This is a Python and Streamlit prototype for screening one **ILLUSTRATIVE** real-estate acquisition case. It is not a valuation opinion, an approval system, or investment advice. The point is to make the calculation and the remaining uncertainty easy to inspect.

**Author:** [Hossein Dehghan](https://github.com/hossiendehghan989) — Industrial Engineering graduate focused on applied AI, data science, energy intelligence, and industrial analytics.

| Decision summary | Downside view | Review files |
| --- | --- | --- |
| ![Decision summary](docs/images/decision-summary.png) | ![Downside view](docs/images/downside-risk.png) | ![Review package](docs/images/review-package.png) |

## Why I built it

I wanted a small decision-support system rather than another opaque dashboard. The model keeps the assumptions visible, calculates the debt and cash-flow paths explicitly, shows downside before upside, and records enough context for another person to challenge the result. This is the same working style I use in my other projects, including [GridWise AI](https://github.com/hossiendehghan989/gridwise-ai) and [Tesla Stock Analysis](https://github.com/hossiendehghan989/Tesla-Stock-Analysis): understand the system, make assumptions explicit, build the simplest useful solution, and measure the result.

## Try it in 60 seconds

Run these commands from the repository root on Python 3.11 or 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock && streamlit run dashboard.py
```

Open the local URL printed by Streamlit. Change an assumption, inspect the downside flags, select **Prepare review files**, and download the ZIP or formula-based Excel reconciliation workbook. Every bundled input and output remains **ILLUSTRATIVE**. The dashboard and CLI review package both use 5,000 seeded downside simulations.

For an owner-supplied case, run locally with `python scripts/screen_deal.py path/to/deal.json --output deal-review`; start from [the JSON template](docs/templates/deal_template.json) and read [USING_A_REAL_DEAL](docs/USING_A_REAL_DEAL.md).

**Live demo:** [atlasre-screening-demo.streamlit.app](https://atlasre-screening-demo.streamlit.app/) — uses ILLUSTRATIVE data, has no authentication, is not for sensitive data, and the free app may take a short time to wake up if it has been idle.

## What the default case says

The default illustrative case displays **REJECT / REWORK**. Its flags show that the source package is not verified, unlevered NPV is negative, and levered IRR is below the 12% hurdle. The current figures are **11.97% levered IRR**, **9.32% unlevered IRR**, **1.70x equity multiple**, and a **$12,193,012 exit value**. These are reproducible model outputs, not market evidence.

## What is included

| Area | Implemented behavior | Boundary |
| --- | --- | --- |
| Acquisition | Annual NOI, terminal value, levered and unlevered cash flows, IRR, NPV, equity multiple, and DSCR | No tax, capex reserve, property-level operating statement, or valuation opinion |
| Debt | Monthly payment, interest, amortization, balloon balance, annual debt roll-up, and LTV/DSCR sizing | No debt stack, hedge, refinance, or loan-document covenant model |
| Downside | Named stress cases plus seeded, reproducible Monte Carlo risk summaries | No historical probability calibration |
| Governance | Assumption register, source-status gate, lineage, and run fingerprint | No persistent approval ledger, RBAC, or retention service |
| Review package | Memo, assumptions, risk summary, annual debt schedule, lease references, Excel reconciliation workbook, and ZIP download | Source status remains `REVIEW REQUIRED` unless the caller supplies reviewer and source reference |
| Excel reconciliation | Live formulas for annual NOI, monthly debt, IRR, NPV, PMT, IPMT, PPMT, equity multiple, and formula-to-model differences | Workbook must be recalculated in Excel or LibreOffice; it does not validate source documents |
| Lease and portfolio | Illustrative rent-roll bridge, allocation checks, and concentration diagnostics | No complete lease economics, tenant-credit evidence, or multi-period fund optimizer |

## Why this is code instead of another spreadsheet

A spreadsheet can implement many of the same calculations. I used code here because I wanted the assumptions, validation, tests, downside cases, and generated review files to live together and be repeatable. The Excel workbook is still included, but it is a reconciliation surface rather than the only source of truth.

The supplied annual NOI is year-one NOI. Growth begins in year two. Exit value is final-year NOI divided by exit cap rate. Acquisition and selling costs are percentages of price and exit value, respectively. The core loan is a single amortizing loan calculated monthly. See the [reviewer guide](docs/REVIEWER_GUIDE.md) for the formula map and reconciliation steps.

## What this project does not claim

This is a single-user, local prototype. It has no authentication, immutable audit store, source-document ingestion, live market data, OCR, accounting integration, tax model, FX model, complete lease economics, construction-to-permanent debt, mezzanine or preferred equity, persistent approvals, or production authorization controls. The seeded simulation is reproducible, but it is not calibrated to observed market outcomes. No output is investment advice or an approval.

## Testing and deployment

CI installs `requirements.lock`, runs `ruff check .`, and runs `python -m pytest -q` on every push and pull request. The current package benchmark and reproducibility evidence are documented in [CHANGELOG.md](CHANGELOG.md). For Streamlit Community Cloud settings and deployment steps, see [DEPLOY.md](DEPLOY.md). The generated [illustrative sample package](docs/sample_output/README_ILLUSTRATIVE.md) and [demo script](docs/DEMO_SCRIPT.md) are available for review.

## Repository layout

```text
src/atlasre.py                 core acquisition underwriting
src/advanced_underwriting.py   seeded simulation, stress cases, and risk summaries
src/debt.py                    monthly debt schedules and debt sizing
src/reconciliation.py          formula-based Excel reconciliation workbook
generate_committee_report.py   review-package generator
dashboard.py                   Streamlit interface
tests/                         regression and independent cross-checks
docs/                          indexed reviewer, demo, deployment, and sample materials
```

For the full document map, see [docs/README.md](docs/README.md).

## License

MIT. See [LICENSE](LICENSE).
