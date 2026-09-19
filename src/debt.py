"""Deterministic debt schedules and constraint-based sizing."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DebtTerms:
    annual_rate: float = 0.07
    amortization_years: int = 25
    term_months: int = 60
    interest_only_months: int = 0
    lender_fee_pct: float = 0.01


def _payment_factor(annual_rate: float, amortization_years: int) -> float:
    if annual_rate < 0 or amortization_years <= 0:
        raise ValueError("annual_rate must be non-negative and amortization_years positive")
    if annual_rate == 0:
        return 12 / (amortization_years * 12)
    r = annual_rate / 12
    n = amortization_years * 12
    return float(r * (1 + r) ** n / ((1 + r) ** n - 1) * 12)


def monthly_debt_schedule(principal: float, terms: DebtTerms, draws: list[float] | None = None, noi: list[float] | None = None) -> pd.DataFrame:
    """Build a monthly balance, interest, principal and DSCR schedule.

    Draws are funded at the start of each period. During the IO period only interest
    is paid. At term maturity, the remaining balance is shown as a balloon payoff.
    """
    if principal < 0 or terms.term_months <= 0 or terms.interest_only_months > terms.term_months:
        raise ValueError("principal must be non-negative and term/IO months must be valid")
    draws = draws or [0.0] * terms.term_months
    if len(draws) != terms.term_months:
        raise ValueError("draws length must equal term_months")
    if noi is not None and len(noi) != terms.term_months:
        raise ValueError("noi length must equal term_months")
    monthly_payment = principal * _payment_factor(terms.annual_rate, terms.amortization_years) / 12 if principal else 0.0
    rate = terms.annual_rate / 12
    balance = float(principal)
    rows: list[dict[str, float | int]] = []
    for period in range(1, terms.term_months + 1):
        draw = float(draws[period - 1])
        beginning = balance
        interest = (beginning + draw) * rate
        balance += draw
        scheduled_payment = interest if period <= terms.interest_only_months else min(monthly_payment, balance + interest)
        principal_paid = max(0.0, scheduled_payment - interest)
        balance = max(0.0, balance - principal_paid)
        balloon = balance if period == terms.term_months else 0.0
        dscr = ((float(noi[period - 1]) / 12) / scheduled_payment) if noi is not None and scheduled_payment > 0 else np.nan
        rows.append({"period": period, "beginning_balance": beginning, "draw": draw, "interest": interest, "scheduled_payment": scheduled_payment, "principal_paid": principal_paid, "ending_balance": balance, "balloon_payoff": balloon, "dscr": dscr})
    return pd.DataFrame(rows)


def size_debt_from_constraints(noi: list[float], property_value: float, max_ltv: float, min_dscr: float, terms: DebtTerms) -> dict[str, float]:
    """Size the lesser of LTV and DSCR capacity using the weakest NOI period."""
    if not noi or min(noi) <= 0 or property_value <= 0 or not 0 < max_ltv <= 1 or min_dscr <= 0:
        raise ValueError("NOI, property_value, LTV, and DSCR inputs must be valid")
    dsf = _payment_factor(terms.annual_rate, terms.amortization_years)
    annual_debt_service_capacity = min(noi) / min_dscr
    dscr_limit = annual_debt_service_capacity / dsf
    ltv_limit = property_value * max_ltv
    recommended = min(dscr_limit, ltv_limit)
    return {"ltv_limit": float(ltv_limit), "dscr_limit": float(dscr_limit), "recommended_loan": float(recommended), "implied_ltv": float(recommended / property_value), "binding_constraint": "LTV" if ltv_limit <= dscr_limit else "DSCR", "annual_debt_service": float(recommended * dsf)}


__all__ = ["DebtTerms", "monthly_debt_schedule", "size_debt_from_constraints"]

