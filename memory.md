# RetailForecastAI — Session Memory

Record of what this project already has, and what was done in this session to get it running locally (2026-07-12).

## What the project is

End-to-end retail demand forecasting system on the Rossmann Store Sales dataset (1,115 German stores). Portfolio-grade MLOps pipeline, Python 3.12+.

## What already existed (built into the repo)

| Component | File(s) | Purpose |
|---|---|---|
| ETL | `etl/beam_pipeline.py` | Apache Beam, CSV → GCS → BigQuery, validation/dedup/type-coercion |
| Feature engineering | `spark/feature_engineering.py`, `spark/spark_eda.ipynb` | PySpark rolling averages, lag features, calendar signals, EDA |
| Forecasting | `bq/sql/*.sql` | BigQuery ML ARIMA_PLUS — per-store model, 30-day horizon, 80% CI |
| Database | `db/models.py`, `migrations/` | Postgres via SQLAlchemy async + asyncpg, Alembic migrations. Tables: `forecasts`, `narratives`, `pipeline_runs` |
| API | `api/` | FastAPI — `/health`, `/v1/forecasts/{id}`, `/v1/narrative/{id}`, `POST /v1/pipeline/run` |
| RAG/LLM narratives | `rag/` | LangChain, FAISS vector store, local MiniLM embeddings, LLM-agnostic chat call |
| Dashboard | `streamlit_app.py` | 6-tab Streamlit + Plotly BI dashboard |
| Orchestration | `pipeline/orchestrator.py` | Coordinates ETL → BQ → DB → LLM full run |
| Scripts | `scripts/` | `seed_data.py`, `sync_forecasts.py`, `sync_narratives.py`, `run_bqml.py`, `build_index.py` |
| Tests | `tests/` | pytest, api + etl + rag tests |
| CI/CD | `.github/workflows/` | Lint/type/test on push; semver-tag deploy to Cloud Run via Workload Identity Federation |
| Containerization | `Dockerfile`, `docker-compose.yml` | Multi-stage build, Postgres + API services |

Real dataset in `data/raw/`: `train.csv` (~1M rows), `test.csv`, `store.csv` (1,115 stores) — genuine Kaggle Rossmann data, not synthetic.

## What this session did

**Goal**: make the project runnable locally without a GCP project (no billing, no cloud dependency), while keeping the real GCP/BigQuery ML path intact and untouched for later.

1. **Rebuilt the venv on native arm64 Python** (`/opt/homebrew/bin/python3.13`) — the original setup used Anaconda's x86_64 Python running under Rosetta translation, which was a source of instability on this Apple Silicon (M4) Mac.
2. **Fixed missing/broken dependencies** in `pyproject.toml`:
   - Added `langchain-openai` (was required by `rag/narrative_chain.py`'s openai code path but missing from the `rag` extra)
   - Added `psycopg2-binary` (imported directly by `streamlit_app.py`, missing from `ui` extra)
   - Pinned `pandas>=2.2,<3.0` (pandas 3.x's new pyarrow-backed dtype default was a secondary crash risk)
3. **Found and fixed the real Streamlit crash**: pyarrow's bundled mimalloc allocator segfaults (`EXC_BAD_ACCESS SIGSEGV`) on this macOS build when Streamlit serializes dataframes/charts to the browser via Arrow IPC — confirmed via macOS crash reports (`~/Library/Logs/DiagnosticReports/`), not environment flakiness. Fix: `ARROW_DEFAULT_MEMORY_POOL=system` env var forces Arrow to use the OS allocator instead of the crashing mimalloc one. Baked into `make ui` in the `Makefile`.
4. **Added `config/settings.py: openai_api_base`** and wired it into `rag/narrative_chain.py`'s `ChatOpenAI` call — lets any OpenAI-compatible endpoint (not just OpenAI itself) serve as the narrative LLM via `openai_api_base` override. Currently pointed at local **Ollama** (`http://localhost:11434/v1`, model `llama3`) — free, fully local, zero API cost, no external key needed.
5. **Added `scripts/seed_forecasts_local.py`** — a local substitute for the BigQuery ML training/forecast stage. Computes a real per-store 30-day forecast directly from `data/raw/train.csv` (day-of-week seasonal average + short-term trend adjustment, ±80% CI band from day-of-week std dev) and writes straight into the Postgres `forecasts` table. Produces the same 33,450-row / 1,115-store output the README describes, without needing GCP/BigQuery.
6. **Ran the full local pipeline**: Docker Postgres → Alembic migrations → local forecast seed (33,450 rows) → FAISS index build from `data/business_docs/` → narrative generation for 5 stores via Ollama → FastAPI + Streamlit both verified live.

## Current runnable state

- `make up` — Postgres via Docker
- `make migrate` — Alembic migrations
- `env $(cat .env|grep -v '^#'|xargs) .venv/bin/python scripts/seed_forecasts_local.py` — seed all 1,115 stores' forecasts locally (no GCP)
- `env $(cat .env|grep -v '^#'|xargs) .venv/bin/python -m scripts.build_index` — build FAISS index
- `env $(cat .env|grep -v '^#'|xargs) .venv/bin/python scripts/sync_narratives.py --limit N` — generate LLM narratives via local Ollama
- `env $(cat .env|grep -v '^#'|xargs) .venv/bin/python scripts/sync_narratives.py --limit N --skip-existing` — safely generate the next unfinished narrative batch
- `make run` — FastAPI on :8080
- `make ui` — Streamlit dashboard on :8501 (now includes the Arrow allocator fix automatically)
- `make local-doctor` — check raw data, baseline report, FAISS, DB forecast/narrative counts, and API health

`.env` is configured for: local Postgres, `LLM_PROVIDER=openai` pointed at local Ollama via `OPENAI_API_BASE=http://localhost:11434/v1`, `EMBEDDING_PROVIDER=local` (MiniLM, no API calls).

## Follow-up local hardening session

Non-GCP improvements added after the first local bring-up:

1. **Made local forecasting testable** by allowing `scripts/seed_forecasts_local.py` to read from an injected data directory, while preserving the default real Rossmann CSV path.
2. **Added local forecast tests** in `tests/test_local_forecasting.py` covering store limits, forecast shape, confidence interval sanity, and report generation.
3. **Added `scripts/baseline_compare.py`** to backtest the local seasonal-trend forecaster against simple baselines on the final 30-day holdout window from `data/raw/train.csv`.
4. **Generated baseline artifacts**:
   - `data/reports/baseline_comparison.md`
   - `data/reports/baseline_metrics.csv`
5. **Promoted local workflows into the Makefile**:
   - `make seed-local-forecasts`
   - `make baseline-report`
6. **Updated docs** so README now clearly separates the no-GCP local demo path from the cloud production path.

Current baseline result on 1,115 stores / 33,450 holdout rows: `local_seasonal_trend` is best by MAE among the included local baselines (MAE 1,898.84; MAPE 16.92%).

## Continued local polish

- Added a Streamlit **Model Benchmarks** tab that reads `data/reports/baseline_metrics.csv` and visualizes MAE/RMSE/MAPE/bias for the local baseline comparison.
- Added `scripts/local_doctor.py` plus `make local-doctor` to check no-GCP demo readiness: raw Rossmann CSVs, baseline metrics, FAISS index, PostgreSQL forecast/narrative counts, and FastAPI health.
- Added focused tests for the local doctor helper behavior in `tests/test_local_doctor.py`.
- Added `requirements.lock` plus `make lock` to pin the current local runtime dependency set and reduce fresh-clone drift.
- Updated `scripts/sync_narratives.py` to support `--skip-existing` and save each completed narrative immediately, so interrupted local Ollama batches keep completed work.
- Added FastAPI dashboard/frontend endpoints under `/v1/dashboard/*` for store lists, fleet summaries, daily/weekly trends, day-of-week patterns, narrative coverage, and baseline metrics. This prepares the backend for a future Next.js frontend without direct DB access.

## Current local state after backend-first work

- Forecasts: 33,450 rows for 1,115 stores in local PostgreSQL.
- Narratives: 20 stores currently saved (`STORE_0001` through `STORE_0020`).
- Baseline evidence: local seasonal-trend model beats the included seasonal-naive/moving-average baselines by MAE on the final 30-day holdout.
- Dashboard: includes Network Overview, Store Forecast, Compare, Model Benchmarks, AI Narrative, and About tabs. Sidebar now shows narrative coverage.
- Backend: FastAPI now exposes frontend-ready dashboard endpoints:
  - `/v1/dashboard/stores`
  - `/v1/dashboard/fleet-summary`
  - `/v1/dashboard/daily-trend`
  - `/v1/dashboard/dow-pattern`
  - `/v1/dashboard/weekly-fleet`
  - `/v1/dashboard/narrative-coverage`
  - `/v1/dashboard/baseline-metrics`
- Testing: focused API/dashboard/narrative/local-doctor tests pass locally; full repo lint/test still has older unrelated Spark notebook / optional Beam dependency issues.
- Git: latest local commits are split into multiple meaningful commits, including dashboard coverage UI, dashboard API routes, API tests, and API docs.

## Next.js frontend + live RAG generation session (2026-07-13)

Built the actual product surface on top of the existing FastAPI backend, plus one new backend capability.

### Frontend: Next.js 16 (App Router, Turbopack) + Tailwind CSS v4

- Scaffolded via `npx create-next-app` + `pnpm dlx shadcn@latest init` in `frontend/`. React 19, TypeScript, ESLint.
- Custom **"Liquid Glass" design system** (`frontend/src/app/globals.css` `.liquid-glass` class + `frontend/src/components/liquid-glass-card.tsx`): dark tinted glassmorphism material with backdrop blur, specular highlight layers, progressive edge blur, and a `.liquid-glass-interactive` hover variant (lift + glow) used on landing/clickable cards only, not dashboard data cards by default.
- Validated categorical/chart color palette in `frontend/src/lib/chart-theme.ts` (8-hue dark-mode set, CVD-checked).
- **Landing page** (`/`): hero with an interactive 3D robot (Spline scene, `public/scene.splinecode`, rendered via `@splinetool/react-spline` which pulls in Three.js/WebGL under the hood), live stat row, ambient gradient background (`components/landing/ambient-background.tsx`, careful non-negative z-index layering — negative z-index caused a real bug where the scene painted behind the page background, fixed by using `z-0`/`z-10` instead), Features (bento grid), Tech Stack icon grid, How-it-works pipeline diagram, Results (real backtest numbers), About (real bio), Contact, Footer.
- **Dashboard** (`/dashboard`): sidebar-navigated, 6 sections — Overview, Store Forecast, Compare, Model Benchmarks, AI Narrative, About. All data is live-fetched from the FastAPI backend (`frontend/src/lib/api.ts`), nothing hardcoded.
  - Custom D3 chart components (no charting library): `line-chart.tsx`, `bar-chart.tsx`, `donut-chart.tsx`, `scatter-chart.tsx` — all support a `height`/`compact` prop for dense layouts.
  - Overview tab redesigned twice this session into a **compact, near-single-screen layout** for laptop-size displays: 5 dense stat tiles (colored icon badges), then donut (store tier distribution, computed client-side via percentile split in `lib/tiers.ts`) + scatter (volume vs. forecast CI-width "uncertainty") row, then trend/top-stores/day-of-week row. Every chart has a computed one-line **insight caption** (`lib/insights.ts` — pure functions deriving real takeaways from the fetched data, not hardcoded).
  - Sidebar is **collapsible only on the Overview tab** (defaults collapsed there for space); every other tab always shows the full sidebar with no collapse toggle. Sidebar has a fixed-height (`h-96`) per-section "About this page" description panel so it doesn't resize per tab.
  - Model Benchmarks redesigned from a vertical bar chart (long model-name labels didn't fit) to a horizontal ranked list with short display names + winner badge.
  - About tab includes a "Let's collaborate" panel with a second Spline scene (`public/bye.splinecode`) and a full tech-stack icon grid.
- **Deferred/not built yet**: click-to-zoom/expand modal for Overview charts (user wants: click a chart, it enlarges over a dimmed background, others hide) — explicitly asked to come after the space-efficiency work, not yet started.

### Backend: live RAG narrative generation

- New endpoint `POST /v1/narrative/{product_id}/generate` (`api/routes/narratives.py`) — fetches the store's forecasts, calls `NarrativeChain.generate()` in a thread (`asyncio.to_thread`, since LangChain's `.invoke()` is sync/blocking), persists the result (replaces any existing row), returns it. This is the same one-off "Generate live" flow that already existed in `streamlit_app.py`'s AI Narrative tab, now exposed as a proper API endpoint and wired to a "Generate AI analysis" button in the dashboard (Store Forecast + AI Narrative tabs).
- `rag/narrative_chain.py` refactored: retrieval now happens eagerly (`retriever.invoke(product_id)`) instead of inside the LCEL chain, so the retrieved chunk sources are captured on `self.last_sources` after `.generate()` returns. This didn't change generation behavior/quality, just made retrieval observable.
- `api/schemas.py` `NarrativeResponse` gained an optional `retrieved_sources: list[str] | None` field (backward compatible — `None` on GET replays of DB rows, populated only right after a live `/generate` call).
- Frontend shows this as a "RAG-grounded — N retrieved passages from {file}" badge (`components/dashboard/rag-badge.tsx`) under freshly generated narratives — makes the RAG pipeline visible/provable in the UI, not just backend plumbing. Verified end-to-end via curl against the real local Ollama setup (5 chunks retrieved from `data/business_docs/rossmann_context.txt`).

### Bugs found and fixed along the way

- **`.gitignore` had a blanket `*.json` rule** that was silently excluding `frontend/package.json`, `tsconfig.json`, and `components.json` from git — a fresh clone would have had a broken frontend. Scoped down to just the intended GCP credential patterns (`service-account*.json`, `gcloud-*.json`).
- Deleted dead code left over from the shadcn scaffold step (fully superseded by custom components, zero references): `components/footer.tsx`, `components/logo.tsx`, `components/ui/button.tsx`, `components/ui/card.tsx`, `lib/utils.ts`.
- **`.venv/bin/uvicorn`'s shebang points at a stale path** (`.../RetailForecastAI/.venv/bin/python3.13` — old directory name/casing, doesn't exist). `make run` / direct `.venv/bin/uvicorn` invocation fails with "No such file or directory". Workaround (not yet fixed in the Makefile): run `.venv/bin/python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8080` instead, which bypasses the broken shebang. This should be fixed properly (recreate the venv, or fix the Makefile) in a future session.
- README.md rewritten from 726 lines (Streamlit-only, pre-frontend) down to ~240 lines covering the current full-stack state (intro, why-built, architecture, features, dashboard, tech stack incl. Three.js/Spline, backtest table, quick start, API reference). Tableau added to the tech stack table marked *(in progress)* — not actually integrated yet, user plans to add it themselves.

### Git hygiene this session

- All work committed locally in ~30 small, logically-grouped, honestly-timestamped commits (no backdating) — grouped by real unit of work (e.g. "Add live RAG narrative generation endpoint", "Redesign dashboard Overview as a compact layout"), not padded to hit an arbitrary count.
- **8 commits are currently ahead of `origin/main`, not pushed.** User pushes manually themselves.
- `scripts/commit_groups.sh` (a one-off commit-grouping helper, superseded by doing real commits directly) is still sitting untracked in the repo — user said they'll delete it themselves. Don't recreate it.
