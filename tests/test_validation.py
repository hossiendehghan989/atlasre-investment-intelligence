from dataclasses import replace
from datetime import date

import numpy as np
import pandas as pd
import pytest

from src.atlasre import DealInputs, market_score, underwrite_deal
from src.committee_analytics import sensitivity_table
from src.debt import DebtTerms, monthly_debt_schedule
from src.governance import (
    audit_event,
    default_lineage,
    lineage_record,
    model_run_fingerprint,
    verify_audit_chain,
    versioned_assumptions,
)
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


# Cross-module validation edge cases


def test_zero_rate_debt_has_no_interest_and_deterministic_principal():
    schedule = monthly_debt_schedule(120_000, DebtTerms(annual_rate=0, amortization_years=10, term_months=12))
    assert schedule["interest"].sum() == pytest.approx(0)
    assert schedule["principal_paid"].sum() == pytest.approx(12_000)


def test_invalid_deal_and_market_inputs_fail_loudly():
    with pytest.raises(ValueError, match="growth"):
        underwrite_deal(DealInputs(10_000_000, 650_000, annual_noi_growth=-1.0))
    with pytest.raises(ValueError, match="normalized"):
        market_score(
            {"population_growth": 2, "employment_growth": 0.5, "rent_growth": 0.5, "liquidity": 0.5, "risk": 0.5}
        )


def test_governance_rejects_malformed_audit_and_tracks_version():
    first = audit_event("created", "analyst", {"deal": "A"})
    assert verify_audit_chain([first])
    malformed = {"action": "created"}
    assert not verify_audit_chain([malformed])
    register = versioned_assumptions(
        {"exit_cap": (0.06, "%")},
        deal_id="A",
        version=3,
        verified_by="reviewer",
        supersedes={"exit_cap": "A:exit_cap:v2"},
    )
    assert register.iloc[0]["assumption_id"] == "A:exit_cap:v3"
    assert register.iloc[0]["status"] == "VERIFIED"
    assert register.iloc[0]["supersedes"] == "A:exit_cap:v2"
    assert len(model_run_fingerprint("v1", register.rename(columns={"assumption_id": "id"}), default_lineage())) == 64


def test_lineage_requires_inputs_and_portfolio_is_repeatable():
    with pytest.raises(ValueError, match="lineage"):
        lineage_record("irr", 0.1, [], "method")
    deals = pd.DataFrame(
        [
            {"asset": "A", "equity_required": 100, "risk_adjusted_score": 80, "levered_irr": 0.15, "minimum_dscr": 1.3},
            {"asset": "B", "equity_required": 100, "risk_adjusted_score": 60, "levered_irr": 0.14, "minimum_dscr": 1.3},
        ]
    )
    left = portfolio_allocation(deals, 1_000, max_single_asset_pct=0.5)
    right = portfolio_allocation(deals, 1_000, max_single_asset_pct=0.5)
    assert left["recommended_allocation"].equals(right["recommended_allocation"])
