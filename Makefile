.DEFAULT_GOAL := help

# ── Variables ────────────────────────────────────────────────────
PYTHON   := python3
VENV     := .venv
PIP      := $(VENV)/bin/pip
PYTEST   := $(VENV)/bin/pytest
RUFF     := $(VENV)/bin/ruff
MYPY     := $(VENV)/bin/mypy
UVICORN  := $(VENV)/bin/uvicorn
ALEMBIC  := $(VENV)/bin/alembic

# ── Help ─────────────────────────────────────────────────────────
.PHONY: help
help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── Setup ────────────────────────────────────────────────────────
.PHONY: install
install:  ## Create venv and install all dependency groups
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[base,etl,rag,api,ui,dev]"

.PHONY: env
env:  ## Copy .env.example → .env (won't overwrite)
	@test -f .env || cp .env.example .env && echo "Created .env — fill in your secrets"

# ── Code quality ─────────────────────────────────────────────────
.PHONY: lint
lint:  ## Run Ruff linter
	$(RUFF) check .

.PHONY: format
format:  ## Auto-format with Ruff
	$(RUFF) format .

.PHONY: typecheck
typecheck:  ## Run mypy type checker
	$(MYPY) api config db pipeline rag etl

.PHONY: check
check: lint typecheck  ## Run lint + typecheck

# ── Tests ────────────────────────────────────────────────────────
.PHONY: test
test:  ## Run the full test suite with coverage
	$(PYTEST) --tb=short

.PHONY: test-fast
test-fast:  ## Run tests without coverage (faster feedback)
	$(PYTEST) --no-cov --tb=short

# ── Local services ───────────────────────────────────────────────
.PHONY: up
up:  ## Start local PostgreSQL via Docker Compose
	docker compose up -d postgres
	@echo "Waiting for postgres to be ready..."
	@until docker compose exec postgres pg_isready -U retail; do sleep 1; done

.PHONY: down
down:  ## Stop all Docker Compose services
	docker compose down

# ── Database migrations ──────────────────────────────────────────
.PHONY: migrate
migrate:  ## Apply all pending Alembic migrations
	env $$(cat .env | grep -v '^#' | xargs) $(ALEMBIC) upgrade head

.PHONY: sync-forecasts
sync-forecasts:  ## Pull forecasts from BigQuery into PostgreSQL
	$(VENV)/bin/python scripts/sync_forecasts.py

.PHONY: sync-narratives
sync-narratives:  ## Generate AI narratives and save to PostgreSQL (first 20 stores)
	$(VENV)/bin/python scripts/sync_narratives.py --limit 20

.PHONY: ui
ui:  ## Launch the Streamlit demo UI (http://localhost:8501)
	$(VENV)/bin/streamlit run streamlit_app.py

.PHONY: migration
migration:  ## Generate a new migration (make migration msg="your description")
	$(ALEMBIC) revision --autogenerate -m "$(msg)"

.PHONY: migrate-down
migrate-down:  ## Roll back the last migration
	$(ALEMBIC) downgrade -1

# ── Run API ──────────────────────────────────────────────────────
.PHONY: run
run:  ## Start the FastAPI dev server (auto-reload)
	$(UVICORN) api.main:app --reload --host 0.0.0.0 --port 8080

# ── Data / index ─────────────────────────────────────────────────
.PHONY: build-index
build-index:  ## (Re)build the FAISS embedding index from data/business_docs
	$(PYTHON) -m scripts.build_index

.PHONY: seed
seed:  ## Upload synthetic sales CSV to GCS (dev only)
	$(PYTHON) -m scripts.seed_data

# ── Pipeline ─────────────────────────────────────────────────────
.PHONY: etl-local
etl-local:  ## Run the Beam ETL with DirectRunner (local)
	$(PYTHON) -m etl.beam_pipeline --runner DirectRunner

# ── Docker ───────────────────────────────────────────────────────
.PHONY: docker-build
docker-build:  ## Build the production Docker image
	docker build --target runtime -t retail-forecasting-api:local .

.PHONY: docker-run
docker-run:  ## Run the API container locally (requires .env)
	docker run --rm -p 8080:8080 --env-file .env retail-forecasting-api:local

# ── CI shortcut ──────────────────────────────────────────────────
.PHONY: ci
ci: check test  ## Full CI check: lint + typecheck + tests
