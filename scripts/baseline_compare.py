"""
Backtest local forecasting logic against simple baselines.

This stays fully local: it reads ``data/raw/train.csv``, holds out the last
N calendar days, predicts that holdout window using only prior history, and
writes a compact Markdown report plus a CSV metrics table.

Usage:
    .venv/bin/python scripts/baseline_compare.py
    .venv/bin/python scripts/baseline_compare.py --stores 100 --horizon 30
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
REPORT_DIR = Path(__file__).resolve().parent.parent / "data" / "reports"


@dataclass(frozen=True)
class MetricRow:
    model: str
    mae: float
    rmse: float
    mape_pct: float
    bias_pct: float


def load_sales(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    train = pd.read_csv(
        data_dir / "train.csv",
        usecols=["Store", "Date", "Sales", "Open"],
        dtype={"Store": "int32", "Sales": "float64", "Open": "int8"},
        parse_dates=["Date"],
    )
    train["product_id"] = train["Store"].map(lambda store: f"STORE_{store:04d}")
    train["dow"] = train["Date"].dt.dayofweek
    return train


def _safe_mape(actual: pd.Series, predicted: pd.Series) -> float:
    nonzero = actual > 0
    if not nonzero.any():
        return 0.0
    return float((np.abs((actual[nonzero] - predicted[nonzero]) / actual[nonzero])).mean() * 100)


def _metrics(model: str, actual: pd.Series, predicted: pd.Series) -> MetricRow:
    errors = predicted - actual
    return MetricRow(
        model=model,
        mae=float(np.abs(errors).mean()),
        rmse=float(np.sqrt(np.square(errors).mean())),
        mape_pct=_safe_mape(actual, predicted),
        bias_pct=float(errors.sum() / actual.sum() * 100) if actual.sum() else 0.0,
    )


def _predict_store(history: pd.DataFrame, target_dates: list[pd.Timestamp]) -> dict[str, list[float]]:
    open_history = history[history["Open"] == 1].copy()
    if open_history.empty:
        zeros = [0.0 for _ in target_dates]
        return {
            "local_seasonal_trend": zeros,
            "seasonal_naive_7d": zeros,
            "moving_average_7d": zeros,
            "moving_average_28d": zeros,
        }

    last_date = history["Date"].max()
    recent_cut = last_date - pd.DateOffset(weeks=8)
    older_cut = last_date - pd.DateOffset(weeks=16)

    dow_mean = open_history[open_history["Date"] > recent_cut].groupby("dow")["Sales"].mean()
    recent_avg = open_history[open_history["Date"] > recent_cut]["Sales"].mean()
    older_avg = open_history[(open_history["Date"] > older_cut) & (open_history["Date"] <= recent_cut)]["Sales"].mean()
    trend = float(np.clip(recent_avg / older_avg, 0.7, 1.3)) if older_avg and not pd.isna(older_avg) else 1.0

    by_date = history.set_index("Date")["Sales"]
    ma7 = float(open_history.tail(7)["Sales"].mean())
    ma28 = float(open_history.tail(28)["Sales"].mean())

    local: list[float] = []
    seasonal_naive: list[float] = []
    moving7: list[float] = []
    moving28: list[float] = []

    for fdate in target_dates:
        dow = fdate.dayofweek
        base = float(dow_mean.get(dow, recent_avg if not pd.isna(recent_avg) else 0.0))
        local.append(max(base * trend, 0.0))

        prior_week = fdate - pd.DateOffset(days=7)
        seasonal_naive.append(float(by_date.get(prior_week, base)))
        moving7.append(ma7)
        moving28.append(ma28)

    return {
        "local_seasonal_trend": local,
        "seasonal_naive_7d": seasonal_naive,
        "moving_average_7d": moving7,
        "moving_average_28d": moving28,
    }


def compare_baselines(
    *,
    data_dir: Path = DATA_DIR,
    horizon_days: int = 30,
    num_stores: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sales = load_sales(data_dir)
    cutoff = sales["Date"].max() - pd.DateOffset(days=horizon_days)
    history = sales[sales["Date"] <= cutoff]
    holdout = sales[sales["Date"] > cutoff]

    store_ids = sorted(holdout["Store"].unique())
    if num_stores:
        store_ids = store_ids[:num_stores]

    prediction_frames: list[pd.DataFrame] = []
    for store in store_ids:
        store_history = history[history["Store"] == store]
        store_holdout = holdout[holdout["Store"] == store].sort_values("Date")
        target_dates = list(store_holdout["Date"])
        predictions = _predict_store(store_history, target_dates)

        frame = pd.DataFrame(
            {
                "product_id": f"STORE_{store:04d}",
                "forecast_date": target_dates,
                "actual_units": list(store_holdout["Sales"]),
                **predictions,
            }
        )
        prediction_frames.append(frame)

    predictions_df = pd.concat(prediction_frames, ignore_index=True)
    metric_rows = [
        _metrics(model, predictions_df["actual_units"], predictions_df[model]).__dict__
        for model in ("local_seasonal_trend", "seasonal_naive_7d", "moving_average_7d", "moving_average_28d")
    ]
    metrics_df = pd.DataFrame(metric_rows).sort_values("mae").reset_index(drop=True)
    return metrics_df, predictions_df


def write_report(metrics: pd.DataFrame, predictions: pd.DataFrame, report_dir: Path = REPORT_DIR) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "baseline_metrics.csv"
    md_path = report_dir / "baseline_comparison.md"

    metrics.to_csv(csv_path, index=False)
    best = metrics.iloc[0]
    sample_count = len(predictions)
    store_count = predictions["product_id"].nunique()
    start = predictions["forecast_date"].min().date()
    end = predictions["forecast_date"].max().date()

    lines = [
        "# Local Baseline Forecast Comparison",
        "",
        "Backtest on the final holdout window from the Rossmann training data.",
        "",
        f"- Stores evaluated: {store_count:,}",
        f"- Forecast rows evaluated: {sample_count:,}",
        f"- Holdout window: {start} to {end}",
        f"- Best model by MAE: `{best['model']}`",
        "",
        "| Model | MAE | RMSE | MAPE % | Bias % |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in metrics.itertuples(index=False):
        lines.append(
            f"| `{row.model}` | {row.mae:,.2f} | {row.rmse:,.2f} | {row.mape_pct:,.2f} | {row.bias_pct:,.2f} |"
        )
    lines.extend(
        [
            "",
            "Notes:",
            "- `local_seasonal_trend` mirrors the no-GCP local forecast approach: recent day-of-week demand plus a bounded short-term trend adjustment.",
            "- `seasonal_naive_7d` repeats the value from the same weekday one week earlier.",
            "- Moving-average baselines use the last open-store observations before the holdout window.",
            "- MAPE ignores zero-actual rows because percentage error is undefined for closed-store days.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")
    return md_path, csv_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare local Rossmann forecaster against simple baselines.")
    parser.add_argument("--stores", type=int, default=None, help="Limit to first N stores for faster iteration.")
    parser.add_argument("--horizon", type=int, default=30, help="Holdout horizon in days.")
    args = parser.parse_args()

    metrics, predictions = compare_baselines(horizon_days=args.horizon, num_stores=args.stores)
    md_path, csv_path = write_report(metrics, predictions)

    print(metrics.to_string(index=False, float_format=lambda value: f"{value:,.2f}"))
    print(f"\nWrote {md_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()
