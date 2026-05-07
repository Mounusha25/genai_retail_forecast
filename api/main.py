from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes.forecasts import router as forecasts_router
from api.routes.narratives import router as narratives_router
from api.routes.pipeline import router as pipeline_router
from config import get_settings
from config.logging import configure_logging
from db.session import create_tables, dispose_engine

logger = logging.getLogger(__name__)


# ── Lifespan ───────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    cfg = get_settings()
    configure_logging(log_level=cfg.log_level, json_logs=cfg.is_production)
    logger.info("Starting up | env=%s version=%s", cfg.environment, cfg.app_version)
    await create_tables()
    yield
    await dispose_engine()
    logger.info("Shutdown complete")


# ── App factory ────────────────────────────────────────────────


def create_app() -> FastAPI:
    cfg = get_settings()

    app = FastAPI(
        title="GenAI Retail Forecasting API",
        description=("Serves 30-day ARIMA_PLUS demand forecasts and GPT-4 executive summaries for retail products."),
        version=cfg.app_version,
        docs_url=None if cfg.is_production else "/docs",
        redoc_url=None if cfg.is_production else "/redoc",
        openapi_url=None if cfg.is_production else "/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ───────────────────────────────────────────────────
    # Tighten allowed_origins for your actual frontend domain in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not cfg.is_production else [],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # ── Global exception handler ───────────────────────────────
    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. Please try again later."},
        )

    # ── Health check ───────────────────────────────────────────
    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def health() -> dict[str, str]:
        from sqlalchemy import text

        from db.session import _get_engine

        db_status = "ok"
        try:
            async with _get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            db_status = "error"

        overall = "ok" if db_status == "ok" else "degraded"
        return {"status": overall, "version": cfg.app_version, "db": db_status}

    # ── Routers ────────────────────────────────────────────────
    api_prefix = "/v1"
    app.include_router(forecasts_router, prefix=api_prefix)
    app.include_router(narratives_router, prefix=api_prefix)
    app.include_router(pipeline_router, prefix=api_prefix)

    return app


app = create_app()
