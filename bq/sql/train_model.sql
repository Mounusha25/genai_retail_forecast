-- Train (or retrain) the ARIMA_PLUS model.
-- One sub-model is fitted per product_id automatically by BQML.
-- Placeholder tokens {project}, {dataset} are replaced at runtime by bq/client.py.

CREATE OR REPLACE MODEL `{project}.{dataset}.arima_sales_model`
OPTIONS(
  model_type                = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col      = 'total_units',
  time_series_id_col        = 'product_id',
  horizon                   = {horizon},
  auto_arima                = TRUE,
  data_frequency            = 'AUTO_FREQUENCY',
  decompose_time_series     = TRUE,
  clean_spikes_and_dips     = TRUE,
  adjust_step_changes       = TRUE,
  holiday_region            = 'US'
) AS
SELECT date, product_id, total_units
FROM `{project}.{dataset}.v_daily_sales`;
