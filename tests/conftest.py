"""Shared pytest fixtures."""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.main import create_app
from db.models import Base
from db.session import get_db

# ── In-memory SQLite database ──────────────────────────────────


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncSession:
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        yield session
        await session.rollback()


# ── Test FastAPI client ────────────────────────────────────────


@pytest_asyncio.fixture
async def client(engine) -> AsyncClient:
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    async def _override_db():
        async with factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = _override_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
