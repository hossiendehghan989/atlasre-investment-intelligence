# AtlasRE Investment Intelligence

[![CI](https://github.com/hossiendehghan989/atlasre-investment-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/hossiendehghan989/atlasre-investment-intelligence/actions/workflows/ci.yml)

AtlasRE is a Python and Streamlit prototype that calculates and records an **ILLUSTRATIVE** real-estate acquisition screening case from explicit assumptions.

| Decision summary | Downside view | Review files |
| --- | --- | --- |
| ![Decision summary](docs/images/decision-summary.png) | ![Downside view](docs/images/downside-risk.png) | ![Review package](docs/images/review-package.png) |

## Try it in 60 seconds

Run these commands from the repository root on Python 3.11 or 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock && streamlit run dashboard.py
```

Open the local URL printed by Streamlit. Change an assumption, inspect the downside flags, select **Prepare review files**, and download the ZIP or formula-based Excel reconciliation workbook. Every bundled input and output remains **ILLUSTRATIVE**.

## What the decision output looks like

The default illustrative case displays a **REJECT / REWORK** status. Its flag list shows that the source package is not verified, unlevered net present value is negative, and levered internal rate of return is below the 12% hurdle. The dashboard shows the current default figures—11.97% levered IRR and $12,193,012 exit value—together with the assumptions that produced them. These figures are reproducible, not market evidence.

## What is included

| Area | Implemented behavior | Boundary |
| --- | --- | --- |
| Acquisition | Annual NOI, terminal value, levered and unlevered cash flows, IRR, NPV, equity multiple, and DSCR | No tax, capex reserve, property-level operating statement, or valuation opinion |
| Debt | Monthly payment, interest, amortization, balloon balance, annual debt roll-up, and LTV/DSCR sizing | No debt stack, hedge, refinance, or loan-document covenant model |
| Downside | Named stress cases plus seeded, reproducible Monte Carlo risk summaries | No historical probability calibration |
| Governance | Assumption register, source-status gate, lineage, and run fingerprint | No persistent approval ledger, RBAC, or retention service |
| Review package | IC memo, assumptions, risk summary, annual debt schedule, lease references, Excel reconciliation workbook, and ZIP download | Source status remains `REVIEW REQUIRED` unless caller supplies reviewer and source reference |
| Excel reconciliation | Live formulas for annual NOI, monthly debt, IRR, NPV, PMT, IPMT, PPMT, equity multiple, and formula-to-model differences | Workbook must be recalculated in Excel or LibreOffice; it does not validate source documents |
| Lease and portfolio | Illustrative rent-roll bridge, allocation checks, and concentration diagnostics | No complete lease economics, tenant-credit evidence, or multi-period fund optimizer |

## Why this exists / how it differs from a spreadsheet

AtlasRE keeps explicit inputs, a deterministic run fingerprint, source-status gating, downside-first summaries, automated tests, and generated review artifacts in one version-controlled codebase. A spreadsheet can also implement those controls; this repository instead expresses them as code and tests. It does **not** replace a complete underwriting workbook, verified source documents, a valuation process, legal or tax diligence, investment-committee judgment, or specialized real-estate software.

## Modeling conventions

The supplied annual NOI is year-one NOI. Growth begins in year two. Exit value is final-year NOI divided by exit cap rate. Acquisition and selling costs are percentages of price and exit value, respectively. The core loan is a single amortizing loan calculated monthly. The Excel workbook follows the same conventions and places its live formula result beside the static Python model output. See [the reviewer guide](docs/REVIEWER_GUIDE.md) for formula locations and reconciliation steps.

## Limitations and data boundary

This is a single-user, local prototype. It has no authentication, immutable audit store, source-document ingestion, live market data, OCR, accounting integration, tax model, FX model, complete lease economics, construction-to-permanent debt, mezzanine or preferred equity, persistent approvals, or production authorization controls. The seeded simulation is reproducible, but it is not calibrated to observed market outcomes. No output is investment advice or an approval.

## Testing and deployment

The test suite has **102 tests**. CI installs `requirements.lock`, runs `ruff check .`, and runs `python -m pytest -q`. The current package benchmark and reproducibility evidence are documented in [CHANGELOG.md](CHANGELOG.md). For Streamlit Community Cloud settings and deployment steps, see [DEPLOY.md](DEPLOY.md). The generated [illustrative sample package](docs/sample_output/README_ILLUSTRATIVE.md) and [demo script](docs/DEMO_SCRIPT.md) are available for review.

## Repository layout

```text
src/atlasre.py                 core acquisition underwriting
src/advanced_underwriting.py   seeded simulation, stress cases, and risk summaries
src/debt.py                    monthly debt schedules and debt sizing
src/reconciliation.py          formula-based Excel reconciliation workbook
generate_committee_report.py   package generator
dashboard.py                   Streamlit interface
tests/                         regression and independent cross-checks
docs/                          reviewer, demo, deployment, and sample materials
```

## License

MIT. See [LICENSE](LICENSE).
