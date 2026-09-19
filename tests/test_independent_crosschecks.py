import numpy as np
import numpy_financial as npf
import pytest

from src.atlasre import DealInputs, underwrite_deal
from src.debt import DebtTerms, monthly_debt_schedule


def test_levered_irr_matches_numpy_financial_for_fixed_case():
    deal = DealInputs(
        purchase_price=8_500_000,
        annual_noi=620_000,
        hold_years=5,
        annual_noi_growth=0.025,
        exit_cap_rate=0.065,
        leverage=0.55,
        debt_rate=0.0625,
    )
    result = underwrite_deal(deal)
    expected = float(npf.irr(np.asarray(result["cash_flows"], dtype=float)))
    assert result["levered_irr"] == pytest.approx(expected, abs=1e-10)


def test_levered_cash_flows_are_rebuilt_independently_before_irr_check():
    deal = DealInputs(
        purchase_price=8_500_000,
        annual_noi=620_000,
        hold_years=5,
        annual_noi_growth=0.025,
        exit_cap_rate=0.065,
        leverage=0.55,
        debt_rate=0.0625,
        debt_amortization_years=20,
    )
    result = underwrite_deal(deal)

    acquisition = deal.purchase_price * (1 + deal.acquisition_cost_pct)
    debt = deal.purchase_price * deal.leverage
    equity = acquisition - debt
    monthly_rate = deal.debt_rate / 12
    periods = deal.debt_amortization_years * 12
    monthly_payment = debt * monthly_rate * (1 + monthly_rate) ** periods / ((1 + monthly_rate) ** periods - 1)
    balance = debt
    for _ in range(deal.hold_years * 12):
        interest = balance * monthly_rate
        balance -= monthly_payment - interest
    annual_debt_service = monthly_payment * 12
    noi = [deal.annual_noi * (1 + deal.annual_noi_growth) ** year for year in range(deal.hold_years)]
    exit_value = noi[-1] / deal.exit_cap_rate
    selling_cost = exit_value * deal.selling_cost_pct
    rebuilt = [
        -equity,
        *[cash - annual_debt_service for cash in noi[:-1]],
        noi[-1] + exit_value - selling_cost - annual_debt_service - balance,
    ]

    np.testing.assert_allclose(result["cash_flows"], rebuilt, rtol=0, atol=1e-6)
    assert result["levered_irr"] == pytest.approx(float(npf.irr(np.asarray(rebuilt))), abs=1e-10)


def test_unlevered_npv_matches_direct_discounted_cash_flow_sum():
    deal = DealInputs(
        purchase_price=12_000_000,
        annual_noi=780_000,
        hold_years=4,
        annual_noi_growth=0.01,
        exit_cap_rate=0.07,
        discount_rate=0.095,
    )
    result = underwrite_deal(deal)
    cash_flows = result["cash_flows"]
    # Rebuild the unlevered stream from the same fixed case, independently of
    # the model's private _npv helper and its levered cash-flow construction.
    acquisition = deal.purchase_price * (1 + deal.acquisition_cost_pct)
    noi = [deal.annual_noi * (1 + deal.annual_noi_growth) ** year for year in range(deal.hold_years)]
    exit_value = noi[-1] / deal.exit_cap_rate
    unlevered = [
        -acquisition,
        *noi[:-1],
        noi[-1] + exit_value * (1 - deal.selling_cost_pct),
    ]
    expected = sum(flow / (1 + deal.discount_rate) ** period for period, flow in enumerate(unlevered))
    # The public output is the unlevered NPV; cash flows are checked separately
    # above through the fixed-case construction.
    assert result["unlevered_npv"] == pytest.approx(expected, abs=1e-6)
    assert len(cash_flows) == deal.hold_years + 1


def test_monthly_debt_schedule_matches_closed_form_amortization():
    principal = 4_675_000.0
    terms = DebtTerms(annual_rate=0.0625, amortization_years=20, term_months=60)
    schedule = monthly_debt_schedule(principal, terms)
    monthly_rate = terms.annual_rate / 12
    periods = terms.amortization_years * 12
    payment = principal * monthly_rate * (1 + monthly_rate) ** periods / ((1 + monthly_rate) ** periods - 1)
    balance = principal
    expected_balances = []
    for _ in range(terms.term_months):
        interest = balance * monthly_rate
        balance -= payment - interest
        expected_balances.append(balance)
    assert schedule.iloc[0]["scheduled_payment"] == pytest.approx(payment)
    np.testing.assert_allclose(schedule["ending_balance"].to_numpy(), expected_balances, rtol=0, atol=1e-6)
    assert schedule["interest"].sum() > 0
