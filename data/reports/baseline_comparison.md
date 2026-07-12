# Local Baseline Forecast Comparison

Backtest on the final holdout window from the Rossmann training data.

- Stores evaluated: 1,115
- Forecast rows evaluated: 33,450
- Holdout window: 2015-07-02 to 2015-07-31
- Best model by MAE: `local_seasonal_trend`

| Model | MAE | RMSE | MAPE % | Bias % |
|---|---:|---:|---:|---:|
| `local_seasonal_trend` | 1,898.84 | 3,033.18 | 16.92 | 17.06 |
| `seasonal_naive_7d` | 1,936.19 | 3,008.47 | 21.91 | 16.46 |
| `moving_average_28d` | 2,175.10 | 3,100.44 | 23.03 | 2.70 |
| `moving_average_7d` | 2,251.98 | 3,291.47 | 24.74 | 13.28 |

Notes:
- `local_seasonal_trend` mirrors the no-GCP local forecast approach: recent day-of-week demand plus a bounded short-term trend adjustment.
- `seasonal_naive_7d` repeats the value from the same weekday one week earlier.
- Moving-average baselines use the last open-store observations before the holdout window.
- MAPE ignores zero-actual rows because percentage error is undefined for closed-store days.
