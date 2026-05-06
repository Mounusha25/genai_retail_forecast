# CLAUDE.md — GenAI Retail Forecasting Engine

This file is read automatically by Claude Code at the start of every session.
It defines the project structure, tech stack, conventions, and how to work in this codebase.

---

## Project overview

A hybrid ML + Generative AI system that:
1. Ingests raw retail sales data via Apache Beam → GCS → BigQuery
2. Trains time-series forecasts using BigQuery ML (ARIMA_PLUS)
3. Builds a RAG knowledge base from business documents + forecast exports (FAISS or Chroma)
4. Generates GPT-powered executive narratives per product using LangChain
5. Serves everything through a FastAPI + PostgreSQL backend

**Owner:** Mounusha  
**Stack:** Python 3.12, FastAPI, LangChain, BigQuery ML, Apache Beam, GCP Dataflow, FAISS/Chroma, PostgreSQL, Docker

---

## Project structure

```
genai_retail_forecasting/
├── CLAUDE.md                  ← you are here
├── .env                       ← secrets, never commit
├── .env.example               ← committed template
├── pyproject.toml             ← all dependencies
├── Makefile                   ← canonical dev commands
├── Dockerfile
├── docker-compose.yml         ← PostgreSQL + API
│
├── pipeline/                  ← Apache Beam ETL
│   ├── beam_etl.py            ← main pipeline (ReadFromGCS → clean → WriteToBigQuery)
│   └── transforms.py          ← reusable PTransforms
│
├── bqml/                      ← BigQuery ML SQL
│   ├── create_daily_sales.sql
│   ├── train_model.sql
│   ├── generate_forecasts.sql
│   └── evaluate_model.sql
│
├── rag/                       ← RAG index builder
│   ├── build_index.py         ← chunks + embeds + stores to FAISS/Chroma
│   ├── retriever.py           ← LangChain retrieval chain
│   └── embeddings.py          ← embedding model config (swap here for free alternative)
│
├── narratives/                ← GPT narrative generation
│   ├── generator.py           ← generate_forecast_narrative()
│   ├── prompt_templates.py    ← all PromptTemplate definitions
│   └── batch_runner.py        ← ThreadPoolExecutor batch processing
│
├── api/                       ← FastAPI serving layer
│   ├── main.py                ← app entry point
│   ├── routes/
│   │   ├── forecast.py        ← GET /forecast/{product_id}
│   │   └── health.py          ← GET /health
│   ├── models.py              ← SQLAlchemy ORM models
│   └── database.py            ← async DB connection
│
├── data/
│   ├── business_docs/         ← PDFs, TXTs for RAG corpus (gitignored)
│   ├── sample_sales/          ← small CSV for local dev/testing
│   └── faiss_index/           ← built index (gitignored)
│
└── tests/
    ├── test_pipeline.py
    ├── test_rag.py
    └── test_narratives.py
```

---

## Environment variables

All secrets live in `.env`. Never hardcode them. Never commit `.env`.

```bash
# GCP
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GCS_BUCKET=your-gcs-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=               # leave empty if using gcloud ADC

# LLM — OpenAI (default) or swap for Groq/Gemini (see LLM config section)
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai                           # openai | groq | gemini | ollama

# Embeddings — openai (default) or local sentence-transformers
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
make install      # create .venv + pip install pyproject.toml
make up           # docker compose up -d (starts PostgreSQL)
make down         # docker compose down
make migrate      # run Alembic DB migrations
make build-index  # embed data/business_docs/ → faiss_index/
make run          # start FastAPI on localhost:8080
make test         # pytest tests/
make etl-local    # run Beam pipeline with DirectRunner (no GCP billing)
make etl-gcp      # run Beam pipeline on Dataflow (production)
make bqml-train   # execute bqml/train_model.sql in BigQuery
make narratives   # run batch narrative generation for all products
make lint         # ruff + mypy
```

---

## Key conventions

### Python style
- Python 3.12, typed (use type hints everywhere)
- Formatter: `ruff format` — line length 100
- Linter: `ruff check` + `mypy --strict`
- All async functions use `async/await` — no sync DB calls in FastAPI routes
- Use `structlog` for logging, not `print()`

### BigQuery
- All SQL files live in `bqml/` and are executed via `bq query --use_legacy_sql=false`
- Table naming convention: `{project}:{dataset}.{table}` — e.g., `my-project:retail_forecasting.daily_sales`
- Always use `CREATE OR REPLACE` for idempotent SQL

### Beam pipeline
- For local dev, always use `DirectRunner` (no GCP cost)
- For production, use `DataflowRunner` with `--region=us-central1`
- Pipeline entry point: `pipeline/beam_etl.py`
- All `DoFn` classes live in `pipeline/transforms.py`

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
  id             SERIAL PRIMARY KEY,
  product_id     TEXT NOT NULL,
  forecast_date  DATE NOT NULL,
  predicted_sales FLOAT,
  lower_bound    FLOAT,
  upper_bound    FLOAT,
  created_at     TIMESTAMPTZ DEFAULT NOW()
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
1. make etl-local / etl-gcp     → clean raw sales → BigQuery
2. make bqml-train               → retrain ARIMA_PLUS model
3. bqml/generate_forecasts.sql   → export predictions → GCS
4. make build-index              → re-embed docs + forecasts → FAISS
5. make narratives               → GPT summaries for all products → PostgreSQL
```

---

## Testing

```bash
make test                        # run all tests
pytest tests/test_rag.py -v      # RAG unit tests only
pytest tests/ -k "narrative"     # filter by name
```

- Unit tests mock GCP and OpenAI calls — no real API calls in CI
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

---

## What NOT to do

- Never run `make etl-gcp` during local dev — it bills GCP. Use `make etl-local` instead.
- Never commit `.env` — it contains API keys.
- Never hardcode `project_id`, `bucket_name`, or API keys in source files — always read from `os.environ`.
- Never use `time.sleep()` in async code — use `await asyncio.sleep()`.
- Never call `vectorstore.persist()` inside a request handler — only during index build.

---

## Useful one-liners

```bash
# Check what's in your GCS bucket
gsutil ls gs://$GCS_BUCKET/

# Query BigQuery from terminal
bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM retail_forecasting.daily_sales'

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
