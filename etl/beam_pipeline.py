from __future__ import annotations

import csv
import io
import logging
from collections.abc import Iterator
from datetime import date

import apache_beam as beam
from apache_beam.io.gcp.bigquery import BigQueryDisposition, WriteToBigQuery
from apache_beam.metrics import Metrics
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions

from config import get_settings
from etl.schema import BQ_SCHEMA, EXPECTED_COLUMNS, SalesRow

logger = logging.getLogger(__name__)


class ParseSalesRow(beam.DoFn):
    """
    Parse a raw CSV line into a :class:`SalesRow`.

    Metrics tracked per bundle:
      - ``sales/parsed``  — successfully parsed rows
      - ``sales/skipped`` — rows dropped due to validation errors
    """

    def __init__(self) -> None:
        self._parsed = Metrics.counter("sales", "parsed")
        self._skipped = Metrics.counter("sales", "skipped")

    def process(self, line: str) -> Iterator[dict]:  # type: ignore[override]
        line = line.strip()
        if not line:
            return

        try:
            reader = csv.DictReader(io.StringIO(line), fieldnames=EXPECTED_COLUMNS)
            raw = next(reader)

            # Validate required fields
            for field in ("date", "product_id", "store_id"):
                if not (raw.get(field) or "").strip():
                    raise ValueError(f"Empty required field: {field!r}")

            # Validate date format
            parsed_date = date.fromisoformat(raw["date"].strip())

            row = SalesRow(
                date=parsed_date.isoformat(),
                product_id=raw["product_id"].strip().upper(),
                store_id=raw["store_id"].strip(),
                units_sold=max(0.0, float(raw.get("units_sold") or 0)),
                revenue=max(0.0, float(raw.get("revenue") or 0)),
            )

            self._parsed.inc()
            yield row.to_bq_dict()

        except (ValueError, KeyError, StopIteration) as exc:
            self._skipped.inc()
            logging.warning("Skipping malformed row [%.120s]: %s", line, exc)


class FilterHeaderLines(beam.DoFn):
    """Drop the CSV header row (first line of each shard)."""

    def process(self, line: str) -> Iterator[str]:  # type: ignore[override]
        if line.strip().lower().startswith("date"):
            return
        yield line


def build_pipeline_options(
    *,
    runner: str,
    project: str,
    region: str,
    temp_location: str,
    staging_location: str,
    job_name: str = "retail-sales-etl",
    num_workers: int = 4,
    machine_type: str = "n1-standard-4",
) -> PipelineOptions:
    opts = PipelineOptions(
        runner=runner,
        project=project,
        region=region,
        temp_location=temp_location,
        staging_location=staging_location,
        job_name=job_name,
        num_workers=num_workers,
        max_num_workers=num_workers * 4,
        machine_type=machine_type,
        autoscaling_algorithm="THROUGHPUT_BASED",
        disk_size_gb=50,
        use_public_ips=False,
        save_main_session=True,
    )
    opts.view_as(SetupOptions).save_main_session = True
    return opts


def run(
    *,
    runner: str = "DirectRunner",
    input_pattern: str | None = None,
    destination_table: str | None = None,
) -> None:
    """
    Entry point for the Beam ETL pipeline.

    Args:
        runner: ``"DirectRunner"`` for local testing, ``"DataflowRunner"`` for production.
        input_pattern: GCS glob, e.g. ``gs://bucket/sales/*.csv``.
                       Falls back to settings value.
        destination_table: BigQuery table reference.
                           Falls back to settings value.
    """
    cfg = get_settings()

    src = input_pattern or cfg.gcs_raw_path
    table = destination_table or cfg.bq_sales_table

    pipeline_opts = build_pipeline_options(
        runner=runner,
        project=cfg.google_cloud_project,
        region=cfg.dataflow_region,
        temp_location=cfg.gcs_temp,
        staging_location=cfg.gcs_staging,
    )

    logger.info("Starting Beam ETL | runner=%s src=%s dst=%s", runner, src, table)

    with beam.Pipeline(options=pipeline_opts) as pipeline:
        (
            pipeline
            | "ReadRawCSV" >> beam.io.ReadFromText(src, skip_header_lines=1)
            | "FilterHeaders" >> beam.ParDo(FilterHeaderLines())
            | "ParseRows" >> beam.ParDo(ParseSalesRow())
            | "WriteToBQ"
            >> WriteToBigQuery(
                table=table,
                schema=BQ_SCHEMA,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=BigQueryDisposition.WRITE_TRUNCATE,
                batch_size=5_000,
            )
        )

    logger.info("Beam ETL pipeline completed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Retail sales ETL pipeline")
    parser.add_argument("--runner", default="DirectRunner")
    parser.add_argument("--input", default=None)
    parser.add_argument("--table", default=None)
    args = parser.parse_args()

    run(runner=args.runner, input_pattern=args.input, destination_table=args.table)
