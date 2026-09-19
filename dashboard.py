from pathlib import Path

import pandas as pd
import streamlit as st

from src.atlasre import DealInputs, rank_markets, scenario_matrix, underwrite_deal
from src.advanced_underwriting import DevelopmentInputs, development_feasibility, monte_carlo_underwriting, risk_summary, stress_test
from src.committee_analytics import investment_committee_summary, sensitivity_table
from src.institutional import MonthlyDevelopmentInputs, monthly_development_model, size_debt

st.set_page_config(page_title="AtlasRE Investment Intelligence", page_icon="◆", layout="wide")
st.title("AtlasRE Investment Intelligence")
st.caption("Underwriting, development feasibility, and market selection for investment committee review")
st.info("Analytical prototype using illustrative assumptions. Replace all defaults with verified deal, market, financing, and legal inputs before use.")

with st.sidebar:
    st.header("Transaction assumptions")
    price = st.number_input("Purchase price ($)", min_value=100_000, value=10_000_000, step=250_000)
    noi = st.number_input("Annual NOI ($)", min_value=10_000, value=650_000, step=25_000)
    hold = st.slider("Hold period (years)", 1, 15, 5)
    growth = st.slider("NOI growth", -0.05, 0.12, 0.03, 0.005)
    exit_cap = st.slider("Exit cap rate", 0.03, 0.15, 0.06, 0.005)
    leverage = st.slider("Leverage", 0.0, 0.80, 0.50, 0.05)

deal = DealInputs(price, noi, hold, growth, exit_cap, 0.10, 0.03, 0.02, leverage)
underwriting = underwrite_deal(deal)
committee = investment_committee_summary(deal)

underwriting_tab, risk_tab, development_tab, markets_tab = st.tabs(["Underwriting", "Risk & scenarios", "Development", "Markets"])
with underwriting_tab:
    st.header("Investment committee underwriting")
    cols = st.columns(6)
    cols[0].metric("Entry cap", f"{underwriting['entry_cap_rate']:.2%}")
    cols[1].metric("Levered IRR", f"{underwriting['levered_irr']:.2%}")
    cols[2].metric("Unlevered IRR", f"{underwriting['unlevered_irr']:.2%}")
    cols[3].metric("Equity multiple", f"{underwriting['equity_multiple']:.2f}x")
    cols[4].metric("Exit value", f"${underwriting['exit_value']:,.0f}")
    cols[5].metric("Minimum DSCR", f"{underwriting['minimum_dscr']:.2f}x")
    if committee["decision_flag"] == "passes initial screen":
        st.success(f"Initial screen: {committee['decision_flag']}")
    else:
        st.warning(f"Initial screen: {committee['decision_flag']}")
    st.caption(f"Debt balance at exit: ${underwriting['remaining_debt_at_exit']:,.0f} · Break-even exit cap at hurdle: {committee['break_even_exit_cap']:.2%}")
    st.subheader("Growth / exit-cap sensitivity")
    matrix = scenario_matrix(deal)
    st.dataframe(matrix.style.format({"noi_growth": "{:.1%}", "exit_cap_rate": "{:.1%}", "levered_irr": "{:.1%}", "unlevered_irr": "{:.1%}", "exit_value": "${:,.0f}", "npv": "${:,.0f}"}), use_container_width=True, hide_index=True)
    st.subheader("One-way sensitivity: exit cap rate")
    sensitivity = sensitivity_table(deal, "exit_cap_rate", [0.05, 0.055, 0.06, 0.065, 0.07])
    st.dataframe(sensitivity.style.format({"exit_cap_rate": "{:.1%}", "levered_irr": "{:.1%}", "unlevered_npv": "${:,.0f}", "minimum_dscr": "{:.2f}x", "exit_value": "${:,.0f}"}), use_container_width=True, hide_index=True)

with risk_tab:
    st.header("Downside and probability-weighted review")
    stress = stress_test(deal)
    st.dataframe(stress.style.format({"levered_irr": "{:.1%}", "unlevered_irr": "{:.1%}", "npv": "${:,.0f}", "exit_value": "${:,.0f}"}), use_container_width=True, hide_index=True)
    simulations = monte_carlo_underwriting(deal, simulations=2000)
    summary = risk_summary(simulations)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Median IRR", f"{summary['median_irr']:.1%}")
    c2.metric("P10 IRR", f"{summary['p10_irr']:.1%}")
    c3.metric("IRR below hurdle", f"{summary['probability_irr_below_hurdle']:.1%}")
    c4.metric("Negative NPV", f"{summary['probability_negative_npv']:.1%}")
    st.subheader("Simulated levered IRR distribution")
    st.bar_chart(simulations["levered_irr"].round(3).value_counts().sort_index())

with development_tab:
    st.header("Development feasibility")
    development = DevelopmentInputs(land_cost=5_000_000, hard_cost=12_000_000, soft_cost=2_500_000, stabilized_noi=1_800_000, exit_cap_rate=0.06, debt_to_cost=0.55)
    result = development_feasibility(development)
    cols = st.columns(5)
    cols[0].metric("Total cost", f"${result['total_development_cost']:,.0f}")
    cols[1].metric("Equity required", f"${result['equity_required']:,.0f}")
    cols[2].metric("Exit value", f"${result['exit_value']:,.0f}")
    cols[3].metric("Investor IRR", f"{result['investor_irr']:.1%}")
    cols[4].metric("Investor multiple", f"{result['investor_equity_multiple']:.2f}x")
    st.write("The development module includes land, hard costs, soft costs, contingency, construction debt, capitalized interest, a preferred return, and a promote waterfall.")
    monthly_inputs = MonthlyDevelopmentInputs(land_cost=5_000_000, hard_cost=12_000_000, soft_cost=2_500_000, stabilized_annual_noi=1_800_000)
    monthly_model, monthly_summary = monthly_development_model(monthly_inputs)
    st.subheader("Monthly sources-and-uses schedule")
    st.dataframe(monthly_model.tail(12).style.format({"total_draw": "${:,.0f}", "debt_draw": "${:,.0f}", "interest": "${:,.0f}", "ending_debt": "${:,.0f}", "noi": "${:,.0f}", "sale_proceeds": "${:,.0f}"}), use_container_width=True, hide_index=True)
    st.caption(f"Capitalized interest: ${monthly_summary['capitalized_interest']:,.0f} · Project IRR before waterfall: {monthly_summary['project_irr']:.1%}")
    debt_sizing = size_debt(noi, underwriting["entry_cap_rate"], 0.60, 1.25, 0.07, 25, price)
    st.write(f"Debt sizing: ${debt_sizing['recommended_loan']:,.0f} recommended, constrained by the lower of LTV (${debt_sizing['ltv_limit']:,.0f}) and DSCR (${debt_sizing['dscr_limit']:,.0f}).")

with markets_tab:
    st.header("Global market selection")
    markets = pd.read_csv(Path("data/market_inputs.csv"))
    ranked = rank_markets(markets)
    st.dataframe(ranked.style.format({"score_0_100": "{:.1f}", "risk_adjusted_score": "{:.1f}"}), use_container_width=True, hide_index=True)
    st.bar_chart(ranked.set_index("market")["risk_adjusted_score"])
