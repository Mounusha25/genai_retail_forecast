# ── Stage 1: dependency installation ──────────────────────────
FROM python:3.12-slim AS deps

WORKDIR /app

# Install build tools for packages with C extensions (faiss-cpu, asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
# Install all dependency groups except dev
RUN pip install --no-cache-dir \
    ".[base,etl,rag,api]"


# ── Stage 2: runtime image ─────────────────────────────────────
FROM python:3.12-slim AS runtime

# Create a non-root user
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Runtime system libraries only (libpq for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy application source
COPY --chown=app:app . .

# Make entrypoint executable
RUN chmod +x scripts/entrypoint.sh

USER app

EXPOSE 8080

# entrypoint.sh: builds FAISS index if missing → runs migrations → starts uvicorn
ENTRYPOINT ["scripts/entrypoint.sh"]
