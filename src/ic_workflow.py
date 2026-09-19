"""Committee workflow, deal comparison, and downside-first memo generation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from .atlasre import DealInputs, underwrite_deal
from .committee_analytics import investment_committee_summary
from .governance import default_lineage


@dataclass(frozen=True)
class DealCase:
    deal_id: str
    name: str
    inputs: DealInputs
    source_status: str = "REVIEW REQUIRED"


def compare_deals(cases: list[DealCase], hurdle_rate: float = 0.12) -> pd.DataFrame:
    """Produce a side-by-side comparison without hiding source status or flags."""
    rows = []
    for case in cases:
        result = underwrite_deal(case.inputs)
        summary = investment_committee_summary(case.inputs, hurdle_rate)
        rows.append({"deal_id": case.deal_id, "deal": case.name, "source_status": case.source_status, "entry_cap": result["entry_cap_rate"], "levered_irr": result["levered_irr"], "unlevered_irr": result["unlevered_irr"], "equity_multiple": result["equity_multiple"], "minimum_dscr": result["minimum_dscr"], "unlevered_npv": result["unlevered_npv"], "decision_flag": summary["decision_flag"]})
    return pd.DataFrame(rows)


def screening_flags(inputs: DealInputs, hurdle_rate: float = 0.12) -> dict[str, Any]:
    """Return explicit review flags in severity order."""
    result = underwrite_deal(inputs)
    flags: list[dict[str, str]] = []
    if result["unlevered_npv"] < 0:
        flags.append({"severity": "CRITICAL", "flag": "Negative unlevered NPV", "evidence": f"${result['unlevered_npv']:,.0f}"})
    if result["minimum_dscr"] < 1.25:
        flags.append({"severity": "HIGH", "flag": "DSCR below 1.25x", "evidence": f"{result['minimum_dscr']:.2f}x"})
    if result["levered_irr"] < hurdle_rate:
        flags.append({"severity": "HIGH", "flag": "Levered IRR below hurdle", "evidence": f"{result['levered_irr']:.1%} vs {hurdle_rate:.1%}"})
    if not flags:
        flags.append({"severity": "INFO", "flag": "No initial-screen exception", "evidence": "All configured gates passed"})
    return {"deal_id": "UNASSIGNED", "status": "REVIEW REQUIRED", "flags": flags}


def generate_ic_memo(case: DealCase, hurdle_rate: float = 0.12, author: str = "AtlasRE") -> str:
    """Generate a challengeable markdown screening memo from deterministic outputs."""
    result = underwrite_deal(case.inputs)
    summary = investment_committee_summary(case.inputs, hurdle_rate)
    flags = screening_flags(case.inputs, hurdle_rate)["flags"]
    flag_lines = "\n".join(f"- **{f['severity']}** — {f['flag']}: {f['evidence']}" for f in flags)
    return f"""# Investment Committee Screening Memo — {case.name}

**Deal ID:** {case.deal_id}  
**Prepared by:** {author}  
**As of:** {datetime.now(timezone.utc).date().isoformat()}  
**Source status:** **{case.source_status}**

## 1. Decision framing

This is a screening memo, not an approval. The model is deterministic and the supplied inputs remain challengeable until source documents and reviewer sign-off are attached.

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

## 4. Assumption and lineage requirements

- Model version: `deterministic-core-v1`
- Assumption state: **{case.source_status}**
- Required source references: deal inputs, operating statement/rent roll, financing terms, market comparables, legal/title diligence.
- Output lineage: `default_lineage()` records the required input fields and calculation method for key outputs.

## 5. Recommendation gate

**Initial status:** `{summary['decision_flag']}`  
**Next gate:** attach source documents, resolve review-required assumptions, rerun downside cases, then complete deep analysis before recommendation.
"""


__all__ = ["DealCase", "compare_deals", "screening_flags", "generate_ic_memo"]

