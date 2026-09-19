"""Small, deterministic lease-level underwriting foundation.

The lease path is intentionally additive: the existing simplified deal engine
remains the default. This module converts a validated rent roll into monthly
contract rent, vacancy, and NOI proxies that can be challenged line by line.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import calendar
import math
from typing import Literal

import pandas as pd


CreditQuality = Literal["STRONG", "AVERAGE", "WEAK", "UNKNOWN"]


@dataclass(frozen=True)
class Lease:
    tenant: str
    start: date
    end: date
    annual_rent: float
    annual_escalation: float = 0.0
    vacancy_assumption: float = 0.0
    credit_quality: CreditQuality = "UNKNOWN"

    def validate(self) -> None:
        if not self.tenant.strip() or self.end < self.start:
            raise ValueError("lease tenant and dates must be valid")
        if not math.isfinite(self.annual_rent) or self.annual_rent < 0:
            raise ValueError("annual_rent must be finite and non-negative")
        if not -1 < self.annual_escalation <= 1 or not 0 <= self.vacancy_assumption <= 1:
            raise ValueError("escalation must be above -100% and vacancy must be in [0, 1]")
        if self.credit_quality not in {"STRONG", "AVERAGE", "WEAK", "UNKNOWN"}:
            raise ValueError("credit_quality is not recognized")


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _month_index(value: date) -> int:
    return value.year * 12 + value.month


def lease_rollup(leases: list[Lease], start: date, months: int, operating_expense_ratio: float = 0.0) -> pd.DataFrame:
    """Aggregate lease contract rent, vacancy, and NOI into monthly periods."""
    if not leases or months <= 0 or not 0 <= operating_expense_ratio < 1:
        raise ValueError("leases, months, and operating expense ratio must be valid")
    for lease in leases:
        lease.validate()
    first = _month_start(start)
    rows: list[dict[str, object]] = []
    for offset in range(months):
        period = first.replace(year=(first.year * 12 + first.month - 1 + offset) // 12, month=(first.year * 12 + first.month - 1 + offset) % 12 + 1)
        contract_rent = 0.0
        vacancy = 0.0
        active_count = 0
        expiring_count = 0
        for lease in leases:
            if lease.start <= period <= lease.end:
                years_elapsed = max(0, (_month_index(period) - _month_index(_month_start(lease.start))) // 12)
                gross = lease.annual_rent * (1 + lease.annual_escalation) ** years_elapsed / 12
                contract_rent += gross
                vacancy += gross * lease.vacancy_assumption
                active_count += 1
                if _month_index(lease.end) == _month_index(period):
                    expiring_count += 1
        effective_rent = contract_rent - vacancy
        operating_expenses = effective_rent * operating_expense_ratio
        rows.append({"period": period, "active_leases": active_count, "expiring_leases": expiring_count, "contract_rent": contract_rent, "vacancy": vacancy, "effective_rent": effective_rent, "operating_expenses": operating_expenses, "noi": effective_rent - operating_expenses})
    return pd.DataFrame(rows)


def lease_summary(leases: list[Lease]) -> pd.DataFrame:
    """Return an executive rent-roll summary without hiding lease-level inputs."""
    for lease in leases:
        lease.validate()
    return pd.DataFrame([{"tenant": lease.tenant, "start": lease.start.isoformat(), "end": lease.end.isoformat(), "annual_rent": lease.annual_rent, "annual_escalation": lease.annual_escalation, "vacancy_assumption": lease.vacancy_assumption, "credit_quality": lease.credit_quality} for lease in leases])


def illustrative_rent_roll() -> list[Lease]:
    """Return clearly labeled demo leases for the dashboard, never verified data."""
    return [
        Lease("Illustrative anchor tenant", date(2025, 1, 1), date(2029, 12, 31), 420_000, .02, .02, "STRONG"),
        Lease("Illustrative local tenant", date(2025, 7, 1), date(2027, 6, 30), 180_000, .03, .08, "AVERAGE"),
    ]


__all__ = ["CreditQuality", "Lease", "lease_rollup", "lease_summary", "illustrative_rent_roll"]
