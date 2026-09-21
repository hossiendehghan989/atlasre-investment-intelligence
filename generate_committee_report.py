"""Generate a deterministic, downside-first Investment Committee screening package."""
from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path

import pandas as pd

from src.advanced_underwriting import monte_carlo_underwriting, risk_summary, stress_test
from src.atlasre import DealInputs, underwrite_deal
from src.committee_analytics import investment_committee_summary
from src.governance import default_lineage, lineage_json, model_run_fingerprint, versioned_assumptions
from src.ic_workflow import DealCase, ScreeningThresholds, generate_ic_memo, screen_case
from src.institutional import MonthlyDevelopmentInputs, monthly_development_model
from src.lease import (
    LeaseUnderwritingInputs,
    annual_lease_summary,
    illustrative_rent_roll,
    lease_rollup,
    lease_summary,
    underwrite_with_lease_roll,
)
from src.presentation import number_or_na, percent_or_na
from src.reconciliation import build_reconciliation_workbook

MODEL_VERSION = "deterministic-core-v0.10"
DEFAULT_RISK_SIMULATIONS = 5000


def _assumption_values(deal: DealInputs, lease_inputs: LeaseUnderwritingInputs | None) -> dict[str, tuple[object, str]]:
    values: dict[str, tuple[object, str]] = {
        "purchase_price": (deal.purchase_price, "USD"),
        "annual_noi": (deal.annual_noi, "USD / year"),
        "annual_noi_growth": (deal.annual_noi_growth, "%"),
        "exit_cap_rate": (deal.exit_cap_rate, "%"),
        "leverage": (deal.leverage, "%"),
        "debt_rate": (deal.debt_rate, "%"),
        "hold_years": (deal.hold_years, "years"),
    }
    if lease_inputs is not None:
        values.update({
            "lease_rollup_months": (lease_inputs.months, "months"),
            "lease_operating_expense_ratio": (lease_inputs.operating_expense_ratio, "%"),
            "lease_count": (len(lease_inputs.leases), "leases"),
        })
    return values


def _diligence_steps(lease_inputs: LeaseUnderwritingInputs | None) -> str:
    steps = [
        "Reconcile the operating statement and all purchase-price inputs to source documents.",
        "Validate market comparables, exit-cap evidence, and the timing of terminal value.",
        "Obtain and review the financing term sheet, including covenants, fees, amortization, and maturity.",
    ]
    if lease_inputs is not None:
        steps.insert(0, "Reconcile every rent-roll field, expiry, vacancy, rollover, and credit-quality label to source documents.")
    steps.extend([
        "Validate title, legal, tax, engineering, environmental, and insurance diligence.",
        "Replace illustrative assumptions with versioned, reviewer-verified inputs and regenerate this package.",
    ])
    return "\n".join(f"{index}. {step}" for index, step in enumerate(steps, start=1))


def build_screening_package(
    deal: DealInputs,
    deal_id: str = "ATLAS-001",
    source_status: str = "REVIEW REQUIRED",
    verified_by: str | None = None,
    source_reference: str | None = None,
    simulations: int = DEFAULT_RISK_SIMULATIONS,
    lease_inputs: LeaseUnderwritingInputs | None = None,
    model_version: str = MODEL_VERSION,
    hurdle_rate: float = 0.12,
) -> dict[str, bytes]:
    """Return report and supporting files as bytes without hidden filesystem state.

    An optional ``lease_inputs`` path derives annual NOI from the rent roll before
    the existing acquisition engine is run. Without it, the original simplified
    annual-NOI path is used unchanged.
    """
    case_deal = deal
    lease_files: dict[str, bytes] = {}
    reference_leases = illustrative_rent_roll()
    reference_rollup = lease_rollup(reference_leases, reference_leases[0].start, 12, operating_expense_ratio=.20)
    lease_note = (
        "No rent-roll input was supplied. The economic case uses the explicit simplified annual-NOI assumption. "
        "The included lease files are a clearly illustrative reference schedule, not source data."
    )
    lease_files = {
        "lease_summary.csv": lease_summary(reference_leases).to_csv(index=False).encode("utf-8"),
        "lease_monthly_rollup.csv": reference_rollup.to_csv(index=False).encode("utf-8"),
        "lease_annual_summary.csv": annual_lease_summary(reference_rollup).to_csv(index=False).encode("utf-8"),
    }
    if lease_inputs is not None:
        lease_result = underwrite_with_lease_roll(deal, lease_inputs)
        case_deal = lease_result["deal_inputs"]
        monthly = lease_result["lease_monthly_rollup"]
        annual = lease_result["lease_annual_summary"]
        lease_note = (
            f"The economic case uses an optional rent-roll bridge. The annual NOI supplied to the core engine is "
            f"${lease_result['lease_derived_annual_noi']:,.0f}, annualized from {lease_inputs.months} monthly periods."
        )
        lease_files = {
            "lease_summary.csv": lease_summary(lease_inputs.leases).to_csv(index=False).encode("utf-8"),
            "lease_monthly_rollup.csv": monthly.to_csv(index=False).encode("utf-8"),
            "lease_annual_summary.csv": annual.to_csv(index=False).encode("utf-8"),
        }

    case = DealCase(deal_id, "Screening case", case_deal, source_status, verified_by, source_reference)
    screen = screen_case(case, ScreeningThresholds(hurdle_rate=hurdle_rate))
    effective_source_status = screen["source_status"]
    source_gate_note = (
        "The case must not advance to approval while source status is `REVIEW REQUIRED` or while a critical economic flag remains unresolved."
        if effective_source_status != "VERIFIED"
        else "The case remains subject to unresolved critical economic flags and independent committee review."
    )
    underwriting = underwrite_deal(case_deal)
    simulations_df = monte_carlo_underwriting(case_deal, simulations=simulations, seed=42)
    risk = risk_summary(simulations_df, hurdle_rate=hurdle_rate)

    def risk_percent(key: str) -> str:
        return percent_or_na(risk[key], 2)

    def risk_number(key: str) -> str:
        return number_or_na(risk[key], prefix="$")

    stress = stress_test(case_deal)
    monthly_development, _development_summary = monthly_development_model(
        MonthlyDevelopmentInputs(5_000_000, 12_000_000, 2_500_000)
    )
    assumptions = versioned_assumptions(
        _assumption_values(deal, lease_inputs),
        deal_id=deal_id,
        version=1,
        source="Source-backed screening input" if effective_source_status == "VERIFIED" else "Illustrative dashboard input",
        verified_by=verified_by if effective_source_status == "VERIFIED" else "",
    )
    lineage = default_lineage()
    if lease_inputs is not None:
        lineage.append({
            "output": "annual_noi",
            "value": "derived",
            "inputs": ["lease_rollup_months", "lease_operating_expense_ratio", "lease_count"],
            "method": "sum monthly lease NOI / supplied months x 12",
            "source_refs": ["lease_summary.csv", "lease_monthly_rollup.csv"],
            "assumption_version": 1,
        })
    fingerprint = model_run_fingerprint(model_version, assumptions, lineage)
    committee = investment_committee_summary(case_deal, hurdle_rate=hurdle_rate)
    memo = "# ILLUSTRATIVE — generated from the current package inputs\n\n" + generate_ic_memo(
        case,
        hurdle_rate=hurdle_rate,
        model_version=model_version,
        risk_metrics=risk,
    )
    flags = "\n".join(f"- **{flag['severity']}** — {flag['flag']}: {flag['evidence']}" for flag in screen["flags"])
    thesis = (
        "The case is suitable only for initial, downside-led screening. Its economic outputs remain conditional on "
        "the supplied operating, valuation, financing, and source-verification assumptions."
    )
    report = f"""# ILLUSTRATIVE — AtlasRE Investment Committee Screening Package

> **Status:** This is screening decision support only. It is not an approval, valuation opinion, investment recommendation, or production underwriting output.

## 1. Executive decision frame

| Control | Result |
| --- | --- |
| Deal ID | `{deal_id}` |
| Source status | **{effective_source_status}** |
| Decision status | **{screen['status']}** |
| Model version | `{model_version}` |
| Model-run fingerprint | `{fingerprint}` |

{source_gate_note}

## 2. Thesis

{thesis}

## 3. Downside and governance flags

{flags}

## 4. Key assumptions

| Assumption | Value | Status |
| --- | ---: | --- |
            | Purchase price | ${deal.purchase_price:,.0f} | {effective_source_status} |
            | Annual NOI used in core model | ${case_deal.annual_noi:,.0f} | {effective_source_status} |
            | NOI growth | {case_deal.annual_noi_growth:.2%} | {effective_source_status} |
            | Exit cap rate | {case_deal.exit_cap_rate:.2%} | {effective_source_status} |
            | Leverage | {case_deal.leverage:.2%} | {effective_source_status} |
            | Debt rate | {case_deal.debt_rate:.2%} | {effective_source_status} |

## 5. Economic results

| Metric | Result |
| --- | ---: |
| Entry cap rate | {underwriting['entry_cap_rate']:.2%} |
| Levered IRR | {underwriting['levered_irr']:.2%} |
| Unlevered IRR | {underwriting['unlevered_irr']:.2%} |
| Equity multiple | {underwriting['equity_multiple']:.2f}x |
| Minimum DSCR | {underwriting['minimum_dscr']:.2f}x |
| Unlevered NPV | ${underwriting['unlevered_npv']:,.0f} |
| Remaining debt at exit | ${underwriting['remaining_debt_at_exit']:,.0f} |
| Break-even exit cap at 12% hurdle | {percent_or_na(committee['break_even_exit_cap'])} |

## 6. Risk tails and covenant review

| Risk metric | Result |
| --- | ---: |
| P05 levered IRR | {risk_percent('p05_irr')} |
| P10 levered IRR | {risk_percent('p10_irr')} |
| Expected shortfall, worst 10% IRR | {risk_percent('expected_shortfall_irr_10')} |
| Expected shortfall, worst 10% NPV | {risk_number('expected_shortfall_npv_10')} |
| Worst simulated IRR | {risk_percent('worst_irr')} |
| Probability IRR below hurdle | {risk_percent('probability_irr_below_hurdle')} |
| Probability negative NPV | {risk_percent('probability_negative_npv')} |
| Probability DSCR below 1.25x | {risk_percent('probability_dscr_below_125')} |

## 7. Lease-level evidence

{lease_note}

## 8. Reference schedules

The package includes an illustrative monthly development schedule for reference. It shows draw timing, capitalized interest, stabilization NOI, debt repayment, and exit proceeds. The schedule is not a project-specific budget, draw request, or construction contract review.

## 9. Recommended next diligence steps

{_diligence_steps(lease_inputs)}

## 10. Model fingerprint and traceability

`{fingerprint}`

The fingerprint hashes the model version, assumption snapshot, and lineage records. The package includes `assumptions.csv`, `annual_debt_schedule.csv`, `lineage.json`, `risk_summary.json`, and `stress_cases.csv`. It is a reproducibility handle, not a persistent approval ledger.
"""
    files: dict[str, bytes] = {
        "README_ILLUSTRATIVE.md": f"""# ILLUSTRATIVE sample package

Every file in this package is generated from the repository's default illustrative case. It is not a deal file, source document, valuation opinion, or investment recommendation.

- Model version: `{model_version}`
- Run fingerprint: `{fingerprint}`
- Source status: `{effective_source_status}`
- Downside simulation count: `{simulations}` with seed `42`

Open `excel_reconciliation.xlsx` in Excel or LibreOffice to recalculate its live formulas. See `docs/REVIEWER_GUIDE.md` in the repository for review steps and model boundaries.
""".encode(),
        "investment_committee_memo.md": memo.encode("utf-8"),
        "investment_committee_report.md": report.encode("utf-8"),
        "stress_cases.csv": stress.to_csv(index=False).encode("utf-8"),
        "annual_debt_schedule.csv": pd.DataFrame(underwriting["debt_schedule"]).to_csv(index=False).encode("utf-8"),
        "monthly_development_model.csv": monthly_development.to_csv(index=False).encode("utf-8"),
        "assumptions.csv": assumptions.to_csv(index=False).encode("utf-8"),
        "lineage.json": lineage_json(lineage).encode("utf-8"),
        "risk_summary.json": json.dumps(risk, indent=2).encode("utf-8"),
        "excel_reconciliation.xlsx": build_reconciliation_workbook(
            case_deal,
            hurdle_rate=hurdle_rate,
            model_version=model_version,
            source_status=effective_source_status,
            deal_id=deal_id,
        ),
    }
    files.update(lease_files)
    return files


def screening_package_zip(
    deal: DealInputs,
    deal_id: str = "ATLAS-001",
    source_status: str = "REVIEW REQUIRED",
    verified_by: str | None = None,
    source_reference: str | None = None,
    simulations: int = DEFAULT_RISK_SIMULATIONS,
    lease_inputs: LeaseUnderwritingInputs | None = None,
    model_version: str = MODEL_VERSION,
    hurdle_rate: float = 0.12,
) -> bytes:
    """Return the complete screening package as a downloadable ZIP file."""
    files = build_screening_package(
        deal,
        deal_id,
        source_status,
        verified_by,
        source_reference,
        simulations,
        lease_inputs,
        model_version,
        hurdle_rate,
    )
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(files):
            archive.writestr(name, files[name])
    return buffer.getvalue()


def write_screening_package(out: Path | None = None, deal: DealInputs | None = None) -> Path:
    """Write a default, clearly illustrative package for local inspection."""
    out = out or Path(__file__).resolve().parent / "artifacts"
    out.mkdir(exist_ok=True)
    files = build_screening_package(deal or DealInputs(10_000_000, 650_000, hold_years=5, leverage=0.5))
    for name, content in files.items():
        (out / name).write_bytes(content)
    print(out / "investment_committee_report.md")
    return out


if __name__ == "__main__":
    write_screening_package()
