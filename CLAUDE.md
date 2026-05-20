# CLAUDE.md — GenAI Retail Forecasting Engine

This file is read automatically by Claude Code at the start of every session.
It defines the project structure, tech stack, conventions, and how to work in this codebase.

---

## Project overview

A hybrid ML + Generative AI system that:
1. Ingests raw retail sales data via Apache Beam → GCS → BigQuery
2. **Engineers time-series features using PySpark** (rolling windows, lag features, calendar signals)
3. Trains time-series forecasts using BigQuery ML (ARIMA_PLUS) on PySpark-enriched feature tables
4. Builds a RAG knowledge base from business documents + forecast exports (FAISS or Chroma)
5. Generates GPT-powered executive narratives per product using LangChain
6. Serves everything through a FastAPI + PostgreSQL backend

**Owner:** Mounusha  
**Stack:** Python 3.12, FastAPI, LangChain, BigQuery ML, Apache Beam, PySpark 3.5, GCP Dataflow, FAISS/Chroma, PostgreSQL, Docker

---

## Architecture & Data Flow

```
Raw CSV (GCS)
     │
     ▼
[Apache Beam ETL]  ←── etl/beam_pipeline.py
     │  Ingests, validates, loads raw sales rows
     ▼
BigQuery (raw_sales table)
     │
     ▼
[PySpark Feature Engineering]  ←── spark/feature_engineering.py   ★ NEW
     │  Rolling windows, lag features, calendar signals,
     │  store-level revenue ranks — written back to GCS parquet
     ▼
BigQuery (sales_features table)  ←── loaded from PySpark output
     │
     ▼
[BigQuery ML — ARIMA_PLUS]  ←── bq/train_model.sql
     │  Trains on enriched feature table
     ▼
BigQuery (forecast_output table)
     │
     ├──▶ [RAG Index Builder]  ←── rag/build_index.py
     │         FAISS / Chroma over docs + forecast exports
     │
     ├──▶ [GPT Narrative Generator]  ←── narratives/generator.py
     │         LangChain + LLM summaries per product
     │
     └──▶ [FastAPI Backend]  ←── api/main.py
               │
               ▼
         [Streamlit Dashboard]  ←── streamlit_app.py
```

---

## Project structure

```
genai_retail_forecasting/
├── CLAUDE.md                        ← you are here
├── .env                             ← secrets, never commit
├── .env.example                     ← committed template
├── pyproject.toml                   ← all dependencies (includes pyspark>=3.5)
├── Makefile                         ← canonical dev commands
├── Dockerfile
├── docker-compose.yml               ← PostgreSQL + API
│
├── etl/                             ← Apache Beam ingestion
│   ├── beam_pipeline.py             ← ReadFromGCS → validate → WriteToBigQuery
│   ├── schema.py                    ← SalesRow dataclass + BQ_SCHEMA
│   └── __init__.py
│
├── spark/                           ← PySpark feature engineering  ★ NEW
│   ├── feature_engineering.py       ← main Spark job (rolling windows, lags, calendar)
│   ├── spark_eda.ipynb              ← PySpark EDA notebook (scale analysis)
│   └── __init__.py
│
├── bq/                              ← BigQuery ML SQL
│   ├── create_daily_sales.sql
│   ├── train_model.sql              ← trains on sales_features (PySpark output)
│   ├── generate_forecasts.sql
│   └── evaluate_model.sql
│
├── rag/                             ← RAG index builder
│   ├── build_index.py               ← chunks + embeds + stores to FAISS/Chroma
│   ├── retriever.py                 ← LangChain retrieval chain
│   └── embeddings.py               ← embedding model config
│
├── narratives/                      ← GPT narrative generation
│   ├── generator.py                 ← generate_forecast_narrative()
│   ├── prompt_templates.py          ← all PromptTemplate definitions
│   └── batch_runner.py             ← ThreadPoolExecutor batch processing
│
├── api/                             ← FastAPI serving layer
│   ├── main.py                      ← app entry point
│   ├── routes/
│   │   ├── forecast.py              ← GET /forecast/{product_id}
│   │   └── health.py                ← GET /health
│   ├── models.py                    ← SQLAlchemy ORM models
│   └── database.py                  ← async DB connection
│
├── data/
│   ├── business_docs/               ← PDFs, TXTs for RAG corpus (gitignored)
│   ├── sample_sales/                ← small CSV for local dev/testing
│   └── faiss_index/                 ← built index (gitignored)
│
└── tests/
    ├── test_pipeline.py
    ├── test_spark_features.py        ← PySpark unit tests  ★ NEW
    ├── test_rag.py
    └── test_narratives.py
```

---

## PySpark Feature Engineering — `spark/feature_engineering.py`  ★ NEW

This module is the **feature layer** between raw ingestion and BigQuery ML training.
It reads the raw sales parquet from GCS, engineers features at scale, and writes
an enriched parquet back to GCS which is then loaded into the `sales_features` BigQuery table.

### Features produced

| Feature | Type | Description |
|---|---|---|
| `rolling_avg_units_7d` | Window | 7-day rolling avg of units_sold per product+store |
| `rolling_avg_units_30d` | Window | 30-day rolling avg of units_sold per product+store |
| `rolling_revenue_7d` | Window | 7-day rolling sum of revenue per product+store |
| `rolling_stddev_7d` | Window | 7-day rolling std deviation (demand volatility signal) |
| `lag_1d_units` | Lag | Units sold 1 day ago |
| `lag_7d_units` | Lag | Units sold 7 days ago (same-weekday signal) |
| `lag_14d_units` | Lag | Units sold 14 days ago |
| `lag_30d_units` | Lag | Units sold 30 days ago (monthly baseline) |
| `day_of_week` | Calendar | 1=Sunday … 7=Saturday |
| `week_of_year` | Calendar | ISO week number |
| `month` | Calendar | Month of year (1–12) |
| `is_weekend` | Calendar | Binary flag for Sat/Sun |
| `store_revenue_rank` | Rank | Daily store rank by revenue (competitive context) |

### Running the Spark job

```bash
# Local mode (PySpark on your machine — no cluster needed)
make spark-features

# Or manually:
python spark/feature_engineering.py \
  --input  gs://$GCS_BUCKET/sales/raw/*.parquet \
  --output gs://$GCS_BUCKET/sales/features/

# On Dataproc (GCP managed Spark cluster)
gcloud dataproc jobs submit pyspark spark/feature_engineering.py \
  --cluster=retail-spark-cluster \
  --region=us-central1 \
  -- --input gs://$GCS_BUCKET/sales/raw/*.parquet \
     --output gs://$GCS_BUCKET/sales/features/
```

### Spark configuration notes
- Uses `spark.sql.adaptive.enabled=true` — automatically optimizes join strategies and partition sizes
- Uses `spark.sql.adaptive.coalescePartitions.enabled=true` — reduces shuffle partitions dynamically
- For local dev, Spark runs in `local[*]` mode (uses all CPU cores, no cluster needed)
- For production (GCP), target Dataproc with `n1-standard-4` workers (same as Dataflow)

### Testing the Spark job locally

```bash
make spark-features-local   # runs with sample_sales/ data, DirectRunner equivalent
pytest tests/test_spark_features.py -v
```

---

## Environment variables

All secrets live in `.env`. Never hardcode them. Never commit `.env`.

```bash
# GCP
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GCS_BUCKET=your-gcs-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=               # leave empty if using gcloud ADC

# PySpark  ★ NEW
SPARK_MASTER=local[*]                         # local[*] for dev, yarn/k8s for prod
SPARK_RAW_INPUT=gs://your-bucket/sales/raw/
SPARK_FEATURE_OUTPUT=gs://your-bucket/sales/features/

# LLM — OpenAI (default) or swap for Groq/Gemini
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai                           # openai | groq | gemini | ollama

# Embeddings
EMBEDDING_PROVIDER=openai                     # openai | local | gemini

# Database
DATABASE_URL=postgresql+asyncpg://retail:retail@localhost:5432/retail

# API
SCHEDULER_SECRET=your-hex-secret
ENVIRONMENT=development                       # development | production
```

---

## LLM provider config (how to swap to free alternatives)

The LLM and embedding models are configured in `rag/embeddings.py` and `narratives/generator.py`.
To switch providers, only change `LLM_PROVIDER` and `EMBEDDING_PROVIDER` in `.env` — no code changes needed.

### LLM options

| Provider | Model | Cost | API Key needed |
|---|---|---|---|
| `openai` | gpt-4 | ~$0.03/1K tokens | Yes — platform.openai.com |
| `openai` | gpt-3.5-turbo | ~$0.002/1K tokens | Yes — much cheaper |
| `groq` | llama-3.1-70b-versatile | Free tier | Yes — console.groq.com |
| `gemini` | gemini-1.5-flash | Free tier (60 RPM) | Yes — aistudio.google.com |
| `ollama` | llama3 | Free, local | No — ollama.ai |

### Embedding options

| Provider | Model | Cost | Notes |
|---|---|---|---|
| `openai` | text-embedding-ada-002 | $0.0001/1K tokens | Best quality |
| `local` | all-MiniLM-L6-v2 | Free | Runs on CPU, good for dev |
| `gemini` | embedding-001 | Free tier | GoogleGenerativeAIEmbeddings |

---

## Dev commands (Makefile)

```bash
make install             # create .venv + pip install pyproject.toml
make up                  # docker compose up -d (starts PostgreSQL)
make down                # docker compose down
make migrate             # run Alembic DB migrations
make build-index         # embed data/business_docs/ → faiss_index/
make run                 # start FastAPI on localhost:8080
make test                # pytest tests/
make etl-local           # run Beam pipeline with DirectRunner (no GCP billing)
make etl-gcp             # run Beam pipeline on Dataflow (production)
make spark-features      # ★ NEW: run PySpark feature engineering (local mode)
make spark-features-gcp  # ★ NEW: submit PySpark job to Dataproc (production)
make bqml-train          # execute bq/train_model.sql in BigQuery
make narratives          # run batch narrative generation for all products
make lint                # ruff + mypy
```

---

## Key conventions

### Python style
- Python 3.12, typed (use type hints everywhere)
- Formatter: `ruff format` — line length 100
- Linter: `ruff check` + `mypy --strict`
- All async functions use `async/await` — no sync DB calls in FastAPI routes
- Use `structlog` for logging, not `print()`

### PySpark conventions  ★ NEW
- Always initialize SparkSession via `build_spark_session()` in `spark/feature_engineering.py` — never inline
- Use `pyspark.sql.functions as F` — never use string expressions for column operations
- All window specs must be explicitly defined with `.partitionBy()` + `.orderBy()` — no implicit ordering
- Call `spark.stop()` explicitly at the end of every script entry point
- For unit tests, use `pyspark.sql.SparkSession.builder.master("local[2]")` — limit to 2 cores in CI
- Never call `.count()` inside a loop — collect aggregations as a single action

### BigQuery
- All SQL files live in `bq/` and are executed via `bq query --use_legacy_sql=false`
- Table naming convention: `{project}:{dataset}.{table}` — e.g., `my-project:retail_forecasting.daily_sales`
- Always use `CREATE OR REPLACE` for idempotent SQL
- `train_model.sql` must reference `sales_features` (PySpark output), not `raw_sales`

### Beam pipeline
- For local dev, always use `DirectRunner` (no GCP cost)
- For production, use `DataflowRunner` with `--region=us-central1`
- Pipeline entry point: `etl/beam_pipeline.py`
- All `DoFn` classes live inline in `etl/beam_pipeline.py`

### RAG index
- Index is rebuilt from scratch each weekly run (`make build-index`)
- FAISS is the default (faster reads). Chroma can be enabled via `VECTOR_STORE=chroma` in `.env`
- Chunk size: 512 tokens, overlap: 64 tokens (defined in `rag/build_index.py`)
- Index persisted to `data/faiss_index/` (gitignored — rebuild on each machine)

### API
- All routes return JSON with shape `{product_id, forecasts: [...], narrative: "..."}`
- Use `databases` library for async PostgreSQL queries (not SQLAlchemy sync)
- Health check at `GET /health` must always return 200 for Docker health checks

---

## Database schema

```sql
-- forecasts: output from BigQuery ML, loaded weekly
CREATE TABLE forecasts (
  id              SERIAL PRIMARY KEY,
  product_id      TEXT NOT NULL,
  forecast_date   DATE NOT NULL,
  predicted_sales FLOAT,
  lower_bound     FLOAT,
  upper_bound     FLOAT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- narratives: GPT-generated summaries, loaded weekly
CREATE TABLE narratives (
  id           SERIAL PRIMARY KEY,
  product_id   TEXT NOT NULL,
  narrative    TEXT,
  context_docs JSONB,
  model_used   TEXT,
  generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON forecasts(product_id, forecast_date);
CREATE INDEX ON narratives(product_id);
```

---

## Weekly pipeline execution order

Run these in sequence (or via Cloud Scheduler targeting the `/run-pipeline` endpoint):

```
1. make etl-local / etl-gcp       → clean raw sales CSV → BigQuery (raw_sales)
2. make spark-features             → PySpark feature engineering → GCS parquet  ★ NEW
3. bq load sales_features          → load PySpark output → BigQuery (sales_features)  ★ NEW
4. make bqml-train                 → retrain ARIMA_PLUS on sales_features
5. bq/generate_forecasts.sql       → export predictions → GCS
6. make build-index                → re-embed docs + forecasts → FAISS
7. make narratives                 → GPT summaries for all products → PostgreSQL
```

---

## Testing

```bash
make test                              # run all tests
pytest tests/test_spark_features.py -v # PySpark unit tests only  ★ NEW
pytest tests/test_rag.py -v            # RAG unit tests only
pytest tests/ -k "narrative"           # filter by name
```

- Unit tests mock GCP and OpenAI calls — no real API calls in CI
- PySpark tests use `local[2]` master — no cluster required in CI
- Use `pytest-asyncio` for async FastAPI route tests
- Sample data for tests lives in `data/sample_sales/` (small, committed to repo)

---

## Common errors and fixes

| Error | Cause | Fix |
|---|---|---|
| `DefaultCredentialsError` | Not authenticated to GCP | Run `gcloud auth application-default login` |
| `FAISS index not found` | Index not built yet | Run `make build-index` |
| `Cannot connect to Docker daemon` | Docker Desktop not running | Open Docker Desktop app |
| `openai.AuthenticationError` | Missing or wrong API key | Check `OPENAI_API_KEY` in `.env` |
| `RateLimitError` from OpenAI | Too many parallel requests | Reduce `max_workers` in `batch_runner.py` to 2 |
| BigQuery `404 Not found: Dataset` | Dataset not created | Run `bq mk --location=US your-project:retail_forecasting` |
| `relation "forecasts" does not exist` | Migrations not run | Run `make migrate` |
| `JAVA_HOME not set` | Java missing for PySpark | Install JDK 11: `brew install openjdk@11` (Mac) or `apt install openjdk-11-jdk` (Linux) |
| `pyspark.errors.AnalysisException: Path does not exist` | Spark input GCS path wrong | Check `SPARK_RAW_INPUT` in `.env`; run `gsutil ls $SPARK_RAW_INPUT` |
| `WindowFunction without partitionBy` | Missing `.partitionBy()` on window spec | All window specs in `spark/feature_engineering.py` must have explicit partition keys |

---

## What NOT to do

- Never run `make etl-gcp` or `make spark-features-gcp` during local dev — both bill GCP.
- Never commit `.env` — it contains API keys.
- Never hardcode `project_id`, `bucket_name`, or API keys in source files — always read from `os.environ`.
- Never use `time.sleep()` in async code — use `await asyncio.sleep()`.
- Never call `vectorstore.persist()` inside a request handler — only during index build.
- Never call `.toPandas()` on a large Spark DataFrame — use `.limit(n).toPandas()` for sampling only.
- Never train BigQuery ML directly on `raw_sales` — always train on `sales_features` (PySpark output).

---

## Useful one-liners

```bash
# Check what's in your GCS bucket
gsutil ls gs://$GCS_BUCKET/

# Verify PySpark feature output on GCS  ★ NEW
gsutil ls gs://$GCS_BUCKET/sales/features/

# Quick Spark schema check (local)
python -c "
from pyspark.sql import SparkSession
spark = SparkSession.builder.master('local[2]').appName('check').getOrCreate()
df = spark.read.parquet('data/sample_sales/')
df.printSchema()
df.show(5)
"

# Query BigQuery from terminal
bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM retail_forecasting.daily_sales'

# Check feature table row count after Spark job  ★ NEW
bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM retail_forecasting.sales_features'

# Tail API logs
docker compose logs -f api

# Wipe and rebuild the DB from scratch
make down && docker volume rm genai_retail_forecasting_pgdata && make up && make migrate

# Test the API endpoint
curl http://localhost:8080/forecast/product_001 | python3 -m json.tool

# Check BQML model evaluation
bq query --use_legacy_sql=false \
  'SELECT * FROM ML.EVALUATE(MODEL retail_forecasting.sales_forecast_model) LIMIT 5'
```