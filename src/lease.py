"""Deterministic lease-level underwriting primitives.

The lease path is additive. The simplified annual-NOI path remains the default;
callers must opt into deriving NOI from a rent roll. Each monthly output retains
contract rent, economic vacancy, rollover vacancy, and rollover rent separately
so a reviewer can challenge the assumptions line by line.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
import math
from typing import Any, Literal

import pandas as pd

from .atlasre import DealInputs, underwrite_deal


CreditQuality = Literal["STRONG", "AVERAGE", "WEAK", "UNKNOWN"]


@dataclass(frozen=True)
class Lease:
    """A simple contractual lease with an optional deterministic rollover path.

    ``rollover_vacancy_months=None`` means that no replacement tenant is assumed
    after expiry. When a non-negative number is provided, a replacement lease is
    assumed to start after that many vacant months at the stated rent change.
    This is an explicit simplifying assumption, not an occupancy forecast.
    """

    tenant: str
    start: date
    end: date
    annual_rent: float
    annual_escalation: float = 0.0
    vacancy_assumption: float = 0.0
    credit_quality: CreditQuality = "UNKNOWN"
    rollover_vacancy_months: int | None = None
    rollover_rent_change: float = 0.0

    def validate(self) -> None:
        if not self.tenant.strip() or self.end < self.start:
            raise ValueError("lease tenant and dates must be valid")
        if not math.isfinite(self.annual_rent) or self.annual_rent < 0:
            raise ValueError("annual_rent must be finite and non-negative")
        if not math.isfinite(self.annual_escalation) or not math.isfinite(self.vacancy_assumption) or not math.isfinite(self.rollover_rent_change):
            raise ValueError("lease rates must be finite")
        if not -1 < self.annual_escalation <= 1 or not 0 <= self.vacancy_assumption <= 1:
            raise ValueError("escalation must be above -100% and vacancy must be in [0, 1]")
        if not -1 < self.rollover_rent_change <= 1:
            raise ValueError("rollover rent change must be above -100% and at most 100%")
        if self.rollover_vacancy_months is not None and (not isinstance(self.rollover_vacancy_months, int) or self.rollover_vacancy_months < 0):
            raise ValueError("rollover_vacancy_months must be a non-negative integer or None")
        if self.credit_quality not in {"STRONG", "AVERAGE", "WEAK", "UNKNOWN"}:
            raise ValueError("credit_quality is not recognized")


@dataclass(frozen=True)
class LeaseUnderwritingInputs:
    """Optional rent-roll inputs used to derive annual NOI for the core engine."""

    leases: tuple[Lease, ...]
    start: date
    months: int = 12
    operating_expense_ratio: float = 0.0

    def validate(self) -> None:
        if not self.leases or self.months <= 0 or not 0 <= self.operating_expense_ratio < 1:
            raise ValueError("leases, months, and operating expense ratio must be valid")
        for lease in self.leases:
            lease.validate()


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _month_index(value: date) -> int:
    return value.year * 12 + value.month


def _period_from_offset(first: date, offset: int) -> date:
    absolute_month = first.year * 12 + first.month - 1 + offset
    return first.replace(year=absolute_month // 12, month=absolute_month % 12 + 1)


def _annual_contract_rent(lease: Lease, period_index: int) -> float:
    start_index = _month_index(_month_start(lease.start))
    years_elapsed = max(0, (period_index - start_index) // 12)
    return lease.annual_rent * (1 + lease.annual_escalation) ** years_elapsed


def _rollover_state(lease: Lease, period_index: int) -> tuple[float, float, bool]:
    """Return replacement rent, named rollover vacancy, and post-expiry activity."""
    if lease.rollover_vacancy_months is None:
        return 0.0, 0.0, False
    end_index = _month_index(_month_start(lease.end))
    first_after_expiry = end_index + 1
    rollover_start = first_after_expiry + lease.rollover_vacancy_months
    annual_at_expiry = _annual_contract_rent(lease, end_index)
    if first_after_expiry <= period_index < rollover_start:
        return 0.0, annual_at_expiry / 12, True
    if period_index >= rollover_start:
        years_elapsed = (period_index - rollover_start) // 12
        replacement_annual_rent = annual_at_expiry * (1 + lease.rollover_rent_change) * (1 + lease.annual_escalation) ** years_elapsed
        return replacement_annual_rent / 12, 0.0, True
    return 0.0, 0.0, False


def lease_rollup(leases: list[Lease] | tuple[Lease, ...], start: date, months: int, operating_expense_ratio: float = 0.0) -> pd.DataFrame:
    """Aggregate a rent roll into transparent monthly rent, vacancy, and NOI.

    The schedule operates at monthly granularity. A lease beginning or ending
    within a month is included for that contractual month; day-count proration is
    intentionally outside this foundation's scope.
    """
    input_leases = tuple(leases)
    LeaseUnderwritingInputs(input_leases, start, months, operating_expense_ratio).validate()
    first = _month_start(start)
    rows: list[dict[str, object]] = []
    for offset in range(months):
        period = _period_from_offset(first, offset)
        period_index = _month_index(period)
        contract_rent = 0.0
        rollover_rent = 0.0
        vacancy = 0.0
        rollover_vacancy = 0.0
        active_count = 0
        expiring_count = 0
        rollover_count = 0
        for lease in input_leases:
            start_index = _month_index(_month_start(lease.start))
            end_index = _month_index(_month_start(lease.end))
            if start_index <= period_index <= end_index:
                gross = _annual_contract_rent(lease, period_index) / 12
                contract_rent += gross
                vacancy += gross * lease.vacancy_assumption
                active_count += 1
                if period_index == end_index:
                    expiring_count += 1
            elif period_index > end_index:
                replacement_rent, named_vacancy, is_rollover = _rollover_state(lease, period_index)
                rollover_rent += replacement_rent
                rollover_vacancy += named_vacancy
                rollover_count += int(is_rollover)
        potential_rent = contract_rent + rollover_rent + rollover_vacancy
        effective_rent = contract_rent + rollover_rent - vacancy
        operating_expenses = effective_rent * operating_expense_ratio
        rows.append({
            "period": period,
            "active_leases": active_count,
            "expiring_leases": expiring_count,
            "rollover_leases": rollover_count,
            "contract_rent": contract_rent,
            "rollover_rent": rollover_rent,
            "vacancy": vacancy,
            "rollover_vacancy": rollover_vacancy,
            "potential_rent": potential_rent,
            "effective_rent": effective_rent,
            "operating_expenses": operating_expenses,
            "noi": effective_rent - operating_expenses,
        })
    return pd.DataFrame(rows)


def annual_lease_summary(monthly_rollup: pd.DataFrame) -> pd.DataFrame:
    """Aggregate a validated monthly roll-up into calendar-year NOI evidence."""
    required = {
        "period", "contract_rent", "rollover_rent", "vacancy", "rollover_vacancy",
        "potential_rent", "effective_rent", "operating_expenses", "noi",
    }
    missing = required.difference(monthly_rollup.columns)
    if missing:
        raise ValueError(f"monthly rollup must include {sorted(required)}")
    data = monthly_rollup.copy()
    data["year"] = pd.to_datetime(data["period"]).dt.year
    columns = [
        "contract_rent", "rollover_rent", "vacancy", "rollover_vacancy", "potential_rent",
        "effective_rent", "operating_expenses", "noi",
    ]
    return data.groupby("year", as_index=False)[columns].sum()


def lease_derived_annual_noi(inputs: LeaseUnderwritingInputs) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    """Return the rent roll, annual summary, and annualized forward NOI.

    NOI is derived from the full supplied horizon and annualized when the horizon
    is shorter or longer than 12 months. The averaging rule is explicit so a
    reviewer can reproduce the number from ``lease_monthly_rollup.csv``.
    """
    inputs.validate()
    monthly = lease_rollup(inputs.leases, inputs.start, inputs.months, inputs.operating_expense_ratio)
    annual = annual_lease_summary(monthly)
    annualized_noi = float(monthly["noi"].sum() / inputs.months * 12)
    return monthly, annual, annualized_noi


def underwrite_with_lease_roll(deal: DealInputs, inputs: LeaseUnderwritingInputs) -> dict[str, Any]:
    """Run the existing acquisition engine using an explicit lease-derived NOI.

    The original ``DealInputs`` instance is not mutated. This preserves the
    simplified path while making the optional rent-roll bridge inspectable.
    """
    monthly, annual, annualized_noi = lease_derived_annual_noi(inputs)
    lease_derived_deal = replace(deal, annual_noi=annualized_noi)
    return {
        "lease_monthly_rollup": monthly,
        "lease_annual_summary": annual,
        "lease_derived_annual_noi": annualized_noi,
        "underwriting": underwrite_deal(lease_derived_deal),
        "deal_inputs": lease_derived_deal,
    }


def lease_summary(leases: list[Lease] | tuple[Lease, ...]) -> pd.DataFrame:
    """Return an executive rent-roll summary without hiding lease-level inputs."""
    input_leases = tuple(leases)
    for lease in input_leases:
        lease.validate()
    return pd.DataFrame([
        {
            "tenant": lease.tenant,
            "start": lease.start.isoformat(),
            "end": lease.end.isoformat(),
            "annual_rent": lease.annual_rent,
            "annual_escalation": lease.annual_escalation,
            "vacancy_assumption": lease.vacancy_assumption,
            "rollover_vacancy_months": lease.rollover_vacancy_months,
            "rollover_rent_change": lease.rollover_rent_change,
            "credit_quality": lease.credit_quality,
        }
        for lease in input_leases
    ])


def illustrative_rent_roll() -> list[Lease]:
    """Return clearly labeled demo leases for the dashboard, never verified data."""
    return [
        Lease("Illustrative anchor tenant", date(2025, 1, 1), date(2029, 12, 31), 420_000, .02, .02, "STRONG", rollover_vacancy_months=3, rollover_rent_change=.01),
        Lease("Illustrative local tenant", date(2025, 7, 1), date(2027, 6, 30), 180_000, .03, .08, "AVERAGE", rollover_vacancy_months=6, rollover_rent_change=-.05),
    ]


__all__ = [
    "CreditQuality", "Lease", "LeaseUnderwritingInputs", "lease_rollup", "annual_lease_summary",
    "lease_derived_annual_noi", "underwrite_with_lease_roll", "lease_summary", "illustrative_rent_roll",
]
