import pandas as pd
import pyarrow as pa
import pytest

from src.portfolio import portfolio_allocation, portfolio_risk_view


def test_portfolio_risk_view_reports_exposure_not_only_weighted_return():
    deals = pd.DataFrame([
        {"asset": "A", "equity_required": 100, "risk_adjusted_score": 90, "levered_irr": .16, "minimum_dscr": 1.40},
        {"asset": "B", "equity_required": 100, "risk_adjusted_score": 60, "levered_irr": -.05, "minimum_dscr": 1.10},
    ])
    allocation = portfolio_allocation(deals, 200, max_single_asset_pct=1.0, min_dscr=1.0)
    risk = portfolio_risk_view(allocation, min_dscr=1.25)
    assert risk["invested_capital"] == pytest.approx(200)
    assert risk["dscr_breach_exposure"] > 0
    assert risk["negative_irr_exposure"] > 0
    assert 0 < risk["concentration_hhi"] <= 1


def test_portfolio_risk_view_handles_no_invested_capital():
    allocation = pd.DataFrame([{"recommended_allocation": 0.0, "levered_irr": .1, "minimum_dscr": 1.3, "allocation_weight": 0.0}])
    risk = portfolio_risk_view(allocation)
    assert risk["invested_capital"] == 0
    assert risk["concentration_hhi"] == 0


def test_portfolio_allocation_with_unallocated_summary_is_arrow_compatible():
    deals = pd.DataFrame([
        {"asset": "A", "equity_required": 100, "risk_adjusted_score": 90, "levered_irr": .16, "minimum_dscr": 1.40},
        {"asset": "B", "equity_required": 100, "risk_adjusted_score": 60, "levered_irr": .12, "minimum_dscr": 1.35},
    ])

    allocation = portfolio_allocation(deals, 500, max_single_asset_pct=1.0)

    assert "UNALLOCATED" in allocation["asset"].tolist()
    assert isinstance(allocation.index, pd.RangeIndex)
    pa.Table.from_pandas(allocation)
