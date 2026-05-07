"""
scripts/sync_forecasts.py
--------------------------
Pull the latest forecasts from BigQuery `forecasts_30d` and upsert them
into the local PostgreSQL `forecasts` table.

Run with:
    .venv/bin/python scripts/sync_forecasts.py
    .venv/bin/python scripts/sync_forecasts.py --product STORE_0001  # single store
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.cloud import bigquery
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import get_settings
from db.models import Forecast


async def sync(product_id: str | None = None) -> None:
    cfg = get_settings()

    # ── 1. Fetch from BigQuery ─────────────────────────────────
    bq = bigquery.Client(project=cfg.google_cloud_project, location=cfg.bq_location)
    where = f"WHERE product_id = '{product_id.upper()}'" if product_id else ""
    sql = f"""
        SELECT forecast_date, product_id, forecast_units, ci_lower, ci_upper, generated_at
        FROM `{cfg.google_cloud_project}.{cfg.bq_dataset}.forecasts_30d`
        {where}
        ORDER BY product_id, forecast_date
    """
    rows = list(bq.query(sql).result())
    if not rows:
        print("No rows returned from BigQuery — run `--step forecast` first.")
        return
    print(f"Fetched {len(rows)} rows from BigQuery.")

    # ── 2. Write to PostgreSQL ─────────────────────────────────
    engine = create_async_engine(cfg.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Clear existing forecasts for the affected product(s)
        if product_id:
            await session.execute(delete(Forecast).where(Forecast.product_id == product_id.upper()))
        else:
            await session.execute(delete(Forecast))

        now = datetime.now(UTC)
        objects = [
            Forecast(
                product_id=row.product_id,
                forecast_date=row.forecast_date,
                forecast_units=float(row.forecast_units),
                ci_lower=float(row.ci_lower) if row.ci_lower is not None else None,
                ci_upper=float(row.ci_upper) if row.ci_upper is not None else None,
                generated_at=now,
            )
            for row in rows
        ]
        session.add_all(objects)
        await session.commit()

    await engine.dispose()
    print(f"Synced {len(objects)} forecasts to PostgreSQL.")

    # ── 3. Summary ─────────────────────────────────────────────
    products = {r.product_id for r in rows}
    print(f"Products synced: {len(products)}")
    print(f"Sample products: {sorted(products)[:5]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync BigQuery forecasts to PostgreSQL")
    parser.add_argument("--product", help="Sync a single product_id only", default=None)
    args = parser.parse_args()
    asyncio.run(sync(args.product))


if __name__ == "__main__":
    main()
