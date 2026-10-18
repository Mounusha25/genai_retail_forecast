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


# ── Dashboard ──────────────────────────────────────────────────


class StoreListResponse(BaseModel):
    count: int = Field(..., ge=0)
    stores: list[str]


class FleetSummaryRow(BaseModel):
    product_id: str
    total_30d: float = Field(..., ge=0)
    avg_daily: float = Field(..., ge=0)
    peak_day: float = Field(..., ge=0)
    avg_ci_width: float | None = Field(default=None, ge=0)


class FleetSummaryResponse(BaseModel):
    count: int = Field(..., ge=0)
    stores: list[FleetSummaryRow]


class DailyTrendRow(BaseModel):
    forecast_date: date
    total_units: float = Field(..., ge=0)
    avg_per_store: float = Field(..., ge=0)
    stores_active: int = Field(..., ge=0)


class DailyTrendResponse(BaseModel):
    count: int = Field(..., ge=0)
    days: list[DailyTrendRow]


class DayOfWeekPatternRow(BaseModel):
    dow: int = Field(..., ge=0, le=6)
    day_abbr: str
    avg_units: float = Field(..., ge=0)
    total_units: float = Field(..., ge=0)


class DayOfWeekPatternResponse(BaseModel):
    count: int = Field(..., ge=0)
    days: list[DayOfWeekPatternRow]


class WeeklyFleetRow(BaseModel):
    week_start: date
    total_units: float = Field(..., ge=0)
    avg_per_store: float = Field(..., ge=0)


class WeeklyFleetResponse(BaseModel):
    count: int = Field(..., ge=0)
    weeks: list[WeeklyFleetRow]


class NarrativeCoverageResponse(BaseModel):
    narrative_rows: int = Field(..., ge=0)
    stores_with_narratives: int = Field(..., ge=0)
    total_stores: int = Field(..., ge=0)
    coverage_pct: float = Field(..., ge=0, le=100)


class BaselineMetricRow(BaseModel):
    model: str
    mae: float = Field(..., ge=0)
    rmse: float = Field(..., ge=0)
    mape_pct: float = Field(..., ge=0)
    bias_pct: float


class BaselineMetricsResponse(BaseModel):
    count: int = Field(..., ge=0)
    metrics: list[BaselineMetricRow]


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
