import numpy as np
import pytest

from src.advanced_underwriting import monte_carlo_underwriting, risk_summary, stress_test
from src.atlasre import DealInputs
from src.institutional import MonthlyDevelopmentInputs, WaterfallTier, multi_tier_waterfall, monthly_development_model


def test_multi_tier_waterfall_balances_and_only_promotes_residual_profit():
    result = multi_tier_waterfall(
        equity=10_000_000,
        total_distributable_cash=20_000_000,
        pref_rate=0.08,
        hold_years=5,
        tiers=[WaterfallTier(0.12, 0.20, "Tier 1"), WaterfallTier(0.18, 0.30, "Tier 2")],
    )
    assert result["distribution_check"] == pytest.approx(20_000_000)
    assert result["return_of_capital"] == pytest.approx(10_000_000)
    assert result["gp_promote"] > 0
    assert len(result["tiers"]) == 2


def test_multi_tier_waterfall_does_not_promote_when_only_capital_returns():
    result = multi_tier_waterfall(10_000_000, 10_000_000, 0.08, 5, [WaterfallTier(0.12, 0.2)])
    assert result["gp_promote"] == pytest.approx(0)
    assert result["lp_total_distribution"] == pytest.approx(10_000_000)


def test_monthly_development_output_has_peak_debt_and_annualized_irr():
    _, summary = monthly_development_model(MonthlyDevelopmentInputs(5_000_000, 12_000_000, 2_500_000))
    assert summary["peak_debt_balance"] >= summary["debt_commitment"]
    assert np.isfinite(summary["project_irr"])
    assert -1 < summary["project_irr"] < 2


def test_correlated_monte_carlo_is_reproducible_and_exposes_risk_tails():
    deal = DealInputs(10_000_000, 650_000, leverage=0.5)
    first = monte_carlo_underwriting(deal, simulations=250, seed=99)
    second = monte_carlo_underwriting(deal, simulations=250, seed=99)
    assert first.equals(second)
    summary = risk_summary(first)
    assert summary["p05_irr"] <= summary["median_irr"] <= summary["p95_irr"]
    assert summary["expected_shortfall_irr_10"] <= summary["p10_irr"]
    assert summary["expected_shortfall_npv_10"] <= summary["median_npv"]
    assert 0 <= summary["probability_dscr_below_125"] <= 1


def test_stress_test_contains_rate_and_combined_downside_cases():
    table = stress_test(DealInputs(10_000_000, 650_000, leverage=0.5))
    assert {"Rate shock", "Combined downside"}.issubset(set(table["case"]))
    base = table.loc[table["case"] == "Base case", "levered_irr"].iloc[0]
    downside = table.loc[table["case"] == "Combined downside", "levered_irr"].iloc[0]
    assert downside < base
