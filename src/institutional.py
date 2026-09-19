"""Institutional real-estate modeling extensions.

This module keeps assumptions explicit and returns inspectable schedules rather than
opaque summary numbers. Monthly cash flows are annualized correctly before being
presented as project or equity IRR.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import pairwise

import numpy as np
import pandas as pd

from .atlasre import _irr
from .validation import integer, non_negative, positive, unit_interval


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


@dataclass(frozen=True)
class WaterfallTier:
    """A hurdle and promote applied to profit above the prior hurdle."""

    hurdle_rate: float
    promote_pct: float
    name: str = "Tier"


def _annualize_monthly_irr(monthly_irr: float) -> float:
    return float((1 + monthly_irr) ** 12 - 1) if np.isfinite(monthly_irr) and monthly_irr > -1 else float("nan")


def _validate_inputs(p: MonthlyDevelopmentInputs) -> None:
    for name in ("land_cost", "hard_cost", "soft_cost", "stabilized_annual_noi", "exit_cap_rate"):
        positive(getattr(p, name), name)
    for name in ("contingency_pct", "interest_rate", "lender_fee_pct", "pref_rate"):
        non_negative(getattr(p, name), name)
    unit_interval(p.max_ltc, "max_ltc", inclusive_one=False)
    unit_interval(p.promote_pct, "promote_pct", inclusive_one=False)
    integer(p.construction_months, "construction_months", minimum=1)
    integer(p.stabilization_months, "stabilization_months", minimum=0)
    integer(p.hold_months_after_stabilization, "hold_months_after_stabilization", minimum=1)
    integer(p.noi_ramp_months, "noi_ramp_months", minimum=1)


def monthly_development_model(p: MonthlyDevelopmentInputs) -> tuple[pd.DataFrame, dict[str, float | list[float]]]:
    """Create a monthly sources-and-uses, capitalized-interest, and exit model."""
    _validate_inputs(p)
    direct_cost = p.land_cost + p.hard_cost + p.soft_cost
    contingency = (p.hard_cost + p.soft_cost) * p.contingency_pct
    total_cost = direct_cost + contingency
    total_months = p.construction_months + p.stabilization_months + p.hold_months_after_stabilization
    months = np.arange(1, total_months + 1)
    in_construction = months <= p.construction_months
    land_draw = np.where(months == 1, p.land_cost, 0.0)
    hard_draw = np.where(in_construction, p.hard_cost / p.construction_months, 0.0)
    soft_draw = np.where(in_construction, p.soft_cost / p.construction_months, 0.0)
    contingency_draw = np.where(in_construction, contingency / p.construction_months, 0.0)
    total_draw = land_draw + hard_draw + soft_draw + contingency_draw
    debt_draw = total_draw * p.max_ltc
    lender_fee = np.where(months == 1, total_cost * p.max_ltc * p.lender_fee_pct, 0.0)
    balance = 0.0
    interest: list[float] = []
    ending_balance: list[float] = []
    rate = p.interest_rate / 12
    for draw in debt_draw:
        # Draws are funded at period start; interest accrues on the post-draw balance.
        monthly_interest = (balance + float(draw)) * rate
        balance += float(draw) + monthly_interest
        interest.append(monthly_interest)
        ending_balance.append(balance)
    income_start = p.construction_months + p.stabilization_months
    operating_months = np.arange(total_months) - income_start + 1
    ramp = np.clip(operating_months / p.noi_ramp_months, 0, 1)
    noi = np.where(operating_months > 0, p.stabilized_annual_noi / 12 * ramp, 0.0)
    exit_value = p.stabilized_annual_noi / p.exit_cap_rate
    sale_proceeds = np.zeros(total_months)
    sale_proceeds[-1] = exit_value
    debt_repayment = np.zeros(total_months)
    debt_repayment[-1] = ending_balance[-1]
    df = pd.DataFrame({
        "month": months,
        "land_draw": land_draw,
        "hard_draw": hard_draw,
        "soft_draw": soft_draw,
        "contingency_draw": contingency_draw,
        "total_draw": total_draw,
        "debt_draw": debt_draw,
        "lender_fee": lender_fee,
        "interest": interest,
        "ending_debt": ending_balance,
        "noi": noi,
        "sale_proceeds": sale_proceeds,
        "debt_repayment": debt_repayment,
    })
    equity_flow = -(df["total_draw"] - df["debt_draw"] + df["lender_fee"]) + df["noi"] + df["sale_proceeds"] - df["debt_repayment"]
    # Project IRR is unlevered: financing cash flows (draws, interest, and
    # repayment) are excluded. Equity IRR below is levered and includes the
    # actual equity contributions and debt repayment.
    project_flow = -df["total_draw"] + df["noi"] + df["sale_proceeds"]
    total_equity = float((df["total_draw"] - df["debt_draw"] + df["lender_fee"]).sum())
    return df, {
        "total_cost": float(total_cost),
        "contingency": float(contingency),
        "debt_commitment": float(debt_draw.sum()),
        "peak_debt_balance": float(max(ending_balance)),
        "equity_required": total_equity,
        "lender_fee": float(lender_fee.sum()),
        "capitalized_interest": float(sum(interest)),
        "exit_value": float(exit_value),
        "project_irr": _annualize_monthly_irr(_irr(project_flow)),
        "equity_irr_pre_waterfall": _annualize_monthly_irr(_irr(equity_flow)),
        "project_cash_flows": project_flow.tolist(),
        "equity_cash_flows": equity_flow.tolist(),
    }


def size_debt(noi: float, cap_rate: float, max_ltv: float, dscr_requirement: float, interest_rate: float, amortization_years: int, value: float) -> dict[str, float]:
    """Size debt from the binding of LTV and amortizing DSCR constraints."""
    for name, number in (("noi", noi), ("cap_rate", cap_rate), ("interest_rate", interest_rate), ("value", value), ("dscr_requirement", dscr_requirement)):
        positive(number, name)
    unit_interval(max_ltv, "max_ltv")
    integer(amortization_years, "amortization_years", minimum=1)
    r = interest_rate / 12
    n = amortization_years * 12
    annual_payment_factor = (r * (1 + r) ** n) / ((1 + r) ** n - 1) * 12
    dscr_loan = (noi / dscr_requirement) / annual_payment_factor
    ltv_loan = value * max_ltv
    loan = min(dscr_loan, ltv_loan)
    return {"property_value": value, "ltv_limit": ltv_loan, "dscr_limit": dscr_loan, "recommended_loan": loan, "implied_ltv": loan / value, "underwriting_dscr": noi / (loan * annual_payment_factor), "binding_constraint": "LTV" if ltv_loan <= dscr_loan else "DSCR"}


def multi_tier_waterfall(equity: float, total_distributable_cash: float, pref_rate: float, hold_years: int, tiers: Iterable[WaterfallTier]) -> dict[str, object]:
    """Distribute cash through return of capital, pref, and ordered promote tiers.

    `total_distributable_cash` is total cash available at exit, including return of
    contributed equity. Each tier's promote applies only to profit above its prior
    hurdle. Any cash above the highest hurdle receives the highest tier promote.
    """
    if equity <= 0 or total_distributable_cash < 0 or hold_years <= 0 or pref_rate < 0:
        raise ValueError("equity, cash, hold years, and pref must be valid")
    ordered = list(tiers)
    if not ordered or any(t.hurdle_rate <= pref_rate or not 0 <= t.promote_pct < 1 for t in ordered):
        raise ValueError("tiers must be non-empty, above pref, and have valid promote percentages")
    if any(left.hurdle_rate >= right.hurdle_rate for left, right in pairwise(ordered)):
        raise ValueError("waterfall tiers must be strictly increasing")
    cash_remaining = float(total_distributable_cash)
    return_of_capital = min(equity, cash_remaining)
    cash_remaining -= return_of_capital
    pref_due = equity * ((1 + pref_rate) ** hold_years - 1)
    lp_pref = min(pref_due, cash_remaining)
    cash_remaining -= lp_pref
    lp_profit = lp_pref
    gp_promote = 0.0
    previous_hurdle_profit = pref_due
    tier_rows: list[dict[str, float | str]] = []
    for index, tier in enumerate(ordered):
        hurdle_profit = equity * ((1 + tier.hurdle_rate) ** hold_years - 1)
        capacity = max(0.0, hurdle_profit - previous_hurdle_profit)
        tier_cash = min(cash_remaining, capacity) if index < len(ordered) - 1 else cash_remaining
        gp_share = tier_cash * tier.promote_pct
        lp_share = tier_cash - gp_share
        lp_profit += lp_share
        gp_promote += gp_share
        cash_remaining -= tier_cash
        tier_rows.append({"tier": tier.name, "hurdle_rate": tier.hurdle_rate, "promote_pct": tier.promote_pct, "tier_cash": tier_cash, "lp_share": lp_share, "gp_share": gp_share})
        previous_hurdle_profit = hurdle_profit
    lp_total = return_of_capital + lp_profit
    gp_total = gp_promote
    return {"return_of_capital": return_of_capital, "lp_preferred_return": lp_pref, "lp_profit": lp_profit, "gp_promote": gp_promote, "lp_total_distribution": lp_total, "gp_total_distribution": gp_total, "distribution_check": lp_total + gp_total, "unallocated_cash": cash_remaining, "tiers": tier_rows, "lp_cash_flows": [-equity] + [0.0] * (hold_years - 1) + [lp_total], "gp_cash_flows": [0.0] * hold_years + [gp_total]}


def lp_gp_waterfall(equity: float, distributable_profit: float, pref_rate: float, hold_years: int, promote_pct: float) -> dict[str, float]:
    """Backward-compatible single-promote wrapper using total proceeds semantics."""
    result = multi_tier_waterfall(equity, equity + distributable_profit, pref_rate, hold_years, [WaterfallTier(pref_rate + 0.0001, promote_pct, "Promote")])
    return {key: value for key, value in result.items() if isinstance(value, (float, int))}


def assumption_quality(inputs: dict[str, float | str | int]) -> pd.DataFrame:
    """Create a review checklist so assumptions are not mistaken for facts."""
    return pd.DataFrame([{"assumption": name, "value": value, "status": "REVIEW REQUIRED", "source": "Not supplied; illustrative input"} for name, value in inputs.items()])


__all__ = ["MonthlyDevelopmentInputs", "WaterfallTier", "assumption_quality", "lp_gp_waterfall", "monthly_development_model", "multi_tier_waterfall", "size_debt"]
