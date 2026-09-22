from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import load_workbook

from generate_committee_report import build_screening_package
from scripts.screen_deal import run
from src.atlasre import DealInputs, underwrite_deal
from src.ic_workflow import DealCase, generate_ic_memo, screen_case
from src.reconciliation import build_reconciliation_workbook

ROOT = Path(__file__).resolve().parents[1]


def template_payload() -> dict[str, object]:
    payload = json.loads((ROOT / "docs/templates/deal_template.json").read_text(encoding="utf-8"))
    payload["simulations"] = 1
    return payload


def test_whitespace_only_source_evidence_cannot_verify_case(tmp_path):
    payload = template_payload()
    payload.update({
        "source_status": "VERIFIED",
        "verified_by": "   ",
        "source_reference": "\t\n",
        "leverage": 0.25,
    })
    input_path = tmp_path / "whitespace-evidence.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    output = run(input_path, tmp_path / "review")
    report = (output / "investment_committee_report.md").read_text(encoding="utf-8")

    assert "Source status | **REVIEW REQUIRED**" in report
    assert "Decision status | **PASSES INITIAL SCREEN**" not in report


def test_generated_memo_and_report_escape_deal_identifier_html():
    deal = DealInputs(10_000_000, 650_000, leverage=0.25)
    unsafe_identifier = "<script>alert(1)</script>"
    memo = generate_ic_memo(DealCase(unsafe_identifier, "<b>case</b>", deal))
    report = build_screening_package(deal, deal_id=unsafe_identifier, simulations=1)["investment_committee_report.md"].decode("utf-8")

    assert unsafe_identifier not in memo
    assert unsafe_identifier not in report
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in memo
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in report


def test_existing_output_directory_is_rejected_before_writing(tmp_path):
    input_path = tmp_path / "deal.json"
    input_path.write_text(json.dumps(template_payload()), encoding="utf-8")
    output = tmp_path / "review"

    run(input_path, output)
    with pytest.raises(ValueError, match="output directory already exists"):
        run(input_path, output)


def test_long_hold_workbook_reconciliation_references_dynamic_metric_rows():
    workbook_bytes = build_reconciliation_workbook(DealInputs(10_000_000, 650_000, hold_years=15, leverage=0.50))
    workbook = load_workbook(BytesIO(workbook_bytes), data_only=False)
    cash_flows = workbook["Cash Flows"]
    reconciliation = workbook["Reconciliation"]

    assert cash_flows["A21"].value == "Unlevered IRR"
    assert cash_flows["A24"].value == "Equity multiple"
    assert reconciliation["B8"].value == "='Cash Flows'!B21"
    assert reconciliation["B11"].value == "='Cash Flows'!B24"


@pytest.mark.parametrize(
    "deal",
    [
        DealInputs(1e300, 650_000),
        DealInputs(10_000_000, 1e300),
        DealInputs(10_000_000, 650_000, discount_rate=1e300),
    ],
)
def test_extreme_numeric_inputs_are_rejected_before_overflow(deal):
    with pytest.raises(ValueError):
        underwrite_deal(deal)


def test_screened_case_with_whitespace_evidence_stays_review_required():
    case = DealCase(
        "A",
        "Whitespace evidence",
        DealInputs(10_000_000, 650_000, leverage=0.25),
        "VERIFIED",
        verified_by=" ",
        source_reference="\t",
    )

    screened = screen_case(case)

    assert screened["source_status"] == "REVIEW REQUIRED"
    assert any(flag["severity"] == "GOVERNANCE" for flag in screened["flags"])
