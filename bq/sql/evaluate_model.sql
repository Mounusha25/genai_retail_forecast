-- Return per-product ARIMA_PLUS model parameters and fit statistics.
-- ARIMA_PLUS evaluation returns model order, AIC, log-likelihood, and variance.

SELECT
  product_id,
  non_seasonal_p,
  non_seasonal_d,
  non_seasonal_q,
  has_drift,
  ROUND(log_likelihood, 4) AS log_likelihood,
  ROUND(AIC, 4)            AS aic,
  ROUND(variance, 6)       AS variance,
  seasonal_periods,
  has_holiday_effect,
  has_spikes_and_dips,
  has_step_changes
FROM
  ML.ARIMA_EVALUATE(MODEL `{project}.{dataset}.arima_sales_model`)
ORDER BY aic ASC;
