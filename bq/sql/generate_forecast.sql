-- Materialise 30-day per-product forecasts with 80 % confidence intervals.
-- Truncates and rewrites the destination table on each run.

CREATE OR REPLACE TABLE `{project}.{dataset}.forecasts_30d` AS
SELECT
  CAST(forecast_timestamp AS DATE)              AS forecast_date,
  product_id,
  ROUND(forecast_value, 2)                      AS forecast_units,
  ROUND(prediction_interval_lower_bound, 2)     AS ci_lower,
  ROUND(prediction_interval_upper_bound, 2)     AS ci_upper,
  confidence_level,
  CURRENT_TIMESTAMP()                           AS generated_at
FROM
  ML.FORECAST(
    MODEL `{project}.{dataset}.arima_sales_model`,
    STRUCT({horizon} AS horizon, 0.8 AS confidence_level)
  )
ORDER BY product_id, forecast_date;
