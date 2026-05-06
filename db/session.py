from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        cfg = get_settings()
        _engine = create_async_engine(
            cfg.database_url,
            pool_size=cfg.db_pool_size,
            max_overflow=cfg.db_max_overflow,
            pool_timeout=cfg.db_pool_timeout,
            pool_pre_ping=True,          # validate connections before use
            echo=not cfg.is_production,  # SQL logging in dev only
        )
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an :class:`AsyncSession`."""
    async with _get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables() -> None:
    """Create all tables defined in ``db.models``.  Called on app startup."""
    from db.models import Base

    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    """Release connection pool.  Called on app shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
