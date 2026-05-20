"""
PySpark feature engineering for retail demand forecasting.

This module reads raw sales data from GCS and engineers time-series features:
- Rolling window aggregations (7-day, 30-day)
- Lag features (1d, 7d, 14d, 30d)
- Calendar signals (day_of_week, week_of_year, month, is_weekend)
- Store-level competitive context (revenue rank)

Output is written back to GCS as parquet for BigQuery ML ingestion.
"""

import argparse
import sys
from typing import Optional

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def build_spark_session(app_name: str = "RetailFeatureEngineering") -> SparkSession:
    """
    Build and configure a SparkSession with adaptive query execution enabled.

    Args:
        app_name: Name for the Spark application.

    Returns:
        Configured SparkSession instance.
    """
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .getOrCreate()
    )


def engineer_features(
    spark: SparkSession,
    input_path: str,
    output_path: str,
    sample_fraction: Optional[float] = None,
) -> None:
    """
    Read raw sales data, engineer time-series features, and write enriched output.

    Features engineered:
    - rolling_avg_units_7d: 7-day rolling average of units sold
    - rolling_avg_units_30d: 30-day rolling average of units sold
    - rolling_revenue_7d: 7-day rolling sum of revenue
    - rolling_stddev_7d: 7-day rolling standard deviation (demand volatility)
    - lag_1d_units, lag_7d_units, lag_14d_units, lag_30d_units: Historical lags
    - day_of_week, week_of_year, month: Calendar features
    - is_weekend: Binary flag for weekend
    - store_revenue_rank: Daily store rank by revenue (competitive context)

    Args:
        spark: Active SparkSession.
        input_path: GCS path to raw sales parquet/CSV.
        output_path: GCS path for engineered features output.
        sample_fraction: Optional sample fraction for testing (0.0 to 1.0).

    Raises:
        FileNotFoundError: If input path does not exist.
    """
    # Read raw data
    df = spark.read.parquet(input_path)

    # Optional sampling for testing
    if sample_fraction is not None:
        df = df.sample(fraction=sample_fraction, seed=42)
        spark.logger.info(f"Sampled DataFrame to {sample_fraction*100:.1f}%")

    spark.logger.info(f"Input records: {df.count():,}")

    # ────────────────────────────────────────────────────────────────
    # 1. Rolling window aggregations
    # ────────────────────────────────────────────────────────────────
    window_7d = (
        Window.partitionBy("product_id", "store_id")
        .orderBy("date")
        .rangeBetween(-6 * 86400, 0)  # 6 days in seconds
    )
    window_30d = (
        Window.partitionBy("product_id", "store_id")
        .orderBy("date")
        .rangeBetween(-29 * 86400, 0)  # 29 days in seconds
    )

    df = df.withColumn("rolling_avg_units_7d", F.avg("units_sold").over(window_7d))
    df = df.withColumn("rolling_avg_units_30d", F.avg("units_sold").over(window_30d))
    df = df.withColumn("rolling_revenue_7d", F.sum("revenue").over(window_7d))
    df = df.withColumn("rolling_stddev_7d", F.stddev("units_sold").over(window_7d))

    spark.logger.info("✓ Rolling window aggregations computed")

    # ────────────────────────────────────────────────────────────────
    # 2. Lag features for time-series modeling
    # ────────────────────────────────────────────────────────────────
    lag_window = Window.partitionBy("product_id", "store_id").orderBy("date")
    for lag_days in [1, 7, 14, 30]:
        col_name = f"lag_{lag_days}d_units"
        df = df.withColumn(col_name, F.lag("units_sold", lag_days).over(lag_window))

    spark.logger.info("✓ Lag features computed")

    # ────────────────────────────────────────────────────────────────
    # 3. Calendar features
    # ────────────────────────────────────────────────────────────────
    df = (
        df.withColumn("day_of_week", F.dayofweek("date"))
        .withColumn("week_of_year", F.weekofyear("date"))
        .withColumn("month", F.month("date"))
        .withColumn("is_weekend", (F.dayofweek("date").isin(1, 7)).cast("int"))
    )

    spark.logger.info("✓ Calendar features computed")

    # ────────────────────────────────────────────────────────────────
    # 4. Store-level revenue rank (competitive context)
    # ────────────────────────────────────────────────────────────────
    store_window = Window.partitionBy("date").orderBy(F.desc("revenue"))
    df = df.withColumn("store_revenue_rank", F.rank().over(store_window))

    spark.logger.info("✓ Store revenue rank computed")

    # ────────────────────────────────────────────────────────────────
    # 5. Drop rows with null lags (cold-start period) and write output
    # ────────────────────────────────────────────────────────────────
    df_clean = df.dropna(subset=["lag_1d_units", "lag_7d_units"])

    spark.logger.info(f"Records after lag nulls removal: {df_clean.count():,}")
    spark.logger.info(f"Partitions: {df_clean.rdd.getNumPartitions()}")

    # Write output
    df_clean.write.mode("overwrite").parquet(output_path)

    spark.logger.info(f"✓ Feature engineering complete")
    spark.logger.info(f"✓ Output written to: {output_path}")


def main() -> None:
    """Entry point for PySpark feature engineering job."""
    parser = argparse.ArgumentParser(
        description="Engineer time-series features for retail forecasting"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="GCS or local path to raw sales parquet (e.g., gs://bucket/sales/raw/*.parquet)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="GCS or local path for engineered features output (e.g., gs://bucket/sales/features/)",
    )
    parser.add_argument(
        "--sample",
        type=float,
        default=None,
        help="Optional sample fraction for testing (0.0 to 1.0)",
    )

    args = parser.parse_args()

    try:
        spark = build_spark_session()
        engineer_features(spark, args.input, args.output, args.sample)
        spark.stop()
        sys.exit(0)
    except Exception as e:
        spark.logger.error(f"Feature engineering failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
