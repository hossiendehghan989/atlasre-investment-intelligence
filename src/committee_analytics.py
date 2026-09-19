"""Decision-committee views built on the AtlasRE underwriting engine."""
from __future__ import annotations

import pandas as pd
from scipy.optimize import brentq

from .atlasre import DealInputs, underwrite_deal


def sensitivity_table(base: DealInputs, parameter: str, values: list[float]) -> pd.DataFrame:
    """Return a one-way sensitivity table for a supported deal assumption."""
    supported = {"purchase_price", "annual_noi", "annual_noi_growth", "exit_cap_rate", "leverage", "debt_rate"}
    if parameter not in supported:
        raise ValueError(f"parameter must be one of {sorted(supported)}")
    rows = []
    for value in values:
        scenario = DealInputs(**{**base.__dict__, parameter: value})
        result = underwrite_deal(scenario)
        rows.append({parameter: value, "levered_irr": result["levered_irr"], "unlevered_npv": result["unlevered_npv"], "minimum_dscr": result["minimum_dscr"], "exit_value": result["exit_value"]})
    return pd.DataFrame(rows)


def break_even_exit_cap(base: DealInputs, target_irr: float = 0.12) -> float:
    """Solve for the exit cap rate that produces a target levered IRR."""
    def objective(cap: float) -> float:
        deal = DealInputs(**{**base.__dict__, "exit_cap_rate": cap})
        return float(underwrite_deal(deal)["levered_irr"] - target_irr)
    try:
        return float(brentq(objective, 0.02, 0.15))
    except ValueError:
        return float("nan")


def investment_committee_summary(base: DealInputs, hurdle_rate: float = 0.12) -> dict[str, str | float]:
    """Create concise decision flags without hiding the underlying metrics."""
    result = underwrite_deal(base)
    flags = []
    if result["levered_irr"] < hurdle_rate:
        flags.append("return below hurdle")
    if result["minimum_dscr"] < 1.25:
        flags.append("thin debt coverage")
    if result["unlevered_npv"] < 0:
        flags.append("negative unlevered NPV")
    if not flags:
        flags.append("passes initial screen")
    return {"decision_flag": "; ".join(flags), "levered_irr": result["levered_irr"], "minimum_dscr": result["minimum_dscr"], "unlevered_npv": result["unlevered_npv"], "break_even_exit_cap": break_even_exit_cap(base, hurdle_rate)}
