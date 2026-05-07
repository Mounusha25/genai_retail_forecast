# GenAI Retail Demand Forecasting Engine

> **Production-grade ML + Generative AI system** that ingests raw retail sales, trains time-series forecasting models on BigQuery ML, and delivers 30-day demand forecasts alongside LLM-generated executive narratives — all through a FastAPI backend and a real-time Streamlit BI dashboard.

---

## Table of Contents

1. [Overview](#overview)
2. [Live Dashboard](#live-dashboard)
3. [Architecture](#architecture)
4. [Component Breakdown](#component-breakdown)
   - [1. ETL Pipeline (Apache Beam)](#1-etl-pipeline-apache-beam)
   - [2. BigQuery ML Forecasting](#2-bigquery-ml-forecasting)
   - [3. RAG + Narrative Engine (LangChain)](#3-rag--narrative-engine-langchain)
   - [4. FastAPI Backend](#4-fastapi-backend)
   - [5. Streamlit BI Dashboard](#5-streamlit-bi-dashboard)
   - [6. PostgreSQL Data Store](#6-postgresql-data-store)
5. [Tech Stack](#tech-stack)
6. [Project Structure](#project-structure)
7. [Data Flow](#data-flow)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Local Development](#local-development)
10. [Environment Variables](#environment-variables)
11. [API Reference](#api-reference)
12. [Key Design Decisions](#key-design-decisions)

---

## Overview

This project demonstrates a complete, end-to-end **MLOps + GenAI** pipeline built for retail demand forecasting at scale. It covers every layer of a production system:

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Ingestion | Apache Beam → GCS → BigQuery | Clean and load raw sales CSVs |
| Forecasting | BigQuery ML ARIMA_PLUS | Train and generate 30-day demand forecasts |
| RAG Index | FAISS + Sentence-Transformers | Build searchable knowledge base from business docs |
| Narratives | LangChain + LLaMA 3.3-70B (Groq) | GPT-powered executive summaries per store |
| Backend API | FastAPI + asyncpg + PostgreSQL | Serve forecasts and narratives with async I/O |
| Dashboard | Streamlit + Plotly | 5-tab real-time BI dashboard with 1,115-store fleet |
| CI/CD | GitHub Actions + Cloud Run + WIF | Zero-downtime deploy on every semver tag |

**Dataset**: Rossmann Store Sales — 1,115 stores across Germany, Aug–Sep 2015, 33,450 forecast rows, 24.81M total predicted units.

---

## Live Dashboard

The Streamlit dashboard provides five tabs of business intelligence:

| Tab | Contents |
|-----|----------|
| 🌐 **Network Overview** | Fleet KPIs, daily demand trend, day-of-week patterns, Top-15 stores, store tier distribution (High/Mid/Low), volume histogram with P25/P50/P75 lines, weekly bar chart, risk-vs-volume scatter |
| 📊 **Store Forecast** | Per-store 5 KPIs, forecast line + 80% CI band + peak marker, weekly bar, DOW pattern, benchmark bullet chart (vs P25/P50/P75/P90), week-over-week change, CSV export |
| 🔀 **Compare** | Multi-store overlay chart, comparison summary table with percentile ranks across all 1,115 stores |
| 🤖 **AI Narrative** | LLM-generated executive summary per store, with live regeneration button |
| ℹ️ **About** | System architecture, tech stack, dataset info, quick-start guide |

```bash
# Run the dashboard
make ui          # or:
streamlit run streamlit_app.py --server.port 8501
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        DATA INGESTION LAYER                                  │
│                                                                              │
│  Raw CSVs ──► GCS Bucket ──► Apache Beam (DirectRunner / Dataflow)           │
│               (gs://bucket/raw/)    ParseSalesRow DoFn                       │
│                                     • validation                             │
│                                     • type coercion                          │
│                                     • deduplication                          │
│                                          │                                   │
│                                          ▼                                   │
│                                   BigQuery                                   │
│                          retail_forecasting.daily_sales                      │
└──────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          FORECASTING LAYER                                   │
│                                                                              │
│  BigQuery ML                                                                 │
│  ┌─────────────────────────────────────────────────────┐                    │
│  │ CREATE OR REPLACE MODEL retail_forecasting.forecast │                    │
│  │   OPTIONS(model_type='ARIMA_PLUS',                  │                    │
│  │           time_series_timestamp_col='date',          │                    │
│  │           time_series_data_col='units_sold',         │                    │
│  │           time_series_id_col='product_id',           │                    │
│  │           horizon=30,                                │                    │
│  │           auto_arima=TRUE,                           │                    │
│  │           data_frequency='DAILY',                    │                    │
│  │           decompose_time_series=TRUE)                │                    │
│  └─────────────────────────────────────────────────────┘                    │
│                                          │                                   │
│                            ML.FORECAST() ▼                                   │
│                     30-day predictions + 80% CI bands                        │
│                     exported to GCS → synced to PostgreSQL                   │
└──────────────────────────────────────────────────────────────────────────────┘
                                          │
                     ┌────────────────────┴──────────────────┐
                     ▼                                        ▼
┌──────────────────────────────┐     ┌──────────────────────────────────────┐
│     RAG KNOWLEDGE BASE       │     │         POSTGRESQL (Docker)          │
│                              │     │                                      │
│  Business docs (PDF/TXT/MD)  │     │  ┌──────────────┐ ┌──────────────┐  │
│         │                    │     │  │  forecasts   │ │  narratives  │  │
│  RecursiveCharacterSplitter  │     │  │  product_id  │ │  product_id  │  │
│  chunk=600 / overlap=80      │     │  │  date        │ │  summary     │  │
│         │                    │     │  │  forecast    │ │  model_used  │  │
│  HuggingFace Embeddings      │     │  │  ci_lower    │ │  generated   │  │
│  (all-MiniLM-L6-v2)          │     │  │  ci_upper    │ └──────────────┘  │
│         │                    │     │  └──────────────┘                   │
│   FAISS Index (disk)         │     │  ┌───────────────────────────────┐  │
│  data/faiss_index/           │     │  │     pipeline_runs (audit)     │  │
└──────────────┬───────────────┘     └──────────────────────────────────┘  │
               │                                          │                  │
               ▼                                          │                  │
┌──────────────────────────────┐                          │                  │
│     NARRATIVE ENGINE         │                          │                  │
│                              │                          │                  │
│  LangChain RAG Chain:        │                          │                  │
│  product_id → MMR retriever  │◄─── forecast rows ───────┘                  │
│      → ChatPromptTemplate    │                                             │
│      → LLaMA 3.3-70B (Groq) │                                             │
│      → StrOutputParser       │                                             │
│  3-paragraph executive brief │                                             │
│  saved to narratives table   │                                             │
└──────────────────────────────┘                                             │
               │                                                             │
               └──────────────────────┐                                      │
                                      ▼                                      │
┌──────────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI BACKEND                                   │
│                                                                              │
│  GET /health                   — DB connectivity check                       │
│  GET /v1/forecasts/{id}        — 30-day forecast rows + CI bands             │
│  GET /v1/narrative/{id}        — latest LLM executive summary                │
│  POST /v1/pipeline/run         — trigger full pipeline (authenticated)       │
│                                                                              │
│  • asyncpg connection pool (size=10, overflow=20)                            │
│  • Pydantic v2 request/response validation                                   │
│  • structlog structured JSON logging                                         │
│  • CORS middleware (tightened in production)                                 │
└──────────────────────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                        STREAMLIT BI DASHBOARD                                │
│                                                                              │
│  Direct psycopg2 queries to PostgreSQL (fleet-wide analytics)                │
│  + FastAPI calls (per-store forecast + narrative)                            │
│  5-tab Plotly dashboard · @st.cache_data TTL caching                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. ETL Pipeline (Apache Beam)

**File:** `etl/beam_pipeline.py`

The pipeline reads raw CSV files from Google Cloud Storage and writes clean rows to BigQuery using Apache Beam's unified batch/streaming model.

**Key steps:**
- `ReadFromGCS` — reads all `*.csv` files from `gs://{bucket}/raw/`
- `ParseSalesRow` (custom `DoFn`) — validates schema, coerces types, normalises `product_id` to uppercase, clamps negative units/revenue to zero, tracks `sales/parsed` and `sales/skipped` Beam metrics
- `WriteToBigQuery` — streams rows into `retail_forecasting.daily_sales` with `CREATE_IF_NEEDED` / `WRITE_APPEND` disposition

**Runners:**
```bash
make etl-local    # DirectRunner — no GCP cost, for development
make etl-gcp      # DataflowRunner — production, auto-scales
```

---

### 2. BigQuery ML Forecasting

**Files:** `bq/sql/`

Four SQL files execute the full ML lifecycle:

| File | Purpose |
|------|---------|
| `create_view.sql` | Aggregates raw sales into a clean `daily_sales` view |
| `train_model.sql` | Trains `ARIMA_PLUS` model with auto-ARIMA, seasonal decomposition |
| `generate_forecast.sql` | Calls `ML.FORECAST()` for 30-day horizon with 80% CI |
| `evaluate_model.sql` | Computes MAE, MAPE, RMSE via `ML.EVALUATE()` |

**Model configuration:**
```sql
CREATE OR REPLACE MODEL retail_forecasting.sales_forecast_model
OPTIONS(
  model_type           = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col      = 'units_sold',
  time_series_id_col        = 'product_id',
  horizon                   = 30,
  auto_arima                = TRUE,
  data_frequency            = 'DAILY',
  decompose_time_series     = TRUE
)
```

The `ARIMA_PLUS` model automatically detects trend, seasonality, and holiday effects. Each `product_id` gets its own fitted model — BigQuery handles all parallelisation transparently.

---

### 3. RAG + Narrative Engine (LangChain)

**Files:** `rag/narrative_chain.py`, `rag/vector_store.py`, `rag/prompts.py`

#### Vector Store Build (`rag/vector_store.py`)
1. Loads all PDF / TXT / Markdown from `data/business_docs/`
2. Chunks with `RecursiveCharacterTextSplitter` (chunk=600, overlap=80 tokens)
3. Embeds with `all-MiniLM-L6-v2` (local, free) or `text-embedding-3-small` (OpenAI)
4. Persists a FAISS index to `data/faiss_index/`

#### Narrative Generation (`rag/narrative_chain.py`)
```
product_id
    │
    ▼
MMR Retriever (k=5, fetch_k=15)  ← FAISS index
    │
    ▼
ChatPromptTemplate (SYSTEM + HUMAN)
    │
    ▼
LLaMA 3.3-70B via Groq API  (free tier, 70B params)
    │
    ▼
StrOutputParser → 3-paragraph executive brief
```

**MMR (Maximum Marginal Relevance)** is used instead of plain similarity search to ensure retrieved context chunks are both relevant *and* diverse — avoiding redundant passages being fed to the LLM.

**Retry policy:** `tenacity` with exponential back-off (2s → 30s, 3 attempts) handles Groq rate limits gracefully.

**LLM providers are swappable** — change `LLM_PROVIDER` in `.env` with no code changes:

| Provider | Model | Notes |
|----------|-------|-------|
| `groq` | `llama-3.3-70b-versatile` | Default — free tier, fast |
| `openai` | `gpt-4o` | Best quality, paid |

---

### 4. FastAPI Backend

**Files:** `api/main.py`, `api/routes/`, `api/schemas.py`, `api/dependencies.py`

A fully async REST API with production-grade features:

- **Async SQLAlchemy** with `asyncpg` driver — no blocking I/O in request handlers
- **Connection pool** — size=10, max_overflow=20, timeout=30s (all configurable via env vars)
- **Pydantic v2** — strict request/response validation with `model_validate`
- **Lifespan events** — `create_tables()` on startup, `dispose_engine()` on shutdown
- **Structured logging** — `structlog` with JSON mode in production
- **Pipeline trigger** — `POST /v1/pipeline/run` authenticated via `SCHEDULER_SECRET` header, runs the full orchestrator as a background task with audit logging to `pipeline_runs` table

**Endpoints:**

```
GET  /health                    → {"status": "ok", "db": "ok", "version": "1.0.0"}
GET  /v1/forecasts/{product_id} → ForecastsResponse (30 rows + CI bands)
GET  /v1/narrative/{product_id} → NarrativeResponse (latest LLM summary)
POST /v1/pipeline/run           → 202 Accepted (authenticated, async background job)
GET  /docs                      → Swagger UI (dev only)
GET  /redoc                     → ReDoc (dev only)
```

---

### 5. Streamlit BI Dashboard

**File:** `streamlit_app.py`

A 1,200-line professional BI dashboard built with Streamlit + Plotly. Uses **direct psycopg2 connections** for fleet-wide analytical queries (bypassing async for simplicity) and **FastAPI HTTP calls** for per-store forecast/narrative data.

**Data layer:**
- `@st.cache_data(ttl=300)` on all DB queries — prevents redundant database hits
- `_pg_dsn()` strips SQLAlchemy DSN prefixes for psycopg2 compatibility
- Graceful degradation — all charts show `st.warning` if DB is unreachable

**Fleet data (from PostgreSQL):**

| Metric | Value |
|--------|-------|
| Total stores | 1,115 |
| Forecast horizon | Aug 1 – Aug 30, 2015 |
| Total predicted units | 24.81M |
| Avg per store (30d) | 22,252 units |
| Top store | STORE_1114 (105.7K) |
| Busiest weekday | Monday (avg 817 units/store) |
| Store tier distribution | 562 Low / 536 Mid / 17 High |

---

### 6. PostgreSQL Data Store

**Schema (`db/models.py`):**

```sql
-- Numeric forecasts from BigQuery ML
CREATE TABLE forecasts (
    id           SERIAL PRIMARY KEY,
    product_id   VARCHAR(64) NOT NULL,
    forecast_date DATE NOT NULL,
    forecast_units FLOAT NOT NULL,
    ci_lower     FLOAT,
    ci_upper     FLOAT,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ix_forecasts_product_date ON forecasts(product_id, forecast_date);

-- LLM executive summaries
CREATE TABLE narratives (
    id           SERIAL PRIMARY KEY,
    product_id   VARCHAR(64) NOT NULL,
    summary      TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_narratives_product_generated ON narratives(product_id, generated_at);

-- Pipeline execution audit log
CREATE TABLE pipeline_runs (
    id          SERIAL PRIMARY KEY,
    status      VARCHAR(32) NOT NULL,  -- running | success | failed
    triggered_by VARCHAR(64) NOT NULL,
    started_at  TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    error       TEXT
);
```

Migrations are managed with **Alembic** (`make migrate`).

---

## Tech Stack

| Category | Technology | Version |
|----------|-----------|---------|
| Language | Python | 3.12 |
| API Framework | FastAPI | ≥0.111 |
| ORM / DB | SQLAlchemy (async) + asyncpg | ≥2.0 / ≥0.29 |
| Migrations | Alembic | ≥1.13 |
| Database | PostgreSQL | 16 (Docker) |
| ETL | Apache Beam | ≥2.55 |
| Cloud Storage | Google Cloud Storage | ≥2.16 |
| ML Platform | BigQuery ML ARIMA_PLUS | — |
| LLM (default) | LLaMA 3.3-70B via Groq | free tier |
| LLM (alt) | GPT-4o via OpenAI | paid |
| RAG Framework | LangChain | ≥0.2 |
| Vector Store | FAISS (CPU) | ≥1.7 |
| Embeddings | all-MiniLM-L6-v2 (local) | — |
| Data Validation | Pydantic v2 | ≥2.7 |
| Dashboard | Streamlit + Plotly | ≥1.35 / ≥5.22 |
| Logging | structlog | ≥24.1 |
| Linter | Ruff | ≥0.4 |
| Type checker | mypy (strict) | ≥1.10 |
| Testing | pytest + pytest-asyncio | ≥8.2 |
| Containerisation | Docker + docker-compose | — |
| CI/CD | GitHub Actions | — |
| Cloud Deploy | Google Cloud Run | — |
| Auth (GCP) | Workload Identity Federation | keyless |
| Retry logic | tenacity | ≥8.3 |

---

## Project Structure

```
genai_retail_forecasting/
│
├── api/                        ← FastAPI application
│   ├── main.py                 ← App factory, lifespan, CORS, error handlers
│   ├── routes/
│   │   ├── forecasts.py        ← GET /v1/forecasts/{product_id}
│   │   ├── narratives.py       ← GET /v1/narrative/{product_id}
│   │   └── pipeline.py         ← POST /v1/pipeline/run (authenticated)
│   ├── dependencies.py         ← DbSession dependency, auth guard
│   └── schemas.py              ← Pydantic v2 request/response models
│
├── bq/                         ← BigQuery client + SQL
│   ├── client.py               ← BQ client wrapper
│   └── sql/
│       ├── create_view.sql     ← Aggregated daily_sales view
│       ├── train_model.sql     ← ARIMA_PLUS model training
│       ├── generate_forecast.sql ← ML.FORECAST() → GCS export
│       └── evaluate_model.sql  ← ML.EVALUATE() metrics
│
├── config/
│   ├── settings.py             ← Pydantic-settings, all env vars typed
│   └── logging.py              ← structlog configuration
│
├── db/
│   ├── models.py               ← SQLAlchemy ORM (Forecast, Narrative, PipelineRun)
│   └── session.py              ← Async engine + session factory
│
├── etl/
│   ├── beam_pipeline.py        ← Apache Beam pipeline (GCS → BigQuery)
│   └── schema.py               ← BQ schema + SalesRow dataclass
│
├── migrations/                 ← Alembic migrations
│   ├── env.py
│   └── versions/
│
├── pipeline/
│   └── orchestrator.py         ← Full pipeline coordinator (ETL → BQ → DB → LLM)
│
├── rag/
│   ├── vector_store.py         ← Build/load FAISS index
│   ├── narrative_chain.py      ← LangChain RAG → LLM narrative generation
│   └── prompts.py              ← System + human prompt templates
│
├── scripts/
│   ├── seed_data.py            ← Generate synthetic Rossmann-style sales data
│   ├── sync_forecasts.py       ← BQ → PostgreSQL forecast sync
│   ├── sync_narratives.py      ← Batch narrative generation for all stores
│   ├── build_index.py          ← Build FAISS vector index from docs
│   └── run_bqml.py             ← Execute BQ ML SQL files
│
├── tests/
│   ├── conftest.py             ← pytest fixtures (async DB, mocked settings)
│   ├── test_api.py             ← FastAPI endpoint tests (httpx AsyncClient)
│   ├── test_etl.py             ← Beam pipeline unit tests
│   └── test_rag.py             ← RAG chain tests (mocked LLM)
│
├── data/
│   ├── business_docs/          ← PDFs/TXTs for RAG corpus (gitignored)
│   ├── faiss_index/            ← Built FAISS index (gitignored)
│   └── sample_sales/           ← Small CSV for local dev/testing
│
├── streamlit_app.py            ← 5-tab Streamlit BI dashboard
├── docker-compose.yml          ← PostgreSQL + FastAPI services
├── Dockerfile                  ← Multi-stage build (builder + runtime)
├── Makefile                    ← All dev commands
├── pyproject.toml              ← Dependencies, ruff, mypy, pytest config
└── .env.example                ← Environment variable template
```

---

## Data Flow

```
Weekly pipeline execution order:

Step 1  make etl-local / etl-gcp
        Raw CSVs in GCS → Beam validation → BigQuery daily_sales table

Step 2  make bqml-train
        BigQuery ML trains ARIMA_PLUS model per product_id

Step 3  make bqml-forecast
        ML.FORECAST() generates 30-day predictions + 80% CI → BQ forecast table

Step 4  make sync-forecasts
        BigQuery forecast rows → PostgreSQL forecasts table

Step 5  make build-index
        business_docs/ + forecast summaries → chunked → embedded → FAISS index

Step 6  make sync-narratives
        For each store: retrieve RAG context + forecasts → LLaMA 3.3-70B → PostgreSQL narratives

Step 7  Dashboard auto-refreshes
        Streamlit reads PostgreSQL directly (fleet analytics, @st.cache_data TTL=300s)
        FastAPI serves per-store forecasts + narratives on demand
```

This full pipeline can also be triggered via HTTP:
```bash
curl -X POST http://localhost:8080/v1/pipeline/run \
  -H "X-Scheduler-Secret: your-secret"
```

---

## CI/CD Pipeline

Two GitHub Actions workflows:

### `ci.yml` — Runs on every push to `main`/`develop` and all PRs

```
push / PR → Ruff lint → Ruff format check → mypy --strict → pytest (PostgreSQL service)
                                                               │
                                                               └─► codecov coverage report
                                                               └─► Docker build validation
```

### `deploy.yml` — Runs on semver tags (`v*.*.*`) or manual workflow dispatch

```
git tag v1.2.3 && git push --tags
        │
        ▼
  Lint + Test (gate)
        │
        ▼
  Keyless GCP auth via Workload Identity Federation (no long-lived service account keys)
        │
        ▼
  Docker build → push to Artifact Registry
  (us-central1-docker.pkg.dev/{project}/retail-forecasting/retail-forecasting-api:{tag})
        │
        ▼
  gcloud run deploy retail-forecasting-api
  --image {image} --region us-central1 --platform managed
  --set-env-vars DATABASE_URL,OPENAI_API_KEY,...
        │
        ▼
  Smoke test: curl https://{service-url}/health → {"status":"ok"}
```

**Security note:** Deployment uses [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation) — no service account JSON keys are stored in GitHub Secrets.

---

## Local Development

### Prerequisites
- Python 3.12+
- Docker Desktop
- `gcloud` CLI (for GCP features only)

### Setup

```bash
# 1. Clone and create virtual environment
git clone https://github.com/your-username/genai_retail_forecasting
cd genai_retail_forecasting
make install               # creates .venv and installs all deps

# 2. Copy and fill in environment variables
cp .env.example .env
# Edit .env — minimum required: DATABASE_URL, GROQ_API_KEY (or OPENAI_API_KEY)

# 3. Start PostgreSQL
make up                    # docker compose up -d

# 4. Run migrations
make migrate               # alembic upgrade head

# 5. Seed local data (generates synthetic Rossmann-style sales)
python scripts/seed_data.py

# 6. Build the RAG index (put PDFs/TXTs in data/business_docs/ first)
make build-index

# 7. Generate narratives
make sync-narratives

# 8. Start the API
make run                   # uvicorn on localhost:8080

# 9. Open the dashboard
make ui                    # streamlit on localhost:8501
```

### All Makefile Commands

```bash
make install          # Set up virtualenv + install deps
make up               # Start Docker services (PostgreSQL)
make down             # Stop Docker services
make migrate          # Run Alembic migrations
make run              # Start FastAPI (localhost:8080)
make ui               # Start Streamlit dashboard (localhost:8501)
make test             # Run pytest test suite
make lint             # Ruff + mypy checks
make etl-local        # Run Beam ETL with DirectRunner (free)
make etl-gcp          # Run Beam ETL on Dataflow (GCP billing)
make bqml-train       # Train ARIMA_PLUS model in BigQuery
make bqml-forecast    # Generate 30-day forecasts
make sync-forecasts   # Sync BQ forecasts → PostgreSQL
make build-index      # Build FAISS RAG index
make sync-narratives  # Generate LLM narratives for all stores
```

---

## Environment Variables

```bash
# ── GCP ─────────────────────────────────────────────────────
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GCS_BUCKET=your-gcs-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=       # blank = use gcloud ADC

# ── Database ────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://retail:retail@localhost:5432/retail

# ── LLM Provider ────────────────────────────────────────────
LLM_PROVIDER=groq                      # groq | openai
GROQ_API_KEY=gsk_...                   # free at console.groq.com
OPENAI_API_KEY=sk-...                  # paid at platform.openai.com

# ── Embeddings ──────────────────────────────────────────────
EMBEDDING_PROVIDER=local               # local (free) | openai (paid)

# ── Security ────────────────────────────────────────────────
SCHEDULER_SECRET=your-random-hex-secret

# ── Runtime ─────────────────────────────────────────────────
ENVIRONMENT=development                # development | production
```

---

## API Reference

### `GET /health`
```json
{"status": "ok", "version": "1.0.0", "db": "ok"}
```

### `GET /v1/forecasts/{product_id}`
```json
{
  "product_id": "STORE_0001",
  "count": 30,
  "forecasts": [
    {
      "forecast_date": "2015-08-01",
      "forecast_units": 487.3,
      "ci_lower": 401.1,
      "ci_upper": 573.5,
      "generated_at": "2026-05-07T00:00:00Z"
    }
  ]
}
```

### `GET /v1/narrative/{product_id}`
```json
{
  "product_id": "STORE_0001",
  "summary": "STORE_0001 is forecast to sell approximately 14,619 units over the next 30 days...",
  "generated_at": "2026-05-07T01:00:00Z"
}
```

### `POST /v1/pipeline/run` _(authenticated)_
```bash
curl -X POST http://localhost:8080/v1/pipeline/run \
  -H "X-Scheduler-Secret: $SCHEDULER_SECRET"
# → 202 Accepted
```

Interactive docs available at `http://localhost:8080/docs` (development mode).

---

## Key Design Decisions

**Why Apache Beam?**
Beam's unified programming model means the same pipeline code runs locally (`DirectRunner`) for free during development and on managed `Dataflow` in production with auto-scaling — no code changes needed.

**Why BigQuery ML over a Python model?**
ARIMA_PLUS in BQML trains one model *per product* (1,115+ models) automatically, in parallel, with zero infrastructure management. The same SQL call handles model versioning, training, forecasting, and evaluation.

**Why FAISS over a managed vector DB?**
For a weekly-rebuild RAG index of business documents, FAISS (CPU) is instant, free, and portable. Chroma or Pinecone can be dropped in by changing one line in `rag/vector_store.py`.

**Why LangChain with MMR retrieval?**
Maximum Marginal Relevance ensures the k=5 retrieved chunks are diverse rather than semantically redundant — producing richer LLM context for nuanced executive summaries.

**Why Groq for LLM inference?**
Groq's LPU hardware delivers LLaMA 3.3-70B inference at ~800 tokens/second on the free tier — fast enough for real-time dashboard regeneration. Swapping to GPT-4o requires only an env var change.

**Why async FastAPI + asyncpg?**
Async I/O allows the API to handle dozens of concurrent forecast requests without thread blocking. The connection pool (size=10, overflow=20) handles burst traffic from the Streamlit dashboard's parallel chart loads.

**Why Workload Identity Federation?**
WIF eliminates the need to store long-lived GCP service account JSON keys as GitHub Secrets, reducing the blast radius of a potential credential leak.

---

## Author

**Mounusha** — Data Engineering & GenAI  
Stack: Python · FastAPI · BigQuery ML · LangChain · Apache Beam · Streamlit · GCP

---

*Built as a portfolio-grade end-to-end ML + GenAI system demonstrating production patterns: async APIs, streaming ETL, ML pipelines, RAG, LLM integration, containerisation, and CI/CD with keyless GCP deployment.*
