from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select

from api.dependencies import DbSession, verify_scheduler_secret
from api.schemas import PipelineRunResponse, PipelineTriggerResponse
from db.models import PipelineRun

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@router.post(
    "/run",
    response_model=PipelineTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger the full forecasting pipeline (Cloud Scheduler endpoint)",
    dependencies=[Depends(verify_scheduler_secret)],
)
async def trigger_pipeline(
    background_tasks: BackgroundTasks,
    triggered_by: str = "scheduler",
    db: DbSession = None,  # type: ignore[assignment]
) -> PipelineTriggerResponse:
    # Create an audit run record in the "running" state
    run = PipelineRun(
        status="running",
        triggered_by=triggered_by,
        started_at=datetime.now(UTC),
    )
    db.add(run)
    await db.flush()  # get the auto-generated id
    run_id = run.id

    background_tasks.add_task(_execute_pipeline, run_id)

    return PipelineTriggerResponse(run_id=run_id, status="queued")


@router.get(
    "/runs/{run_id}",
    response_model=PipelineRunResponse,
    summary="Poll the status of a pipeline run",
)
async def get_run_status(run_id: int, db: DbSession) -> PipelineRunResponse:
    result = await db.execute(select(PipelineRun).where(PipelineRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found.")
    return PipelineRunResponse.model_validate(run)


async def _execute_pipeline(run_id: int) -> None:
    """
    Background task that runs the full pipeline and updates the audit record.
    Imported inline to avoid circular imports.
    """
    from db.session import _get_session_factory  # noqa: PLC0415
    from pipeline.orchestrator import Orchestrator  # noqa: PLC0415

    session_factory = _get_session_factory()

    async with session_factory() as db:
        try:
            await Orchestrator().run()
            run = await db.get(PipelineRun, run_id)
            if run:
                run.status = "success"
                run.finished_at = datetime.now(UTC)
            await db.commit()
            logger.info("Pipeline run %d completed successfully", run_id)

        except Exception as exc:
            logger.exception("Pipeline run %d failed", run_id)
            run = await db.get(PipelineRun, run_id)
            if run:
                run.status = "failed"
                run.finished_at = datetime.now(UTC)
                run.error = str(exc)[:2000]
            await db.commit()
