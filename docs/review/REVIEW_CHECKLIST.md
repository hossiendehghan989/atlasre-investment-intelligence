# Independent model review checklist

Use one row per finding. Mark **Agree**, **Disagree**, or **Unclear**, add comments, and assign severity: **Blocker / Material / Minor / Informational**.

| Topic | Review point | Agree / disagree / unclear | Comments | Severity |
| --- | --- | --- | --- | --- |
| Year-one NOI | Supplied annual NOI is treated as year-one NOI and growth starts in year two. |  |  |  |
| Exit NOI | Exit value uses final-year NOI divided by exit cap rate. |  |  |  |
| Debt amortization | Monthly amortization, interest, principal, balloon balance, and annual roll-up are coherent. |  |  |  |
| Exit and selling costs | Selling cost is applied to exit value and deducted at exit. |  |  |  |
| Equity multiple | Definition uses positive levered distributions divided by negative levered contributions. |  |  |  |
| DSCR | Minimum DSCR uses annual NOI divided by annual debt service; no-debt output is appropriately unavailable or disclosed. |  |  |  |
| Downside / Monte Carlo | Seed, shock distributions, clipping bounds, simulation count, and first-root IRR convention are disclosed and appropriate for screening. |  |  |  |
| Source-status gating | `VERIFIED` requires both a non-empty verifier and source reference; otherwise output remains `REVIEW REQUIRED`. |  |  |  |
| Taxes | Property and income tax treatment is either adequate for the use case or clearly out of scope. |  |  |  |
| Capex reserve | Capital expenditure reserve and recurring capital needs are addressed or clearly excluded. |  |  |  |
| TI / LC | Tenant improvements and leasing commissions are addressed or clearly excluded. |  |  |  |
| Refinance | Refinance, maturity, balloon, and capital-stack effects are addressed or clearly excluded. |  |  |  |
| Valuation | Exit cap and terminal value evidence requirements are clear. |  |  |  |
| Reconciliation | Excel formula outputs and Python outputs can be compared and differences are visible. |  |  |  |
| Scope | Prototype boundaries prevent treating the output as an approval, valuation, or source-document validation. |  |  |  |

## Finding summary

**Overall disposition:** [OWNER TO FILL: reviewer disposition]

**Highest-severity finding:** [OWNER TO FILL: finding reference]

**Reviewer name/contact:** [OWNER TO FILL: name/contact]
