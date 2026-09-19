"""Portfolio-level decision support with explicit, enforceable constraints."""
from __future__ import annotations

import math

import pandas as pd

from .validation import positive, unit_interval


def _validate_columns(deals: pd.DataFrame, required: set[str]) -> None:
    missing = required.difference(deals.columns)
    if missing:
        raise ValueError(f"deals must include {sorted(required)}")


def allocate_capital(deals: pd.DataFrame, available_equity: float, max_single_asset_pct: float = 0.40, min_dscr: float = 1.25) -> pd.Series:
    """Allocate capital by score while re-allocating around binding concentration caps."""
    positive(available_equity, "available_equity")
    unit_interval(max_single_asset_pct, "max_single_asset_pct")
    positive(min_dscr, "min_dscr")
    _validate_columns(deals, {"equity_required", "minimum_dscr", "risk_adjusted_score"})
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
        equity_caps = deals.loc[proposed.index, "equity_required"].astype(float).clip(upper=cap)
        capped = proposed[proposed > equity_caps + 1e-9]
        if capped.empty:
            allocation.loc[proposed.index] += proposed
            remaining = 0.0
            break
        for idx in sorted(capped.index, key=str):
            allocation.loc[idx] += float(equity_caps.loc[idx])
            remaining -= float(equity_caps.loc[idx])
            active.remove(idx)
    return allocation


def portfolio_allocation(deals: pd.DataFrame, available_equity: float, max_single_asset_pct: float = 0.40, min_dscr: float = 1.25) -> pd.DataFrame:
    """Return allocation, eligibility, and a reason for every constraint decision."""
    required = {"asset", "equity_required", "risk_adjusted_score", "levered_irr", "minimum_dscr"}
    _validate_columns(deals, required)
    positive(available_equity, "available_equity")
    unit_interval(max_single_asset_pct, "max_single_asset_pct")
    positive(min_dscr, "min_dscr")
    output = deals.copy()
    output["capital_eligible"] = output["equity_required"] <= available_equity
    output["dscr_eligible"] = output["minimum_dscr"] >= min_dscr
    output["eligible"] = output["capital_eligible"] & output["dscr_eligible"]
    output["recommended_allocation"] = allocate_capital(output, available_equity, max_single_asset_pct, min_dscr)
    allocated = float(output["recommended_allocation"].sum())
    unallocated = float(available_equity - allocated)
    output["unallocated_equity"] = 0.0
    output["allocation_weight"] = output["recommended_allocation"] / allocated if allocated else 0.0
    output["constraint_flag"] = output.apply(lambda row: "Pass" if row["eligible"] and row["recommended_allocation"] > 0 else "Review", axis=1)
    output["constraint_reason"] = output.apply(
        lambda row: (
            "Equity requirement cap"
            if row["recommended_allocation"] > 0 and row["recommended_allocation"] >= row["equity_required"] - 1e-9
            else "Concentration cap"
            if row["recommended_allocation"] > 0 and row["recommended_allocation"] >= available_equity * max_single_asset_pct - 1e-9
            else "Allocated"
            if row["recommended_allocation"] > 0
            else "Capital limit"
            if not row["capital_eligible"]
            else "DSCR gate"
            if not row["dscr_eligible"]
            else "No score / rationed"
        ),
        axis=1,
    )
    if unallocated > 1e-9:
        output = pd.concat([
            output,
            pd.DataFrame([{
                "asset": "UNALLOCATED",
                "equity_required": float("nan"),
                "risk_adjusted_score": float("nan"),
                "levered_irr": float("nan"),
                "minimum_dscr": float("nan"),
                "capital_eligible": False,
                "dscr_eligible": False,
                "eligible": False,
                "recommended_allocation": 0.0,
                "unallocated_equity": unallocated,
                "allocation_weight": 0.0,
                "constraint_flag": "SUMMARY",
                "constraint_reason": "Available capital not allocated",
            }], index=["UNALLOCATED"]),
        ], ignore_index=False)
    # Streamlit serializes data frames through Arrow. Keep the display index
    # homogeneous so an optional UNALLOCATED summary row cannot coerce it into
    # a mixed integer/string object column during serialization.
    return output.reset_index(drop=True)


def portfolio_risk_view(allocation: pd.DataFrame, min_dscr: float = 1.25) -> dict[str, float]:
    """Summarize financed exposure to return, coverage, and concentration risk."""
    positive(min_dscr, "min_dscr")
    _validate_columns(allocation, {"recommended_allocation", "levered_irr", "minimum_dscr", "allocation_weight"})
    invested = allocation[allocation["recommended_allocation"] > 0]
    invested_capital = float(invested["recommended_allocation"].sum())
    if invested_capital <= 0:
        return {"invested_capital": 0.0, "weighted_irr": 0.0, "minimum_dscr": 0.0, "dscr_breach_exposure": 0.0, "negative_irr_exposure": 0.0, "concentration_hhi": 0.0, "max_asset_weight": 0.0}
    weights = invested["recommended_allocation"] / invested_capital
    return {"invested_capital": invested_capital, "weighted_irr": float((invested["levered_irr"] * weights).sum()), "minimum_dscr": float(invested["minimum_dscr"].min()), "dscr_breach_exposure": float(invested.loc[invested["minimum_dscr"] < min_dscr, "recommended_allocation"].sum() / invested_capital), "negative_irr_exposure": float(invested.loc[invested["levered_irr"] < 0, "recommended_allocation"].sum() / invested_capital), "concentration_hhi": float((weights**2).sum()), "max_asset_weight": float(weights.max())}


def portfolio_snapshot(deals: pd.DataFrame, available_equity: float, max_single_asset_pct: float = 0.40, min_dscr: float = 1.25) -> dict[str, float]:
    output = portfolio_allocation(deals, available_equity, max_single_asset_pct, min_dscr)
    allocated = float(output["recommended_allocation"].sum())
    risk = portfolio_risk_view(output, min_dscr)
    capital_eligible_assets = float((output["equity_required"] <= available_equity).sum())
    return {"available_equity": float(available_equity), "eligible_assets": capital_eligible_assets, "allocated_equity": allocated, "unallocated_equity": float(available_equity - allocated), "weighted_irr": risk["weighted_irr"], "minimum_portfolio_dscr": risk["minimum_dscr"], "concentration_limit": float(max_single_asset_pct), "dscr_breach_exposure": risk["dscr_breach_exposure"], "concentration_hhi": risk["concentration_hhi"]}


__all__ = ["allocate_capital", "portfolio_allocation", "portfolio_risk_view", "portfolio_snapshot"]
