import pytest

from src.atlasre import DealInputs
from src.ic_workflow import DealCase, ScreeningThresholds, compare_deals, screen_case


def test_unverified_case_cannot_pass_even_when_metrics_pass():
    inputs = DealInputs(10_000_000, 650_000, leverage=0.25, discount_rate=0.05)
    unverified = screen_case(DealCase("A", "Unverified", inputs, "REVIEW REQUIRED"))
    verified = screen_case(DealCase("A", "Verified", inputs, "VERIFIED"))
    assert unverified["status"] == "REVIEW REQUIRED"
    assert verified["status"] in {"PASSES INITIAL SCREEN", "REVIEW REQUIRED", "REJECT / REWORK"}
    assert any(flag["severity"] == "GOVERNANCE" for flag in unverified["flags"])


def test_verified_source_requires_reviewer_and_source_reference():
    inputs = DealInputs(10_000_000, 650_000, leverage=0.25)
    missing_evidence = screen_case(DealCase("A", "Missing evidence", inputs, "VERIFIED"))
    verified = screen_case(
        DealCase(
            "A",
            "Verified",
            inputs,
            "VERIFIED",
            verified_by="reviewer-1",
            source_reference="document:abc123",
        )
    )

    assert missing_evidence["source_status"] == "REVIEW REQUIRED"
    assert any(flag["severity"] == "GOVERNANCE" for flag in missing_evidence["flags"])
    assert verified["source_status"] == "VERIFIED"
    assert not any(flag["severity"] == "GOVERNANCE" for flag in verified["flags"])


def test_critical_economic_flag_is_rework_not_review():
    case = DealCase("B", "Overpriced", DealInputs(50_000_000, 100_000, leverage=0.5), "VERIFIED")
    screened = screen_case(case, ScreeningThresholds(hurdle_rate=.12))
    assert screened["status"] == "REJECT / REWORK"
    assert any(flag["severity"] == "CRITICAL" for flag in screened["flags"])


def test_ic_comparison_requires_cases_and_exposes_governance_counts():
    with pytest.raises(ValueError, match="at least one"):
        compare_deals([])
    result = compare_deals([DealCase("A", "A", DealInputs(10_000_000, 650_000))])
    assert {"decision_status", "critical_flags", "review_flags"}.issubset(result.columns)
    assert result.iloc[0]["source_status"] == "REVIEW REQUIRED"
