"""Portfolio-level decision support with explicit, enforceable constraints."""
from __future__ import annotations

import math

import pandas as pd


def allocate_capital(deals: pd.DataFrame, available_equity: float, max_single_asset_pct: float = 0.40, min_dscr: float = 1.25) -> pd.Series:
    """Allocate capital by score while re-allocating around binding concentration caps."""
    if available_equity <= 0 or not 0 < max_single_asset_pct <= 1 or min_dscr <= 0:
        raise ValueError("capital, concentration, and DSCR constraints must be valid")
    if any(column not in deals.columns for column in ("equity_required", "minimum_dscr", "risk_adjusted_score")):
        raise ValueError("deals must include equity_required, minimum_dscr, and risk_adjusted_score")
    if any(not math.isfinite(float(value)) for column in ("equity_required", "minimum_dscr", "risk_adjusted_score") for value in deals[column]):
        raise ValueError("portfolio inputs must be finite")
    eligible = (deals["equity_required"] <= available_equity) & (deals["minimum_dscr"] >= min_dscr) & (deals["risk_adjusted_score"] > 0)
    scores = deals["risk_adjusted_score"].where(eligible, 0.0).astype(float)
    allocation = pd.Series(0.0, index=deals.index)
    remaining = float(available_equity)
    active = set(scores[scores > 0].index)
    cap = available_equity * max_single_asset_pct
    while active and remaining > 1e-9:
        active_scores = scores.loc[sorted(active, key=str)]
        total_score = float(active_scores.sum())
        if total_score <= 0:
            break
        proposed = active_scores / total_score * remaining
        capped = proposed[proposed > cap + 1e-9]
        if capped.empty:
            allocation.loc[proposed.index] += proposed
            remaining = 0.0
            break
        for idx in sorted(capped.index, key=str):
            allocation.loc[idx] += cap
            remaining -= cap
            active.remove(idx)
    return allocation


def portfolio_allocation(deals: pd.DataFrame, available_equity: float, max_single_asset_pct: float = 0.40, min_dscr: float = 1.25) -> pd.DataFrame:
    """Return allocation, eligibility and constraint diagnostics for each asset."""
    required = {"asset", "equity_required", "risk_adjusted_score", "levered_irr", "minimum_dscr"}
    if not required.issubset(deals.columns):
        raise ValueError(f"deals must include {sorted(required)}")
    output = deals.copy()
    output["eligible"] = (output["equity_required"] <= available_equity) & (output["minimum_dscr"] >= min_dscr)
    output["recommended_allocation"] = allocate_capital(output, available_equity, max_single_asset_pct, min_dscr)
    allocated = output["recommended_allocation"].sum()
    output["allocation_weight"] = output["recommended_allocation"] / allocated if allocated else 0.0
    output["constraint_flag"] = output.apply(lambda row: "Pass" if row["eligible"] and row["recommended_allocation"] > 0 else "Review", axis=1)
    return output


def portfolio_snapshot(deals: pd.DataFrame, available_equity: float, max_single_asset_pct: float = 0.40, min_dscr: float = 1.25) -> dict[str, float]:
    output = portfolio_allocation(deals, available_equity, max_single_asset_pct, min_dscr)
    allocated = float(output["recommended_allocation"].sum())
    capital_eligible_assets = float((output["equity_required"] <= available_equity).sum())
    return {
        "available_equity": float(available_equity),
        "eligible_assets": capital_eligible_assets,
        "allocated_equity": allocated,
        "unallocated_equity": float(available_equity - allocated),
        "weighted_irr": float((output["levered_irr"] * output["recommended_allocation"]).sum() / allocated) if allocated else 0.0,
        "minimum_portfolio_dscr": float(output.loc[output["recommended_allocation"] > 0, "minimum_dscr"].min()) if allocated else 0.0,
        "concentration_limit": float(max_single_asset_pct),
    }


__all__ = ["allocate_capital", "portfolio_allocation", "portfolio_snapshot"]
