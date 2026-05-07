"""
scripts/run_bqml.py
-------------------
Execute the full BigQuery ML pipeline in sequence:
  1. Create / refresh the daily_sales view
  2. Train the ARIMA_PLUS model
  3. Generate 30-day forecasts
  4. Evaluate the model

Run with:
    python scripts/run_bqml.py
    python scripts/run_bqml.py --step train   # single step
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure repo root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bq.client import BigQueryClient  # noqa: E402
from config import get_settings  # noqa: E402

STEPS = ["view", "train", "forecast", "evaluate"]


def run_step(client: BigQueryClient, step: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  Step: {step.upper()}")
    print(f"{'=' * 60}")
    t0 = time.perf_counter()

    if step == "view":
        client.create_view()
    elif step == "train":
        client.train_model()
    elif step == "forecast":
        client.generate_forecast()
    elif step == "evaluate":
        rows = client.evaluate_model()
        if rows:
            print("\nModel evaluation metrics:")
            for r in rows:
                for k, v in r.items():
                    print(f"  {k}: {v}")

    elapsed = time.perf_counter() - t0
    print(f"  Done in {elapsed:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BigQuery ML pipeline steps")
    parser.add_argument(
        "--step",
        choices=STEPS + ["all"],
        default="all",
        help="Which step to run (default: all)",
    )
    args = parser.parse_args()

    cfg = get_settings()
    print(f"Project : {cfg.google_cloud_project}")
    print(f"Dataset : {cfg.bq_dataset}")
    print(f"Horizon : {cfg.forecast_horizon_days} days")

    client = BigQueryClient()

    steps_to_run = STEPS if args.step == "all" else [args.step]
    for step in steps_to_run:
        run_step(client, step)

    print("\nBigQuery ML pipeline complete.")


if __name__ == "__main__":
    main()
