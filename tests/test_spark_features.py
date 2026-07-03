"""Unit tests for spark/feature_engineering.py — uses a local[2] Spark session, no cluster required."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

pyspark = pytest.importorskip("pyspark")

from pyspark.sql import SparkSession  # noqa: E402

from spark.feature_engineering import engineer_features  # noqa: E402

EXPECTED_COLUMNS = {
    "date",
    "product_id",
    "store_id",
    "units_sold",
    "revenue",
    "rolling_avg_units_7d",
    "rolling_avg_units_30d",
    "rolling_revenue_7d",
    "rolling_stddev_7d",
    "lag_1d_units",
    "lag_7d_units",
    "lag_14d_units",
    "lag_30d_units",
    "day_of_week",
    "week_of_year",
    "month",
    "is_weekend",
    "store_revenue_rank",
}


@pytest.fixture(scope="module")
def spark() -> Iterator[SparkSession]:
    session = SparkSession.builder.master("local[2]").appName("test_spark_features").getOrCreate()
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


@pytest.fixture
def sample_csv(tmp_path) -> str:
    """10 consecutive days for one store + a same-day competitor, no gaps."""
    path = tmp_path / "sales.csv"
    rows = ["date,product_id,store_id,units_sold,revenue"]
    units = [100, 110, 90, 120, 130, 80, 140, 150, 95, 160]  # day 7 (idx 6) = 140
    for i, u in enumerate(units):
        day = 2 + i  # 2024-01-02 .. 2024-01-11 (Tue..Thu, includes one weekend)
        rows.append(f"2024-01-{day:02d},SKU-1,STORE-A,{u},{u * 10}")
        # a lower-revenue competitor on the same dates, to test store_revenue_rank
        rows.append(f"2024-01-{day:02d},SKU-1,STORE-B,{u // 2},{(u // 2) * 5}")
    path.write_text("\n".join(rows))
    return str(path)


def _run(spark: SparkSession, sample_csv: str, tmp_path):
    output = str(tmp_path / "features_out")
    return engineer_features(spark, sample_csv, output, input_format="csv")


class TestEngineerFeatures:
    def test_produces_expected_columns(self, spark, sample_csv, tmp_path):
        df = _run(spark, sample_csv, tmp_path)
        assert set(df.columns) == EXPECTED_COLUMNS

    def test_drops_cold_start_rows(self, spark, sample_csv, tmp_path):
        df = _run(spark, sample_csv, tmp_path)
        nulls = df.filter(df.lag_1d_units.isNull() | df.lag_7d_units.isNull()).count()
        assert nulls == 0

    def test_lag_1d_matches_previous_day(self, spark, sample_csv, tmp_path):
        df = _run(spark, sample_csv, tmp_path)
        row = df.filter((df.store_id == "STORE-A") & (df.date == "2024-01-11")).collect()[0]
        assert row["units_sold"] == 160
        assert row["lag_1d_units"] == 95  # 2024-01-10
        assert row["lag_7d_units"] == 90  # 2024-01-04

    def test_rolling_avg_7d_is_a_narrow_window(self, spark, sample_csv, tmp_path):
        # Regression guard: a prior bug computed rangeBetween in seconds against a
        # DateType orderBy column (whose native units are days), silently stretching
        # the "7-day" window to span decades. With 10 consecutive daily rows all
        # falling in the same 7-day window would equal a 30-day average.
        df = _run(spark, sample_csv, tmp_path)
        row = df.filter((df.store_id == "STORE-A") & (df.date == "2024-01-11")).collect()[0]
        assert row["rolling_avg_units_7d"] != row["rolling_avg_units_30d"]
        # window covers 2024-01-05..01-11 units: 120, 130, 80, 140, 150, 95, 160
        assert row["rolling_avg_units_7d"] == pytest.approx(125.0, abs=0.5)

    def test_is_weekend_flag(self, spark, sample_csv, tmp_path):
        df = _run(spark, sample_csv, tmp_path)
        # 2024-01-06 and 2024-01-07 are a Saturday/Sunday
        weekend_rows = df.filter(df.date.isin("2024-01-06", "2024-01-07")).collect()
        assert all(r["is_weekend"] == 1 for r in weekend_rows)
        weekday_row = df.filter(df.date == "2024-01-09").collect()[0]
        assert weekday_row["is_weekend"] == 0

    def test_store_revenue_rank_orders_by_revenue_desc(self, spark, sample_csv, tmp_path):
        df = _run(spark, sample_csv, tmp_path)
        rows = {r["store_id"]: r["store_revenue_rank"] for r in df.filter(df.date == "2024-01-11").collect()}
        assert rows["STORE-A"] < rows["STORE-B"]  # STORE-A has higher revenue → rank 1

    def test_sample_fraction_reduces_row_count(self, spark, sample_csv, tmp_path):
        full = _run(spark, sample_csv, tmp_path)
        sampled = engineer_features(
            spark, sample_csv, str(tmp_path / "features_sampled"), input_format="csv", sample_fraction=0.5
        )
        assert sampled.count() <= full.count()
