"""Advanced underwriting: development, uncertainty, and downside analytics."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from .atlasre import DealInputs, _irr, _npv, underwrite_deal, validate_deal

MAX_SIMULATIONS = 20_000


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
    numeric_fields = (
        "land_cost",
        "hard_cost",
        "soft_cost",
        "contingency_pct",
        "construction_years",
        "stabilization_years",
        "stabilized_noi",
        "exit_cap_rate",
        "debt_to_cost",
        "construction_rate",
        "preferred_return",
        "promote",
    )
    if any(not isfinite(float(getattr(project, name))) for name in numeric_fields):
        raise ValueError("development inputs must be finite")
    if min(project.land_cost, project.hard_cost, project.soft_cost, project.stabilized_noi) <= 0:
        raise ValueError("project costs and stabilized NOI must be positive")
    if not isinstance(project.construction_years, int) or not isinstance(project.stabilization_years, int):
        raise ValueError("development timing must be integer years")
    if project.construction_years <= 0 or project.stabilization_years < 0 or project.exit_cap_rate <= 0:
        raise ValueError("development timing and exit cap must be valid")
    if not 0 <= project.contingency_pct <= 1 or not 0 <= project.debt_to_cost < 1 or not 0 <= project.promote < 1:
        raise ValueError("contingency, debt_to_cost, and promote must be within range")
    if not 0 <= project.construction_rate <= 1 or not 0 <= project.preferred_return <= 1:
        raise ValueError("construction rate and preferred return must be within range")
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


def _first_irr_roots(cash_flows: np.ndarray) -> np.ndarray:
    """Return the same first reachable roots selected by ``src.atlasre._irr``.

    The rate grid is evaluated for every simulation in one array operation, then
    the existing scalar NPV function refines only the first bracket for each
    scenario.  Keeping ``_npv`` inside ``brentq`` preserves the public model's
    first-root convention and its numerical results while avoiding millions of
    repeated grid evaluations.
    """
    rate_grid = np.concatenate(
        [np.array([-0.999999, -0.99, -0.90, -0.50, -0.10, 0.0]), np.logspace(-4, 3, 500)]
    )
    periods = np.arange(cash_flows.shape[1], dtype=float)
    discount_factors = np.power(1 + rate_grid[:, None], periods)
    npv_grid = cash_flows @ (1 / discount_factors).T
    left = npv_grid[:, :-1]
    right = npv_grid[:, 1:]
    candidates = (left == 0) | (np.isfinite(left) & np.isfinite(right) & (np.signbit(left) != np.signbit(right)))
    has_candidate = candidates.any(axis=1)
    first_index = candidates.argmax(axis=1)
    roots = np.full(cash_flows.shape[0], np.nan, dtype=float)

    for row_index in np.flatnonzero(has_candidate):
        grid_index = int(first_index[row_index])
        left_rate = float(rate_grid[grid_index])
        if left[row_index, grid_index] == 0:
            roots[row_index] = left_rate
            continue
        right_rate = float(rate_grid[grid_index + 1])
        flow = cash_flows[row_index]
        roots[row_index] = float(brentq(lambda rate: _npv(rate, flow), left_rate, right_rate))
    return roots


def _vectorized_underwriting_outputs(
    deal: DealInputs,
    prices: np.ndarray,
    growth: np.ndarray,
    exit_caps: np.ndarray,
    debt_rates: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate simulation outputs using the core model's annual conventions."""
    count = prices.size
    years = np.arange(deal.hold_years, dtype=float)
    acquisition = prices * (1 + deal.acquisition_cost_pct)
    debt = prices * deal.leverage
    equity = acquisition - debt
    noi = deal.annual_noi * np.power(1 + growth[:, None], years)
    exit_value = noi[:, -1] / exit_caps
    selling_cost = exit_value * deal.selling_cost_pct

    debt_service = np.zeros((count, deal.hold_years), dtype=float)
    balance = debt.copy()
    monthly_rate = debt_rates / 12
    amortization_periods = deal.debt_amortization_years * 12
    payment = np.where(
        monthly_rate == 0,
        debt / amortization_periods,
        debt * (monthly_rate * np.power(1 + monthly_rate, amortization_periods))
        / (np.power(1 + monthly_rate, amortization_periods) - 1),
    )
    for year in range(deal.hold_years):
        annual_service = np.zeros(count, dtype=float)
        for _ in range(12):
            interest = balance * monthly_rate
            principal = np.minimum(np.maximum(payment - interest, 0.0), balance)
            annual_service += interest + principal
            balance = np.maximum(0.0, balance - principal)
        debt_service[:, year] = annual_service

    unlevered_flows = np.empty((count, deal.hold_years + 1), dtype=float)
    unlevered_flows[:, 0] = -acquisition
    unlevered_flows[:, 1:] = noi
    unlevered_flows[:, -1] += exit_value - selling_cost
    discount_factors = np.power(1 + deal.discount_rate, np.arange(deal.hold_years + 1, dtype=float))
    unlevered_npv = np.sum(unlevered_flows / discount_factors, axis=1)

    levered_flows = unlevered_flows.copy()
    levered_flows[:, 0] = -equity
    levered_flows[:, 1:] -= debt_service
    levered_flows[:, -1] -= balance
    levered_irr = _first_irr_roots(levered_flows)
    minimum_dscr = np.min(
        np.divide(noi, debt_service, out=np.full_like(noi, np.inf), where=debt_service != 0), axis=1
    )
    return levered_irr, unlevered_npv, minimum_dscr


def monte_carlo_underwriting(
    deal: DealInputs,
    simulations: int = 5000,
    seed: int = 42,
    correlation: float = -0.25,
) -> pd.DataFrame:
    """Run reproducible correlated shocks to growth, exit cap, price, and debt rate.

    Simulation inputs, the random number generator, clipping bounds, result
    schema, and the core model's first-root IRR semantics are unchanged.  The
    scenario calculations are batched so the same seeded default package can be
    prepared interactively.
    """
    validate_deal(deal)
    if isinstance(simulations, bool) or not isinstance(simulations, int) or not 0 < simulations <= MAX_SIMULATIONS:
        raise ValueError(f"simulations must be an integer between 1 and {MAX_SIMULATIONS}")
    if not isfinite(float(correlation)) or not -1 < correlation < 1:
        raise ValueError("correlation must be finite and between -1 and 1")
    rng = np.random.default_rng(seed)
    cov = np.array(
        [
            [1.0, correlation, 0.15, 0.0],
            [correlation, 1.0, -0.10, 0.0],
            [0.15, -0.10, 1.0, 0.20],
            [0.0, 0.0, 0.20, 1.0],
        ]
    )
    if np.linalg.eigvalsh(cov).min() < -1e-10:
        raise ValueError("shock covariance matrix must be positive semi-definite")
    shocks = rng.multivariate_normal(np.zeros(4), cov, simulations, check_valid="raise")
    growth = deal.annual_noi_growth + shocks[:, 0] * 0.02
    exit_caps = np.clip(deal.exit_cap_rate + shocks[:, 1] * 0.008, 0.025, 0.20)
    prices = deal.purchase_price * np.exp(shocks[:, 2] * 0.03)
    debt_rates = np.clip(deal.debt_rate + shocks[:, 3] * 0.0075, 0.01, 0.20)
    levered_irr, unlevered_npv, minimum_dscr = _vectorized_underwriting_outputs(
        deal, prices, growth, exit_caps, debt_rates
    )
    return pd.DataFrame(
        {
            "purchase_price": prices,
            "noi_growth": growth,
            "exit_cap_rate": exit_caps,
            "debt_rate": debt_rates,
            "levered_irr": levered_irr,
            "unlevered_npv": unlevered_npv,
            "minimum_dscr": minimum_dscr,
        }
    )


def risk_summary(simulations: pd.DataFrame, hurdle_rate: float = 0.12) -> dict[str, float | None]:
    """Summarize each risk series independently; unavailable metrics are ``None``."""
    required = {"levered_irr", "unlevered_npv", "minimum_dscr"}
    if not required.issubset(simulations.columns):
        raise ValueError(f"simulations must include {sorted(required)}")
    irr = simulations["levered_irr"].replace([np.inf, -np.inf], np.nan).dropna()
    npv = simulations["unlevered_npv"].replace([np.inf, -np.inf], np.nan).dropna()
    dscr = simulations["minimum_dscr"].replace([np.inf, -np.inf], np.nan).dropna()
    def quantile(series: pd.Series, probability: float) -> float | None:
        return float(series.quantile(probability)) if not series.empty else None

    irr_tail = irr[irr <= irr.quantile(0.10)] if not irr.empty else irr
    npv_tail = npv[npv <= npv.quantile(0.10)] if not npv.empty else npv
    return {
        "p05_irr": quantile(irr, 0.05),
        "p10_irr": quantile(irr, 0.10),
        "median_irr": quantile(irr, 0.50),
        "p90_irr": quantile(irr, 0.90),
        "p95_irr": quantile(irr, 0.95),
        "expected_shortfall_irr_10": float(irr_tail.mean()) if not irr_tail.empty else None,
        "expected_shortfall_npv_10": float(npv_tail.mean()) if not npv_tail.empty else None,
        "worst_irr": float(irr.min()) if not irr.empty else None,
        "probability_irr_below_hurdle": float((irr < hurdle_rate).mean()) if not irr.empty else None,
        "probability_negative_npv": float((npv < 0).mean()) if not npv.empty else None,
        "median_npv": quantile(npv, 0.50),
        "probability_dscr_below_125": float((dscr < 1.25).mean()) if not dscr.empty else None,
    }


def stress_test(deal: DealInputs) -> pd.DataFrame:
    """Evaluate named, auditable downside cases used in committee review."""
    cases = {"Base case": {}, "No growth": {"annual_noi_growth": 0.0}, "Exit cap expansion": {"exit_cap_rate": deal.exit_cap_rate + 0.015}, "Cost inflation": {"purchase_price": deal.purchase_price * 1.08}, "Rate shock": {"debt_rate": min(deal.debt_rate + 0.02, 0.20)}, "Combined downside": {"annual_noi_growth": -0.01, "exit_cap_rate": deal.exit_cap_rate + 0.02, "purchase_price": deal.purchase_price * 1.08, "debt_rate": min(deal.debt_rate + 0.02, 0.20)}}
    rows = []
    for name, overrides in cases.items():
        scenario = DealInputs(**{**deal.__dict__, **overrides})
        result = underwrite_deal(scenario)
        rows.append({"case": name, "levered_irr": result["levered_irr"], "unlevered_irr": result["unlevered_irr"], "npv": result["unlevered_npv"], "exit_value": result["exit_value"], "minimum_dscr": result["minimum_dscr"]})
    return pd.DataFrame(rows)
