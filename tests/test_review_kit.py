import json
from pathlib import Path

import pytest

from generate_committee_report import build_screening_package
from scripts.screen_deal import load_deal, run
from src.atlasre import DealInputs, validate_deal
from src.presentation import metric_help, number_or_na, percent_or_na

ROOT = Path(__file__).resolve().parents[1]


def test_risk_summary_handles_no_debt_series_independently():
    from src.advanced_underwriting import monte_carlo_underwriting, risk_summary
    from src.atlasre import DealInputs

    summary = risk_summary(monte_carlo_underwriting(DealInputs(10_000_000, 650_000, leverage=0), simulations=20))
    assert summary["probability_dscr_below_125"] is None
    assert summary["p05_irr"] is not None


def test_dashboard_regressions_and_illustrative_notice():
    from src.atlasre import underwrite_deal

    for deal in (DealInputs(10_000_000, 650_000, leverage=0.0), DealInputs(500_000_000, 650_000, leverage=0.5)):
        validate_deal(deal)
        result = underwrite_deal(deal)
        assert "inf" not in number_or_na(result["minimum_dscr"]).lower()


@pytest.mark.parametrize(
    ("label", "target", "message"),
    [
        ("Purchase price ($)", 0, "purchase_price and annual_noi must be positive"),
        ("Purchase price ($)", 10**15, "purchase_price and annual_noi must not exceed"),
    ],
)
def test_dashboard_shows_clear_validation_error_without_traceback(label, target, message):
    deal = DealInputs(target, 650_000) if label == "Purchase price ($)" else DealInputs(10_000_000, 650_000)
    with pytest.raises(ValueError, match=message):
        validate_deal(deal)


def test_dashboard_does_not_substitute_unlevered_irr_for_nonconvergent_levered_irr():
    from src.atlasre import underwrite_deal

    result = underwrite_deal(DealInputs(10_000_000_000, 650_000, leverage=0.5))
    assert percent_or_na(result["levered_irr"]) == "N/A"
    assert percent_or_na(result["unlevered_irr"]) == "-73.71%"
    assert metric_help(result["levered_irr"], "IRR did not converge") == "IRR did not converge"


def test_generated_package_does_not_substitute_nonconvergent_irr():
    files = build_screening_package(DealInputs(10_000_000_000, 650_000, leverage=0.5), simulations=10)
    report = files["investment_committee_report.md"].decode()
    memo = files["investment_committee_memo.md"].decode()

    assert "| Levered IRR | N/A — IRR did not converge |" in report
    assert "| Unlevered IRR | -73.71% |" in report
    assert "| Levered IRR | N/A — IRR did not converge |" in memo


def test_template_validates_and_runs_end_to_end(tmp_path):
    template_path = ROOT / "docs/templates/deal_template.json"
    payload = json.loads(template_path.read_text())
    payload["simulations"] = 10
    input_path = tmp_path / "deal.json"
    input_path.write_text(json.dumps(payload))
    assert load_deal(input_path)["purchase_price"] == 10_000_000
    output = run(input_path, tmp_path / "review")
    assert (output / "investment_committee_memo.md").exists()
    assert (output / "assumptions.csv").exists()
    assert (output / "risk_summary.json").exists()
    assert (output / "annual_debt_schedule.csv").exists()
    assert (output / "excel_reconciliation.xlsx").exists()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("purchase_price", None, "missing required fields"),
        ("annual_noi", float("nan"), "must be finite"),
        ("leverage", -0.1, "cannot be negative"),
        ("hold_years", 5.5, "must be an integer"),
        ("simulations", 0, "positive integer"),
    ],
)
def test_invalid_input_is_rejected_clearly(tmp_path, field, value, message):
    payload = json.loads((ROOT / "docs/templates/deal_template.json").read_text())
    if value is None:
        payload.pop(field)
    else:
        payload[field] = value
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload, allow_nan=True))
    with pytest.raises(ValueError, match=message):
        load_deal(path)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("hold_years", 10**15, "must not exceed"),
        ("annual_noi_growth", 1e300, "no greater than 100%"),
        ("debt_rate", 1e15, "debt rate"),
        ("debt_amortization_years", 10**15, "must not exceed"),
        ("simulations", 10**15, "between 1 and"),
    ],
)
def test_hostile_numeric_magnitudes_are_rejected_before_package_generation(tmp_path, field, value, message):
    payload = json.loads((ROOT / "docs/templates/deal_template.json").read_text())
    payload[field] = value
    path = tmp_path / "hostile-numeric.json"
    path.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match=message):
        run(path, tmp_path / "review")


def test_verified_source_gate_requires_both_evidence(tmp_path):
    payload = json.loads((ROOT / "docs/templates/deal_template.json").read_text())
    payload["simulations"] = 10
    payload["source_status"] = "VERIFIED"
    payload["verified_by"] = ""
    payload["source_reference"] = ""
    input_path = tmp_path / "deal.json"
    input_path.write_text(json.dumps(payload))
    report = (run(input_path, tmp_path / "review") / "investment_committee_report.md").read_text()
    assert "Source status | **REVIEW REQUIRED**" in report
    assert "Decision status" in report


def test_cli_verified_source_gate_passes_only_with_both_evidence(tmp_path):
    payload = json.loads((ROOT / "docs/templates/deal_template.json").read_text())
    payload.update({"simulations": 10, "source_status": "VERIFIED", "verified_by": "Owner reviewer", "source_reference": "local://source.pdf"})
    input_path = tmp_path / "verified.json"
    input_path.write_text(json.dumps(payload))
    report = (run(input_path, tmp_path / "verified-review") / "investment_committee_report.md").read_text()
    assert "Source status | **VERIFIED**" in report
