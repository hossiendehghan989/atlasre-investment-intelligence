# AtlasRE Investment Intelligence — Institutional Evolution

## 1. Current strengths

AtlasRE already had a strong, unusually transparent foundation for a portfolio prototype: the Python engine separates assumptions from calculations; the underwriting layer reports both levered and unlevered outcomes; the development module includes draws, capitalized interest, stabilization and a promote waterfall; and the risk layer is reproducible through seeded simulation. The test suite covers the highest-value financial behaviors rather than only UI paths.

The gap was not another valuation formula. The gap was operating-model completeness: source lineage, versioned assumptions, a portfolio constraint layer, and a committee workflow that records what was decided and why. This iteration addresses those gaps without replacing the tested financial core.

## 2. Opinionated target architecture

| Layer | Current implementation | Production direction |
| --- | --- | --- |
| Experience | Streamlit decision surface | Next.js / React shell with role-aware IC workspace |
| API | Python functions called by Streamlit | FastAPI contracts around `src/` engines |
| Financial core | `src/atlasre.py`, `advanced_underwriting.py`, `institutional.py` | Versioned Python package with typed scenario inputs |
| Persistence | CSV and generated artifacts | PostgreSQL + PostGIS for assets, assumptions, sources, decisions |
| Semantic intelligence | Not yet persisted | Object storage + OCR + embeddings in pgvector |
| Governance | New register, lineage, hash-chain primitives | Immutable event store with signed review checkpoints |
| Orchestration | Deterministic modules | LangGraph-style agents with tool permissions and citations |

The financial core remains deterministic. AI may extract, compare, summarize and propose; it must never silently mutate a model assumption or hide a source.

## 3. High-level schema

- `assets`: canonical property identity, address, geography, asset type and identity-resolution confidence.
- `deals`: transaction, status, sponsor, strategy, version pointer and current IC stage.
- `documents`: uploaded file metadata, checksum, OCR status, extraction confidence and storage URI.
- `document_facts`: extracted values with page/cell citation, confidence and reviewer status.
- `assumptions`: deal/version/field/value/unit/source/status/owner and supersession links.
- `scenarios`: scenario name, shock vector, model version and generated outputs.
- `portfolio_constraints`: LTV, DSCR, concentration, liquidity and ESG limits.
- `ic_decisions`: stage, decision, conditions, decision-maker and timestamp.
- `audit_events`: append-only hash-chained events for every material change.

## 4. Agent architecture

1. **Document Agent** extracts facts and citations; it can create review-required facts but cannot approve them.
2. **Market Research Agent** assembles market evidence, normalizes timestamps and flags stale or illustrative sources.
3. **Underwriting Agent** maps approved facts into a typed assumption register and calls deterministic engines.
4. **Risk Agent** runs sensitivity, stress and Monte Carlo analysis and writes downside-first findings.
5. **Portfolio Impact Agent** tests allocation under real constraints and concentration limits.
6. **IC Memo Agent** renders a memo from approved outputs, with every claim linked to a lineage record.

Each agent emits `{claim, inputs, method, source_refs, confidence, reviewer_status}`. The orchestration layer rejects outputs without source references or assumption IDs.

## 5. 8–12 week build order

| Phase | Weeks | Outcome |
| --- | ---: | --- |
| Foundation | 1–2 | FastAPI boundary, Postgres schema, asset/deal versioning, audit events |
| Document intelligence | 3–4 | PDF/Excel ingestion, OCR, cited extraction and review queue |
| Underwriting productization | 5–6 | Lease-level monthly model, debt stack, waterfall and API contracts |
| Risk and portfolio | 7–8 | Correlated Monte Carlo, portfolio optimizer, early-warning rules |
| IC workflow | 9–10 | Role-based gates, side-by-side comparison, memo generation |
| Monitoring and reporting | 11–12 | Actual-vs-underwritten variance, investor reporting, observability |

## 6. Open-source shortlist

- **FastAPI, Pydantic, SQLAlchemy/SQLModel** for typed API boundaries.
- **PostgreSQL, PostGIS, pgvector** for transactional, geospatial and semantic retrieval needs.
- **pypdf, openpyxl, OCRmyPDF/Tesseract** for document processing with reviewable citations.
- **LangGraph** for explicit stateful agent orchestration and human approval checkpoints.
- **NumPy, pandas, SciPy, NumPyro/PyMC** for deterministic and probabilistic financial analysis.
- **OpenTelemetry and Evidently** for tracing model runs and monitoring data drift.

## 7. Non-negotiable controls

No recommendation without a cited source or an explicit `REVIEW REQUIRED` label. No model output without an assumption version. No IC approval without a recorded decision, actor, timestamp and audit hash. Downside cases appear before upside cases in every review surface.

This repository remains an analytical prototype, not investment, legal, tax or engineering advice.
"""}}]} ts=multi_tool_use.parallel.parallel  code/analysis  代 result  code: 400 ฝ่ายขายละคร: Invalid tool parameters. Need due malformed first tool in batch maybe JSON issue caused all? Need retry only failed? It says invalid tool params no execution likely. Use write calls individually or parallel with correct. First had weird. Do 3 calls. is code okay? Need ensure first content string. Let's call.Xitsonga. First tool payload likely bad JSON due accidental `{


## Implemented hardening in v0.4

The repository now contains a dedicated `src/debt.py` engine for monthly loan schedules, interest-only periods, balloon maturity, DSCR observations, and binding LTV-versus-DSCR sizing. `src/ic_workflow.py` adds deterministic side-by-side deal comparison, explicit severity-ranked screening flags, and a downside-first screening memo generator. `src/governance.py` now creates stable assumption IDs with version, effective timestamp, source, reviewer and supersession fields. `src/portfolio.py` uses an active-set allocator that re-allocates around concentration caps and excludes assets that fail the minimum DSCR gate.

These are working calculations and outputs, not simulated agents. AI orchestration remains deliberately outside the repository until document extraction, source storage, reviewer permissions, and a reproducible model-run contract are implemented.


## Quant-control decisions in v0.5

The model treats periodicity as a first-class control. Monthly development cash flows are modeled at monthly frequency, loan interest accrues on post-draw balances, and reported IRRs are annualized from monthly IRRs. Debt sizing uses the weakest modeled NOI period for DSCR capacity and reports the binding LTV or DSCR constraint. Waterfall distributions are checked against total distributable cash, and promote is applied only to profit above the applicable hurdle. Correlated Monte Carlo shocks are seeded for reproducibility and expose tail and covenant-breach statistics rather than only a mean case.


## v0.6 control surface

The reference implementation now treats invalid numerical inputs as model errors rather than silently clipped values. IRR root-finding is bracket-scanned, zero-rate debt is a supported limiting case, and debt schedule vectors are length- and finiteness-checked. Market scores require normalized finite factors and weights that sum to one. Audit verification is defensive against malformed events, lineage requires explicit input assumptions, and portfolio allocation is deterministic for repeated identical inputs.
