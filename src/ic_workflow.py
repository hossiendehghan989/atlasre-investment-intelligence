"""Typed committee workflow, comparison, and downside-first memo generation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, TypedDict

import pandas as pd

from .atlasre import DealInputs, underwrite_deal
from .committee_analytics import investment_committee_summary


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

    def validate(self) -> None:
        if not self.deal_id or not self.name or self.source_status not in {"VERIFIED", "REVIEW REQUIRED"}:
            raise ValueError("deal identity and source_status must be valid")


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
    flags: list[ScreeningFlag] = []
    if case.source_status != thresholds.source_status_required:
        flags.append({"severity": "GOVERNANCE", "flag": "Source package is not verified", "evidence": case.source_status})
    if result["unlevered_npv"] < 0:
        flags.append({"severity": "CRITICAL", "flag": "Negative unlevered NPV", "evidence": f"${result['unlevered_npv']:,.0f}"})
    if result["minimum_dscr"] < thresholds.minimum_dscr:
        flags.append({"severity": "HIGH", "flag": f"DSCR below {thresholds.minimum_dscr:.2f}x", "evidence": f"{result['minimum_dscr']:.2f}x"})
    if result["levered_irr"] < thresholds.hurdle_rate:
        flags.append({"severity": "HIGH", "flag": "Levered IRR below hurdle", "evidence": f"{result['levered_irr']:.1%} vs {thresholds.hurdle_rate:.1%}"})
    if not flags:
        flags.append({"severity": "INFO", "flag": "No initial-screen exception", "evidence": "All configured gates passed"})
    if any(flag["severity"] == "CRITICAL" for flag in flags):
        status: DecisionStatus = "REJECT / REWORK"
    elif any(flag["severity"] in {"HIGH", "GOVERNANCE"} for flag in flags):
        status = "REVIEW REQUIRED"
    else:
        status = "PASSES INITIAL SCREEN"
    return {"deal_id": case.deal_id, "status": status, "flags": flags, "metrics": result}


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
        rows.append({"deal_id": case.deal_id, "deal": case.name, "source_status": case.source_status, "decision_status": screen["status"], "critical_flags": sum(flag["severity"] == "CRITICAL" for flag in flags), "review_flags": sum(flag["severity"] in {"HIGH", "GOVERNANCE"} for flag in flags), "entry_cap": result["entry_cap_rate"], "levered_irr": result["levered_irr"], "unlevered_irr": result["unlevered_irr"], "equity_multiple": result["equity_multiple"], "minimum_dscr": result["minimum_dscr"], "unlevered_npv": result["unlevered_npv"], "decision_flag": summary["decision_flag"]})
    return pd.DataFrame(rows)


def screening_flags(inputs: DealInputs, hurdle_rate: float = 0.12) -> dict[str, Any]:
    """Backward-compatible metric-only screening with explicit review status."""
    case = DealCase("UNASSIGNED", "Unassigned deal", inputs, "REVIEW REQUIRED")
    return screen_case(case, ScreeningThresholds(hurdle_rate=hurdle_rate))


def generate_ic_memo(case: DealCase, hurdle_rate: float = 0.12, author: str = "AtlasRE") -> str:
    """Generate a challengeable memo whose recommendation cannot bypass governance."""
    result = underwrite_deal(case.inputs)
    summary = investment_committee_summary(case.inputs, hurdle_rate)
    screen = screen_case(case, ScreeningThresholds(hurdle_rate=hurdle_rate))
    flag_lines = "\n".join(f"- **{flag['severity']}** — {flag['flag']}: {flag['evidence']}" for flag in screen["flags"])
    return f"""# Investment Committee Screening Memo — {case.name}

**Deal ID:** {case.deal_id}  
**Prepared by:** {author}  
**As of:** {datetime.now(timezone.utc).date().isoformat()}  
**Source status:** **{case.source_status}**
**Decision status:** **{screen['status']}**

## 1. Decision framing

This is a screening memo, not an approval. The deterministic model cannot substitute for verified source documents, reviewer sign-off, legal diligence, tax analysis, engineering review, or market evidence.

## 2. Downside first

{flag_lines}

## 3. Core outputs

| Metric | Result |
| --- | ---: |
| Entry cap rate | {result['entry_cap_rate']:.2%} |
| Levered IRR | {result['levered_irr']:.2%} |
| Unlevered IRR | {result['unlevered_irr']:.2%} |
| Equity multiple | {result['equity_multiple']:.2f}x |
| Minimum DSCR | {result['minimum_dscr']:.2f}x |
| Unlevered NPV | ${result['unlevered_npv']:,.0f} |
| Exit value | ${result['exit_value']:,.0f} |
| Break-even exit cap | {summary['break_even_exit_cap']:.2%} |

## 4. Traceability gate

- Model version: `deterministic-core-v1`
- Assumption state: **{case.source_status}**
- Required source references: deal inputs, operating statement/rent roll, financing terms, market comparables, legal/title diligence.
- Output lineage: key outputs must reference explicit assumptions and source IDs before approval.

## 5. Recommendation gate

**Initial status:** `{screen['status']}`
**Next gate:** resolve every CRITICAL, HIGH, and GOVERNANCE flag, attach source documents, then rerun the downside cases before recommendation.
"""


__all__ = ["DealCase", "ScreeningThresholds", "screen_case", "compare_deals", "screening_flags", "generate_ic_memo"]
