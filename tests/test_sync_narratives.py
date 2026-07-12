from __future__ import annotations

from datetime import date

import pytest

from db.models import Forecast, Narrative
from scripts.sync_narratives import _fetch_product_ids


async def _seed_forecast(db_session, product_id: str) -> None:
    db_session.add(
        Forecast(
            product_id=product_id,
            forecast_date=date(2024, 1, 1),
            forecast_units=100.0,
        )
    )


@pytest.mark.asyncio
async def test_fetch_product_ids_can_skip_existing_narratives(db_session):
    await _seed_forecast(db_session, "STORE_0001")
    await _seed_forecast(db_session, "STORE_0002")
    await _seed_forecast(db_session, "STORE_0003")
    db_session.add(Narrative(product_id="STORE_0001", summary="Already done."))
    await db_session.commit()

    product_ids = await _fetch_product_ids(db_session, limit=2, skip_existing=True)

    assert product_ids == ["STORE_0002", "STORE_0003"]


@pytest.mark.asyncio
async def test_fetch_product_ids_keeps_existing_when_requested(db_session):
    await _seed_forecast(db_session, "STORE_0001")
    await _seed_forecast(db_session, "STORE_0002")
    db_session.add(Narrative(product_id="STORE_0001", summary="Already done."))
    await db_session.commit()

    product_ids = await _fetch_product_ids(db_session, limit=2, skip_existing=False)

    assert product_ids == ["STORE_0001", "STORE_0002"]
