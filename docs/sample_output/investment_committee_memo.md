# ILLUSTRATIVE — generated from the current package inputs

# Investment Committee Screening Memo — Screening case

**Deal ID:** ATLAS-001  
**Prepared by:** AtlasRE  
**As of:** 2026-09-19
**Source status:** **REVIEW REQUIRED**
**Decision status:** **REJECT / REWORK**
**Model-run fingerprint:** `d82f5d59e1af3e3baf426aedf1dad9c0a1a127e4aa63626441e980183aafa170`

## 1. Decision framing

This is a screening memo, not an approval. The deterministic model cannot substitute for verified source documents, reviewer sign-off, legal diligence, tax analysis, engineering review, or market evidence.

## 2. Downside first

- **GOVERNANCE** — Source package is not verified: REVIEW REQUIRED
- **CRITICAL** — Negative unlevered NPV: $-278,827
- **HIGH** — Levered IRR below hurdle: 12.0% vs 12.0%

### Risk tails

| Metric | Result |
| --- | ---: |
| Expected shortfall, worst 10% IRR | 2.06% |
| Expected shortfall, worst 10% NPV | $-2,247,768 |
| Probability negative NPV | 57.78% |
| Probability DSCR below 1.25x | 0.44% |

## 3. Core outputs

| Metric | Result |
| --- | ---: |
| Entry cap rate | 6.50% |
| Levered IRR | 11.97% |
| Unlevered IRR | 9.32% |
| Equity multiple | 1.70x |
| Minimum DSCR | 1.51x |
| Unlevered NPV | $-278,827 |
| Exit value | $12,193,012 |
| Break-even exit cap | 5.99% |

## 4. Assumptions and traceability

The assumption register carries stable IDs, version, source status, and supersession fields. The model-run fingerprint above hashes the model version, assumption snapshot, and lineage records used in this memo.

## 5. Recommended next diligence steps

1. Reconcile the rent roll and operating statement to source documents.
2. Validate exit-cap evidence, terminal-value timing, and market comparables.
3. Obtain and review the financing term sheet, including covenants, fees, amortization, and maturity.
4. Replace illustrative assumptions with source-backed, reviewer-verified inputs and rerun this memo.

## 6. Recommendation gate

**Initial status:** `REJECT / REWORK`
**Next gate:** resolve every CRITICAL, HIGH, and GOVERNANCE flag, attach source documents, then rerun the downside cases before recommendation.
