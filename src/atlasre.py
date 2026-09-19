"""AtlasRE: transparent real-estate underwriting and investment intelligence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.optimize import brentq


@dataclass(frozen=True)
class DealInputs:
    purchase_price: float
    annual_noi: float
    hold_years: int = 5
    annual_noi_growth: float = 0.03
    exit_cap_rate: float = 0.06
    discount_rate: float = 0.10
    acquisition_cost_pct: float = 0.03
    selling_cost_pct: float = 0.02
    leverage: float = 0.0
    debt_rate: float = 0.06
    debt_amortization_years: int = 20


def validate_deal(deal: DealInputs) -> None:
    if deal.purchase_price <= 0 or deal.annual_noi <= 0:
        raise ValueError("purchase_price and annual_noi must be positive")
    if not 0 <= deal.leverage < 1:
        raise ValueError("leverage must be between 0 and 1")
    if deal.hold_years < 1 or deal.exit_cap_rate <= 0 or deal.discount_rate <= 0:
        raise ValueError("hold_years, exit_cap_rate, and discount_rate must be positive")


def _irr(cash_flows: Iterable[float]) -> float:
    flows = np.asarray(list(cash_flows), dtype=float)
    if not (np.any(flows > 0) and np.any(flows < 0)):
        return float("nan")
    def npv(rate: float) -> float:
        return float(sum(value / (1 + rate) ** i for i, value in enumerate(flows)))
    try:
        return float(brentq(npv, -0.99, 10.0))
    except ValueError:
        return float("nan")


def underwrite_deal(deal: DealInputs) -> dict[str, float | list[float]]:
    """Produce unlevered and levered underwriting outputs."""
    validate_deal(deal)
    acquisition = deal.purchase_price * (1 + deal.acquisition_cost_pct)
    debt = deal.purchase_price * deal.leverage
    equity = acquisition - debt
    noi = [deal.annual_noi * (1 + deal.annual_noi_growth) ** year for year in range(1, deal.hold_years + 1)]
    exit_value = noi[-1] / deal.exit_cap_rate
    selling_cost = exit_value * deal.selling_cost_pct
    unlevered_flows = [-acquisition] + noi[:-1] + [noi[-1] + exit_value - selling_cost]
    unlevered_irr = _irr(unlevered_flows)
    discount_flows = sum(flow / (1 + deal.discount_rate) ** i for i, flow in enumerate(unlevered_flows))
    annual_debt_service = 0.0
    remaining_debt = 0.0
    debt_schedule = []
    if debt:
        r = deal.debt_rate / 12
        periods = deal.debt_amortization_years * 12
        monthly_payment = debt * (r * (1 + r) ** periods) / ((1 + r) ** periods - 1)
        annual_debt_service = monthly_payment * 12
        balance = debt
        for year in range(1, deal.hold_years + 1):
            interest = 0.0
            principal = 0.0
            for _ in range(12):
                interest += balance * r
                principal += min(monthly_payment - balance * r, balance)
                balance = max(0.0, balance - (monthly_payment - balance * r))
            debt_schedule.append({"year": year, "interest": interest, "principal": principal, "ending_balance": balance})
        remaining_debt = balance
    dscr = [cash / annual_debt_service for cash in noi] if annual_debt_service else [float("inf")] * len(noi)
    levered_flows = [-equity] + [cash - annual_debt_service for cash in noi[:-1]] + [noi[-1] + exit_value - selling_cost - annual_debt_service - remaining_debt]
    levered_irr = _irr(levered_flows)
    return {
        "entry_cap_rate": deal.annual_noi / deal.purchase_price,
        "equity_required": equity,
        "debt_amount": debt,
        "annual_debt_service": annual_debt_service,
        "remaining_debt_at_exit": remaining_debt,
        "minimum_dscr": float(min(dscr)),
        "debt_schedule": debt_schedule,
        "exit_value": exit_value,
        "unlevered_irr": unlevered_irr,
        "levered_irr": levered_irr,
        "unlevered_npv": float(discount_flows),
        "equity_multiple": float(sum(max(flow, 0) for flow in levered_flows) / abs(levered_flows[0])),
        "cash_flows": levered_flows,
    }


def scenario_matrix(base: DealInputs, growth_rates=(0.0, 0.03, 0.06), exit_caps=(0.05, 0.06, 0.08)) -> pd.DataFrame:
    """Evaluate downside, base, and upside combinations."""
    rows = []
    for growth in growth_rates:
        for exit_cap in exit_caps:
            deal = DealInputs(**{**base.__dict__, "annual_noi_growth": growth, "exit_cap_rate": exit_cap})
            result = underwrite_deal(deal)
            rows.append({"noi_growth": growth, "exit_cap_rate": exit_cap, "levered_irr": result["levered_irr"], "unlevered_irr": result["unlevered_irr"], "exit_value": result["exit_value"], "npv": result["unlevered_npv"]})
    return pd.DataFrame(rows)


def market_score(market: dict[str, float], weights: dict[str, float] | None = None) -> dict[str, float]:
    """Score a market using normalized growth, liquidity, yield, and risk inputs."""
    weights = weights or {"population_growth": 0.25, "employment_growth": 0.20, "rent_growth": 0.25, "liquidity": 0.15, "risk": 0.15}
    positive = ["population_growth", "employment_growth", "rent_growth", "liquidity"]
    score = sum(market.get(key, 0.0) * weight for key, weight in weights.items() if key != "risk")
    score += (1 - market.get("risk", 0.5)) * weights.get("risk", 0.15)
    return {"score_0_100": float(np.clip(score * 100, 0, 100)), "risk_adjusted_score": float(np.clip(score * (1 - market.get("risk", 0.5)) * 100, 0, 100))}


def rank_markets(markets: pd.DataFrame) -> pd.DataFrame:
    required = {"market", "population_growth", "employment_growth", "rent_growth", "liquidity", "risk"}
    missing = required.difference(markets.columns)
    if missing:
        raise ValueError(f"Missing market columns: {sorted(missing)}")
    rows = []
    for _, row in markets.iterrows():
        rows.append({"market": row["market"], **market_score(row.to_dict())})
    return pd.DataFrame(rows).sort_values("risk_adjusted_score", ascending=False).reset_index(drop=True)


def portfolio_exposure(deals: pd.DataFrame, capital: float) -> pd.DataFrame:
    """Allocate capital proportionally to risk-adjusted opportunity scores."""
    required = {"asset", "equity_required", "risk_adjusted_score"}
    if not required.issubset(deals.columns):
        raise ValueError(f"deals must include {sorted(required)}")
    data = deals.copy()
    data["eligible"] = (data["equity_required"] <= capital).astype(int)
    weights = data["risk_adjusted_score"].clip(lower=0) * data["eligible"]
    data["allocation_weight"] = weights / weights.sum() if weights.sum() else 0
    data["recommended_allocation"] = data["allocation_weight"] * capital
    return data
