import numpy as np
import pytest

from src.advanced_underwriting import (
    DevelopmentInputs,
    development_feasibility,
    monte_carlo_underwriting,
    risk_summary,
    stress_test,
)
from src.atlasre import DealInputs


def test_development_waterfall_balances_capital():
    result = development_feasibility(DevelopmentInputs(5_000_000, 12_000_000, 2_500_000, stabilized_noi=1_800_000))
    assert result["total_development_cost"] > 0
    assert result["equity_required"] + result["debt_amount"] == result["total_development_cost"]
    assert result["investor_equity_multiple"] > 0


@pytest.mark.parametrize("field", ["land_cost", "hard_cost", "soft_cost", "stabilized_noi"])
@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_development_feasibility_rejects_non_finite_cost_inputs(field, value):
    inputs = DevelopmentInputs(5_000_000, 12_000_000, 2_500_000, stabilized_noi=1_800_000)
    invalid = {**inputs.__dict__, field: value}

    with pytest.raises(ValueError, match="finite"):
        development_feasibility(DevelopmentInputs(**invalid))


@pytest.mark.parametrize(
    "field", ["contingency_pct", "debt_to_cost", "construction_rate", "preferred_return", "promote"]
)
def test_development_feasibility_rejects_negative_percentages(field):
    inputs = DevelopmentInputs(5_000_000, 12_000_000, 2_500_000, stabilized_noi=1_800_000)
    invalid = {**inputs.__dict__, field: -0.01}

    with pytest.raises(ValueError):
        development_feasibility(DevelopmentInputs(**invalid))


def test_monte_carlo_is_reproducible_and_has_downside_metrics():
    deal = DealInputs(10_000_000, 650_000, leverage=0.5)
    simulations = monte_carlo_underwriting(deal, simulations=100, seed=7)
    repeat = monte_carlo_underwriting(deal, simulations=100, seed=7)
    assert np.allclose(simulations["levered_irr"], repeat["levered_irr"])
    summary = risk_summary(simulations)
    assert 0 <= summary["probability_irr_below_hurdle"] <= 1


def test_default_seeded_simulation_preserves_review_package_outputs():
    """Protect the pre-vectorization 5,000-simulation screening-package results."""
    summary = risk_summary(monte_carlo_underwriting(DealInputs(10_000_000, 650_000, leverage=0.5)))
    expected = {
        "p05_irr": 0.027605464492026867,
        "p10_irr": 0.04749271852064083,
        "median_irr": 0.12065976556190172,
        "p90_irr": 0.1934208639821643,
        "p95_irr": 0.21298965994158556,
        "expected_shortfall_irr_10": 0.020560463567169562,
        "expected_shortfall_npv_10": -2247767.6431427486,
        "worst_irr": -0.13972425058858162,
        "probability_irr_below_hurdle": 0.4962,
        "probability_negative_npv": 0.5778,
        "median_npv": -260937.42855946207,
        "probability_dscr_below_125": 0.0044,
    }
    assert summary == pytest.approx(expected, abs=1e-8)


def test_stress_test_contains_combined_downside():
    table = stress_test(DealInputs(10_000_000, 650_000))
    assert "Combined downside" in set(table["case"])
