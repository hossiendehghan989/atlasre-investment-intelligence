import pytest

from src.atlasre import DealInputs, underwrite_deal
from src.presentation import (
    fraction_from_percent,
    metric_help,
    number_or_na_report,
    percent_or_na,
    percent_or_na_report,
)


def test_fraction_from_percent_preserves_model_fraction_values():
    assert fraction_from_percent(3.0) == pytest.approx(0.03)
    assert fraction_from_percent(6.0) == pytest.approx(0.06)
    assert fraction_from_percent(50.0) == pytest.approx(0.50)
    assert fraction_from_percent(12.0) == pytest.approx(0.12)
    assert fraction_from_percent(-5.0) == pytest.approx(-0.05)


def test_percent_display_conversion_keeps_underwriting_results_identical():
    direct = DealInputs(10_000_000, 650_000, annual_noi_growth=0.03, exit_cap_rate=0.06, leverage=0.50)
    converted = DealInputs(
        10_000_000,
        650_000,
        annual_noi_growth=fraction_from_percent(3.0),
        exit_cap_rate=fraction_from_percent(6.0),
        leverage=fraction_from_percent(50.0),
    )
    direct_result = underwrite_deal(direct)
    converted_result = underwrite_deal(converted)
    for key in ("levered_irr", "unlevered_npv", "equity_multiple", "minimum_dscr", "exit_value"):
        assert converted_result[key] == pytest.approx(direct_result[key])


def test_percent_or_na_does_not_render_non_finite_values_as_nan():
    assert percent_or_na(0.0599) == "5.99%"
    assert percent_or_na(float("nan")) == "N/A"
    assert percent_or_na(float("inf")) == "N/A"


def test_non_finite_metric_helpers_preserve_metric_identity():
    assert metric_help(float("nan"), "IRR did not converge") == "IRR did not converge"
    assert metric_help(0.05, "IRR did not converge") is None
    assert percent_or_na_report(float("nan"), reason="IRR did not converge") == "N/A — IRR did not converge"
    assert number_or_na_report(float("inf"), suffix="x", reason="DSCR is not defined") == "N/A — DSCR is not defined"
