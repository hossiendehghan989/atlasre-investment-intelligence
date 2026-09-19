from pathlib import Path

import pandas as pd
import streamlit as st

from generate_committee_report import MODEL_VERSION, screening_package_zip
from src.advanced_underwriting import monte_carlo_underwriting, risk_summary, stress_test
from src.atlasre import DealInputs, rank_markets, scenario_matrix, underwrite_deal
from src.committee_analytics import investment_committee_summary, sensitivity_table
from src.debt import DebtTerms, monthly_debt_schedule, size_debt_from_constraints
from src.governance import default_lineage, lineage_json, model_run_fingerprint, versioned_assumptions
from src.ic_workflow import DealCase, compare_deals, generate_ic_memo, screen_case
from src.institutional import MonthlyDevelopmentInputs, monthly_development_model
from src.lease import LeaseUnderwritingInputs, illustrative_rent_roll, lease_summary, underwrite_with_lease_roll
from src.portfolio import portfolio_allocation, portfolio_risk_view, portfolio_snapshot


st.set_page_config(page_title="AtlasRE | Deal Review", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    :root { --ink:#202a33; --muted:#6d7780; --line:#dfe3e6; --navy:#17324d; --red:#a33a3a; --paper:#fbfbfa; }
    .stApp { background:var(--paper); color:var(--ink); }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stSidebar"] { background:#f1f3f2; border-right:1px solid var(--line); }
    [data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:2px; padding:12px 14px; }
    [data-testid="stMetricLabel"] { color:var(--muted); font-size:.78rem; }
    [data-testid="stMetricValue"] { color:var(--ink); font-size:1.45rem; }
    div[data-testid="stDataFrame"] { border:1px solid var(--line); }
    .case-kicker { color:var(--muted); font-size:.78rem; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.2rem; }
    .case-title { color:var(--navy); font-family:Georgia,serif; font-size:2rem; line-height:1.15; margin:0; }
    .case-meta { color:var(--muted); font-size:.85rem; margin-top:.35rem; }
    .status-review { display:inline-block; color:#8b2e2e; background:#f5e7e5; border:1px solid #e5c3bf; padding:6px 10px; border-radius:2px; font-size:.78rem; font-weight:600; letter-spacing:.03em; }
    .status-pass { display:inline-block; color:#2d6044; background:#e8f1ea; border:1px solid #bfd7c5; padding:6px 10px; border-radius:2px; font-size:.78rem; font-weight:600; letter-spacing:.03em; }
    .section-rule { border-top:1px solid var(--line); margin:1.2rem 0 .9rem; }
    .small-note { color:var(--muted); font-size:.78rem; line-height:1.45; }
    h1, h2, h3 { color:var(--navy); }
    h2 { font-family:Georgia,serif; font-weight:500; font-size:1.35rem; }
    h3 { font-size:1rem; font-weight:600; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def run_risk_case(deal: DealInputs, hurdle: float) -> tuple[pd.DataFrame, dict[str, float]]:
    simulations = monte_carlo_underwriting(deal, simulations=2_000, seed=42)
    return simulations, risk_summary(simulations, hurdle)


@st.cache_data(show_spinner=False)
def build_download(deal: DealInputs) -> bytes:
    return screening_package_zip(deal, simulations=1_000)


with st.sidebar:
    st.markdown("### AtlasRE")
    st.caption("Deal review · internal working paper")
    st.markdown("<div class='section-rule'></div>", unsafe_allow_html=True)
    st.markdown("**Case assumptions**")
    price = st.number_input("Purchase price ($)", min_value=100_000, value=10_000_000, step=250_000)
    noi = st.number_input("Annual NOI ($)", min_value=10_000, value=650_000, step=25_000)
    hold = st.slider("Hold period", 1, 15, 5)
    growth = st.slider("NOI growth", -0.05, 0.12, 0.03, 0.005, format="%.1f%%")
    exit_cap = st.slider("Exit cap rate", 0.03, 0.15, 0.06, 0.005, format="%.1f%%")
    leverage = st.slider("Leverage", 0.0, 0.80, 0.50, 0.05, format="%.0f%%")
    hurdle = st.slider("Return hurdle", 0.06, 0.20, 0.12, 0.01, format="%.0f%%")
    st.markdown("<div class='section-rule'></div>", unsafe_allow_html=True)
    st.caption("Change the assumptions to test the case. Confirm figures before circulation.")

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

if any(flag["severity"] == "CRITICAL" for flag in screen["flags"]):
    review_focus = "Primary review point: resolve the critical economic issue before spending time on upside scenarios."
elif current_case.source_status != "VERIFIED":
    review_focus = "Primary review point: confirm the operating statement, rent roll, and debt terms before relying on the return figures."
elif underwriting["minimum_dscr"] < 1.25:
    review_focus = "Primary review point: the debt service cushion is thin; test the case against a weaker NOI path and higher rates."
else:
    review_focus = "Primary review point: challenge terminal value, exit-cap evidence, and the assumptions that drive the operating-income path."

st.markdown("<div class='case-kicker'>Preliminary deal review</div>", unsafe_allow_html=True)
header_left, header_right = st.columns([3, 1])
with header_left:
    st.markdown("<div class='case-title'>Core-plus screening case</div>", unsafe_allow_html=True)
    st.markdown("<div class='case-meta'>ATLAS-001 · initial pass · information still being checked</div>", unsafe_allow_html=True)
with header_right:
    status_class = "status-pass" if screen["status"] == "PASSES INITIAL SCREEN" else "status-review"
    st.markdown(f"<div style='text-align:right;margin-top:12px'><span class='{status_class}'>{screen['status']}</span></div>", unsafe_allow_html=True)

st.markdown("<div class='section-rule'></div>", unsafe_allow_html=True)

st.markdown("## What needs attention")
flags = pd.DataFrame(screen["flags"])
flags = flags.rename(columns={"severity": "Level", "flag": "Issue", "evidence": "Evidence"})
flags["Level"] = flags["Level"].replace({"GOVERNANCE": "GOVERNANCE", "CRITICAL": "CRITICAL", "HIGH": "HIGH", "INFO": "INFO"})
st.dataframe(flags, use_container_width=True, hide_index=True, column_config={"Level": st.column_config.TextColumn(width="small"), "Issue": st.column_config.TextColumn(width="large"), "Evidence": st.column_config.TextColumn(width="medium")})
st.caption("This case stays in review until the open items are resolved and the supporting information is confirmed.")

st.markdown("## Downside first")
downside_cols = st.columns(4)
downside_cols[0].metric("Unlevered NPV", f"${underwriting['unlevered_npv']:,.0f}")
downside_cols[1].metric("Minimum DSCR", f"{underwriting['minimum_dscr']:.2f}x")
downside_cols[2].metric("IRR in worst 10%", f"{risk['expected_shortfall_irr_10']:.1%}")
downside_cols[3].metric("Chance of value loss", f"{risk['probability_negative_npv']:.1%}")

with st.expander("Risk tail detail", expanded=False):
    tail_left, tail_right = st.columns(2)
    with tail_left:
        st.dataframe(pd.DataFrame({"Measure": ["P05 IRR", "P10 IRR", "Worst simulated IRR", "Probability IRR below hurdle"], "Value": [f"{risk['p05_irr']:.1%}", f"{risk['p10_irr']:.1%}", f"{risk['worst_irr']:.1%}", f"{risk['probability_irr_below_hurdle']:.1%}"]}), use_container_width=True, hide_index=True)
    with tail_right:
        st.dataframe(pd.DataFrame({"Measure": ["Expected shortfall NPV", "Probability DSCR < 1.25x", "Break-even exit cap", "Debt at exit"], "Value": [f"${risk['expected_shortfall_npv_10']:,.0f}", f"{risk['probability_dscr_below_125']:.1%}", f"{committee['break_even_exit_cap']:.2%}", f"${underwriting['remaining_debt_at_exit']:,.0f}"]}), use_container_width=True, hide_index=True)

st.markdown("## Current case")
base_cols = st.columns(5)
base_cols[0].metric("Entry cap", f"{underwriting['entry_cap_rate']:.2%}")
base_cols[1].metric("Levered IRR", f"{underwriting['levered_irr']:.2%}")
base_cols[2].metric("Unlevered IRR", f"{underwriting['unlevered_irr']:.2%}")
base_cols[3].metric("Equity multiple", f"{underwriting['equity_multiple']:.2f}x")
base_cols[4].metric("Exit value", f"${underwriting['exit_value']:,.0f}")

st.markdown("<div class='section-rule'></div>", unsafe_allow_html=True)
tab_screen, tab_returns, tab_debt, tab_portfolio, tab_audit = st.tabs(["Review note", "Returns", "Debt / rent roll", "Portfolio fit", "Inputs & record"])

with tab_screen:
    left, right = st.columns([2, 1])
    with left:
        st.markdown("### Review note")
        st.write("The case remains at preliminary screening. The current return profile is conditional on the operating assumptions, terminal value, financing terms, and source package. Resolve the governance flag before treating the economic outputs as decision-ready.")
        st.info(review_focus)
        st.markdown("### Next diligence")
        st.write("Reconcile the rent roll and operating statement. Validate the exit-cap evidence and terminal-value timing. Obtain the financing term sheet and review covenants, fees, amortization, and maturity.")
    with right:
        st.markdown("### Working files")
        st.caption("The download contains the review memo, assumptions, stress cases, risk summary, debt schedule, and rent-roll reference files.")
        st.download_button("Download review files", build_download(base_deal), file_name="atlasre-deal-review.zip", mime="application/zip", use_container_width=True)
        st.download_button("Download review memo", generate_ic_memo(current_case, hurdle, model_version=MODEL_VERSION, risk_metrics=risk), file_name="atlasre-deal-review.md", mime="text/markdown", use_container_width=True)

with tab_returns:
    st.markdown("### Stress cases")
    stress = stress_test(base_deal)
    st.dataframe(stress.style.format({"levered_irr": "{:.1%}", "unlevered_irr": "{:.1%}", "npv": "${:,.0f}", "exit_value": "${:,.0f}", "minimum_dscr": "{:.2f}x"}), use_container_width=True, hide_index=True)
    st.markdown("### Exit cap sensitivity")
    sensitivity = sensitivity_table(base_deal, "exit_cap_rate", [0.05, 0.055, 0.06, 0.065, 0.07])
    st.dataframe(sensitivity.style.format({"exit_cap_rate": "{:.1%}", "levered_irr": "{:.1%}", "unlevered_npv": "${:,.0f}", "minimum_dscr": "{:.2f}x", "exit_value": "${:,.0f}"}), use_container_width=True, hide_index=True)
    with st.expander("Scenario grid", expanded=False):
        st.dataframe(scenario_matrix(base_deal).style.format({"noi_growth": "{:.1%}", "exit_cap_rate": "{:.1%}", "levered_irr": "{:.1%}", "unlevered_irr": "{:.1%}", "exit_value": "${:,.0f}", "npv": "${:,.0f}"}), use_container_width=True, hide_index=True)

with tab_debt:
    st.markdown("### Debt schedule")
    terms = DebtTerms(annual_rate=0.07, amortization_years=25, term_months=hold * 12, interest_only_months=12)
    monthly_noi = [noi * (1 + growth) ** (month // 12) for month in range(terms.term_months)]
    constrained = size_debt_from_constraints(monthly_noi, price, 0.60, 1.25, terms)
    debt_cols = st.columns(3)
    debt_cols[0].metric("Recommended loan", f"${constrained['recommended_loan']:,.0f}")
    debt_cols[1].metric("Binding constraint", constrained["binding_constraint"])
    debt_cols[2].metric("Implied LTV", f"{constrained['implied_ltv']:.1%}")
    schedule = monthly_debt_schedule(constrained["recommended_loan"], terms, noi=monthly_noi)
    st.dataframe(schedule.tail(12).style.format({"beginning_balance": "${:,.0f}", "interest": "${:,.0f}", "scheduled_payment": "${:,.0f}", "principal_paid": "${:,.0f}", "ending_balance": "${:,.0f}", "balloon_payoff": "${:,.0f}", "dscr": "{:.2f}x"}), use_container_width=True, hide_index=True)

    st.markdown("### Lease reference")
    demo_leases = illustrative_rent_roll()
    lease_inputs = LeaseUnderwritingInputs(tuple(demo_leases), demo_leases[0].start, months=24, operating_expense_ratio=.20)
    lease_case = underwrite_with_lease_roll(base_deal, lease_inputs)
    st.caption("This rent roll is a reference schedule only. It does not replace source-backed lease review.")
    lease_cols = st.columns(3)
    lease_cols[0].metric("Lease-derived annual NOI", f"${lease_case['lease_derived_annual_noi']:,.0f}")
    lease_cols[1].metric("Lease-path IRR", f"{lease_case['underwriting']['levered_irr']:.1%}")
    lease_cols[2].metric("Lease-path DSCR", f"{lease_case['underwriting']['minimum_dscr']:.2f}x")
    st.dataframe(lease_summary(demo_leases).style.format({"annual_rent": "${:,.0f}", "annual_escalation": "{:.1%}", "vacancy_assumption": "{:.1%}", "rollover_rent_change": "{:.1%}"}), use_container_width=True, hide_index=True)

with tab_portfolio:
    st.markdown("### Allocation check")
    ranked = rank_markets(pd.read_csv(Path("data/market_inputs.csv")))
    portfolio_deals = pd.DataFrame([
        {"asset": "Core-plus logistics · Dubai", "equity_required": underwriting["equity_required"], "risk_adjusted_score": float(ranked.iloc[0]["risk_adjusted_score"]), "levered_irr": underwriting["levered_irr"], "minimum_dscr": underwriting["minimum_dscr"]},
        {"asset": "Residential value-add · London", "equity_required": underwriting["equity_required"] * 0.8, "risk_adjusted_score": float(ranked.iloc[1]["risk_adjusted_score"]), "levered_irr": underwriting["levered_irr"] - 0.015, "minimum_dscr": underwriting["minimum_dscr"] - 0.05},
    ])
    capital = st.number_input("Available equity ($)", min_value=1_000_000, value=25_000_000, step=1_000_000)
    snapshot = portfolio_snapshot(portfolio_deals, capital)
    pcols = st.columns(4)
    pcols[0].metric("Eligible assets", f"{int(snapshot['eligible_assets'])}")
    pcols[1].metric("Allocated equity", f"${snapshot['allocated_equity']:,.0f}")
    pcols[2].metric("Unallocated", f"${snapshot['unallocated_equity']:,.0f}")
    pcols[3].metric("Concentration HHI", f"{snapshot['concentration_hhi']:.3f}")
    allocation = portfolio_allocation(portfolio_deals, capital)
    st.dataframe(allocation.style.format({"equity_required": "${:,.0f}", "risk_adjusted_score": "{:.1f}", "levered_irr": "{:.1%}", "minimum_dscr": "{:.2f}x", "recommended_allocation": "${:,.0f}"}), use_container_width=True, hide_index=True)
    portfolio_risk = portfolio_risk_view(allocation)
    st.caption(f"DSCR-breach exposure: {portfolio_risk['dscr_breach_exposure']:.1%} · Negative-IRR exposure: {portfolio_risk['negative_irr_exposure']:.1%}")

with tab_audit:
    st.markdown("### Inputs and run record")
    audit_left, audit_right = st.columns([1, 2])
    with audit_left:
        st.write("Source status")
        st.markdown(f"**{current_case.source_status}**")
        st.write("Model version")
        st.code(MODEL_VERSION, language=None)
    with audit_right:
        st.write("Run ID")
        st.code(fingerprint, language=None)
        st.caption("This ID ties the figures to the assumptions and calculation record used for this run.")
    st.markdown("### Assumption register")
    st.dataframe(assumptions, use_container_width=True, hide_index=True)
    with st.expander("Lineage", expanded=False):
        st.json(default_lineage())
        st.download_button("Download lineage JSON", lineage_json(default_lineage()), file_name="atlasre-lineage.json", mime="application/json")
    comparison_case = DealCase("ATLAS-002", "Higher-growth challenge case", DealInputs(price * 1.05, noi * 1.08, hold, growth + 0.01, exit_cap - 0.005, hurdle - 0.02, 0.03, 0.02, leverage))
    with st.expander("Challenge case", expanded=False):
        st.dataframe(compare_deals([current_case, comparison_case], hurdle).style.format({"entry_cap": "{:.2%}", "levered_irr": "{:.2%}", "unlevered_irr": "{:.2%}", "equity_multiple": "{:.2f}x", "minimum_dscr": "{:.2f}x", "unlevered_npv": "${:,.0f}"}), use_container_width=True, hide_index=True)

st.markdown("<div class='section-rule'></div>", unsafe_allow_html=True)
st.markdown("<div class='small-note'>Internal working paper. Figures are subject to confirmation and are not investment advice.</div>", unsafe_allow_html=True)
