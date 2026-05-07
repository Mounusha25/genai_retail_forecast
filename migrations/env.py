"""Alembic environment for async SQLAlchemy."""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# ── Load application models so Alembic can detect them ────────
from db.models import Base  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Substitute DATABASE_URL from the environment
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):  # type: ignore[no-untyped-def]
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def _clean_url_and_ssl(url: str) -> tuple[str, dict[str, object]]:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    ssl_keys = {"ssl", "sslmode", "channel_binding"}
    needs_ssl = bool(params.keys() & ssl_keys) or parsed.hostname not in ("localhost", "127.0.0.1", None)
    clean_params = {k: v for k, v in params.items() if k not in ssl_keys}
    clean_url = urlunparse(parsed._replace(query=urlencode(clean_params, doseq=True)))
    return clean_url, ({"ssl": True} if needs_ssl else {})


async def run_async_migrations() -> None:
    raw_url = config.get_main_option("sqlalchemy.url")
    assert raw_url is not None
    url, connect_args = _clean_url_and_ssl(raw_url)
    engine = create_async_engine(url, connect_args=connect_args)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
