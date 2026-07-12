from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from scripts.baseline_compare import compare_baselines, write_report
from scripts.seed_forecasts_local import build_forecasts


def _write_train_csv(tmp_path, days: int = 90) -> None:
    rows = []
    start = date(2024, 1, 1)
    for store in (1, 2):
        for offset in range(days):
            current = start + timedelta(days=offset)
            is_open = int(current.weekday() != 6)
            base = 100 * store
            rows.append(
                {
                    "Store": store,
                    "Date": current.isoformat(),
                    "Sales": 0 if not is_open else base + current.weekday() * 10 + offset,
                    "Open": is_open,
                }
            )
    pd.DataFrame(rows).to_csv(tmp_path / "train.csv", index=False)


def test_build_forecasts_from_fixture_data(tmp_path):
    _write_train_csv(tmp_path)

    forecasts = build_forecasts(num_stores=1, horizon_days=7, data_dir=tmp_path)

    assert len(forecasts) == 7
    assert forecasts["product_id"].nunique() == 1
    assert forecasts["product_id"].iloc[0] == "STORE_0001"
    assert forecasts["forecast_units"].ge(0).all()
    assert forecasts["ci_lower"].le(forecasts["forecast_units"]).all()
    assert forecasts["ci_upper"].ge(forecasts["forecast_units"]).all()


def test_build_forecasts_respects_store_limit(tmp_path):
    _write_train_csv(tmp_path)

    forecasts = build_forecasts(num_stores=2, horizon_days=3, data_dir=tmp_path)

    assert len(forecasts) == 6
    assert set(forecasts["product_id"]) == {"STORE_0001", "STORE_0002"}


def test_baseline_comparison_writes_report(tmp_path):
    _write_train_csv(tmp_path, days=100)

    metrics, predictions = compare_baselines(data_dir=tmp_path, horizon_days=14, num_stores=2)
    report_path, csv_path = write_report(metrics, predictions, report_dir=tmp_path / "reports")

    assert set(metrics["model"]) == {
        "local_seasonal_trend",
        "seasonal_naive_7d",
        "moving_average_7d",
        "moving_average_28d",
    }
    assert len(predictions) == 28
    assert report_path.exists()
    assert csv_path.exists()
    assert "Best model by MAE" in report_path.read_text()
