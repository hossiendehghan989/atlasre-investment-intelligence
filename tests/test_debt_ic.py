import pandas as pd
import pytest

from src.atlasre import DealInputs
from src.debt import DebtTerms, monthly_debt_schedule, size_debt_from_constraints
from src.ic_workflow import DealCase, compare_deals, generate_ic_memo, screening_flags


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
