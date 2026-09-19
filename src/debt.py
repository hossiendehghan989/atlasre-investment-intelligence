"""Deterministic debt schedules and constraint-based sizing."""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .validation import integer, non_negative, unit_interval


@dataclass(frozen=True)
class DebtTerms:
    annual_rate: float = 0.07
    amortization_years: int = 25
    term_months: int = 60
    interest_only_months: int = 0
    lender_fee_pct: float = 0.01

    def validate(self) -> None:
        non_negative(self.annual_rate, "annual_rate")
        unit_interval(self.lender_fee_pct, "lender_fee_pct")
        integer(self.amortization_years, "amortization_years", minimum=1)
        integer(self.term_months, "term_months", minimum=1)
        integer(self.interest_only_months, "interest_only_months", minimum=0)
        if not 0 <= self.interest_only_months <= self.term_months:
            raise ValueError("interest_only_months must be within the loan term")
        if not 0 <= self.lender_fee_pct <= 1:
            raise ValueError("lender_fee_pct must be between 0 and 1")


def _payment_factor(annual_rate: float, amortization_years: int) -> float:
    if annual_rate < 0 or amortization_years <= 0:
        raise ValueError("annual_rate must be non-negative and amortization_years positive")
    if annual_rate == 0:
        return 1 / amortization_years
    r = annual_rate / 12
    n = amortization_years * 12
    return float(r * (1 + r) ** n / ((1 + r) ** n - 1) * 12)


def monthly_debt_schedule(principal: float, terms: DebtTerms, draws: list[float] | None = None, noi: list[float] | None = None) -> pd.DataFrame:
    """Build a monthly balance, interest, principal, DSCR, and balloon schedule."""
    terms.validate()
    non_negative(principal, "principal")
    draw_values = [0.0] * terms.term_months if draws is None else list(draws)
    if len(draw_values) != terms.term_months or any(not math.isfinite(float(value)) or value < 0 for value in draw_values):
        raise ValueError("draws must contain one finite non-negative value per term month")
    noi_values = None if noi is None else list(noi)
    if noi_values is not None and (len(noi_values) != terms.term_months or any(not math.isfinite(float(value)) or value < 0 for value in noi_values)):
        raise ValueError("NOI must contain one finite non-negative value per term month")
    monthly_payment = principal * _payment_factor(terms.annual_rate, terms.amortization_years) / 12 if principal else 0.0
    rate = terms.annual_rate / 12
    balance = float(principal)
    rows: list[dict[str, float | int]] = []
    for period, draw in enumerate(draw_values, start=1):
        beginning = balance
        interest = (beginning + draw) * rate
        balance += draw
        scheduled_payment = interest if period <= terms.interest_only_months else min(monthly_payment, balance + interest)
        principal_paid = max(0.0, min(scheduled_payment - interest, balance))
        balance = max(0.0, balance - principal_paid)
        balloon = balance if period == terms.term_months else 0.0
        dscr = ((noi_values[period - 1] / 12) / scheduled_payment) if noi_values is not None and scheduled_payment > 0 else np.nan
        rows.append({"period": period, "beginning_balance": beginning, "draw": draw, "interest": interest, "scheduled_payment": scheduled_payment, "principal_paid": principal_paid, "ending_balance": balance, "balloon_payoff": balloon, "dscr": dscr})
    return pd.DataFrame(rows)


def size_debt_from_constraints(noi: list[float], property_value: float, max_ltv: float, min_dscr: float, terms: DebtTerms) -> dict[str, float | str]:
    """Size the lesser of LTV and DSCR capacity using the weakest NOI period."""
    terms.validate()
    noi_values = list(noi)
    if not noi_values or any(not math.isfinite(float(value)) or value <= 0 for value in noi_values) or not math.isfinite(property_value) or property_value <= 0 or not 0 < max_ltv <= 1 or min_dscr <= 0:
        raise ValueError("NOI, property value, LTV, and DSCR inputs must be valid")
    dsf = _payment_factor(terms.annual_rate, terms.amortization_years)
    dscr_limit = (min(noi_values) / min_dscr) / dsf
    ltv_limit = property_value * max_ltv
    recommended = min(dscr_limit, ltv_limit)
    return {"ltv_limit": float(ltv_limit), "dscr_limit": float(dscr_limit), "recommended_loan": float(recommended), "implied_ltv": float(recommended / property_value), "binding_constraint": "LTV" if ltv_limit <= dscr_limit else "DSCR", "annual_debt_service": float(recommended * dsf)}


__all__ = ["DebtTerms", "monthly_debt_schedule", "size_debt_from_constraints"]
