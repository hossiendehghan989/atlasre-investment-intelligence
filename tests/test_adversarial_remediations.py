from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import load_workbook

from generate_committee_report import build_screening_package
from scripts.screen_deal import run
from src.atlasre import DealInputs
from src.ic_workflow import DealCase, generate_ic_memo
from src.reconciliation import build_reconciliation_workbook

ROOT = Path(__file__).resolve().parents[1]


def _template_payload() -> dict[str, object]:
    payload = json.loads((ROOT / "docs/templates/deal_template.json").read_text(encoding="utf-8"))
    payload["simulations"] = 1
    return payload


def test_whitespace_only_source_evidence_cannot_verify_a_case(tmp_path):
    payload = _template_payload()
    payload.update(
        {
            "source_status": "VERIFIED",
            "verified_by": "  \t",
            "source_reference": "\n  ",
            "leverage": 0.25,
        }
    )
    input_path = tmp_path / "whitespace-evidence.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    report = (run(input_path, tmp_path / "review") / "investment_committee_report.md").read_text(encoding="utf-8")

    assert "Source status | **REVIEW REQUIRED**" in report
    assert "Decision status | **PASSES INITIAL SCREEN**" not in report


def test_generated_memo_and_report_escape_deal_identifier_html():
    deal = DealInputs(10_000_000, 650_000, leverage=0.25)
    unsafe_identifier = "<script>alert(1)</script>"
    memo = generate_ic_memo(DealCase(unsafe_identifier, "<b>case</b>", deal))
    report = build_screening_package(deal, deal_id=unsafe_identifier, simulations=1)[
        "investment_committee_report.md"
    ].decode("utf-8")

    assert unsafe_identifier not in memo
    assert unsafe_identifier not in report
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in memo
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in report


def test_existing_output_directory_is_rejected_before_overwrite(tmp_path):
    input_path = tmp_path / "deal.json"
    input_path.write_text(json.dumps(_template_payload()), encoding="utf-8")
    output_path = tmp_path / "review"

    run(input_path, output_path)
    original_report = (output_path / "investment_committee_report.md").read_bytes()

    with pytest.raises(ValueError, match="output directory already exists"):
        run(input_path, output_path)

    assert (output_path / "investment_committee_report.md").read_bytes() == original_report


def test_long_hold_workbook_uses_metric_rows_after_cash_flows():
    workbook = load_workbook(
        BytesIO(build_reconciliation_workbook(DealInputs(10_000_000, 650_000, hold_years=15, leverage=0.50))),
        data_only=False,
    )
    cash_flows = workbook["Cash Flows"]
    reconciliation = workbook["Reconciliation"]

    assert cash_flows["A21"].value == "Unlevered IRR"
    assert cash_flows["A24"].value == "Equity multiple"
    assert reconciliation["B8"].value == "='Cash Flows'!B21"
    assert reconciliation["B11"].value == "='Cash Flows'!B24"
    assert all("B11" not in reconciliation.cell(row, 2).value for row in range(8, 12))
