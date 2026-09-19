# AtlasRE Investment Intelligence

## A transparent decision-support system for global real-estate investing

AtlasRE is a portfolio project designed around the real questions faced by a real-estate investment and development firm: **Which opportunity deserves attention? What assumptions drive its return? How fragile is the thesis? How should an investment committee compare markets and deals?**

The project is intentionally aligned with the public strategy of global real-estate investment platforms that combine REIT exposure, luxury development, general investments, advisory, and brokerage. It is not affiliated with Tamleek, does not use private company data, and does not provide investment advice. Its purpose is to demonstrate the author's ability to convert finance and real-estate reasoning into a tested analytical product.

## Why this project stands out

Most real-estate portfolio projects stop at a property-value calculator. AtlasRE goes further by connecting four layers:

1. **Underwriting:** NOI growth, entry yield, exit capitalization, debt, equity, IRR, NPV, and equity multiple.
2. **Scenario analysis:** downside, base, and upside combinations across growth and exit-cap assumptions.
3. **Market intelligence:** risk-adjusted market ranking across growth, employment, rents, liquidity, and risk.
4. **Portfolio thinking:** capital allocation across eligible opportunities using risk-adjusted scores.

The result is not a black-box prediction. It is an auditable investment committee workflow in which every important output can be traced to an explicit assumption.

## Core model

For each opportunity, the engine forecasts NOI through the hold period:

```text
NOI_t = NOI_0 × (1 + growth)^t
```

The terminal value is estimated through the exit capitalization method:

```text
Exit Value = Forward NOI / Exit Cap Rate
```

The cash-flow engine then accounts for acquisition costs, selling costs, debt, annual debt service, and equity contributions. It reports both levered and unlevered returns because leverage can improve equity returns while increasing refinancing and downside risk.

## What the dashboard shows

The Streamlit dashboard contains two decision surfaces. The underwriting view allows an investment committee member to change purchase price, NOI, growth, hold period, exit cap, and leverage. It immediately shows entry cap, levered IRR, unlevered IRR, equity multiple, exit value, and a full sensitivity matrix.

The market view ranks illustrative global markets using a transparent weighted score. The sample inputs are placeholders and are visibly labeled as such. This is deliberate: the project demonstrates the methodology without presenting invented market statistics as facts.

## Example underwriting assumptions

| Input | Illustrative value |
| --- | ---: |
| Purchase price | $10,000,000 |
| Annual NOI | $650,000 |
| Hold period | 5 years |
| NOI growth | 3.0% |
| Exit cap rate | 6.0% |
| Leverage | 50.0% |

These values are defaults for demonstration and must be replaced with verified asset-level information before any real decision.

## Engineering quality

The repository includes a modular Python engine, a Streamlit interface, automated tests, input validation, and a clear separation between assumptions and calculations. The test suite covers cash-flow structure, scenario behavior, market-risk ranking, and capital-allocation constraints.

## Quick start

```bash
git clone https://github.com/hossiendehghan989/atlasre-investment-intelligence.git
cd atlasre-investment-intelligence
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
streamlit run dashboard.py
```

## Project structure

```text
.
├── dashboard.py
├── data/market_inputs.csv
├── requirements.txt
├── src/atlasre.py
└── tests/test_atlasre.py
```

## Resume-ready description

> Built **AtlasRE Investment Intelligence**, a transparent real-estate underwriting and market-ranking platform that models NOI growth, exit capitalization, leverage, IRR, NPV, equity multiples, downside/base/upside scenarios, and risk-adjusted global-market allocation. Delivered a tested Streamlit investment-committee dashboard using Python, pandas, SciPy, and reproducible analytical assumptions.

## Why it is relevant to global real-estate leadership

The project is built around strategic questions rather than a generic coding exercise. It demonstrates an understanding of selective asset acquisition, stakeholder value, cross-market comparison, investment advisory, and the relationship between development assumptions and returns. It also reflects the legal and governance reality of property transactions by keeping assumptions explicit and separating analytical output from an investment decision.

## Limitations

This is a research and portfolio prototype. The default market data is illustrative, not a live market feed. The valuation is not a full development feasibility model and does not include taxes, construction draws, operating-expense detail, waterfall structures, preferred returns, FX exposure, refinancing, or legal diligence. The system must not be used as a substitute for verified financial, legal, tax, engineering, or market analysis.

## License

MIT License.
