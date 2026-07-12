from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from fastapi import APIRouter
from sqlalchemy import distinct, func, select

from api.dependencies import DbSession
from api.schemas import (
    BaselineMetricRow,
    BaselineMetricsResponse,
    DailyTrendResponse,
    DailyTrendRow,
    DayOfWeekPatternResponse,
    DayOfWeekPatternRow,
    FleetSummaryResponse,
    FleetSummaryRow,
    NarrativeCoverageResponse,
    StoreListResponse,
    WeeklyFleetResponse,
    WeeklyFleetRow,
)
from db.models import Forecast, Narrative

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

BASELINE_METRICS_PATH = Path(__file__).resolve().parents[2] / "data" / "reports" / "baseline_metrics.csv"
TOTAL_STORES = 1115
DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@router.get("/stores", response_model=StoreListResponse, summary="List stores with forecast rows")
async def list_stores(db: DbSession) -> StoreListResponse:
    result = await db.execute(select(Forecast.product_id).distinct().order_by(Forecast.product_id))
    stores = [row[0] for row in result.all()]
    return StoreListResponse(count=len(stores), stores=stores)


@router.get("/fleet-summary", response_model=FleetSummaryResponse, summary="Fleet-level per-store forecast summary")
async def fleet_summary(db: DbSession) -> FleetSummaryResponse:
    ci_width = Forecast.ci_upper - Forecast.ci_lower
    result = await db.execute(
        select(
            Forecast.product_id,
            func.sum(Forecast.forecast_units).label("total_30d"),
            func.avg(Forecast.forecast_units).label("avg_daily"),
            func.max(Forecast.forecast_units).label("peak_day"),
            func.avg(ci_width).label("avg_ci_width"),
        )
        .group_by(Forecast.product_id)
        .order_by(func.sum(Forecast.forecast_units).desc())
    )
    rows = [
        FleetSummaryRow(
            product_id=row.product_id,
            total_30d=float(row.total_30d or 0),
            avg_daily=float(row.avg_daily or 0),
            peak_day=float(row.peak_day or 0),
            avg_ci_width=float(row.avg_ci_width) if row.avg_ci_width is not None else None,
        )
        for row in result.all()
    ]
    return FleetSummaryResponse(count=len(rows), stores=rows)


@router.get("/daily-trend", response_model=DailyTrendResponse, summary="Fleet daily aggregate forecast trend")
async def daily_trend(db: DbSession) -> DailyTrendResponse:
    result = await db.execute(
        select(
            Forecast.forecast_date,
            func.sum(Forecast.forecast_units).label("total_units"),
            func.avg(Forecast.forecast_units).label("avg_per_store"),
            func.count(distinct(Forecast.product_id)).label("stores_active"),
        )
        .group_by(Forecast.forecast_date)
        .order_by(Forecast.forecast_date)
    )
    rows = [
        DailyTrendRow(
            forecast_date=row.forecast_date,
            total_units=float(row.total_units or 0),
            avg_per_store=float(row.avg_per_store or 0),
            stores_active=int(row.stores_active or 0),
        )
        for row in result.all()
    ]
    return DailyTrendResponse(count=len(rows), days=rows)


@router.get("/dow-pattern", response_model=DayOfWeekPatternResponse, summary="Average forecast by day of week")
async def day_of_week_pattern(db: DbSession) -> DayOfWeekPatternResponse:
    result = await db.execute(select(Forecast.forecast_date, Forecast.forecast_units))
    totals: dict[int, float] = defaultdict(float)
    counts: dict[int, int] = defaultdict(int)

    for forecast_date, units in result.all():
        dow = forecast_date.weekday()
        totals[dow] += float(units or 0)
        counts[dow] += 1

    rows = [
        DayOfWeekPatternRow(
            dow=dow,
            day_abbr=DAY_ABBR[dow],
            avg_units=totals[dow] / counts[dow] if counts[dow] else 0.0,
            total_units=totals[dow],
        )
        for dow in range(7)
        if counts[dow]
    ]
    return DayOfWeekPatternResponse(count=len(rows), days=rows)


@router.get("/weekly-fleet", response_model=WeeklyFleetResponse, summary="Fleet weekly aggregate forecast totals")
async def weekly_fleet(db: DbSession) -> WeeklyFleetResponse:
    result = await db.execute(select(Forecast.forecast_date, Forecast.forecast_units, Forecast.product_id))
    totals: dict[date, float] = defaultdict(float)
    stores_by_week: dict[date, set[str]] = defaultdict(set)

    for forecast_date, units, product_id in result.all():
        week_start = forecast_date - timedelta(days=forecast_date.weekday())
        totals[week_start] += float(units or 0)
        stores_by_week[week_start].add(product_id)

    rows = [
        WeeklyFleetRow(
            week_start=week_start,
            total_units=totals[week_start],
            avg_per_store=totals[week_start] / len(stores_by_week[week_start]) if stores_by_week[week_start] else 0.0,
        )
        for week_start in sorted(totals)
    ]
    return WeeklyFleetResponse(count=len(rows), weeks=rows)


@router.get("/narrative-coverage", response_model=NarrativeCoverageResponse, summary="Narrative generation coverage")
async def narrative_coverage(db: DbSession) -> NarrativeCoverageResponse:
    result = await db.execute(
        select(
            func.count(Narrative.id).label("narrative_rows"),
            func.count(distinct(Narrative.product_id)).label("stores_with_narratives"),
        )
    )
    row = result.one()
    stores_with_narratives = int(row.stores_with_narratives or 0)
    return NarrativeCoverageResponse(
        narrative_rows=int(row.narrative_rows or 0),
        stores_with_narratives=stores_with_narratives,
        total_stores=TOTAL_STORES,
        coverage_pct=stores_with_narratives / TOTAL_STORES * 100,
    )


@router.get("/baseline-metrics", response_model=BaselineMetricsResponse, summary="Local baseline model metrics")
async def baseline_metrics() -> BaselineMetricsResponse:
    if not BASELINE_METRICS_PATH.exists():
        return BaselineMetricsResponse(count=0, metrics=[])

    with BASELINE_METRICS_PATH.open(newline="") as fh:
        metrics = [
            BaselineMetricRow(
                model=row["model"],
                mae=float(row["mae"]),
                rmse=float(row["rmse"]),
                mape_pct=float(row["mape_pct"]),
                bias_pct=float(row["bias_pct"]),
            )
            for row in csv.DictReader(fh)
        ]
    return BaselineMetricsResponse(count=len(metrics), metrics=metrics)
