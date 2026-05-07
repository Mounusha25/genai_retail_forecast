from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

# ── Forecasts ──────────────────────────────────────────────────


class ForecastRow(BaseModel):
    forecast_date: date
    forecast_units: float = Field(..., ge=0)
    ci_lower: float | None = None
    ci_upper: float | None = None

    model_config = {"from_attributes": True}


class ForecastsResponse(BaseModel):
    product_id: str
    count: int
    forecasts: list[ForecastRow]


# ── Narratives ─────────────────────────────────────────────────


class NarrativeResponse(BaseModel):
    product_id: str
    summary: str
    generated_at: datetime

    model_config = {"from_attributes": True}


# ── Pipeline ───────────────────────────────────────────────────


class PipelineTriggerResponse(BaseModel):
    run_id: int
    status: Literal["queued"]
    message: str = "Pipeline queued. Check /pipeline/runs/{run_id} for status."


class PipelineRunResponse(BaseModel):
    id: int
    status: str
    triggered_by: str
    started_at: datetime
    finished_at: datetime | None
    error: str | None

    model_config = {"from_attributes": True}


# ── Health ─────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    db: Literal["ok", "error"]
