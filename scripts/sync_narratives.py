"""
scripts/sync_narratives.py
---------------------------
Generate AI narratives for stores using LangChain + Groq and persist them
to the PostgreSQL `narratives` table.

Reads forecast rows from PostgreSQL (not BigQuery) so there is no extra
GCP cost.  Set GROQ_API_KEY in .env before running.

Usage
-----
# Generate narratives for up to 20 stores (default)
.venv/bin/python scripts/sync_narratives.py

# Single store
.venv/bin/python scripts/sync_narratives.py --product STORE_0001

# Custom batch size & worker concurrency
.venv/bin/python scripts/sync_narratives.py --limit 50 --workers 2
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # type: ignore[import]

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import get_settings
from db.models import Forecast, Narrative
from rag.narrative_chain import NarrativeChain

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sync_narratives")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _row_to_dict(row: Forecast) -> dict:
    return {
        "forecast_date": str(row.forecast_date),
        "forecast_units": row.forecast_units,
        "ci_lower": row.ci_lower,
        "ci_upper": row.ci_upper,
    }


async def _fetch_product_ids(session: AsyncSession, limit: int) -> list[str]:
    """Return up to *limit* distinct product_ids that have forecast rows."""
    result = await session.execute(text(f"SELECT DISTINCT product_id FROM forecasts ORDER BY product_id LIMIT {limit}"))
    return [row[0] for row in result.fetchall()]


async def _fetch_forecasts_for(session: AsyncSession, product_id: str) -> list[Forecast]:
    result = await session.execute(
        select(Forecast).where(Forecast.product_id == product_id).order_by(Forecast.forecast_date)
    )
    return list(result.scalars().all())


async def _save_narrative(session: AsyncSession, product_id: str, summary: str) -> None:
    """Replace existing narrative (if any) and insert the fresh one."""
    await session.execute(delete(Narrative).where(Narrative.product_id == product_id))
    session.add(
        Narrative(
            product_id=product_id,
            summary=summary,
            generated_at=datetime.now(UTC),
        )
    )
    await session.commit()


# ── Core worker (sync — runs in thread pool) ──────────────────────────────────


def _generate_one(
    chain: NarrativeChain,
    product_id: str,
    forecast_rows: list[dict],
) -> tuple[str, str | Exception]:
    """
    Generate a narrative for *product_id*.
    Returns ``(product_id, narrative_text)`` on success,
    or ``(product_id, exception)`` on failure.
    """
    try:
        narrative = chain.generate(product_id, forecast_rows)
        return product_id, narrative
    except Exception as exc:  # noqa: BLE001
        return product_id, exc


# ── Main ──────────────────────────────────────────────────────────────────────


async def sync(
    product_id: str | None,
    limit: int,
    workers: int,
    delay: float,
) -> None:
    cfg = get_settings()
    engine = create_async_engine(cfg.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # ── 1. Determine which stores to process ──────────────────
    async with async_session() as session:
        if product_id:
            product_ids = [product_id.upper()]
            logger.info("Single-store mode: %s", product_ids[0])
        else:
            product_ids = await _fetch_product_ids(session, limit)
            logger.info("Found %d product_ids to process (limit=%d)", len(product_ids), limit)

    if not product_ids:
        logger.warning("No products with forecasts found — run sync_forecasts.py first.")
        await engine.dispose()
        return

    # ── 2. Load forecast rows for every product ────────────────
    async with async_session() as session:
        pid_to_rows: dict[str, list[dict]] = {}
        for pid in product_ids:
            rows = await _fetch_forecasts_for(session, pid)
            if rows:
                pid_to_rows[pid] = [_row_to_dict(r) for r in rows]
            else:
                logger.warning("No forecast rows for %s — skipping", pid)

    if not pid_to_rows:
        logger.error("No forecast data available. Exiting.")
        await engine.dispose()
        return

    # ── 3. Generate narratives (thread pool for Groq calls) ────
    chain = NarrativeChain()
    results: list[tuple[str, str | Exception]] = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for i, (pid, rows) in enumerate(pid_to_rows.items()):
            if i > 0 and delay > 0:
                time.sleep(delay)  # rate-limit Groq free tier
            fut = pool.submit(_generate_one, chain, pid, rows)
            futures[fut] = pid

        total = len(futures)
        for done, fut in enumerate(as_completed(futures), start=1):
            pid, result = fut.result()
            if isinstance(result, Exception):
                logger.error("[%d/%d] FAILED %s: %s", done, total, pid, result)
            else:
                logger.info("[%d/%d] OK %s (%d chars)", done, total, pid, len(result))
            results.append((pid, result))

    # ── 4. Persist to PostgreSQL ───────────────────────────────
    saved = 0
    async with async_session() as session:
        for pid, narrative in results:
            if isinstance(narrative, str):
                await _save_narrative(session, pid, narrative)
                saved += 1

    await engine.dispose()
    logger.info("Saved %d/%d narratives to PostgreSQL.", saved, len(results))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and save AI narratives to PostgreSQL.")
    parser.add_argument(
        "--product",
        metavar="STORE_ID",
        default=None,
        help="Process a single store (e.g. STORE_0001). Omit to process all.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max number of stores to process (default: 20).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Number of parallel Groq workers (default: 2, max recommended: 3).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to wait between launching Groq requests (default: 1.0).",
    )
    args = parser.parse_args()
    asyncio.run(sync(args.product, args.limit, args.workers, args.delay))


if __name__ == "__main__":
    main()
