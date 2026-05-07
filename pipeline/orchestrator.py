from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from config import get_settings

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Coordinates the full forecasting pipeline end-to-end:

    1. Beam ETL   — reads raw CSVs from GCS, writes clean rows to BigQuery.
    2. BQ view    — refreshes the aggregated daily-sales view.
    3. BQ train   — retrains the ARIMA_PLUS model.
    4. BQ forecast — materialises the 30-day forecast table.
    5. DB ingest  — syncs BQ forecast rows to PostgreSQL.
    6. Narratives — generates GPT-4 summaries per product and writes to PostgreSQL.
    """

    def __init__(self) -> None:
        self._cfg = get_settings()

    # ── Top-level entry point ──────────────────────────────────

    async def run(self) -> None:
        start = datetime.now(UTC)
        logger.info("Pipeline started at %s", start.isoformat())

        await self._run_etl()
        await asyncio.to_thread(self._run_bq)
        await self._sync_forecasts_to_postgres()
        await self._generate_narratives()

        elapsed = (datetime.now(UTC) - start).total_seconds()
        logger.info("Pipeline finished in %.1f s", elapsed)

    # ── Step 1: Beam ETL ───────────────────────────────────────

    async def _run_etl(self) -> None:
        logger.info("Step 1/4 — Beam ETL")
        from etl.beam_pipeline import run as beam_run  # noqa: PLC0415

        await asyncio.to_thread(
            beam_run,
            runner="DataflowRunner" if self._cfg.is_production else "DirectRunner",
        )

    # ── Step 2: BigQuery (view + train + forecast) ─────────────

    def _run_bq(self) -> None:
        logger.info("Step 2/4 — BigQuery ML (view → train → forecast)")
        from bq.client import BigQueryClient  # noqa: PLC0415

        bq = BigQueryClient()
        bq.create_view()
        bq.train_model()
        bq.generate_forecast()

        metrics = bq.evaluate_model()
        for row in metrics[:5]:
            logger.info(
                "Model eval | product=%s mape=%.2f%% rmse=%.2f",
                row.get("product_id"),
                row.get("mape_pct", 0),
                row.get("rmse", 0),
            )

    # ── Step 3: Sync BQ forecasts → PostgreSQL ─────────────────

    async def _sync_forecasts_to_postgres(self) -> None:
        logger.info("Step 3/4 — Syncing BQ forecasts to PostgreSQL")
        from sqlalchemy import delete  # noqa: PLC0415

        from bq.client import BigQueryClient  # noqa: PLC0415
        from db.models import Forecast  # noqa: PLC0415
        from db.session import _get_session_factory  # noqa: PLC0415

        bq = BigQueryClient()
        product_ids = await asyncio.to_thread(self._list_products, bq)
        session_factory = _get_session_factory()

        total = 0
        for pid in product_ids:
            rows = await asyncio.to_thread(bq.fetch_forecasts, pid)
            if not rows:
                continue

            async with session_factory() as db:
                # Replace existing forecasts for this product atomically
                await db.execute(delete(Forecast).where(Forecast.product_id == pid))
                db.add_all(
                    [
                        Forecast(
                            product_id=pid,
                            forecast_date=row["forecast_date"],
                            forecast_units=row["forecast_units"],
                            ci_lower=row.get("ci_lower"),
                            ci_upper=row.get("ci_upper"),
                            generated_at=datetime.now(UTC),
                        )
                        for row in rows
                    ]
                )
                await db.commit()
            total += len(rows)

        logger.info("Synced %d forecast rows across %d products", total, len(product_ids))

    @staticmethod
    def _list_products(bq: object) -> list[str]:
        """Query BigQuery for the distinct product IDs in the forecast table."""
        from google.cloud import bigquery as bq_lib  # noqa: PLC0415

        from config import get_settings as _cfg  # noqa: PLC0415

        cfg = _cfg()
        client = bq_lib.Client(project=cfg.google_cloud_project)
        sql = f"SELECT DISTINCT product_id FROM `{cfg.bq_forecast_table}` ORDER BY 1"
        return [row["product_id"] for row in client.query(sql).result()]

    # ── Step 4: Generate RAG narratives ────────────────────────

    async def _generate_narratives(self) -> None:
        logger.info("Step 4/4 — Generating RAG narratives")
        from sqlalchemy import delete, select  # noqa: PLC0415

        from db.models import Forecast, Narrative  # noqa: PLC0415
        from db.session import _get_session_factory  # noqa: PLC0415
        from rag.narrative_chain import NarrativeChain  # noqa: PLC0415

        chain = NarrativeChain()
        session_factory = _get_session_factory()
        generated = 0

        async with session_factory() as db:
            result = await db.execute(select(Forecast.product_id).distinct().order_by(Forecast.product_id))
            product_ids = [row[0] for row in result.all()]

        for pid in product_ids:
            try:
                async with session_factory() as db:
                    result = await db.execute(
                        select(Forecast).where(Forecast.product_id == pid).order_by(Forecast.forecast_date)
                    )
                    forecast_rows = [
                        {
                            "forecast_date": str(r.forecast_date),
                            "forecast_units": r.forecast_units,
                            "ci_lower": r.ci_lower,
                            "ci_upper": r.ci_upper,
                        }
                        for r in result.scalars().all()
                    ]

                summary = await asyncio.to_thread(chain.generate, pid, forecast_rows)

                async with session_factory() as db:
                    await db.execute(delete(Narrative).where(Narrative.product_id == pid))
                    db.add(
                        Narrative(
                            product_id=pid,
                            summary=summary,
                            generated_at=datetime.now(UTC),
                        )
                    )
                    await db.commit()

                generated += 1
                logger.info("Narrative generated for %s", pid)

            except Exception:
                logger.exception("Failed to generate narrative for %s — skipping", pid)

        logger.info("Generated %d narratives", generated)
