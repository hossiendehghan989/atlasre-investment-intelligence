from pathlib import Path

import pandas as pd
import streamlit as st

from src.atlasre import DealInputs, market_score, rank_markets, scenario_matrix, underwrite_deal

st.set_page_config(page_title="AtlasRE Investment Intelligence", page_icon="◆", layout="wide")
st.title("AtlasRE Investment Intelligence")
st.caption("Transparent underwriting and market intelligence for global real-estate decisions")
st.info("This dashboard is an analytical prototype using illustrative assumptions. It is not investment advice and does not use private Tamleek data.")

st.header("Investment committee underwriting")
left, right = st.columns(2)
price = left.number_input("Purchase price ($)", min_value=100_000, value=10_000_000, step=250_000)
noi = left.number_input("Annual NOI ($)", min_value=10_000, value=650_000, step=25_000)
hold = left.slider("Hold period (years)", 1, 15, 5)
growth = right.slider("Annual NOI growth", 0.0, 0.10, 0.03, 0.005)
exit_cap = right.slider("Exit cap rate", 0.03, 0.12, 0.06, 0.005)
leverage = right.slider("Leverage", 0.0, 0.80, 0.50, 0.05)

deal = DealInputs(price, noi, hold, growth, exit_cap, 0.10, 0.03, 0.02, leverage)
result = underwrite_deal(deal)
cols = st.columns(5)
cols[0].metric("Entry cap", f"{result['entry_cap_rate']:.2%}")
cols[1].metric("Levered IRR", f"{result['levered_irr']:.2%}")
cols[2].metric("Unlevered IRR", f"{result['unlevered_irr']:.2%}")
cols[3].metric("Equity multiple", f"{result['equity_multiple']:.2f}x")
cols[4].metric("Exit value", f"${result['exit_value']:,.0f}")

st.subheader("Scenario matrix")
scenarios = scenario_matrix(deal)
st.dataframe(scenarios.style.format({"noi_growth": "{:.1%}", "exit_cap_rate": "{:.1%}", "levered_irr": "{:.1%}", "unlevered_irr": "{:.1%}", "exit_value": "${:,.0f}", "npv": "${:,.0f}"}), use_container_width=True, hide_index=True)

st.header("Global market intelligence")
markets = pd.read_csv(Path("data/market_inputs.csv"))
ranked = rank_markets(markets)
st.dataframe(ranked.style.format({"score_0_100": "{:.1f}", "risk_adjusted_score": "{:.1f}"}), use_container_width=True, hide_index=True)
st.bar_chart(ranked.set_index("market")["risk_adjusted_score"])
st.caption("Market inputs are illustrative placeholders. Replace them with verified public data before making a decision.")
