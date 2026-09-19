"""Portfolio-level decision support with explicit constraints."""
from __future__ import annotations

import pandas as pd


def portfolio_snapshot(deals: pd.DataFrame, available_equity: float, max_single_asset_pct: float = 0.40) -> dict[str, float]:
    required = {"asset", "equity_required", "risk_adjusted_score", "levered_irr", "minimum_dscr"}
    missing = required.difference(deals.columns)
    if missing:
        raise ValueError(f"deals must include {sorted(required)}; missing {sorted(missing)}")
    if available_equity <= 0 or not 0 < max_single_asset_pct <= 1:
        raise ValueError("available_equity must be positive and max_single_asset_pct must be in (0, 1]")
    eligible = deals[deals["equity_required"] <= available_equity].copy()
    scores = eligible["risk_adjusted_score"].clip(lower=0)
    allocation = pd.Series(0.0, index=eligible.index) if scores.sum() == 0 else scores / scores.sum() * available_equity
    allocation = allocation.clip(upper=available_equity * max_single_asset_pct)
    return {
        "available_equity": float(available_equity),
        "eligible_assets": float(len(eligible)),
        "allocated_equity": float(allocation.sum()),
        "unallocated_equity": float(available_equity - allocation.sum()),
        "weighted_irr": float((eligible.loc[allocation.index, "levered_irr"] * allocation).sum() / allocation.sum()) if allocation.sum() else 0.0,
        "minimum_portfolio_dscr": float(eligible.loc[allocation.index, "minimum_dscr"].min()) if len(allocation) else 0.0,
        "concentration_limit": float(max_single_asset_pct),
    }


def portfolio_allocation(deals: pd.DataFrame, available_equity: float, max_single_asset_pct: float = 0.40) -> pd.DataFrame:
    """Return an auditable allocation table with eligibility and constraint flags."""
    required = {"asset", "equity_required", "risk_adjusted_score", "levered_irr", "minimum_dscr"}
    if not required.issubset(deals.columns):
        raise ValueError(f"deals must include {sorted(required)}")
    output = deals.copy()
    output["eligible"] = output["equity_required"] <= available_equity
    scores = output["risk_adjusted_score"].clip(lower=0) * output["eligible"]
    output["allocation_weight"] = scores / scores.sum() if scores.sum() else 0.0
    output["recommended_allocation"] = (output["allocation_weight"] * available_equity).clip(upper=available_equity * max_single_asset_pct)
    output["constraint_flag"] = output.apply(lambda row: "Pass" if row["eligible"] and row["minimum_dscr"] >= 1.25 else "Review", axis=1)
    return output


__all__ = ["portfolio_snapshot", "portfolio_allocation"]


if __name__ == "__main__":
    print("Portfolio analytics module ready")

