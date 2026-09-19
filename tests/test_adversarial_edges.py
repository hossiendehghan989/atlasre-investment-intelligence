import pandas as pd
import pytest

from src.atlasre import DealInputs, market_score, underwrite_deal
from src.debt import DebtTerms, monthly_debt_schedule
from src.governance import audit_event, lineage_record, verify_audit_chain, versioned_assumptions
from src.portfolio import portfolio_allocation


def test_zero_rate_debt_has_no_interest_and_deterministic_principal():
    schedule = monthly_debt_schedule(120_000, DebtTerms(annual_rate=0, amortization_years=10, term_months=12))
    assert schedule["interest"].sum() == pytest.approx(0)
    assert schedule["principal_paid"].sum() == pytest.approx(12_000)


def test_invalid_deal_and_market_inputs_fail_loudly():
    with pytest.raises(ValueError, match="growth"):
        underwrite_deal(DealInputs(10_000_000, 650_000, annual_noi_growth=-1.0))
    with pytest.raises(ValueError, match="normalized"):
        market_score({"population_growth": 2, "employment_growth": .5, "rent_growth": .5, "liquidity": .5, "risk": .5})


def test_governance_rejects_malformed_audit_and_tracks_version():
    first = audit_event("created", "analyst", {"deal": "A"})
    assert verify_audit_chain([first])
    malformed = {"action": "created"}
    assert not verify_audit_chain([malformed])
    register = versioned_assumptions({"exit_cap": (.06, "%")}, deal_id="A", version=3, verified_by="reviewer")
    assert register.iloc[0]["assumption_id"] == "A:exit_cap:v3"
    assert register.iloc[0]["status"] == "VERIFIED"


def test_lineage_requires_inputs_and_portfolio_is_repeatable():
    with pytest.raises(ValueError, match="lineage"):
        lineage_record("irr", 0.1, [], "method")
    deals = pd.DataFrame([
        {"asset": "A", "equity_required": 100, "risk_adjusted_score": 80, "levered_irr": .15, "minimum_dscr": 1.3},
        {"asset": "B", "equity_required": 100, "risk_adjusted_score": 60, "levered_irr": .14, "minimum_dscr": 1.3},
    ])
    left = portfolio_allocation(deals, 1_000, max_single_asset_pct=.5)
    right = portfolio_allocation(deals, 1_000, max_single_asset_pct=.5)
    assert left["recommended_allocation"].equals(right["recommended_allocation"])
