"""
scripts/seed_forecasts_local.py
--------------------------------
Local-only substitute for the BigQuery ML forecasting stage.

Reads the real Rossmann `data/raw/train.csv` + `data/raw/store.csv`,
computes a per-store 30-day forecast directly in Python (day-of-week
seasonal average with a short-term trend adjustment, +/- 80% CI band
from the day-of-week standard deviation), and writes the results
straight into the PostgreSQL `forecasts` table.

This exists so the project is runnable without a GCP project /
BigQuery ML / Apache Beam — those stages are unchanged and still the
"real" path documented in the README, this is a local dev shortcut
that fills the same `forecasts` table with the same schema.

Usage:
    .venv/bin/python scripts/seed_forecasts_local.py
    .venv/bin/python scripts/seed_forecasts_local.py --stores 50   # faster subset
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import get_settings
from db.models import Base, Forecast

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def build_forecasts(
    num_stores: int | None,
    horizon_days: int,
    data_dir: Path = DATA_DIR,
) -> pd.DataFrame:
    train = pd.read_csv(
        data_dir / "train.csv",
        usecols=["Store", "Date", "Sales", "Open"],
        dtype={"Store": "int32", "Sales": "float64", "Open": "int8"},
        parse_dates=["Date"],
    )
    train = train[train["Open"] == 1]
    train["dow"] = train["Date"].dt.dayofweek

    store_ids = sorted(train["Store"].unique())
    if num_stores:
        store_ids = store_ids[:num_stores]
    train = train[train["Store"].isin(store_ids)]

    last_date = train["Date"].max()
    recent_cut = last_date - pd.DateOffset(weeks=8)
    older_cut = last_date - pd.DateOffset(weeks=16)

    dow_stats = (
        train[train["Date"] > recent_cut]
        .groupby(["Store", "dow"])["Sales"]
        .agg(["mean", "std"])
        .rename(columns={"mean": "dow_mean", "std": "dow_std"})
    )

    recent_avg = train[train["Date"] > recent_cut].groupby("Store")["Sales"].mean()
    older_avg = train[(train["Date"] > older_cut) & (train["Date"] <= recent_cut)].groupby("Store")["Sales"].mean()
    trend = (recent_avg / older_avg.replace(0, np.nan)).clip(lower=0.7, upper=1.3).fillna(1.0)

    forecast_dates = [last_date + timedelta(days=d) for d in range(1, horizon_days + 1)]

    rows = []
    for store in store_ids:
        product_id = f"STORE_{store:04d}"
        store_trend = float(trend.get(store, 1.0))
        for fdate in forecast_dates:
            dow = fdate.dayofweek
            try:
                mean, std = dow_stats.loc[(store, dow)]
            except KeyError:
                mean, std = recent_avg.get(store, 0.0), recent_avg.get(store, 0.0) * 0.15
            if pd.isna(std) or std == 0:
                std = mean * 0.12
            forecast_units = round(float(mean) * store_trend, 1)
            ci_half = round(1.28 * float(std), 1)  # ~80% CI
            rows.append(
                {
                    "product_id": product_id,
                    "forecast_date": fdate.date(),
                    "forecast_units": max(forecast_units, 0.0),
                    "ci_lower": max(forecast_units - ci_half, 0.0),
                    "ci_upper": forecast_units + ci_half,
                }
            )

    return pd.DataFrame(rows)


async def write_to_postgres(df: pd.DataFrame) -> None:
    cfg = get_settings()
    engine = create_async_engine(cfg.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        await session.execute(delete(Forecast))
        objects = [Forecast(**row) for row in df.to_dict(orient="records")]
        session.add_all(objects)
        await session.commit()

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed PostgreSQL forecasts table from local Rossmann CSVs (no GCP/BQ needed)"
    )
    parser.add_argument("--stores", type=int, default=None, help="Limit to first N stores (default: all 1,115)")
    args = parser.parse_args()

    cfg = get_settings()
    df = build_forecasts(args.stores, cfg.forecast_horizon_days)
    print(f"Computed {len(df)} forecast rows for {df['product_id'].nunique()} stores.")

    asyncio.run(write_to_postgres(df))
    print(f"Wrote {len(df)} rows to PostgreSQL `forecasts` table.")


if __name__ == "__main__":
    main()
