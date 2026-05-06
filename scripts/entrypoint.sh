#!/bin/sh
# entrypoint.sh — Container startup script for Cloud Run
#
# Runs three jobs in order before handing off to uvicorn:
#   1. Build the FAISS index from data/business_docs/ (only if missing)
#   2. Run Alembic migrations (idempotent — safe to run every startup)
#   3. Start the FastAPI server
#
# All three must succeed; any failure aborts startup so Cloud Run
# marks the instance as unhealthy and rolls back.
set -e

echo "[entrypoint] Starting retail-forecasting-api ..."

# ── 1. FAISS index ────────────────────────────────────────────────
FAISS_DIR="${FAISS_INDEX_PATH:-data/faiss_index}"
if [ ! -d "$FAISS_DIR" ] || [ -z "$(ls -A "$FAISS_DIR" 2>/dev/null)" ]; then
  echo "[entrypoint] FAISS index not found at $FAISS_DIR — building now ..."
  python -m scripts.build_index
  echo "[entrypoint] FAISS index built."
else
  echo "[entrypoint] FAISS index found at $FAISS_DIR — skipping build."
fi

# ── 2. Database migrations ────────────────────────────────────────
echo "[entrypoint] Running Alembic migrations ..."
alembic upgrade head
echo "[entrypoint] Migrations complete."

# ── 3. Start the API ──────────────────────────────────────────────
echo "[entrypoint] Starting uvicorn on 0.0.0.0:${PORT:-8080} ..."
exec uvicorn api.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8080}" \
  --workers "${UVICORN_WORKERS:-2}" \
  --proxy-headers \
  --forwarded-allow-ips "*"
