import pytest

from src.atlasre import DealInputs, underwrite_deal
from src.presentation import fraction_from_percent


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
