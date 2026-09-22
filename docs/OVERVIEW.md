# AtlasRE overview

I built AtlasRE as a personal engineering project around a narrow question: **given explicit assumptions, what does a real-estate acquisition model calculate, how fragile is that result, and what still needs to be checked by a person?**

The project is a Python and Streamlit prototype for early-stage screening of one acquisition case. It keeps the formulas, assumptions, downside flags, source status, and review artifacts close together so that an analyst can inspect the work instead of trusting a black-box number.

## Who it is for

The intended user is an analyst or reviewer who wants to check the formulas, assumptions, reconciliation workbook, and downside flags before spending more time on a case. Any real deal, source documents, reviewer identity, and evidence of validation must be supplied separately by the owner.

## What it produces

A local run produces a screening memo, assumptions register, risk summary, annual debt schedule, stress cases, lineage record, and formula-based Excel reconciliation workbook. The dashboard presents the bundled illustrative case and lets a reviewer inspect the same type of artifacts.

## Boundaries

This is not a valuation opinion, approval workflow, investment recommendation, source-document verifier, tax or legal analysis, accounting system, market-data service, or production underwriting platform. Bundled data and demo outputs are **ILLUSTRATIVE**. The model does not verify source documents, valuation, legal matters, tax, capex reserves, TI/LC, refinance terms, tenant credit, or a complete capital stack.

## How I would evaluate it in 30 minutes

1. Open the local demo using the commands in [README](../README.md), or inspect the hosted demo without entering confidential data.
2. Download the Excel workbook from the dashboard, open it in Excel or LibreOffice, and recalculate formulas.
3. Compare the workbook's **Reconciliation** sheet with the static model outputs and read [REVIEWER_GUIDE](REVIEWER_GUIDE.md).
4. Inspect `risk_summary.json`, the annual debt schedule, the assumptions register, and the source-status gate.
5. Record disagreements and unclear items using [REVIEW_CHECKLIST](review/REVIEW_CHECKLIST.md). This repository does not claim that an independent review has occurred.

## Author

**Hossein Dehghan** — Industrial Engineering graduate working on applied AI, data science, energy intelligence, and industrial analytics. The project follows the same principles I use elsewhere: understand the system, make assumptions explicit, build the simplest useful solution, and measure the result.

## Repository basis

The descriptions above are based on the current dashboard, core model, generated review package, tests, and reviewer guide. They are not evidence that the prototype has been used with a real deal or independently validated.
