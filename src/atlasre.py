"""Transparent real-estate underwriting and market intelligence primitives."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite

import numpy as np
import pandas as pd
from scipy.optimize import brentq

MAX_CURRENCY_INPUT = 100_000_000_000_000
MAX_HOLD_YEARS = 100
MAX_AMORTIZATION_YEARS = 100


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


def _finite(value: float, name: str) -> None:
    if not isfinite(float(value)):
        raise ValueError(f"{name} must be finite")


def validate_deal(deal: DealInputs) -> None:
    for name in ("purchase_price", "annual_noi", "annual_noi_growth", "exit_cap_rate", "discount_rate", "acquisition_cost_pct", "selling_cost_pct", "leverage", "debt_rate"):
        _finite(getattr(deal, name), name)
    if deal.purchase_price <= 0 or deal.annual_noi <= 0:
        raise ValueError("purchase_price and annual_noi must be positive")
    if deal.purchase_price > MAX_CURRENCY_INPUT or deal.annual_noi > MAX_CURRENCY_INPUT:
        raise ValueError(f"purchase_price and annual_noi must not exceed {MAX_CURRENCY_INPUT:g}")
    if deal.hold_years < 1 or deal.debt_amortization_years < 1:
        raise ValueError("hold_years and debt_amortization_years must be positive")
    if deal.hold_years > MAX_HOLD_YEARS or deal.debt_amortization_years > MAX_AMORTIZATION_YEARS:
        raise ValueError(f"hold_years and debt_amortization_years must not exceed {MAX_HOLD_YEARS}")
    if deal.annual_noi_growth <= -1 or deal.annual_noi_growth > 1:
        raise ValueError("growth must be above -100% and no greater than 100%")
    if not 0 < deal.exit_cap_rate <= 1 or not 0 <= deal.discount_rate <= 1 or not 0 <= deal.debt_rate <= 1:
        raise ValueError("exit cap must be in (0, 1]; discount rate and debt rate must be in [0, 1]")
    if not 0 <= deal.acquisition_cost_pct <= 1 or not 0 <= deal.selling_cost_pct <= 1:
        raise ValueError("transaction cost percentages must be between 0 and 1")
    if not 0 <= deal.leverage < 1:
        raise ValueError("leverage must be in [0, 1)")


def _npv(rate: float, cash_flows: np.ndarray) -> float:
    if rate <= -1:
        return float("nan")
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        discount_factors = np.power(1 + rate, np.arange(cash_flows.size, dtype=float))
        discounted = np.divide(cash_flows, discount_factors, out=np.zeros_like(cash_flows), where=np.isfinite(discount_factors) & (discount_factors != 0))
    return float(np.sum(discounted))


def _irr(cash_flows: Iterable[float]) -> float:
    """Return the first economically reachable IRR, or NaN when none exists.

    A scanned bracket is used instead of assuming a root between -99% and 1,000%.
    This makes negative-return and high-return cases explicit while remaining
    deterministic for conventional real-estate cash-flow streams.
    """
    flows = np.asarray(list(cash_flows), dtype=float)
    if flows.size < 2 or not np.all(np.isfinite(flows)) or not (np.any(flows > 0) and np.any(flows < 0)):
        return float("nan")
    rates = np.concatenate([np.array([-0.999999, -0.99, -0.90, -0.50, -0.10, 0.0]), np.logspace(-4, 3, 500)])
    values = np.array([_npv(float(rate), flows) for rate in rates])
    for left, right, left_value, right_value in zip(rates[:-1], rates[1:], values[:-1], values[1:]):
        if left_value == 0:
            return float(left)
        if np.isfinite(left_value) and np.isfinite(right_value) and np.signbit(left_value) != np.signbit(right_value):
            return float(brentq(lambda rate: _npv(rate, flows), float(left), float(right)))
    return float("nan")


def underwrite_deal(deal: DealInputs) -> dict[str, float | list[float]]:
    """Produce auditable annual underwriting outputs.

    Convention: ``annual_noi`` is the NOI for year one of ownership. Growth is
    applied from year two onward, so the year-one NOI is not grown before the
    first period is measured.
    """
    validate_deal(deal)
    acquisition = deal.purchase_price * (1 + deal.acquisition_cost_pct)
    debt = deal.purchase_price * deal.leverage
    equity = acquisition - debt
    noi = [deal.annual_noi * (1 + deal.annual_noi_growth) ** year for year in range(deal.hold_years)]
    exit_value = noi[-1] / deal.exit_cap_rate
    selling_cost = exit_value * deal.selling_cost_pct
    unlevered_flows = [
        -acquisition,
        *noi[:-1],
        noi[-1] + exit_value - selling_cost,
    ]
    unlevered_irr = _irr(unlevered_flows)
    discount_flows = _npv(deal.discount_rate, np.asarray(unlevered_flows, dtype=float))
    annual_debt_service = 0.0
    debt_service_schedule: list[float] = []
    remaining_debt = 0.0
    debt_schedule: list[dict[str, float | int]] = []
    if debt > 0:
        r = deal.debt_rate / 12
        periods = deal.debt_amortization_years * 12
        monthly_payment = debt / periods if r == 0 else debt * (r * (1 + r) ** periods) / ((1 + r) ** periods - 1)
        annual_debt_service = monthly_payment * 12
        balance = debt
        for year in range(1, deal.hold_years + 1):
            interest = 0.0
            principal = 0.0
            for _ in range(12):
                monthly_interest = balance * r
                scheduled_principal = min(max(monthly_payment - monthly_interest, 0.0), balance)
                interest += monthly_interest
                principal += scheduled_principal
                balance = max(0.0, balance - scheduled_principal)
            debt_schedule.append({"year": year, "interest": interest, "principal": principal, "ending_balance": balance})
            debt_service_schedule.append(interest + principal)
        remaining_debt = balance
    if debt:
        annual_debt_service = debt_service_schedule[0]
    else:
        debt_service_schedule = [0.0] * len(noi)
    dscr = [cash / service if service else float("inf") for cash, service in zip(noi, debt_service_schedule)]
    levered_flows = [-equity] + [cash - service for cash, service in zip(noi[:-1], debt_service_schedule[:-1])] + [noi[-1] + exit_value - selling_cost - debt_service_schedule[-1] - remaining_debt]
    total_distributions = sum(flow for flow in levered_flows if flow > 0)
    total_equity_invested = -sum(flow for flow in levered_flows if flow < 0)
    equity_multiple = total_distributions / total_equity_invested if total_equity_invested else float("nan")
    return {
        "entry_cap_rate": deal.annual_noi / deal.purchase_price,
        "equity_required": equity,
        "debt_amount": debt,
        "annual_debt_service": annual_debt_service,
        "remaining_debt_at_exit": remaining_debt,
        "minimum_dscr": float(min(dscr)),
        "debt_schedule": debt_schedule,
        "debt_service_schedule": debt_service_schedule,
        "exit_value": exit_value,
        "unlevered_irr": unlevered_irr,
        "levered_irr": _irr(levered_flows),
        "unlevered_npv": discount_flows,
        "total_distributions": float(total_distributions),
        "total_equity_invested": float(total_equity_invested),
        "equity_multiple": float(equity_multiple),
        "cash_flows": levered_flows,
    }


def scenario_matrix(
    base: DealInputs,
    growth_rates=(0.0, 0.03, 0.06),
    exit_caps=(0.05, 0.06, 0.08),
) -> pd.DataFrame:
    """Build a grid of growth and exit-cap assumptions for comparison."""
    if not growth_rates or not exit_caps:
        raise ValueError("scenario grids cannot be empty")
    rows: list[dict[str, float]] = []
    for growth in growth_rates:
        for exit_cap in exit_caps:
            deal = DealInputs(
                **{
                    **base.__dict__,
                    "annual_noi_growth": float(growth),
                    "exit_cap_rate": float(exit_cap),
                }
            )
            result = underwrite_deal(deal)
            rows.append(
                {
                    "noi_growth": float(growth),
                    "exit_cap_rate": float(exit_cap),
                    "levered_irr": result["levered_irr"],
                    "unlevered_irr": result["unlevered_irr"],
                    "exit_value": result["exit_value"],
                    "npv": result["unlevered_npv"],
                }
            )
    return pd.DataFrame(rows)


def market_score(market: dict[str, float], weights: dict[str, float] | None = None) -> dict[str, float]:
    """Return one risk-adjusted composite score on a 0-100 scale.

    ``risk`` is a downside factor, so it enters exactly once as ``1 - risk``
    under its configured weight. ``risk_adjusted_score`` is retained as a
    compatibility alias for the same composite score; it is not multiplied by
    risk a second time.
    """
    weights = weights or {"population_growth": 0.25, "employment_growth": 0.20, "rent_growth": 0.25, "liquidity": 0.15, "risk": 0.15}
    required = {"population_growth", "employment_growth", "rent_growth", "liquidity", "risk"}
    if not required.issubset(market) or any(not isfinite(float(market[key])) for key in required):
        raise ValueError(f"market must include finite values for {sorted(required)}")
    if any(weight < 0 for weight in weights.values()) or not np.isclose(sum(weights.values()), 1.0):
        raise ValueError("market weights must be non-negative and sum to 1")
    if any(not 0 <= market[key] <= 1 for key in required):
        raise ValueError("market factors must be normalized to [0, 1]")
    score = sum(market[key] * weight for key, weight in weights.items() if key != "risk") + (1 - market["risk"]) * weights["risk"]
    composite = float(np.clip(score * 100, 0, 100))
    return {"score_0_100": composite, "risk_adjusted_score": composite}


def rank_markets(markets: pd.DataFrame) -> pd.DataFrame:
    required = {"market", "population_growth", "employment_growth", "rent_growth", "liquidity", "risk"}
    missing = required.difference(markets.columns)
    if missing:
        raise ValueError(f"Missing market columns: {sorted(missing)}")
    rows = [{"market": row["market"], **market_score(row.to_dict())} for _, row in markets.iterrows()]
    return pd.DataFrame(rows).sort_values(["risk_adjusted_score", "market"], ascending=[False, True]).reset_index(drop=True)


def portfolio_exposure(deals: pd.DataFrame, capital: float) -> pd.DataFrame:
    """Return a naive score-weighted exposure screen.

    This legacy helper is intentionally not the constrained portfolio allocator.
    It filters only on whether an asset's required equity fits available capital,
    then allocates the remaining capital in proportion to non-negative score.
    Callers that need DSCR gates, concentration caps, or allocation reasons must
    use ``src.portfolio.portfolio_allocation`` instead.
    """
    required = {"asset", "equity_required", "risk_adjusted_score"}
    if capital <= 0 or not required.issubset(deals.columns):
        raise ValueError(f"capital must be positive and deals must include {sorted(required)}")
    data = deals.copy()
    data["eligible"] = (data["equity_required"] <= capital).astype(int)
    weights = data["risk_adjusted_score"].clip(lower=0) * data["eligible"]
    data["allocation_weight"] = weights / weights.sum() if weights.sum() else 0.0
    data["recommended_allocation"] = data["allocation_weight"] * capital
    data["allocation_method"] = "naive score-weighted screen"
    return data
