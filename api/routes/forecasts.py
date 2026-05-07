from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from api.dependencies import DbSession
from api.schemas import ForecastRow, ForecastsResponse
from db.models import Forecast

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])


@router.get(
    "/{product_id}",
    response_model=ForecastsResponse,
    summary="Get 30-day demand forecast for a product",
)
async def get_forecasts(product_id: str, db: DbSession) -> ForecastsResponse:
    result = await db.execute(
        select(Forecast).where(Forecast.product_id == product_id.upper()).order_by(Forecast.forecast_date)
    )
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No forecasts found for product {product_id!r}. Ensure the pipeline has run at least once.",
        )

    return ForecastsResponse(
        product_id=product_id.upper(),
        count=len(rows),
        forecasts=[ForecastRow.model_validate(r) for r in rows],
    )
