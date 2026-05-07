"""
Seed script: upload sample CSV data to GCS for local development/testing.

Usage:
    python -m scripts.seed_data
"""

from __future__ import annotations

import csv
import io
import random
from datetime import date, timedelta

from google.cloud import storage

from config import get_settings


def generate_sales_csv(num_skus: int = 10, days: int = 730) -> str:
    """Generate a synthetic sales CSV with 2 years of daily data."""
    rows = [["date", "product_id", "store_id", "units_sold", "revenue"]]
    today = date.today()
    start = today - timedelta(days=days)

    for sku_n in range(1, num_skus + 1):
        sku = f"SKU-{sku_n:03d}"
        base_demand = random.randint(5, 200)
        unit_price = round(random.uniform(5.0, 150.0), 2)

        for d in range(days):
            day = start + timedelta(days=d)
            # Simple trend + weekly seasonality + noise
            trend = 1 + d / days * 0.1
            weekly_factor = 1.2 if day.weekday() in (4, 5) else 1.0
            noise = random.uniform(0.7, 1.3)
            units = max(0, round(base_demand * trend * weekly_factor * noise))
            revenue = round(units * unit_price, 2)
            rows.append([day.isoformat(), sku, "S01", units, revenue])

    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    return buf.getvalue()


def main() -> None:
    cfg = get_settings()
    client = storage.Client(project=cfg.google_cloud_project)
    bucket = client.bucket(cfg.gcs_bucket)

    blob_name = "sales/seed_data.csv"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(generate_sales_csv(), content_type="text/csv")

    print(f"Seeded gs://{cfg.gcs_bucket}/{blob_name}")


if __name__ == "__main__":
    main()
