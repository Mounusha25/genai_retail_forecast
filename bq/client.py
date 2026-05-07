from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import get_settings

logger = logging.getLogger(__name__)

_SQL_DIR = Path(__file__).parent / "sql"


def _load_sql(filename: str, **kwargs: Any) -> str:
    """Load a SQL file from bq/sql/ and substitute {placeholders}."""
    raw = (_SQL_DIR / filename).read_text()
    return raw.format(**kwargs)


class BigQueryClient:
    """
    Thin wrapper around ``google.cloud.bigquery.Client`` that:
    - Injects project / dataset placeholders into SQL templates.
    - Retries transient BigQuery errors with exponential back-off.
    - Blocks until each job completes (suitable for batch pipelines).
    """

    def __init__(self) -> None:
        cfg = get_settings()
        self._project = cfg.google_cloud_project
        self._dataset = cfg.bq_dataset
        self._location = cfg.bq_location
        self._horizon = cfg.forecast_horizon_days
        self._client = bigquery.Client(project=self._project, location=self._location)

    # ── Internal helpers ───────────────────────────────────────

    def _placeholders(self) -> dict[str, Any]:
        return {
            "project": self._project,
            "dataset": self._dataset,
            "horizon": self._horizon,
        }

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        stop=stop_after_attempt(4),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _run_query(self, sql: str, job_config: QueryJobConfig | None = None) -> bigquery.QueryJob:
        job = self._client.query(
            sql,
            job_config=job_config or QueryJobConfig(),
        )
        job.result()  # block until done
        logger.info("BQ job complete | job_id=%s bytes=%s", job.job_id, job.total_bytes_processed)
        return job

    # ── Public API ─────────────────────────────────────────────

    def create_view(self) -> None:
        logger.info("Creating/refreshing v_daily_sales view")
        self._run_query(_load_sql("create_view.sql", **self._placeholders()))

    def train_model(self) -> None:
        logger.info("Training ARIMA_PLUS model (horizon=%d days)", self._horizon)
        self._run_query(_load_sql("train_model.sql", **self._placeholders()))

    def generate_forecast(self) -> None:
        logger.info("Materialising %d-day forecasts", self._horizon)
        self._run_query(_load_sql("generate_forecast.sql", **self._placeholders()))

    def evaluate_model(self) -> list[dict[str, Any]]:
        logger.info("Evaluating model accuracy")
        job = self._run_query(_load_sql("evaluate_model.sql", **self._placeholders()))
        return [dict(row) for row in job.result()]

    def fetch_forecasts(self, product_id: str) -> list[dict[str, Any]]:
        """Fetch the most recent 30-day forecast for a given product."""
        sql = f"""
            SELECT
                CAST(forecast_date AS STRING) AS forecast_date,
                forecast_units,
                ci_lower,
                ci_upper,
                generated_at
            FROM `{self._project}.{self._dataset}.forecasts_30d`
            WHERE product_id = @product_id
            ORDER BY forecast_date
        """
        job_config = QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("product_id", "STRING", product_id.upper()),
            ],
        )
        job = self._run_query(sql, job_config)
        return [dict(row) for row in job.result()]
