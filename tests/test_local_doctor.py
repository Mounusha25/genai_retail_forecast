from __future__ import annotations

from scripts.local_doctor import CheckResult, has_failures, pg_dsn_from_database_url


def test_pg_dsn_from_database_url_strips_async_driver_and_query():
    dsn = pg_dsn_from_database_url("postgresql+asyncpg://retail:retail@localhost:5432/retail?sslmode=require")

    assert dsn == "postgresql://retail:retail@localhost:5432/retail"


def test_has_failures_only_fails_hard_failures_by_default():
    results = [
        CheckResult("raw_data", "ok", "present"),
        CheckResult("api_health", "warn", "not running", strict_failure=True),
    ]

    assert has_failures(results, strict=False) is False
    assert has_failures(results, strict=True) is True


def test_has_failures_always_fails_explicit_fail():
    results = [CheckResult("raw_data", "fail", "missing", strict_failure=True)]

    assert has_failures(results, strict=False) is True
