import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from scripts.screen_deal import load_deal, run

ROOT = Path(__file__).resolve().parents[1]


def test_risk_summary_handles_no_debt_series_independently():
    from src.advanced_underwriting import monte_carlo_underwriting, risk_summary
    from src.atlasre import DealInputs

    summary = risk_summary(monte_carlo_underwriting(DealInputs(10_000_000, 650_000, leverage=0), simulations=20))
    assert summary["probability_dscr_below_125"] is None
    assert summary["p05_irr"] is not None


def test_dashboard_regressions_and_illustrative_notice():
    for label, target in (("Leverage", 0.0), ("Purchase price ($)", 500_000_000)):
        app = AppTest.from_file(str(ROOT / "dashboard.py")).run(timeout=120)
        widget = next(w for w in (app.slider if label == "Leverage" else app.number_input) if w.label == label)
        widget.set_value(target)
        app.run(timeout=120)
        assert not app.exception, [exception.value for exception in app.exception]
        assert any("Illustrative data only" in warning.value for warning in app.warning)


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
