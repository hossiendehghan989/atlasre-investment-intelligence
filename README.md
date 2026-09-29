# AtlasRE Investment Intelligence

> **Make the assumptions visible. Stress the downside. Explain the decision.**

<p align="center">
  <a href="https://atlasre-screening-demo.streamlit.app/"><img src="https://img.shields.io/badge/Live%20demo-Streamlit-FF4B4B?logo=streamlit&logoColor=white" alt="Live demo" /></a>
  <a href="https://github.com/hossiendehghan989/atlasre-investment-intelligence/actions/workflows/ci.yml"><img src="https://github.com/hossiendehghan989/atlasre-investment-intelligence/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/status-research%20prototype-F4B942.svg" alt="Research prototype" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0B8F8C.svg" alt="MIT License" /></a>
</p>

AtlasRE is a Python and Streamlit decision-support prototype for screening an **illustrative** real-estate acquisition case. It is designed around a practical question:

> **When assumptions are explicit, can a reviewer see how a deal reaches its answer, what could break it, and what still needs verification?**

This is not a valuation opinion, approval system, or investment advice. It is a transparent engineering study of cash-flow modeling, debt constraints, downside analysis, governance, and review-package generation.

## Start here

| If you want to... | Open this |
| --- | --- |
| See the workflow quickly | [Launch the illustrative Streamlit demo](https://atlasre-screening-demo.streamlit.app/) |
| Understand the formulas and controls | [Read the reviewer guide](docs/REVIEWER_GUIDE.md) |
| Run a real owner-supplied case locally | [Read USING_A_REAL_DEAL](docs/USING_A_REAL_DEAL.md) |
| Inspect the architecture | [Read ATLASRE_ARCHITECTURE](ATLASRE_ARCHITECTURE.md) |
| See the project in the broader portfolio | [Open Hossein Dehghan's profile](https://github.com/hossiendehghan989) |

## The default case

The default illustrative case displays **REJECT / REWORK**. Its flags show that the source package is not verified, unlevered NPV is negative, and levered IRR is below the 12% hurdle. The current model outputs are **11.97% levered IRR**, **9.32% unlevered IRR**, **1.70x equity multiple**, and a **$12,193,012 exit value**.

These are reproducible model outputs, not market evidence.

## What the system covers

| Decision layer | Implemented behavior | Important boundary |
| --- | --- | --- |
| Acquisition | NOI, terminal value, levered/unlevered cash flows, IRR, NPV, equity multiple, DSCR | No tax, capex reserve, or valuation opinion |
| Debt | Monthly payment, interest, amortization, balloon balance, annual roll-up, LTV/DSCR sizing | No debt stack, hedge, refinance, or covenant model |
| Downside | Named stress cases and seeded, reproducible Monte Carlo summaries | No historical probability calibration |
| Governance | Assumption register, source-status gate, lineage, and run fingerprint | No persistent approval ledger or RBAC |
| Review package | Memo, assumptions, risk summary, debt schedule, lease references, Excel reconciliation, ZIP download | Source status remains `REVIEW REQUIRED` without reviewer evidence |
| Lease and portfolio | Rent-roll bridge, allocation checks, concentration diagnostics | No complete lease economics or multi-period fund optimizer |

## Try it in 60 seconds

Run on Python 3.11 or 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
streamlit run dashboard.py
```

The [live demo](https://atlasre-screening-demo.streamlit.app/) uses illustrative data, has no authentication, is not for sensitive information, and may take a short time to wake if idle.

For an owner-supplied case:

```bash
python scripts/screen_deal.py path/to/deal.json --output deal-review
```

Start from the [JSON template](docs/templates/deal_template.json) and read [USING_A_REAL_DEAL](docs/USING_A_REAL_DEAL.md) first.

## What to inspect in the code

The project is deliberately more than a dashboard. The core flow is:

```text
Assumptions → Validation → Cash flows → Debt schedule → Downside analysis
           → Governance gates → Review memo + Excel reconciliation package
```

- `src/atlasre.py` — core acquisition underwriting
- `src/advanced_underwriting.py` — seeded simulation, stress cases, and risk summaries
- `src/debt.py` — monthly debt schedules and sizing
- `src/reconciliation.py` — formula-based Excel reconciliation workbook
- `generate_committee_report.py` — review-package generator
- `dashboard.py` — Streamlit interface
- `tests/` — regression and independent cross-checks
- `docs/` — reviewer, demo, deployment, and sample materials

## Why code instead of another spreadsheet?

A spreadsheet can implement many of these calculations. AtlasRE uses code so that assumptions, validation, tests, downside cases, generated review files, and run fingerprints live together and remain repeatable. The Excel workbook is included as a reconciliation surface—not as the only source of truth.

## Testing and deployment

CI installs the locked dependencies, runs Ruff, and executes the test suite on every push and pull request. For deployment details, see [DEPLOY.md](DEPLOY.md). For the formula map and reconciliation steps, see the [reviewer guide](docs/REVIEWER_GUIDE.md).

## Honest limitations

This is a single-user, local prototype. It has no authentication, immutable audit store, source-document ingestion, live market data, OCR, accounting integration, tax model, FX model, complete lease economics, persistent approvals, or production authorization controls. The seeded simulation is reproducible but not calibrated to observed market outcomes. No output is investment advice or an approval.

## License

MIT. See [LICENSE](LICENSE).

## Author

Built by [Hossein Dehghan](https://github.com/hossiendehghan989) at the intersection of **industrial engineering, applied AI, decision support, and transparent financial modeling**.
