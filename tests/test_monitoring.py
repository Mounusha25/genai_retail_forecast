from __future__ import annotations

import json
from datetime import date, timedelta

import pandas as pd

from monitoring import EvaluationSnapshot, QualityGateConfig, evaluate_quality_gate
from scripts.monitor_forecasts import run_monitoring


def _snapshot(*, mae: float, mape: float = 10.0, bias: float = 1.0) -> EvaluationSnapshot:
    return EvaluationSnapshot(
        model="model",
        model_version="v1",
        window_start=date(2024, 1, 1),
        window_end=date(2024, 1, 30),
        sample_count=30,
        store_count=1,
        mae=mae,
        rmse=mae * 1.2,
        mape_pct=mape,
        bias_pct=bias,
    )


def _write_train_csv(path, days: int = 150) -> None:
    rows: list[dict[str, object]] = []
    start = date(2024, 1, 1)
    for store in (1, 2):
        for offset in range(days):
            current = start + timedelta(days=offset)
            is_open = int(current.weekday() != 6)
            rows.append(
                {
                    "Store": store,
                    "Date": current.isoformat(),
                    "Sales": 0 if not is_open else 100 * store + current.weekday() * 5 + offset,
                    "Open": is_open,
                }
            )
    pd.DataFrame(rows).to_csv(path / "train.csv", index=False)


def test_quality_gate_recommends_retraining_on_regression() -> None:
    result = evaluate_quality_gate(
        _snapshot(mae=125),
        _snapshot(mae=100),
        QualityGateConfig(max_mape_pct=25, max_abs_bias_pct=20, max_mae_regression_pct=15),
    )

    assert result.status == "fail"
    assert result.retrain_recommended is True
    assert "MAE regression" in result.violations[0]


def test_quality_gate_passes_within_thresholds() -> None:
    result = evaluate_quality_gate(_snapshot(mae=105), _snapshot(mae=100))

    assert result.status == "pass"
    assert result.retrain_recommended is False
    assert result.violations == ()


def test_monitoring_writes_versioned_history(tmp_path) -> None:
    _write_train_csv(tmp_path)

    report, history_path, report_path = run_monitoring(
        data_dir=tmp_path,
        output_dir=tmp_path / "reports",
        model_version="test-v2",
        windows=3,
        horizon_days=14,
        step_days=14,
        num_stores=2,
    )

    saved = json.loads(report_path.read_text())
    assert history_path.exists()
    assert report["model_version"] == "test-v2"
    assert len(saved["evaluations"]) == 3
    assert saved["latest"]["sample_count"] == 28
    assert saved["latest"]["status"] in {"pass", "fail"}
