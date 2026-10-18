"""Run rolling forecast backtests and produce a versioned monitoring report."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitoring import EvaluationSnapshot, QualityGateConfig, evaluate_quality_gate
from scripts.baseline_compare import DATA_DIR, REPORT_DIR, compare_baselines, load_sales

DEFAULT_MODEL = "local_seasonal_trend"


def run_monitoring(
    *,
    data_dir: Path = DATA_DIR,
    output_dir: Path = REPORT_DIR,
    model: str = DEFAULT_MODEL,
    model_version: str = "local-seasonal-trend-v1",
    windows: int = 4,
    horizon_days: int = 30,
    step_days: int = 30,
    num_stores: int | None = None,
    config: QualityGateConfig | None = None,
) -> tuple[dict[str, object], Path, Path]:
    """Evaluate rolling windows and write CSV history plus the latest gate report."""
    if windows < 2:
        raise ValueError("windows must be at least 2 so a reference window exists")

    thresholds = config or QualityGateConfig()
    latest_date = pd.Timestamp(load_sales(data_dir)["Date"].max())
    evaluation_ends = [latest_date - pd.DateOffset(days=step_days * offset) for offset in reversed(range(windows))]

    snapshots: list[EvaluationSnapshot] = []
    for evaluation_end in evaluation_ends:
        metrics, predictions = compare_baselines(
            data_dir=data_dir,
            horizon_days=horizon_days,
            num_stores=num_stores,
            holdout_end=evaluation_end,
        )
        model_rows = metrics[metrics["model"] == model]
        if model_rows.empty:
            raise ValueError(f"Model {model!r} is not present in the backtest output")
        metric = model_rows.iloc[0]
        snapshots.append(
            EvaluationSnapshot(
                model=model,
                model_version=model_version,
                window_start=pd.Timestamp(predictions["forecast_date"].min()).date(),
                window_end=pd.Timestamp(predictions["forecast_date"].max()).date(),
                sample_count=len(predictions),
                store_count=int(predictions["product_id"].nunique()),
                mae=float(metric["mae"]),
                rmse=float(metric["rmse"]),
                mape_pct=float(metric["mape_pct"]),
                bias_pct=float(metric["bias_pct"]),
            )
        )

    reference = snapshots[0]
    evaluations: list[dict[str, object]] = []
    for snapshot in snapshots:
        gate = evaluate_quality_gate(snapshot, reference, thresholds)
        evaluations.append({**snapshot.to_dict(), **gate.to_dict()})

    report: dict[str, object] = {
        "available": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "model_version": model_version,
        "reference_window_end": reference.window_end.isoformat(),
        "gate_config": asdict(thresholds),
        "latest": evaluations[-1],
        "evaluations": evaluations,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    history_path = output_dir / "monitoring_history.csv"
    report_path = output_dir / "monitoring_report.json"
    pd.DataFrame(evaluations).to_csv(history_path, index=False)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report, history_path, report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run rolling forecast monitoring and retraining quality gates.")
    parser.add_argument("--stores", type=int, default=None, help="Limit to the first N stores for a faster run.")
    parser.add_argument("--windows", type=int, default=4, help="Number of rolling holdout windows (minimum: 2).")
    parser.add_argument("--horizon", type=int, default=30, help="Days in each holdout window.")
    parser.add_argument("--step-days", type=int, default=30, help="Days between evaluation windows.")
    parser.add_argument("--model-version", default="local-seasonal-trend-v1")
    parser.add_argument("--max-mape", type=float, default=25.0)
    parser.add_argument("--max-abs-bias", type=float, default=20.0)
    parser.add_argument("--max-mae-regression", type=float, default=15.0)
    parser.add_argument("--fail-on-gate", action="store_true", help="Exit non-zero when the latest gate fails.")
    args = parser.parse_args()

    config = QualityGateConfig(
        max_mape_pct=args.max_mape,
        max_abs_bias_pct=args.max_abs_bias,
        max_mae_regression_pct=args.max_mae_regression,
    )
    report, history_path, report_path = run_monitoring(
        model_version=args.model_version,
        windows=args.windows,
        horizon_days=args.horizon,
        step_days=args.step_days,
        num_stores=args.stores,
        config=config,
    )
    latest = report["latest"]
    assert isinstance(latest, dict)
    print(json.dumps(latest, indent=2))
    print(f"\nWrote {history_path}")
    print(f"Wrote {report_path}")
    if args.fail_on_gate and latest["status"] == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
