"""Generate a deterministic, downside-first Investment Committee screening package."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import json
import zipfile

import pandas as pd

from src.advanced_underwriting import monte_carlo_underwriting, risk_summary, stress_test
from src.atlasre import DealInputs, underwrite_deal
from src.governance import assumption_register, default_lineage, lineage_json, model_run_fingerprint
from src.ic_workflow import DealCase, screen_case
from src.institutional import MonthlyDevelopmentInputs, monthly_development_model
from src.lease import illustrative_rent_roll, lease_rollup, lease_summary


def build_screening_package(deal: DealInputs, deal_id: str = "ATLAS-001", source_status: str = "REVIEW REQUIRED", simulations: int = 5000) -> dict[str, bytes]:
    """Return report and supporting files as bytes without hidden filesystem state."""
    case = DealCase(deal_id, "Illustrative acquisition case", deal, source_status)
    underwriting = underwrite_deal(deal)
    simulations_df = monte_carlo_underwriting(deal, simulations=simulations, seed=42)
    risk = risk_summary(simulations_df)
    stress = stress_test(deal)
    monthly, development = monthly_development_model(MonthlyDevelopmentInputs(5_000_000, 12_000_000, 2_500_000))
    demo_leases = illustrative_rent_roll()
    lease_monthly = lease_rollup(demo_leases, demo_leases[0].start, 12, operating_expense_ratio=.20)
    assumptions = assumption_register({"purchase_price": (deal.purchase_price, "USD"), "annual_noi": (deal.annual_noi, "USD / year"), "annual_noi_growth": (deal.annual_noi_growth, "%"), "exit_cap_rate": (deal.exit_cap_rate, "%"), "leverage": (deal.leverage, "%"), "debt_rate": (deal.debt_rate, "%")}, source="Illustrative dashboard input")
    lineage = default_lineage()
    fingerprint = model_run_fingerprint("deterministic-core-v1", assumptions, lineage)
    screen = screen_case(case)
    flags = "\n".join(f"- **{flag['severity']}** — {flag['flag']}: {flag['evidence']}" for flag in screen["flags"])
    report = f"""# AtlasRE Investment Committee Screening Package

> **Status:** Screening decision support only. This package is not an approval, valuation opinion, investment recommendation, or production underwriting output.

## 1. Executive decision frame

| Control | Result |
| --- | --- |
| Deal ID | `{deal_id}` |
| Source status | **{source_status}** |
| Decision status | **{screen['status']}** |
| Model version | `deterministic-core-v1` |
| Model-run fingerprint | `{fingerprint}` |

The case must not advance to approval while source status is `REVIEW REQUIRED` or while any critical economic flag remains unresolved.

## 2. Downside and governance flags

{flags}

## 3. Key assumptions

| Assumption | Value | Status |
| --- | ---: | --- |
| Purchase price | ${deal.purchase_price:,.0f} | REVIEW REQUIRED |
| Annual NOI | ${deal.annual_noi:,.0f} | REVIEW REQUIRED |
| NOI growth | {deal.annual_noi_growth:.2%} | REVIEW REQUIRED |
| Exit cap rate | {deal.exit_cap_rate:.2%} | REVIEW REQUIRED |
| Leverage | {deal.leverage:.2%} | REVIEW REQUIRED |
| Debt rate | {deal.debt_rate:.2%} | REVIEW REQUIRED |

## 4. Economic results

| Metric | Result |
| --- | ---: |
| Entry cap rate | {underwriting['entry_cap_rate']:.2%} |
| Levered IRR | {underwriting['levered_irr']:.2%} |
| Unlevered IRR | {underwriting['unlevered_irr']:.2%} |
| Equity multiple | {underwriting['equity_multiple']:.2f}x |
| Minimum DSCR | {underwriting['minimum_dscr']:.2f}x |
| Unlevered NPV | ${underwriting['unlevered_npv']:,.0f} |
| Remaining debt at exit | ${underwriting['remaining_debt_at_exit']:,.0f} |

## 5. Risk tails and covenant review

| Risk metric | Result |
| --- | ---: |
| P05 levered IRR | {risk['p05_irr']:.2%} |
| P10 levered IRR | {risk['p10_irr']:.2%} |
| Expected shortfall, worst 10% IRR | {risk['expected_shortfall_irr_10']:.2%} |
| Expected shortfall, worst 10% NPV | ${risk['expected_shortfall_npv_10']:,.0f} |
| Worst simulated IRR | {risk['worst_irr']:.2%} |
| Probability IRR below hurdle | {risk['probability_irr_below_hurdle']:.2%} |
| Probability negative NPV | {risk['probability_negative_npv']:.2%} |
| Probability DSCR below 1.25x | {risk['probability_dscr_below_125']:.2%} |

## 6. Recommended next diligence steps

1. Reconcile the rent roll and operating statement to source documents.
2. Validate market comparables, exit-cap evidence, and the timing of the terminal value.
3. Obtain and review the financing term sheet, including covenants, fees, amortization, and maturity.
4. Validate title, legal, tax, engineering, environmental, and insurance diligence.
5. Replace illustrative assumptions with versioned, reviewer-verified inputs and regenerate this package.

## 7. Traceability

Lineage is included in `lineage.json`. The assumption snapshot is included in `assumptions.csv`. The fingerprint above hashes the model version, assumption snapshot, and lineage records.

## 8. Lease-level reference case

The package includes a clearly illustrative lease summary and monthly rent-roll roll-up. These files demonstrate the optional lease path; they are not verified tenant data and do not replace a complete rent-roll, TI/LC, downtime, recovery, capex, or credit review.

## 9. Development reference case

The package includes a separate monthly development reference schedule in `monthly_development_model.csv`. It is not a substitute for a project-specific budget, draw schedule, or construction contract review.
"""
    files: dict[str, bytes] = {
        "investment_committee_report.md": report.encode("utf-8"),
        "stress_cases.csv": stress.to_csv(index=False).encode("utf-8"),
        "monthly_development_model.csv": monthly.to_csv(index=False).encode("utf-8"),
        "assumptions.csv": assumptions.to_csv(index=False).encode("utf-8"),
        "lineage.json": lineage_json(lineage).encode("utf-8"),
        "risk_summary.json": json.dumps(risk, indent=2).encode("utf-8"),
        "lease_summary.csv": lease_summary(demo_leases).to_csv(index=False).encode("utf-8"),
        "lease_monthly_rollup.csv": lease_monthly.to_csv(index=False).encode("utf-8"),
    }
    return files


def screening_package_zip(deal: DealInputs, deal_id: str = "ATLAS-001", source_status: str = "REVIEW REQUIRED", simulations: int = 5000) -> bytes:
    files = build_screening_package(deal, deal_id, source_status, simulations)
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def write_screening_package(out: Path = Path("artifacts"), deal: DealInputs | None = None) -> Path:
    out.mkdir(exist_ok=True)
    files = build_screening_package(deal or DealInputs(10_000_000, 650_000, hold_years=5, leverage=0.5))
    for name, content in files.items():
        (out / name).write_bytes(content)
    print(out / "investment_committee_report.md")
    return out


if __name__ == "__main__":
    write_screening_package()
