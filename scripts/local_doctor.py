"""
Local readiness checks for the no-GCP RetailForecastAI demo path.

Usage:
    .venv/bin/python scripts/local_doctor.py
    .venv/bin/python scripts/local_doctor.py --strict
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pandas as pd
import psycopg2
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
REPORT_PATH = ROOT / "data" / "reports" / "baseline_metrics.csv"
FAISS_DIR = ROOT / "data" / "faiss_index"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str
    strict_failure: bool = False


def _status(ok: bool, strict_failure: bool = False) -> str:
    if ok:
        return "ok"
    return "fail" if strict_failure else "warn"


def pg_dsn_from_database_url(database_url: str) -> str:
    parsed = urlparse(database_url.replace("postgresql+asyncpg://", "postgresql://"))
    return urlunparse(parsed._replace(query=""))


def check_raw_data() -> CheckResult:
    expected = ["train.csv", "test.csv", "store.csv"]
    missing = [name for name in expected if not (RAW_DIR / name).exists()]
    if missing:
        return CheckResult("raw_data", "fail", f"Missing {', '.join(missing)}", strict_failure=True)

    train_size = (RAW_DIR / "train.csv").stat().st_size / (1024 * 1024)
    return CheckResult("raw_data", "ok", f"Rossmann CSVs present; train.csv is {train_size:.1f} MB")


def check_baseline_report() -> CheckResult:
    if not REPORT_PATH.exists():
        return CheckResult("baseline_report", "fail", "Missing data/reports/baseline_metrics.csv", strict_failure=True)

    metrics = pd.read_csv(REPORT_PATH)
    required = {"model", "mae", "rmse", "mape_pct", "bias_pct"}
    missing = required - set(metrics.columns)
    if missing:
        return CheckResult("baseline_report", "fail", f"Missing columns: {', '.join(sorted(missing))}", True)

    best = metrics.sort_values("mae").iloc[0]
    return CheckResult("baseline_report", "ok", f"Best model {best['model']} with MAE {best['mae']:,.0f}")


def check_faiss_index() -> CheckResult:
    faiss_file = FAISS_DIR / "index.faiss"
    pkl_file = FAISS_DIR / "index.pkl"
    ok = faiss_file.exists() and pkl_file.exists()
    detail = "FAISS index files present" if ok else "Missing FAISS index; run make build-index"
    return CheckResult("faiss_index", _status(ok), detail, strict_failure=False)


def check_database(database_url: str) -> list[CheckResult]:
    try:
        with (
            psycopg2.connect(pg_dsn_from_database_url(database_url), connect_timeout=3) as conn,
            conn.cursor() as cur,
        ):
            cur.execute("SELECT COUNT(*), COUNT(DISTINCT product_id) FROM forecasts")
            forecast_rows, stores = cur.fetchone()
            cur.execute("SELECT COUNT(*), COUNT(DISTINCT product_id) FROM narratives")
            narrative_rows, narrative_stores = cur.fetchone()
    except Exception as exc:
        return [
            CheckResult(
                "database",
                "warn",
                f"PostgreSQL unavailable or not migrated: {exc}",
                strict_failure=True,
            )
        ]

    forecast_ok = forecast_rows > 0 and stores > 0
    return [
        CheckResult(
            "forecast_rows",
            _status(forecast_ok),
            f"{forecast_rows:,} rows across {stores:,} stores",
            strict_failure=not forecast_ok,
        ),
        CheckResult(
            "narratives",
            "ok" if narrative_rows else "warn",
            f"{narrative_rows:,} rows across {narrative_stores:,} stores",
            strict_failure=False,
        ),
    ]


def check_api(api_base: str) -> CheckResult:
    try:
        response = requests.get(f"{api_base.rstrip('/')}/health", timeout=3)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        return CheckResult("api_health", "warn", f"API unavailable: {exc}", strict_failure=True)

    ok = data.get("status") == "ok" and data.get("db") == "ok"
    return CheckResult(
        "api_health",
        _status(ok),
        f"status={data.get('status')} db={data.get('db')} version={data.get('version')}",
        strict_failure=not ok,
    )


def run_checks(database_url: str, api_base: str) -> list[CheckResult]:
    results = [
        check_raw_data(),
        check_baseline_report(),
        check_faiss_index(),
    ]
    results.extend(check_database(database_url))
    results.append(check_api(api_base))
    return results


def print_report(results: list[CheckResult]) -> None:
    width = max(len(result.name) for result in results)
    print("RetailForecastAI local doctor")
    print("-" * 34)
    for result in results:
        print(f"{result.status.upper():<5} {result.name:<{width}}  {result.detail}")


def has_failures(results: list[CheckResult], strict: bool) -> bool:
    if strict:
        return any(result.status != "ok" and result.strict_failure for result in results)
    return any(result.status == "fail" for result in results)


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    parser = argparse.ArgumentParser(description="Check local no-GCP demo readiness.")
    parser.add_argument("--strict", action="store_true", help="Treat API/DB warnings as failures.")
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://retail:retail@localhost:5432/retail")
    api_base = os.getenv("API_BASE_URL", "http://localhost:8080")

    results = run_checks(database_url, api_base)
    print_report(results)
    raise SystemExit(1 if has_failures(results, strict=args.strict) else 0)


if __name__ == "__main__":
    main()
