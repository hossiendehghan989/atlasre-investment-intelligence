"""Typed committee workflow, comparison, and downside-first memo generation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from typing import Any, Literal, TypedDict

import pandas as pd

from .atlasre import DealInputs, underwrite_deal
from .committee_analytics import investment_committee_summary
from .governance import assumption_register, default_lineage, model_run_fingerprint
from .presentation import number_or_na_report, percent_or_na, percent_or_na_report

DecisionStatus = Literal["PASSES INITIAL SCREEN", "REVIEW REQUIRED", "REJECT / REWORK"]


@dataclass(frozen=True)
class ScreeningThresholds:
    hurdle_rate: float = 0.12
    minimum_dscr: float = 1.25
    source_status_required: str = "VERIFIED"

    def validate(self) -> None:
        if not 0 <= self.hurdle_rate <= 1 or self.minimum_dscr <= 0 or self.source_status_required != "VERIFIED":
            raise ValueError("screening thresholds are invalid")


@dataclass(frozen=True)
class DealCase:
    deal_id: str
    name: str
    inputs: DealInputs
    source_status: str = "REVIEW REQUIRED"
    verified_by: str | None = None
    source_reference: str | None = None

    def validate(self) -> None:
        if not self.deal_id or not self.name or self.source_status not in {"VERIFIED", "REVIEW REQUIRED"}:
            raise ValueError("deal identity and source_status must be valid")

    def effective_source_status(self) -> str:
        reviewer_and_reference = (self.verified_by, self.source_reference)
        if self.source_status == "VERIFIED" and all(
            isinstance(value, str) and bool(value.strip()) for value in reviewer_and_reference
        ):
            return "VERIFIED"
        return "REVIEW REQUIRED"


class ScreeningFlag(TypedDict):
    severity: Literal["CRITICAL", "HIGH", "GOVERNANCE", "INFO"]
    flag: str
    evidence: str


def screen_case(case: DealCase, thresholds: ScreeningThresholds | None = None) -> dict[str, Any]:
    """Run explicit gates; source-incomplete cases can never pass automatically."""
    case.validate()
    thresholds = thresholds or ScreeningThresholds()
    thresholds.validate()
    result = underwrite_deal(case.inputs)
    source_status = case.effective_source_status()
    flags: list[ScreeningFlag] = []
    if source_status != thresholds.source_status_required:
        evidence = case.source_status
        if case.source_status == "VERIFIED":
            evidence = "VERIFIED requires verified_by and source_reference"
        flags.append({"severity": "GOVERNANCE", "flag": "Source package is not verified", "evidence": evidence})
    if result["unlevered_npv"] < 0:
        flags.append(
            {"severity": "CRITICAL", "flag": "Negative unlevered NPV", "evidence": f"${result['unlevered_npv']:,.0f}"}
        )
    if result["minimum_dscr"] < thresholds.minimum_dscr:
        flags.append(
            {
                "severity": "HIGH",
                "flag": f"DSCR below {thresholds.minimum_dscr:.2f}x",
                "evidence": f"{result['minimum_dscr']:.2f}x",
            }
        )
    if not math.isfinite(float(result["levered_irr"])):
        flags.append(
            {
                "severity": "CRITICAL",
                "flag": "Levered IRR is not economically defined",
                "evidence": "No finite IRR root found",
            }
        )
    elif result["levered_irr"] < thresholds.hurdle_rate:
        flags.append(
            {
                "severity": "HIGH",
                "flag": "Levered IRR below hurdle",
                "evidence": f"{result['levered_irr']:.1%} vs {thresholds.hurdle_rate:.1%}",
            }
        )
    if not flags:
        flags.append(
            {"severity": "INFO", "flag": "No initial-screen exception", "evidence": "All configured gates passed"}
        )
    if any(flag["severity"] == "CRITICAL" for flag in flags):
        status: DecisionStatus = "REJECT / REWORK"
    elif any(flag["severity"] in {"HIGH", "GOVERNANCE"} for flag in flags):
        status = "REVIEW REQUIRED"
    else:
        status = "PASSES INITIAL SCREEN"
    return {
        "deal_id": case.deal_id,
        "status": status,
        "source_status": source_status,
        "flags": flags,
        "metrics": result,
    }


def compare_deals(cases: list[DealCase], hurdle_rate: float = 0.12) -> pd.DataFrame:
    """Produce side-by-side metrics plus governance and decision status."""
    if not cases:
        raise ValueError("at least one deal case is required")
    thresholds = ScreeningThresholds(hurdle_rate=hurdle_rate)
    rows = []
    for case in cases:
        result = underwrite_deal(case.inputs)
        summary = investment_committee_summary(case.inputs, hurdle_rate)
        screen = screen_case(case, thresholds)
        flags = screen["flags"]
        rows.append(
            {
                "deal_id": case.deal_id,
                "deal": case.name,
                "source_status": screen["source_status"],
                "decision_status": screen["status"],
                "critical_flags": sum(flag["severity"] == "CRITICAL" for flag in flags),
                "review_flags": sum(flag["severity"] in {"HIGH", "GOVERNANCE"} for flag in flags),
                "entry_cap": result["entry_cap_rate"],
                "levered_irr": result["levered_irr"],
                "unlevered_irr": result["unlevered_irr"],
                "equity_multiple": result["equity_multiple"],
                "minimum_dscr": result["minimum_dscr"],
                "unlevered_npv": result["unlevered_npv"],
                "decision_flag": summary["decision_flag"],
            }
        )
    return pd.DataFrame(rows)


def screening_flags(inputs: DealInputs, hurdle_rate: float = 0.12) -> dict[str, Any]:
    """Backward-compatible metric-only screening with explicit review status."""
    case = DealCase("UNASSIGNED", "Unassigned deal", inputs, "REVIEW REQUIRED")
    return screen_case(case, ScreeningThresholds(hurdle_rate=hurdle_rate))


def _memo_assumptions(case: DealCase) -> pd.DataFrame:
    values = {
        "purchase_price": (case.inputs.purchase_price, "USD"),
        "annual_noi": (case.inputs.annual_noi, "USD / year"),
        "annual_noi_growth": (case.inputs.annual_noi_growth, "%"),
        "exit_cap_rate": (case.inputs.exit_cap_rate, "%"),
        "leverage": (case.inputs.leverage, "%"),
        "debt_rate": (case.inputs.debt_rate, "%"),
    }
    return assumption_register(values, source="Screening-case input")


def generate_ic_memo(
    case: DealCase,
    hurdle_rate: float = 0.12,
    author: str = "AtlasRE",
    model_version: str = "deterministic-core-v0.10",
    risk_metrics: dict[str, float | None] | None = None,
) -> str:
    """Generate a downside-first screening memo with a reproducibility handle."""
    result = underwrite_deal(case.inputs)
    summary = investment_committee_summary(case.inputs, hurdle_rate)
    screen = screen_case(case, ScreeningThresholds(hurdle_rate=hurdle_rate))
    assumptions = _memo_assumptions(case)
    fingerprint = model_run_fingerprint(model_version, assumptions, default_lineage())
    flag_lines = "\n".join(f"- **{flag['severity']}** — {flag['flag']}: {flag['evidence']}" for flag in screen["flags"])
    tail_section = (
        "Risk tails were not supplied for this memo run; run the screening package before a committee decision."
    )
    if risk_metrics is not None:
        tail_section = f"""| Metric | Result |
| --- | ---: |
| Expected shortfall, worst 10% IRR | {percent_or_na(risk_metrics["expected_shortfall_irr_10"])} |
| Expected shortfall, worst 10% NPV | {"N/A" if risk_metrics["expected_shortfall_npv_10"] is None else f"${risk_metrics['expected_shortfall_npv_10']:,.0f}"} |
| Probability negative NPV | {percent_or_na(risk_metrics["probability_negative_npv"])} |
| Probability DSCR below 1.25x | {percent_or_na(risk_metrics["probability_dscr_below_125"])} |"""
    safe_name = escape(case.name)
    safe_deal_id = escape(case.deal_id)
    return f"""# Investment Committee Screening Memo — {safe_name}

**Deal ID:** {safe_deal_id}{"  "}
**Prepared by:** {author}  
**As of:** {datetime.now(UTC).date().isoformat()}
**Source status:** **{screen["source_status"]}**
**Decision status:** **{screen["status"]}**
**Model-run fingerprint:** `{fingerprint}`

## 1. Decision framing

This is a screening memo, not an approval. The deterministic model cannot substitute for verified source documents, reviewer sign-off, legal diligence, tax analysis, engineering review, or market evidence.

## 2. Downside first

{flag_lines}

### Risk tails

{tail_section}

## 3. Core outputs

| Metric | Result |
| --- | ---: |
| Entry cap rate | {percent_or_na_report(result["entry_cap_rate"])} |
| Levered IRR | {percent_or_na_report(result["levered_irr"], reason="IRR did not converge")} |
| Unlevered IRR | {percent_or_na_report(result["unlevered_irr"], reason="IRR did not converge")} |
| Equity multiple | {number_or_na_report(result["equity_multiple"], decimals=2, suffix="x", reason="Equity multiple is not defined")} |
| Minimum DSCR | {number_or_na_report(result["minimum_dscr"], decimals=2, suffix="x", reason="DSCR is not defined")} |
| Unlevered NPV | {number_or_na_report(result["unlevered_npv"], prefix="$", reason="NPV is not finite")} |
| Exit value | {number_or_na_report(result["exit_value"], prefix="$", reason="Exit value is not finite")} |
| Break-even exit cap | {percent_or_na(summary["break_even_exit_cap"])} |

## 4. Assumptions and traceability

The assumption register carries stable IDs, version, source status, and supersession fields. The model-run fingerprint above hashes the model version, assumption snapshot, and lineage records used in this memo.

## 5. Recommended next diligence steps

1. Reconcile the rent roll and operating statement to source documents.
2. Validate exit-cap evidence, terminal-value timing, and market comparables.
3. Obtain and review the financing term sheet, including covenants, fees, amortization, and maturity.
4. Replace illustrative assumptions with source-backed, reviewer-verified inputs and rerun this memo.

## 6. Recommendation gate

**Initial status:** `{screen["status"]}`
**Next gate:** resolve every CRITICAL, HIGH, and GOVERNANCE flag, attach source documents, then rerun the downside cases before recommendation.
"""


__all__ = ["DealCase", "ScreeningThresholds", "compare_deals", "generate_ic_memo", "screen_case", "screening_flags"]
