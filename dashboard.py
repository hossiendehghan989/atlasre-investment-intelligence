from pathlib import Path

import pandas as pd
import streamlit as st

from generate_committee_report import MODEL_VERSION, screening_package_zip
from src.advanced_underwriting import DevelopmentInputs, development_feasibility, monte_carlo_underwriting, risk_summary, stress_test
from src.atlasre import DealInputs, rank_markets, scenario_matrix, underwrite_deal
from src.committee_analytics import investment_committee_summary, sensitivity_table
from src.debt import DebtTerms, monthly_debt_schedule, size_debt_from_constraints
from src.governance import default_lineage, ic_workflow, lineage_json, model_run_fingerprint, versioned_assumptions
from src.ic_workflow import DealCase, compare_deals, generate_ic_memo, screen_case
from src.institutional import MonthlyDevelopmentInputs, WaterfallTier, monthly_development_model, multi_tier_waterfall, size_debt
from src.lease import LeaseUnderwritingInputs, illustrative_rent_roll, lease_summary, underwrite_with_lease_roll
from src.portfolio import portfolio_allocation, portfolio_risk_view, portfolio_snapshot


st.set_page_config(page_title="AtlasRE Investment Intelligence", page_icon="◆", layout="wide")


@st.cache_data(show_spinner=False)
def run_risk_case(deal: DealInputs, hurdle: float) -> tuple[pd.DataFrame, dict[str, float]]:
    simulations = monte_carlo_underwriting(deal, simulations=2_000, seed=42)
    return simulations, risk_summary(simulations, hurdle)


@st.cache_data(show_spinner=False)
def build_download(deal: DealInputs) -> bytes:
    return screening_package_zip(deal, simulations=1_000)


st.title("AtlasRE Investment Intelligence")
st.caption("Investment Committee decision surface · deterministic, auditable, and illustrative by default")
st.info("Screening workspace using illustrative inputs. Every output is decision support, not investment, legal, tax, engineering, or accounting advice.")

with st.sidebar:
    st.header("Screening assumptions")
    st.caption("Inputs are illustrative until source-backed and reviewer-verified.")
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
current_case = DealCase("ATLAS-001", "Core-plus screening case", base_deal, "REVIEW REQUIRED")
screen = screen_case(current_case)
simulations, risk = run_risk_case(base_deal, hurdle)
assumptions = versioned_assumptions(
    {
        "purchase_price": (price, "USD"),
        "annual_noi": (noi, "USD / year"),
        "annual_noi_growth": (growth, "%"),
        "exit_cap_rate": (exit_cap, "%"),
        "leverage": (leverage, "%"),
        "hurdle_rate": (hurdle, "%"),
    },
    deal_id=current_case.deal_id,
    version=1,
    source="Illustrative dashboard input",
)
fingerprint = model_run_fingerprint(MODEL_VERSION, assumptions, default_lineage())

st.markdown("## Investment Committee decision surface")
status_col, source_col, fingerprint_col = st.columns([1, 1, 2])
status_col.metric("Decision status", screen["status"])
source_col.metric("Source status", current_case.source_status)
fingerprint_col.code(f"Model-run fingerprint\n{fingerprint}", language=None)
st.caption("An unverified source package cannot receive `PASSES INITIAL SCREEN`. Downside and governance appear before attractive base-case metrics.")

flags_df = pd.DataFrame(screen["flags"])
st.dataframe(flags_df, use_container_width=True, hide_index=True)

st.markdown("### Downside and risk tails")
downside_cols = st.columns(5)
downside_cols[0].metric("Expected shortfall IRR (worst 10%)", f"{risk['expected_shortfall_irr_10']:.1%}")
downside_cols[1].metric("Probability negative NPV", f"{risk['probability_negative_npv']:.1%}")
downside_cols[2].metric("Probability DSCR < 1.25x", f"{risk['probability_dscr_below_125']:.1%}")
downside_cols[3].metric("Minimum DSCR", f"{underwriting['minimum_dscr']:.2f}x")
downside_cols[4].metric("Unlevered NPV", f"${underwriting['unlevered_npv']:,.0f}")

package_col, detail_col = st.columns([1, 2])
package_col.download_button(
    "Download IC Screening Package",
    build_download(base_deal),
    file_name="atlasre-ic-screening-package.zip",
    mime="application/zip",
    use_container_width=True,
)
detail_col.caption(
    f"Break-even exit cap at {hurdle:.1%} hurdle: {committee['break_even_exit_cap']:.2%} · "
    f"P05 IRR: {risk['p05_irr']:.1%} · Worst IRR: {risk['worst_irr']:.1%}"
)

st.markdown("### Base-case economic results")
metric_cols = st.columns(6)
metric_cols[0].metric("Entry cap", f"{underwriting['entry_cap_rate']:.2%}")
metric_cols[1].metric("Levered IRR", f"{underwriting['levered_irr']:.2%}")
metric_cols[2].metric("Unlevered IRR", f"{underwriting['unlevered_irr']:.2%}")
metric_cols[3].metric("Equity multiple", f"{underwriting['equity_multiple']:.2f}x")
metric_cols[4].metric("Debt at exit", f"${underwriting['remaining_debt_at_exit']:,.0f}")
metric_cols[5].metric("Exit value", f"${underwriting['exit_value']:,.0f}")

ic_tab, risk_tab, underwriting_tab, lease_development_tab, portfolio_tab, governance_tab, markets_tab = st.tabs([
    "IC workflow", "Risk & scenarios", "Underwriting", "Lease & development", "Portfolio", "Governance", "Markets"
])

with ic_tab:
    st.subheader("Initial-screen workflow")
    st.dataframe(ic_workflow(), use_container_width=True, hide_index=True)
    st.markdown("**Committee presentation order**")
    st.write("Start with source status and the decision state. Review governance and critical flags, tail risk, NPV, DSCR, and stress outcomes. Only then review base-case returns and decide what diligence could change the initial view.")
    st.download_button(
        "Download IC screening memo",
        generate_ic_memo(current_case, hurdle, model_version=MODEL_VERSION, risk_metrics=risk),
        file_name="atlasre-screening-memo.md",
        mime="text/markdown",
    )

with risk_tab:
    st.subheader("Risk engine")
    st.dataframe(
        stress_test(base_deal).style.format({"levered_irr": "{:.1%}", "unlevered_irr": "{:.1%}", "npv": "${:,.0f}", "exit_value": "${:,.0f}", "minimum_dscr": "{:.2f}x"}),
        use_container_width=True,
        hide_index=True,
    )
    risk_cols = st.columns(4)
    risk_cols[0].metric("P05 IRR", f"{risk['p05_irr']:.1%}")
    risk_cols[1].metric("P10 IRR", f"{risk['p10_irr']:.1%}")
    risk_cols[2].metric("Median IRR", f"{risk['median_irr']:.1%}")
    risk_cols[3].metric("P95 IRR", f"{risk['p95_irr']:.1%}")
    st.caption(f"Expected shortfall, worst 10% NPV: ${risk['expected_shortfall_npv_10']:,.0f} · Below-hurdle probability: {risk['probability_irr_below_hurdle']:.1%}")
    st.bar_chart(simulations["levered_irr"].clip(-1, 1).round(3).value_counts().sort_index())

with underwriting_tab:
    st.subheader("Scenario grid")
    st.dataframe(
        scenario_matrix(base_deal).style.format({"noi_growth": "{:.1%}", "exit_cap_rate": "{:.1%}", "levered_irr": "{:.1%}", "unlevered_irr": "{:.1%}", "exit_value": "${:,.0f}", "npv": "${:,.0f}"}),
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("One-way exit-cap sensitivity")
    sensitivity = sensitivity_table(base_deal, "exit_cap_rate", [0.05, 0.055, 0.06, 0.065, 0.07])
    st.dataframe(
        sensitivity.style.format({"exit_cap_rate": "{:.1%}", "levered_irr": "{:.1%}", "unlevered_npv": "${:,.0f}", "minimum_dscr": "{:.2f}x", "exit_value": "${:,.0f}"}),
        use_container_width=True,
        hide_index=True,
    )

with lease_development_tab:
    st.subheader("Optional lease-level foundation")
    st.caption("Illustrative rent roll only. The lease path is explicit and does not silently replace the annual-NOI path. TI/LC, downtime, recoveries, capex, and tenant-credit evidence remain outside this foundation.")
    demo_leases = illustrative_rent_roll()
    lease_inputs = LeaseUnderwritingInputs(tuple(demo_leases), demo_leases[0].start, months=24, operating_expense_ratio=.20)
    lease_case = underwrite_with_lease_roll(base_deal, lease_inputs)
    lease_cols = st.columns(3)
    lease_cols[0].metric("Lease-derived annual NOI", f"${lease_case['lease_derived_annual_noi']:,.0f}")
    lease_cols[1].metric("Lease-path levered IRR", f"{lease_case['underwriting']['levered_irr']:.1%}")
    lease_cols[2].metric("Lease-path minimum DSCR", f"{lease_case['underwriting']['minimum_dscr']:.2f}x")
    st.dataframe(lease_summary(demo_leases).style.format({"annual_rent": "${:,.0f}", "annual_escalation": "{:.1%}", "vacancy_assumption": "{:.1%}", "rollover_rent_change": "{:.1%}"}), use_container_width=True, hide_index=True)
    st.dataframe(lease_case["lease_annual_summary"].style.format({column: "${:,.0f}" for column in lease_case["lease_annual_summary"].columns if column != "year"}), use_container_width=True, hide_index=True)

    st.subheader("Monthly development, debt, and waterfall reference case")
    development = DevelopmentInputs(land_cost=5_000_000, hard_cost=12_000_000, soft_cost=2_500_000, stabilized_noi=1_800_000, exit_cap_rate=0.06, debt_to_cost=0.55)
    result = development_feasibility(development)
    monthly_inputs = MonthlyDevelopmentInputs(land_cost=5_000_000, hard_cost=12_000_000, soft_cost=2_500_000, stabilized_annual_noi=1_800_000)
    monthly_model, monthly_summary = monthly_development_model(monthly_inputs)
    dev_cols = st.columns(4)
    dev_cols[0].metric("Total cost", f"${result['total_development_cost']:,.0f}")
    dev_cols[1].metric("Equity required", f"${result['equity_required']:,.0f}")
    dev_cols[2].metric("Capitalized interest", f"${monthly_summary['capitalized_interest']:,.0f}")
    dev_cols[3].metric("Project IRR before waterfall", f"{monthly_summary['project_irr']:.1%}")
    st.dataframe(monthly_model.tail(12).style.format({"total_draw": "${:,.0f}", "debt_draw": "${:,.0f}", "interest": "${:,.0f}", "ending_debt": "${:,.0f}", "noi": "${:,.0f}", "sale_proceeds": "${:,.0f}"}), use_container_width=True, hide_index=True)

    terms = DebtTerms(annual_rate=0.07, amortization_years=25, term_months=hold * 12, interest_only_months=12)
    monthly_noi = [noi * (1 + growth) ** (month // 12) for month in range(terms.term_months)]
    constrained = size_debt_from_constraints(monthly_noi, price, 0.60, 1.25, terms)
    st.caption(f"Debt sizing binding constraint: **{constrained['binding_constraint']}** · Recommended loan: ${constrained['recommended_loan']:,.0f}")
    schedule = monthly_debt_schedule(constrained["recommended_loan"], terms, noi=monthly_noi)
    st.dataframe(schedule.tail(12).style.format({"beginning_balance": "${:,.0f}", "interest": "${:,.0f}", "scheduled_payment": "${:,.0f}", "principal_paid": "${:,.0f}", "ending_balance": "${:,.0f}", "balloon_payoff": "${:,.0f}", "dscr": "{:.2f}x"}), use_container_width=True, hide_index=True)
    waterfall = multi_tier_waterfall(result["equity_required"], result["equity_required"] + max(result["project_profit_before_waterfall"], 0), 0.08, 5, [WaterfallTier(0.12, 0.20, "Tier 1"), WaterfallTier(0.18, 0.30, "Tier 2")])
    st.dataframe(pd.DataFrame(waterfall["tiers"]).style.format({"hurdle_rate": "{:.1%}", "promote_pct": "{:.1%}", "tier_cash": "${:,.0f}", "lp_share": "${:,.0f}", "gp_share": "${:,.0f}"}), use_container_width=True, hide_index=True)

with portfolio_tab:
    st.subheader("Portfolio impact")
    ranked = rank_markets(pd.read_csv(Path("data/market_inputs.csv")))
    development_reference = development_feasibility(DevelopmentInputs(5_000_000, 12_000_000, 2_500_000, stabilized_noi=1_800_000))
    portfolio_deals = pd.DataFrame([
        {"asset": "Core-plus logistics · Dubai", "equity_required": underwriting["equity_required"], "risk_adjusted_score": float(ranked.iloc[0]["risk_adjusted_score"]), "levered_irr": underwriting["levered_irr"], "minimum_dscr": underwriting["minimum_dscr"]},
        {"asset": "Residential value-add · London", "equity_required": underwriting["equity_required"] * 0.8, "risk_adjusted_score": float(ranked.iloc[1]["risk_adjusted_score"]), "levered_irr": underwriting["levered_irr"] - 0.015, "minimum_dscr": underwriting["minimum_dscr"] - 0.05},
        {"asset": "Development pipeline · Riyadh", "equity_required": development_reference["equity_required"], "risk_adjusted_score": float(ranked.iloc[2]["risk_adjusted_score"]), "levered_irr": development_reference["investor_irr"], "minimum_dscr": 1.35},
    ])
    capital = st.number_input("Available equity ($)", min_value=1_000_000, value=25_000_000, step=1_000_000)
    snapshot = portfolio_snapshot(portfolio_deals, capital)
    pcols = st.columns(5)
    pcols[0].metric("Eligible assets", f"{int(snapshot['eligible_assets'])}")
    pcols[1].metric("Allocated equity", f"${snapshot['allocated_equity']:,.0f}")
    pcols[2].metric("Unallocated", f"${snapshot['unallocated_equity']:,.0f}")
    pcols[3].metric("Weighted IRR", f"{snapshot['weighted_irr']:.1%}")
    pcols[4].metric("Min portfolio DSCR", f"{snapshot['minimum_portfolio_dscr']:.2f}x")
    allocation = portfolio_allocation(portfolio_deals, capital)
    risk_view = portfolio_risk_view(allocation)
    st.caption(f"DSCR-breach exposure: {risk_view['dscr_breach_exposure']:.1%} · Negative-IRR exposure: {risk_view['negative_irr_exposure']:.1%} · Concentration HHI: {risk_view['concentration_hhi']:.3f} · Max asset weight: {risk_view['max_asset_weight']:.1%}")
    st.dataframe(allocation.style.format({"equity_required": "${:,.0f}", "risk_adjusted_score": "{:.1f}", "levered_irr": "{:.1%}", "minimum_dscr": "{:.2f}x", "recommended_allocation": "${:,.0f}"}), use_container_width=True, hide_index=True)

with governance_tab:
    st.subheader("Assumption register and reproducibility")
    st.dataframe(assumptions, use_container_width=True, hide_index=True)
    st.markdown("**Output lineage**")
    st.json(default_lineage())
    st.download_button("Download lineage JSON", lineage_json(default_lineage()), file_name="atlasre-lineage.json", mime="application/json")
    st.code(fingerprint, language=None)
    comparison_case = DealCase("ATLAS-002", "Higher-growth challenge case", DealInputs(price * 1.05, noi * 1.08, hold, growth + 0.01, exit_cap - 0.005, hurdle - 0.02, 0.03, 0.02, leverage))
    st.markdown("**Side-by-side deal comparison**")
    st.dataframe(compare_deals([current_case, comparison_case], hurdle).style.format({"entry_cap": "{:.2%}", "levered_irr": "{:.2%}", "unlevered_irr": "{:.2%}", "equity_multiple": "{:.2f}x", "minimum_dscr": "{:.2f}x", "unlevered_npv": "${:,.0f}"}), use_container_width=True, hide_index=True)
    st.caption("Every default is marked REVIEW REQUIRED until a source citation and reviewer are attached. Fingerprinting provides reproducibility evidence; it does not create a persistent approval record.")

with markets_tab:
    st.subheader("Global market intelligence")
    ranked = rank_markets(pd.read_csv(Path("data/market_inputs.csv")))
    st.dataframe(ranked.style.format({"score_0_100": "{:.1f}", "risk_adjusted_score": "{:.1f}"}), use_container_width=True, hide_index=True)
    st.bar_chart(ranked.set_index("market")["risk_adjusted_score"])
    st.caption("Market inputs are illustrative placeholders; production ingestion must attach timestamped sources and confidence scores.")

st.divider()
st.caption("AtlasRE v0.10 · deterministic financial core + source-aware governance + auditable IC screening · illustrative data only")
