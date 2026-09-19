import numpy as np

from src.institutional import MonthlyDevelopmentInputs, assumption_quality, lp_gp_waterfall, monthly_development_model, size_debt


def test_monthly_model_balances_and_generates_exit():
    df, summary = monthly_development_model(MonthlyDevelopmentInputs(5_000_000, 12_000_000, 2_500_000))
    assert len(df) == 72
    assert np.isclose(df["total_draw"].sum(), summary["total_cost"])
    assert df["sale_proceeds"].iloc[-1] == summary["exit_value"]
    assert df["ending_debt"].iloc[-1] > 0


def test_debt_sizing_uses_binding_constraint():
    result = size_debt(1_000_000, 0.06, 0.60, 1.25, 0.07, 25, 15_000_000)
    assert result["recommended_loan"] <= result["ltv_limit"]
    assert result["underwriting_dscr"] >= 1.25


def test_waterfall_and_assumption_register():
    waterfall = lp_gp_waterfall(10_000_000, 5_000_000, 0.08, 5, 0.20)
    assert waterfall["gp_promote"] >= 0
    register = assumption_quality({"exit_cap_rate": 0.06})
    assert register.iloc[0]["status"] == "REVIEW REQUIRED"
