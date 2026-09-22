# AtlasRE overview

AtlasRE is a Python and Streamlit prototype for early-stage screening of one real-estate acquisition case from explicit assumptions. It addresses the practical review problem of keeping inputs, formulas, downside flags, source-status gating, and reproducible review artifacts visible to an analyst or independent finance reviewer.

## Intended user

The intended user is an analyst or reviewer who wants to inspect the formulas, assumptions, reconciliation workbook, and downside flags before a case is discussed further. The owner must supply any real deal, source documents, reviewer identity, and evidence of use or validation.

## What it produces

A local run produces a screening memo, assumptions register, risk summary, annual debt schedule, stress cases, lineage record, and formula-based Excel reconciliation workbook. The hosted dashboard presents the bundled illustrative case and allows inspection of the same type of artifacts.

## Deliberate boundaries

This is not a valuation opinion, approval, investment recommendation, source-document verifier, tax or legal analysis, accounting system, market-data service, or production underwriting platform. Bundled data and demo outputs are **ILLUSTRATIVE**. The model does not verify source documents, valuation, legal matters, tax, capex reserves, TI/LC, refinance terms, tenant credit, or a complete capital stack.

## How to evaluate this in 30 minutes

1. Open the local demo using the commands in [README](../README.md), or inspect the hosted demo without entering confidential data.
2. Download the Excel workbook from the dashboard, open it in Excel or LibreOffice, and recalculate formulas.
3. Compare the workbook's **Reconciliation** sheet with the static model outputs and read [REVIEWER_GUIDE](REVIEWER_GUIDE.md).
4. Inspect `risk_summary.json`, the annual debt schedule, the assumptions register, and the source-status gate.
5. Record disagreements and unclear items using [REVIEW_CHECKLIST](review/REVIEW_CHECKLIST.md); this repository does not claim that an independent review has occurred.

## Author and development

**Author/contact:** [OWNER TO FILL: name/contact]

## Repository basis

The purpose and boundaries above are based on the repository's current dashboard, core model, generated review package, tests, and existing reviewer guide. They are not evidence that the prototype has been used with a real deal or independently validated.
