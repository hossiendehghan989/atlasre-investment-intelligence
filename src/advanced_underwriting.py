"""Advanced underwriting: development budgets, debt, waterfalls, and risk."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .atlasre import DealInputs, _irr, underwrite_deal


@dataclass(frozen=True)
class DevelopmentInputs:
    land_cost: float
    hard_cost: float
    soft_cost: float
    contingency_pct: float = 0.05
    construction_years: int = 2
    stabilization_years: int = 3
    stabilized_noi: float = 1_000_000
    exit_cap_rate: float = 0.06
    debt_to_cost: float = 0.55
    construction_rate: float = 0.07
    preferred_return: float = 0.08
    promote: float = 0.20


def development_feasibility(project: DevelopmentInputs) -> dict[str, float | list[float]]:
    """Build a transparent development cash-flow and investor waterfall."""
    if min(project.land_cost, project.hard_cost, project.soft_cost, project.stabilized_noi) <= 0:
        raise ValueError("project costs and stabilized NOI must be positive")
    if not 0 <= project.debt_to_cost < 1 or not 0 <= project.promote < 1:
        raise ValueError("debt_to_cost and promote must be between 0 and 1")
    base_cost = project.land_cost + project.hard_cost + project.soft_cost
    contingency = (project.hard_cost + project.soft_cost) * project.contingency_pct
    total_cost = base_cost + contingency
    years = project.construction_years + project.stabilization_years
    draw = total_cost / project.construction_years
    debt = total_cost * project.debt_to_cost
    equity = total_cost - debt
    debt_interest = debt * project.construction_rate * project.construction_years / 2
    exit_value = project.stabilized_noi / project.exit_cap_rate
    project_profit = exit_value - total_cost - debt_interest
    preferred = equity * ((1 + project.preferred_return) ** years - 1)
    residual = max(project_profit - preferred, 0)
    sponsor_promote = residual * project.promote
    investor_profit = project_profit - sponsor_promote
    investor_flows = [-equity] + [0.0] * (years - 1) + [equity + investor_profit]
    sponsor_flows = [0.0] * years + [sponsor_promote]
    return {
        "total_development_cost": total_cost,
        "contingency": contingency,
        "debt_amount": debt,
        "equity_required": equity,
        "annual_construction_draw": draw,
        "capitalized_interest": debt_interest,
        "exit_value": exit_value,
        "project_profit_before_waterfall": project_profit,
        "investor_irr": _irr(investor_flows),
        "investor_equity_multiple": (equity + investor_profit) / equity,
        "sponsor_promote": sponsor_promote,
        "investor_cash_flows": investor_flows,
        "sponsor_cash_flows": sponsor_flows,
    }


def monte_carlo_underwriting(deal: DealInputs, simulations: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Run a reproducible uncertainty simulation over growth, exit cap, and price."""
    rng = np.random.default_rng(seed)
    growth = rng.normal(deal.annual_noi_growth, 0.02, simulations)
    exit_caps = np.clip(rng.normal(deal.exit_cap_rate, 0.008, simulations), 0.03, 0.15)
    prices = deal.purchase_price * rng.lognormal(0, 0.03, simulations)
    rows = []
    for p, g, cap in zip(prices, growth, exit_caps):
        scenario = DealInputs(**{**deal.__dict__, "purchase_price": float(p), "annual_noi_growth": float(g), "exit_cap_rate": float(cap)})
        result = underwrite_deal(scenario)
        rows.append({"purchase_price": p, "noi_growth": g, "exit_cap_rate": cap, "levered_irr": result["levered_irr"], "unlevered_npv": result["unlevered_npv"]})
    return pd.DataFrame(rows)


def risk_summary(simulations: pd.DataFrame, hurdle_rate: float = 0.12) -> dict[str, float]:
    """Summarize return distribution and downside probability."""
    irr = simulations["levered_irr"].replace([np.inf, -np.inf], np.nan).dropna()
    npv = simulations["unlevered_npv"].replace([np.inf, -np.inf], np.nan).dropna()
    return {
        "median_irr": float(irr.median()),
        "p10_irr": float(irr.quantile(0.10)),
        "p90_irr": float(irr.quantile(0.90)),
        "probability_irr_below_hurdle": float((irr < hurdle_rate).mean()),
        "probability_negative_npv": float((npv < 0).mean()),
        "median_npv": float(npv.median()),
    }


def stress_test(deal: DealInputs) -> pd.DataFrame:
    """Evaluate named downside cases used in committee review."""
    cases = {
        "Base case": {},
        "No growth": {"annual_noi_growth": 0.0},
        "Exit cap expansion": {"exit_cap_rate": deal.exit_cap_rate + 0.015},
        "Cost inflation": {"purchase_price": deal.purchase_price * 1.08},
        "Combined downside": {"annual_noi_growth": -0.01, "exit_cap_rate": deal.exit_cap_rate + 0.02, "purchase_price": deal.purchase_price * 1.08},
    }
    rows = []
    for name, overrides in cases.items():
        scenario = DealInputs(**{**deal.__dict__, **overrides})
        result = underwrite_deal(scenario)
        rows.append({"case": name, "levered_irr": result["levered_irr"], "unlevered_irr": result["unlevered_irr"], "npv": result["unlevered_npv"], "exit_value": result["exit_value"]})
    return pd.DataFrame(rows)
