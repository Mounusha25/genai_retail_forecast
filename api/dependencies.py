from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from db.session import get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def verify_scheduler_secret(
    x_scheduler_secret: Annotated[str | None, Header()] = None,
) -> None:
    """
    FastAPI dependency for the /run-pipeline endpoint.
    Validates the shared secret sent by Cloud Scheduler.
    Uses ``secrets.compare_digest`` to prevent timing attacks.
    """
    secret = get_settings().scheduler_secret
    if not secrets.compare_digest(x_scheduler_secret or "", secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing scheduler secret.",
        )
