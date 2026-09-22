import warnings

import pandas as pd
import pytest

from src.atlasre import DealInputs, market_score, portfolio_exposure, rank_markets, scenario_matrix, underwrite_deal


def test_underwriting_has_consistent_cash_flow_outputs():
    deal = DealInputs(10_000_000, 650_000, leverage=0.5)
    result = underwrite_deal(deal)
    assert result["entry_cap_rate"] == pytest.approx(0.065)
    assert len(result["cash_flows"]) == 6
    assert result["equity_multiple"] > 1


def test_debt_service_stops_after_loan_is_fully_amortized():
    deal = DealInputs(10_000_000, 650_000, hold_years=25, leverage=0.5, debt_amortization_years=10)
    result = underwrite_deal(deal)

    assert result["debt_service_schedule"][9] > 0
    assert result["debt_service_schedule"][10:] == pytest.approx([0.0] * 15)
    assert result["cash_flows"][11] == pytest.approx(deal.annual_noi * (1 + deal.annual_noi_growth) ** 10)


def test_very_long_hold_does_not_emit_numeric_overflow_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = underwrite_deal(DealInputs(10_000_000, 650_000, hold_years=100, leverage=0.5))

    assert result["exit_value"] > 0


def test_year_one_noi_is_the_input_noi_before_growth():
    deal = DealInputs(10_000_000, 650_000, hold_years=3, annual_noi_growth=0.10)
    result = underwrite_deal(deal)
    expected_final_noi = 650_000 * (1.10**2)
    assert result["exit_value"] == pytest.approx(expected_final_noi / deal.exit_cap_rate)


def test_equity_multiple_counts_negative_interim_equity_flows_as_new_investment():
    deal = DealInputs(10_000_000, 100_000, hold_years=3, leverage=0.80, debt_rate=0.20)
    result = underwrite_deal(deal)
    negative_flows = sum(flow for flow in result["cash_flows"] if flow < 0)
    positive_flows = sum(flow for flow in result["cash_flows"] if flow > 0)
    assert any(flow < 0 for flow in result["cash_flows"][1:-1])
    assert result["total_equity_invested"] == pytest.approx(-negative_flows)
    assert result["total_distributions"] == pytest.approx(positive_flows)
    assert result["equity_multiple"] == pytest.approx(positive_flows / -negative_flows)


def test_scenario_matrix_changes_exit_value():
    matrix = scenario_matrix(DealInputs(10_000_000, 650_000))
    assert len(matrix) == 9
    assert matrix["exit_value"].max() > matrix["exit_value"].min()


def test_market_ranking_penalizes_risk():
    markets = pd.DataFrame(
        [
            {
                "market": "A",
                "population_growth": 0.8,
                "employment_growth": 0.8,
                "rent_growth": 0.8,
                "liquidity": 0.8,
                "risk": 0.8,
            },
            {
                "market": "B",
                "population_growth": 0.7,
                "employment_growth": 0.7,
                "rent_growth": 0.7,
                "liquidity": 0.7,
                "risk": 0.2,
            },
        ]
    )
    ranked = rank_markets(markets)
    assert ranked.iloc[0]["market"] == "B"
    assert market_score(markets.iloc[1].to_dict())["risk_adjusted_score"] > 0


def test_market_score_applies_risk_once_and_keeps_aliases_consistent():
    market = {
        "population_growth": 0.8,
        "employment_growth": 0.8,
        "rent_growth": 0.8,
        "liquidity": 0.8,
        "risk": 0.8,
    }
    result = market_score(market)
    expected = (0.8 * 0.25) + (0.8 * 0.20) + (0.8 * 0.25) + (0.8 * 0.15) + ((1 - 0.8) * 0.15)
    assert result["score_0_100"] == pytest.approx(expected * 100)
    assert result["risk_adjusted_score"] == pytest.approx(result["score_0_100"])


def test_portfolio_exposure_respects_capital():
    deals = pd.DataFrame(
        [
            {"asset": "A", "equity_required": 100, "risk_adjusted_score": 80},
            {"asset": "B", "equity_required": 100, "risk_adjusted_score": 40},
        ]
    )
    output = portfolio_exposure(deals, 1000)
    assert output["recommended_allocation"].sum() == pytest.approx(1000)
    assert set(output["allocation_method"]) == {"naive score-weighted screen"}
