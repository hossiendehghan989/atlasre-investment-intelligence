import pandas as pd
import pytest

from src.atlasre import DealInputs
from src.debt import DebtTerms, monthly_debt_schedule, size_debt_from_constraints
from src.ic_workflow import DealCase, ScreeningThresholds, compare_deals, generate_ic_memo, screen_case, screening_flags


def test_monthly_debt_schedule_is_balanced_and_shows_balloon():
    terms = DebtTerms(annual_rate=0.06, amortization_years=25, term_months=12, interest_only_months=3)
    schedule = monthly_debt_schedule(1_000_000, terms, noi=[120_000] * 12)
    assert len(schedule) == 12
    assert schedule.loc[0, "principal_paid"] == pytest.approx(0)
    assert schedule.iloc[-1]["balloon_payoff"] == pytest.approx(schedule.iloc[-1]["ending_balance"])
    assert schedule["dscr"].min() > 0


def test_debt_sizing_reports_binding_constraint():
    terms = DebtTerms(annual_rate=0.07, amortization_years=25, term_months=60)
    result = size_debt_from_constraints([650_000] * 60, 10_000_000, 0.60, 1.25, terms)
    assert result["recommended_loan"] <= result["ltv_limit"]
    assert result["binding_constraint"] in {"LTV", "DSCR"}


def test_ic_comparison_and_memo_are_downside_first_and_traceable():
    case = DealCase("A", "Base", DealInputs(10_000_000, 650_000, leverage=0.5))
    comparison = compare_deals([case])
    assert isinstance(comparison, pd.DataFrame)
    assert "decision_flag" in comparison
    assert screening_flags(case.inputs)["flags"]
    memo = generate_ic_memo(case)
    assert memo.index("## 2. Downside first") < memo.index("## 3. Core outputs")
    assert "REVIEW REQUIRED" in memo
    assert "break-even exit cap" in memo.lower()


# Governance edge cases


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
    screened = screen_case(case, ScreeningThresholds(hurdle_rate=0.12))
    assert screened["status"] == "REJECT / REWORK"
    assert any(flag["severity"] == "CRITICAL" for flag in screened["flags"])


def test_ic_comparison_requires_cases_and_exposes_governance_counts():
    with pytest.raises(ValueError, match="at least one"):
        compare_deals([])
    result = compare_deals([DealCase("A", "A", DealInputs(10_000_000, 650_000))])
    assert {"decision_status", "critical_flags", "review_flags"}.issubset(result.columns)
    assert result.iloc[0]["source_status"] == "REVIEW REQUIRED"
