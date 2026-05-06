-- Create or replace the aggregated daily sales view that ARIMA_PLUS trains on.
-- Requirements:
--   - At least 2 years of history per product
--   - One row per (date, product_id); multi-store aggregated
--   - Zero-sale days excluded so the model focuses on active demand

CREATE OR REPLACE VIEW `{project}.{dataset}.v_daily_sales` AS
SELECT
  date,
  product_id,
  SUM(units_sold) AS total_units,
  SUM(revenue)    AS total_revenue
FROM `{project}.{dataset}.sales_clean`
WHERE units_sold > 0
GROUP BY 1, 2
ORDER BY 1, 2;
