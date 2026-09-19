"""Advanced underwriting: development, uncertainty, and downside analytics."""
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
    """Build a transparent annual development screen and simple promote output."""
    if min(project.land_cost, project.hard_cost, project.soft_cost, project.stabilized_noi) <= 0:
        raise ValueError("project costs and stabilized NOI must be positive")
    if project.construction_years <= 0 or project.stabilization_years < 0 or project.exit_cap_rate <= 0:
        raise ValueError("development timing and exit cap must be valid")
    if not 0 <= project.debt_to_cost < 1 or not 0 <= project.promote < 1:
        raise ValueError("debt_to_cost and promote must be between 0 and 1")
    base_cost = project.land_cost + project.hard_cost + project.soft_cost
    contingency = (project.hard_cost + project.soft_cost) * project.contingency_pct
    total_cost = base_cost + contingency
    years = project.construction_years + project.stabilization_years
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
    return {"total_development_cost": total_cost, "contingency": contingency, "debt_amount": debt, "equity_required": equity, "annual_construction_draw": total_cost / project.construction_years, "capitalized_interest": debt_interest, "exit_value": exit_value, "project_profit_before_waterfall": project_profit, "investor_irr": _irr(investor_flows), "investor_equity_multiple": (equity + investor_profit) / equity, "sponsor_promote": sponsor_promote, "investor_cash_flows": investor_flows, "sponsor_cash_flows": sponsor_flows}


def monte_carlo_underwriting(deal: DealInputs, simulations: int = 5000, seed: int = 42, correlation: float = -0.25) -> pd.DataFrame:
    """Run reproducible correlated shocks to growth, exit cap, price, and debt rate."""
    if simulations <= 0 or not -1 < correlation < 1:
        raise ValueError("simulations must be positive and correlation must be between -1 and 1")
    rng = np.random.default_rng(seed)
    cov = np.array([[1.0, correlation, 0.15, 0.0], [correlation, 1.0, -0.10, 0.0], [0.15, -0.10, 1.0, 0.20], [0.0, 0.0, 0.20, 1.0]])
    if np.linalg.eigvalsh(cov).min() < -1e-10:
        raise ValueError("shock covariance matrix must be positive semi-definite")
    shocks = rng.multivariate_normal(np.zeros(4), cov, simulations, check_valid="raise")
    growth = deal.annual_noi_growth + shocks[:, 0] * 0.02
    exit_caps = np.clip(deal.exit_cap_rate + shocks[:, 1] * 0.008, 0.025, 0.20)
    prices = deal.purchase_price * np.exp(shocks[:, 2] * 0.03)
    debt_rates = np.clip(deal.debt_rate + shocks[:, 3] * 0.0075, 0.01, 0.20)
    rows = []
    for p, g, cap, debt_rate in zip(prices, growth, exit_caps, debt_rates):
        scenario = DealInputs(**{**deal.__dict__, "purchase_price": float(p), "annual_noi_growth": float(g), "exit_cap_rate": float(cap), "debt_rate": float(debt_rate)})
        result = underwrite_deal(scenario)
        rows.append({"purchase_price": p, "noi_growth": g, "exit_cap_rate": cap, "debt_rate": debt_rate, "levered_irr": result["levered_irr"], "unlevered_npv": result["unlevered_npv"], "minimum_dscr": result["minimum_dscr"]})
    return pd.DataFrame(rows)


def risk_summary(simulations: pd.DataFrame, hurdle_rate: float = 0.12) -> dict[str, float]:
    """Summarize tails, hurdle failure, NPV loss, and DSCR breach probability."""
    required = {"levered_irr", "unlevered_npv", "minimum_dscr"}
    if not required.issubset(simulations.columns):
        raise ValueError(f"simulations must include {sorted(required)}")
    irr = simulations["levered_irr"].replace([np.inf, -np.inf], np.nan).dropna()
    npv = simulations["unlevered_npv"].replace([np.inf, -np.inf], np.nan).dropna()
    dscr = simulations["minimum_dscr"].replace([np.inf, -np.inf], np.nan).dropna()
    if irr.empty or npv.empty or dscr.empty:
        raise ValueError("simulations contain no finite risk observations")
    irr_tail = irr[irr <= irr.quantile(0.10)]
    npv_tail = npv[npv <= npv.quantile(0.10)]
    return {"p05_irr": float(irr.quantile(0.05)), "p10_irr": float(irr.quantile(0.10)), "median_irr": float(irr.median()), "p90_irr": float(irr.quantile(0.90)), "p95_irr": float(irr.quantile(0.95)), "expected_shortfall_irr_10": float(irr_tail.mean()), "expected_shortfall_npv_10": float(npv_tail.mean()), "worst_irr": float(irr.min()), "probability_irr_below_hurdle": float((irr < hurdle_rate).mean()), "probability_negative_npv": float((npv < 0).mean()), "median_npv": float(npv.median()), "probability_dscr_below_125": float((dscr < 1.25).mean())}


def stress_test(deal: DealInputs) -> pd.DataFrame:
    """Evaluate named, auditable downside cases used in committee review."""
    cases = {"Base case": {}, "No growth": {"annual_noi_growth": 0.0}, "Exit cap expansion": {"exit_cap_rate": deal.exit_cap_rate + 0.015}, "Cost inflation": {"purchase_price": deal.purchase_price * 1.08}, "Rate shock": {"debt_rate": min(deal.debt_rate + 0.02, 0.20)}, "Combined downside": {"annual_noi_growth": -0.01, "exit_cap_rate": deal.exit_cap_rate + 0.02, "purchase_price": deal.purchase_price * 1.08, "debt_rate": min(deal.debt_rate + 0.02, 0.20)}}
    rows = []
    for name, overrides in cases.items():
        scenario = DealInputs(**{**deal.__dict__, **overrides})
        result = underwrite_deal(scenario)
        rows.append({"case": name, "levered_irr": result["levered_irr"], "unlevered_irr": result["unlevered_irr"], "npv": result["unlevered_npv"], "exit_value": result["exit_value"], "minimum_dscr": result["minimum_dscr"]})
    return pd.DataFrame(rows)
