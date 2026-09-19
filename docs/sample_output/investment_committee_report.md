# ILLUSTRATIVE — AtlasRE Investment Committee Screening Package

> **Status:** This is screening decision support only. It is not an approval, valuation opinion, investment recommendation, or production underwriting output.

## 1. Executive decision frame

| Control | Result |
| --- | --- |
| Deal ID | `ATLAS-001` |
| Source status | **REVIEW REQUIRED** |
| Decision status | **REJECT / REWORK** |
| Model version | `deterministic-core-v0.10` |
| Model-run fingerprint | `85a3e556a66a171ebfec0a22fe1407540b5be67470e6c1f4c9b4e475b3502733` |

The case must not advance to approval while source status is `REVIEW REQUIRED` or while a critical economic flag remains unresolved.

## 2. Thesis

The case is suitable only for initial, downside-led screening. Its economic outputs remain conditional on the supplied operating, valuation, financing, and source-verification assumptions.

## 3. Downside and governance flags

- **GOVERNANCE** — Source package is not verified: REVIEW REQUIRED
- **CRITICAL** — Negative unlevered NPV: $-278,827
- **HIGH** — Levered IRR below hurdle: 12.0% vs 12.0%

## 4. Key assumptions

| Assumption | Value | Status |
| --- | ---: | --- |
            | Purchase price | $10,000,000 | REVIEW REQUIRED |
            | Annual NOI used in core model | $650,000 | REVIEW REQUIRED |
            | NOI growth | 3.00% | REVIEW REQUIRED |
            | Exit cap rate | 6.00% | REVIEW REQUIRED |
            | Leverage | 50.00% | REVIEW REQUIRED |
            | Debt rate | 6.00% | REVIEW REQUIRED |

## 5. Economic results

| Metric | Result |
| --- | ---: |
| Entry cap rate | 6.50% |
| Levered IRR | 11.97% |
| Unlevered IRR | 9.32% |
| Equity multiple | 1.70x |
| Minimum DSCR | 1.51x |
| Unlevered NPV | $-278,827 |
| Remaining debt at exit | $4,244,980 |
| Break-even exit cap at 12% hurdle | 5.99% |

## 6. Risk tails and covenant review

| Risk metric | Result |
| --- | ---: |
| P05 levered IRR | 2.76% |
| P10 levered IRR | 4.75% |
| Expected shortfall, worst 10% IRR | 2.06% |
| Expected shortfall, worst 10% NPV | $-2,247,768 |
| Worst simulated IRR | -13.97% |
| Probability IRR below hurdle | 49.62% |
| Probability negative NPV | 57.78% |
| Probability DSCR below 1.25x | 0.44% |

## 7. Lease-level evidence

No rent-roll input was supplied. The economic case uses the explicit simplified annual-NOI assumption. The included lease files are a clearly illustrative reference schedule, not source data.

## 8. Reference schedules

The package includes an illustrative monthly development schedule for reference. It shows draw timing, capitalized interest, stabilization NOI, debt repayment, and exit proceeds. The schedule is not a project-specific budget, draw request, or construction contract review.

## 9. Recommended next diligence steps

1. Reconcile the operating statement and all purchase-price inputs to source documents.
2. Validate market comparables, exit-cap evidence, and the timing of terminal value.
3. Obtain and review the financing term sheet, including covenants, fees, amortization, and maturity.
4. Validate title, legal, tax, engineering, environmental, and insurance diligence.
5. Replace illustrative assumptions with versioned, reviewer-verified inputs and regenerate this package.

## 10. Model fingerprint and traceability

`85a3e556a66a171ebfec0a22fe1407540b5be67470e6c1f4c9b4e475b3502733`

The fingerprint hashes the model version, assumption snapshot, and lineage records. The package includes `assumptions.csv`, `annual_debt_schedule.csv`, `lineage.json`, `risk_summary.json`, and `stress_cases.csv`. It is a reproducibility handle, not a persistent approval ledger.
