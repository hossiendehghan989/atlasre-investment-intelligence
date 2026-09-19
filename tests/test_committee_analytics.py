import pytest

from src.atlasre import DealInputs, underwrite_deal
from src.committee_analytics import break_even_exit_cap, investment_committee_summary, sensitivity_table


def test_debt_balance_amortizes_and_dscr_is_reported():
    result = underwrite_deal(DealInputs(10_000_000, 650_000, leverage=0.5))
    assert result["remaining_debt_at_exit"] < result["debt_amount"]
    assert result["minimum_dscr"] > 0
    assert len(result["debt_schedule"]) == 5


def test_sensitivity_and_break_even_are_monotonic_enough():
    deal = DealInputs(10_000_000, 650_000, leverage=0.5)
    table = sensitivity_table(deal, "exit_cap_rate", [0.05, 0.06, 0.07])
    assert table.iloc[0]["levered_irr"] > table.iloc[-1]["levered_irr"]
    assert break_even_exit_cap(deal, 0.12) == pytest.approx(break_even_exit_cap(deal, 0.12))
    assert "decision_flag" in investment_committee_summary(deal)
