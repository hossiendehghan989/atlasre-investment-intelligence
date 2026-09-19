import pandas as pd

from src.governance import assumption_register, audit_event, verify_audit_chain
from src.portfolio import portfolio_allocation, portfolio_snapshot


def test_audit_chain_is_tamper_evident():
    first = audit_event("screening_created", "analyst", {"deal_id": "ATLAS-001"})
    second = audit_event("assumptions_reviewed", "analyst", {"count": 6}, first["event_hash"])
    assert verify_audit_chain([first, second])
    second["payload"]["count"] = 7
    assert not verify_audit_chain([first, second])


def test_assumption_register_marks_inputs_for_review():
    register = assumption_register({"purchase_price": (10_000_000, "USD")})
    assert register.iloc[0]["status"] == "REVIEW REQUIRED"


def test_portfolio_allocation_respects_concentration_and_reports_constraints():
    deals = pd.DataFrame([
        {"asset": "A", "equity_required": 100, "risk_adjusted_score": 90, "levered_irr": .18, "minimum_dscr": 1.4},
        {"asset": "B", "equity_required": 100, "risk_adjusted_score": 30, "levered_irr": .12, "minimum_dscr": 1.1},
    ])
    output = portfolio_allocation(deals, 1000, max_single_asset_pct=.6)
    assert output["recommended_allocation"].max() <= 600
    assert set(output.loc[output["asset"] != "UNALLOCATED", "constraint_flag"]) == {"Pass", "Review"}
    assert portfolio_snapshot(deals, 1000)["eligible_assets"] == 2


def test_portfolio_allocation_caps_each_deal_and_reports_unallocated_capital():
    deals = pd.DataFrame([
        {"asset": "A", "equity_required": 1_000_000, "risk_adjusted_score": 60, "levered_irr": .18, "minimum_dscr": 1.4},
        {"asset": "B", "equity_required": 1_000_000, "risk_adjusted_score": 40, "levered_irr": .16, "minimum_dscr": 1.4},
    ])

    output = portfolio_allocation(deals, 10_000_000, max_single_asset_pct=1.0)

    assert output.loc[output["asset"] != "UNALLOCATED", "recommended_allocation"].tolist() == [1_000_000, 1_000_000]
    assert output["recommended_allocation"].max() <= output["equity_required"].max()
    assert output.loc[output["asset"] == "UNALLOCATED", "unallocated_equity"].tolist() == [8_000_000.0]
    assert output["unallocated_equity"].sum() == 8_000_000.0
    assert set(output.loc[output["asset"] != "UNALLOCATED", "constraint_reason"]) == {"Equity requirement cap"}


def test_portfolio_allocated_plus_unallocated_equals_available_capital():
    deals = pd.DataFrame([
        {"asset": "A", "equity_required": 1_000_000, "risk_adjusted_score": 60, "levered_irr": .18, "minimum_dscr": 1.4},
        {"asset": "B", "equity_required": 1_000_000, "risk_adjusted_score": 40, "levered_irr": .16, "minimum_dscr": 1.4},
    ])
    available = 10_000_000
    output = portfolio_allocation(deals, available, max_single_asset_pct=1.0)
    assert output["recommended_allocation"].sum() + output["unallocated_equity"].sum() == available
    assert (output.loc[output["asset"] != "UNALLOCATED", "unallocated_equity"] == 0).all()
