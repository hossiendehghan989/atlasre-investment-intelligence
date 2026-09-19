from pathlib import Path

from src.atlasre import DealInputs, underwrite_deal
from src.advanced_underwriting import monte_carlo_underwriting, risk_summary, stress_test
from src.institutional import MonthlyDevelopmentInputs, monthly_development_model, size_debt

out = Path("artifacts")
out.mkdir(exist_ok=True)
deal = DealInputs(10_000_000, 650_000, hold_years=5, leverage=0.5)
underwriting = underwrite_deal(deal)
simulations = monte_carlo_underwriting(deal, simulations=5000)
risk = risk_summary(simulations)
stress = stress_test(deal)
monthly, development = monthly_development_model(MonthlyDevelopmentInputs(5_000_000, 12_000_000, 2_500_000))
debt = size_debt(deal.annual_noi, deal.entry_cap_rate if hasattr(deal, "entry_cap_rate") else 0.06, 0.60, 1.25, 0.07, 25, deal.purchase_price)

report = f'''# AtlasRE Investment Committee Review\n\n## Purpose\n\nThis report is a screening document generated from explicit illustrative assumptions. It is not an approval, valuation opinion, or investment recommendation.\n\n## Acquisition screen\n\n| Metric | Value |\n|---|---:|\n| Purchase price | ${deal.purchase_price:,.0f} |\n| Annual NOI | ${deal.annual_noi:,.0f} |\n| Entry cap rate | {underwriting["entry_cap_rate"]:.2%} |\n| Levered IRR | {underwriting["levered_irr"]:.2%} |\n| Unlevered IRR | {underwriting["unlevered_irr"]:.2%} |\n| Minimum DSCR | {underwriting["minimum_dscr"]:.2f}x |\n| Debt at exit | ${underwriting["remaining_debt_at_exit"]:,.0f} |\n| Unlevered NPV | ${underwriting["unlevered_npv"]:,.0f} |\n\n## Risk distribution\n\n| Metric | Value |\n|---|---:|\n| Median levered IRR | {risk["median_irr"]:.2%} |\n| P10 levered IRR | {risk["p10_irr"]:.2%} |\n| P90 levered IRR | {risk["p90_irr"]:.2%} |\n| Probability IRR below hurdle | {risk["probability_irr_below_hurdle"]:.2%} |\n| Probability of negative NPV | {risk["probability_negative_npv"]:.2%} |\n\n## Development case\n\n| Metric | Value |\n|---|---:|\n| Total development cost | ${development["total_cost"]:,.0f} |\n| Equity required | ${development["equity_required"]:,.0f} |\n| Capitalized interest | ${development["capitalized_interest"]:,.0f} |\n| Exit value | ${development["exit_value"]:,.0f} |\n| Project IRR | {development["project_irr"]:.2%} |\n\n## Initial conclusion\n\nThe opportunity should advance only after rent-roll verification, operating-statement reconciliation, construction-budget validation, financing term-sheet review, title and legal diligence, tax review, and independent market evidence. The model's purpose is to focus that diligence, not replace it.\n'''
(out / "investment_committee_report.md").write_text(report)
stress.to_csv(out / "stress_cases.csv", index=False)
monthly.to_csv(out / "monthly_development_model.csv", index=False)
print(out / "investment_committee_report.md")
