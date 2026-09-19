"""Institutional-style real-estate underwriting extensions."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .atlasre import _irr


@dataclass(frozen=True)
class MonthlyDevelopmentInputs:
    land_cost: float
    hard_cost: float
    soft_cost: float
    contingency_pct: float = 0.05
    construction_months: int = 24
    stabilization_months: int = 12
    hold_months_after_stabilization: int = 36
    stabilized_annual_noi: float = 1_800_000
    noi_ramp_months: int = 12
    exit_cap_rate: float = 0.06
    max_ltc: float = 0.60
    interest_rate: float = 0.07
    lender_fee_pct: float = 0.01
    pref_rate: float = 0.08
    promote_pct: float = 0.20


def _validate_inputs(p: MonthlyDevelopmentInputs) -> None:
    values = [p.land_cost, p.hard_cost, p.soft_cost, p.stabilized_annual_noi]
    if min(values) <= 0 or p.construction_months <= 0 or p.hold_months_after_stabilization <= 0:
        raise ValueError("costs, NOI, construction months, and hold months must be positive")
    if not 0 <= p.max_ltc < 1 or not 0 <= p.promote_pct < 1:
        raise ValueError("max_ltc and promote_pct must be between 0 and 1")


def monthly_development_model(p: MonthlyDevelopmentInputs) -> tuple[pd.DataFrame, dict[str, float | list[float]]]:
    """Create a monthly sources-and-uses and project cash-flow model."""
    _validate_inputs(p)
    total_cost_before_contingency = p.land_cost + p.hard_cost + p.soft_cost
    contingency = (p.hard_cost + p.soft_cost) * p.contingency_pct
    total_cost = total_cost_before_contingency + contingency
    total_months = p.construction_months + p.stabilization_months + p.hold_months_after_stabilization
    months = np.arange(1, total_months + 1)
    hard_draw = np.where(months <= p.construction_months, p.hard_cost / p.construction_months, 0.0)
    soft_draw = np.where(months <= p.construction_months, p.soft_cost / p.construction_months, 0.0)
    land_draw = np.where(months == 1, p.land_cost, 0.0)
    contingency_draw = np.where(months <= p.construction_months, contingency / p.construction_months, 0.0)
    total_draw = land_draw + hard_draw + soft_draw + contingency_draw
    debt = total_cost * p.max_ltc
    debt_draw = total_draw * p.max_ltc
    balance = 0.0
    interest = []
    ending_balance = []
    for draw in debt_draw:
        monthly_interest = balance * p.interest_rate / 12
        balance += draw + monthly_interest
        interest.append(monthly_interest)
        ending_balance.append(balance)
    noi = np.zeros(total_months)
    income_start = p.construction_months + p.stabilization_months
    operating_months = np.arange(total_months) - income_start + 1
    ramp = np.clip(operating_months / max(p.noi_ramp_months, 1), 0, 1)
    noi = p.stabilized_annual_noi / 12 * ramp
    noi[:income_start] = 0
    exit_value = p.stabilized_annual_noi / p.exit_cap_rate
    exit_month = total_months
    sale_proceeds = np.zeros(total_months)
    sale_proceeds[-1] = exit_value
    debt_repayment = np.zeros(total_months)
    debt_repayment[-1] = ending_balance[-1]
    df = pd.DataFrame({"month": months, "land_draw": land_draw, "hard_draw": hard_draw, "soft_draw": soft_draw, "contingency_draw": contingency_draw, "total_draw": total_draw, "debt_draw": debt_draw, "interest": interest, "ending_debt": ending_balance, "noi": noi, "sale_proceeds": sale_proceeds, "debt_repayment": debt_repayment})
    equity_flow = -(df["total_draw"] - df["debt_draw"]) + df["noi"] + df["sale_proceeds"] - df["debt_repayment"]
    project_flow = -df["total_draw"] + df["noi"] + df["sale_proceeds"] - df["interest"] - df["debt_repayment"]
    total_equity = float((df["total_draw"] - df["debt_draw"]).sum())
    return df, {"total_cost": float(total_cost), "contingency": float(contingency), "debt_commitment": float(debt), "equity_required": total_equity, "capitalized_interest": float(sum(interest)), "exit_value": float(exit_value), "project_irr": _irr(project_flow), "equity_irr_pre_waterfall": _irr(equity_flow), "equity_cash_flows": equity_flow.tolist()}


def size_debt(noi: float, cap_rate: float, max_ltv: float, dscr_requirement: float, interest_rate: float, amortization_years: int, value: float) -> dict[str, float]:
    """Size debt from the binding of LTV and DSCR constraints."""
    if min(noi, cap_rate, interest_rate, value) <= 0 or dscr_requirement <= 0:
        raise ValueError("NOI, cap rate, interest rate, value, and DSCR must be positive")
    annual_debt_service_capacity = noi / dscr_requirement
    r = interest_rate / 12
    n = amortization_years * 12
    annual_payment_factor = (r * (1 + r) ** n) / ((1 + r) ** n - 1) * 12
    dscr_loan = annual_debt_service_capacity / annual_payment_factor
    ltv_loan = value * max_ltv
    loan = min(dscr_loan, ltv_loan)
    return {"property_value": value, "ltv_limit": ltv_loan, "dscr_limit": dscr_loan, "recommended_loan": loan, "implied_ltv": loan / value, "underwriting_dscr": noi / (loan * annual_payment_factor)}


def lp_gp_waterfall(equity: float, distributable_profit: float, pref_rate: float, hold_years: int, promote_pct: float) -> dict[str, float]:
    """Apply return of capital, preferred return, then promote."""
    if min(equity, hold_years) <= 0 or not 0 <= promote_pct < 1:
        raise ValueError("equity and hold_years must be positive; promote must be valid")
    pref = equity * ((1 + pref_rate) ** hold_years - 1)
    return_of_capital = min(equity, equity + distributable_profit)
    residual = max(distributable_profit - pref, 0)
    gp_promote = residual * promote_pct
    lp_profit = min(distributable_profit, pref) + residual - gp_promote
    return {"return_of_capital": return_of_capital, "lp_preferred_return": min(distributable_profit, pref), "gp_promote": gp_promote, "lp_profit": lp_profit, "lp_total_distribution": return_of_capital + lp_profit, "gp_total_distribution": gp_promote, "distribution_check": return_of_capital + distributable_profit}


def assumption_quality(inputs: dict[str, float | str | int]) -> pd.DataFrame:
    """Create a review checklist so assumptions are not mistaken for facts."""
    rows = []
    for name, value in inputs.items():
        rows.append({"assumption": name, "value": value, "status": "REVIEW REQUIRED", "source": "Not supplied; illustrative input"})
    return pd.DataFrame(rows)
