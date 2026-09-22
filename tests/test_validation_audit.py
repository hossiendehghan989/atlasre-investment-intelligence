from dataclasses import replace
from datetime import date

import numpy as np
import pandas as pd
import pytest

from src.atlasre import DealInputs
from src.committee_analytics import sensitivity_table
from src.debt import DebtTerms
from src.governance import versioned_assumptions
from src.institutional import MonthlyDevelopmentInputs, size_debt
from src.lease import Lease, LeaseUnderwritingInputs
from src.portfolio import portfolio_allocation


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_lease_rejects_non_finite_rates(bad):
    with pytest.raises(ValueError):
        Lease("Tenant", date(2025, 1, 1), date(2025, 12, 31), bad).validate()


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf, 12.5])
def test_lease_inputs_reject_invalid_month_counters(bad):
    inputs = LeaseUnderwritingInputs(
        (Lease("Tenant", date(2025, 1, 1), date(2025, 12, 31), 120_000),), date(2025, 1, 1), bad
    )
    with pytest.raises(ValueError):
        inputs.validate()


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf, 12.5])
def test_debt_terms_reject_invalid_counters_or_rates(bad):
    terms = (
        replace(DebtTerms(), annual_rate=bad)
        if isinstance(bad, float) and not np.isfinite(bad)
        else replace(DebtTerms(), term_months=bad)
    )
    with pytest.raises(ValueError):
        terms.validate()


@pytest.mark.parametrize(
    "field", ["construction_months", "stabilization_months", "hold_months_after_stabilization", "noi_ramp_months"]
)
def test_development_rejects_fractional_counters(field):
    inputs = MonthlyDevelopmentInputs(5_000_000, 12_000_000, 2_500_000)
    with pytest.raises(ValueError):
        from src.institutional import monthly_development_model

        monthly_development_model(replace(inputs, **{field: 1.5}))


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf, -0.1])
def test_public_numeric_boundaries_reject_bad_values(bad):
    deals = pd.DataFrame(
        [{"asset": "A", "equity_required": 100, "risk_adjusted_score": 1, "levered_irr": 0.1, "minimum_dscr": 1.5}]
    )
    with pytest.raises(ValueError):
        portfolio_allocation(deals, 1_000, min_dscr=bad)
    with pytest.raises(ValueError):
        size_debt(100, 0.06, 0.6, bad, 0.07, 25, 1_000)
    with pytest.raises(ValueError):
        sensitivity_table(DealInputs(1_000, 100), "exit_cap_rate", [bad])


def test_governance_rejects_fractional_versions():
    with pytest.raises(ValueError):
        versioned_assumptions({"price": (100, "USD")}, version=1.5)
