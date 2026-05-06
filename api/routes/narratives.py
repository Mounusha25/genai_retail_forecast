from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from api.dependencies import DbSession
from api.schemas import NarrativeResponse
from db.models import Narrative

router = APIRouter(prefix="/narrative", tags=["Narratives"])


@router.get(
    "/{product_id}",
    response_model=NarrativeResponse,
    summary="Get the latest GPT-4 executive summary for a product",
)
async def get_narrative(product_id: str, db: DbSession) -> NarrativeResponse:
    result = await db.execute(
        select(Narrative)
        .where(Narrative.product_id == product_id.upper())
        .order_by(Narrative.generated_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No narrative found for product {product_id!r}.",
        )

    return NarrativeResponse.model_validate(row)
