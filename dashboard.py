from pathlib import Path

import pandas as pd
import streamlit as st

from src.advanced_underwriting import DevelopmentInputs, monte_carlo_underwriting, risk_summary, stress_test
from src.atlasre import DealInputs, rank_markets, scenario_matrix, underwrite_deal
from src.committee_analytics import investment_committee_summary, sensitivity_table
from src.governance import assumption_register, default_lineage, ic_workflow, lineage_json
from src.institutional import MonthlyDevelopmentInputs, monthly_development_model, size_debt
from src.portfolio import portfolio_allocation, portfolio_snapshot

st.set_page_config(page_title="AtlasRE Investment Intelligence", page_icon="◆", layout="wide")

st.title("AtlasRE Investment Intelligence")
st.caption("Institutional real-estate investment operating system · transparent by design")
st.info("Screening workspace using illustrative inputs. Every output is decision support, not investment, legal, tax, or engineering advice.")

with st.sidebar:
    st.header("Deal assumptions")
    price = st.number_input("Purchase price ($)", min_value=100_000, value=10_000_000, step=250_000)
    noi = st.number_input("Annual NOI ($)", min_value=10_000, value=650_000, step=25_000)
    hold = st.slider("Hold period (years)", 1, 15, 5)
    growth = st.slider("NOI growth", -0.05, 0.12, 0.03, 0.005)
    exit_cap = st.slider("Exit cap rate", 0.03, 0.15, 0.06, 0.005)
    leverage = st.slider("Leverage", 0.0, 0.80, 0.50, 0.05)
    hurdle = st.slider("IC hurdle rate", 0.06, 0.20, 0.12, 0.01)

base_deal = DealInputs(price, noi, hold, growth, exit_cap, hurdle - 0.02, 0.03, 0.02, leverage)
underwriting = underwrite_deal(base_deal)
committee = investment_committee_summary(base_deal, hurdle)

st.markdown("### Decision surface")
metric_cols = st.columns(6)
metric_cols[0].metric("Entry cap", f"{underwriting['entry_cap_rate']:.2%}")
metric_cols[1].metric("Levered IRR", f"{underwriting['levered_irr']:.2%}")
metric_cols[2].metric("Unlevered IRR", f"{underwriting['unlevered_irr']:.2%}")
metric_cols[3].metric("Equity multiple", f"{underwriting['equity_multiple']:.2f}x")
metric_cols[4].metric("Min DSCR", f"{underwriting['minimum_dscr']:.2f}x")
metric_cols[5].metric("Exit value", f"${underwriting['exit_value']:,.0f}")

if committee["decision_flag"] == "passes initial screen":
    st.success(f"Initial screen: {committee['decision_flag']}")
else:
    st.warning(f"Initial screen: {committee['decision_flag']}")
st.caption(f"Debt at exit: ${underwriting['remaining_debt_at_exit']:,.0f} · Break-even exit cap at hurdle: {committee['break_even_exit_cap']:.2%}")

underwriting_tab, risk_tab, development_tab, portfolio_tab, governance_tab, markets_tab = st.tabs([
    "Underwriting", "Risk & scenarios", "Development", "Portfolio", "IC governance", "Markets"
])

with underwriting_tab:
    st.subheader("Downside-first underwriting")
    st.dataframe(
        scenario_matrix(base_deal).style.format({"noi_growth": "{:.1%}", "exit_cap_rate": "{:.1%}", "levered_irr": "{:.1%}", "unlevered_irr": "{:.1%}", "exit_value": "${:,.0f}", "npv": "${:,.0f}"}),
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("One-way exit-cap sensitivity")
    sensitivity = sensitivity_table(base_deal, "exit_cap_rate", [0.05, 0.055, 0.06, 0.065, 0.07])
    st.dataframe(sensitivity.style.format({"exit_cap_rate": "{:.1%}", "levered_irr": "{:.1%}", "unlevered_npv": "${:,.0f}", "minimum_dscr": "{:.2f}x", "exit_value": "${:,.0f}"}), use_container_width=True, hide_index=True)

with risk_tab:
    st.subheader("Risk engine")
    stress = stress_test(base_deal)
    st.dataframe(stress.style.format({"levered_irr": "{:.1%}", "unlevered_irr": "{:.1%}", "npv": "${:,.0f}", "exit_value": "${:,.0f}"}), use_container_width=True, hide_index=True)
    simulations = monte_carlo_underwriting(base_deal, simulations=2000)
    summary = risk_summary(simulations, hurdle)
    risk_cols = st.columns(5)
    risk_cols[0].metric("Median IRR", f"{summary['median_irr']:.1%}")
    risk_cols[1].metric("P10 IRR", f"{summary['p10_irr']:.1%}")
    risk_cols[2].metric("P90 IRR", f"{summary['p90_irr']:.1%}")
    risk_cols[3].metric("Below hurdle", f"{summary['probability_irr_below_hurdle']:.1%}")
    risk_cols[4].metric("Negative NPV", f"{summary['probability_negative_npv']:.1%}")
    st.bar_chart(simulations["levered_irr"].clip(-1, 1).round(3).value_counts().sort_index())

with development_tab:
    st.subheader("Monthly development feasibility")
    development = DevelopmentInputs(land_cost=5_000_000, hard_cost=12_000_000, soft_cost=2_500_000, stabilized_noi=1_800_000, exit_cap_rate=0.06, debt_to_cost=0.55)
    result = development_feasibility(development)
    dev_cols = st.columns(5)
    dev_cols[0].metric("Total cost", f"${result['total_development_cost']:,.0f}")
    dev_cols[1].metric("Equity required", f"${result['equity_required']:,.0f}")
    dev_cols[2].metric("Exit value", f"${result['exit_value']:,.0f}")
    dev_cols[3].metric("Investor IRR", f"{result['investor_irr']:.1%}")
    dev_cols[4].metric("Investor multiple", f"{result['investor_equity_multiple']:.2f}x")
    monthly_inputs = MonthlyDevelopmentInputs(land_cost=5_000_000, hard_cost=12_000_000, soft_cost=2_500_000, stabilized_annual_noi=1_800_000)
    monthly_model, monthly_summary = monthly_development_model(monthly_inputs)
    st.dataframe(monthly_model.tail(12).style.format({"total_draw": "${:,.0f}", "debt_draw": "${:,.0f}", "interest": "${:,.0f}", "ending_debt": "${:,.0f}", "noi": "${:,.0f}", "sale_proceeds": "${:,.0f}"}), use_container_width=True, hide_index=True)
    st.caption(f"Capitalized interest: ${monthly_summary['capitalized_interest']:,.0f} · Project IRR before waterfall: {monthly_summary['project_irr']:.1%}")
    debt_sizing = size_debt(noi, underwriting["entry_cap_rate"], 0.60, 1.25, 0.07, 25, price)
    st.write(f"Debt sizing: ${debt_sizing['recommended_loan']:,.0f} recommended, constrained by the lower of LTV (${debt_sizing['ltv_limit']:,.0f}) and DSCR (${debt_sizing['dscr_limit']:,.0f}).")

with portfolio_tab:
    st.subheader("Portfolio impact")
    markets = pd.read_csv(Path("data/market_inputs.csv"))
    ranked = rank_markets(markets)
    portfolio_deals = pd.DataFrame([
        {"asset": "Core-plus logistics · Dubai", "equity_required": underwriting["equity_required"], "risk_adjusted_score": float(ranked.iloc[0]["risk_adjusted_score"]), "levered_irr": underwriting["levered_irr"], "minimum_dscr": underwriting["minimum_dscr"]},
        {"asset": "Residential value-add · London", "equity_required": underwriting["equity_required"] * 0.8, "risk_adjusted_score": float(ranked.iloc[1]["risk_adjusted_score"]), "levered_irr": underwriting["levered_irr"] - 0.015, "minimum_dscr": underwriting["minimum_dscr"] - 0.05},
        {"asset": "Development pipeline · Riyadh", "equity_required": result["equity_required"], "risk_adjusted_score": float(ranked.iloc[2]["risk_adjusted_score"]), "levered_irr": result["investor_irr"], "minimum_dscr": 1.35},
    ])
    capital = st.number_input("Available equity ($)", min_value=1_000_000, value=25_000_000, step=1_000_000)
    snapshot = portfolio_snapshot(portfolio_deals, capital)
    pcols = st.columns(5)
    pcols[0].metric("Eligible assets", f"{int(snapshot['eligible_assets'])}")
    pcols[1].metric("Allocated equity", f"${snapshot['allocated_equity']:,.0f}")
    pcols[2].metric("Unallocated", f"${snapshot['unallocated_equity']:,.0f}")
    pcols[3].metric("Weighted IRR", f"{snapshot['weighted_irr']:.1%}")
    pcols[4].metric("Min portfolio DSCR", f"{snapshot['minimum_portfolio_dscr']:.2f}x")
    st.dataframe(portfolio_allocation(portfolio_deals, capital).style.format({"equity_required": "${:,.0f}", "risk_adjusted_score": "{:.1f}", "levered_irr": "{:.1%}", "minimum_dscr": "{:.2f}x", "recommended_allocation": "${:,.0f}"}), use_container_width=True, hide_index=True)

with governance_tab:
    st.subheader("Investment committee governance")
    st.dataframe(ic_workflow(), use_container_width=True, hide_index=True)
    assumptions = assumption_register({"purchase_price": (price, "USD"), "annual_noi": (noi, "USD / year"), "noi_growth": (growth, "%"), "exit_cap_rate": (exit_cap, "%"), "leverage": (leverage, "%"), "hurdle_rate": (hurdle, "%")})
    st.markdown("**Versioned assumption register**")
    st.dataframe(assumptions, use_container_width=True, hide_index=True)
    st.markdown("**Output lineage**")
    st.json(default_lineage())
    st.download_button("Download lineage JSON", lineage_json(default_lineage()), file_name="atlasre-lineage.json", mime="application/json")
    st.caption("Every default is marked REVIEW REQUIRED until a source citation and reviewer are attached.")

with markets_tab:
    st.subheader("Global market intelligence")
    ranked = rank_markets(pd.read_csv(Path("data/market_inputs.csv")))
    st.dataframe(ranked.style.format({"score_0_100": "{:.1f}", "risk_adjusted_score": "{:.1f}"}), use_container_width=True, hide_index=True)
    st.bar_chart(ranked.set_index("market")["risk_adjusted_score"])
    st.caption("Market inputs are illustrative placeholders; production ingestion must attach timestamped sources and confidence scores.")

st.divider()
st.caption("AtlasRE v0.3 · deterministic financial core + explicit governance primitives · illustrative data only")
