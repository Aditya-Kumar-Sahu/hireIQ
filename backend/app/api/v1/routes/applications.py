"""Application management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Query, Request
from fastapi.responses import StreamingResponse

from app.agents.orchestrator import ApplicationOrchestrator, run_application_pipeline
from app.api.dependencies import CurrentUser, DBSession, Pagination
from app.core.rate_limit import enforce_rate_limit
from app.models.agent_run import AgentName
from app.models.application import ApplicationStatus
from app.schemas.application import (
    AgentRunResponse,
    ApplicationCreate,
    ApplicationDetailResponse,
    OfferRequest,
    ApplicationResponse,
    ScheduleRequest,
    ApplicationStatusUpdate,
)
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.job import SimilarJobResult
from app.services.progress import ApplicationProgressService
from app.services.jobs import JobService
from app.services.applications import ApplicationService

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=APIResponse[ApplicationResponse], status_code=201)
async def create_application(
    request: Request,
    payload: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ApplicationResponse]:
    enforce_rate_limit(request, "60/minute", "applications:create")
    data = await ApplicationService(db, current_user).create_application(payload)
    await db.commit()
    progress = ApplicationProgressService()
    await progress.reset(data.id)
    await progress.publish(
        data.id,
        "queued",
        {"application_id": str(data.id), "status": data.status.value},
    )
    background_tasks.add_task(run_application_pipeline, data.id)
    return APIResponse(data=data)


@router.get("", response_model=APIResponse[PaginatedResponse[ApplicationResponse]])
async def list_applications(
    db: DBSession,
    current_user: CurrentUser,
    pagination: Pagination,
    job_id: UUID | None = Query(default=None),
    status: ApplicationStatus | None = Query(default=None),
) -> APIResponse[PaginatedResponse[ApplicationResponse]]:
    data = await ApplicationService(db, current_user).list_applications(pagination, job_id, status)
    return APIResponse(data=data)


@router.get("/{application_id}", response_model=APIResponse[ApplicationDetailResponse])
async def get_application(
    application_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ApplicationDetailResponse]:
    data = await ApplicationService(db, current_user).get_application_response(application_id)
    return APIResponse(data=data)


@router.get("/{application_id}/similar-jobs", response_model=APIResponse[list[SimilarJobResult]])
async def similar_jobs_for_application(
    application_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[list[SimilarJobResult]]:
    application = await ApplicationService(db, current_user).get_application(application_id)
    data = await JobService(db, current_user).find_similar_jobs_for_candidate(application.candidate)
    return APIResponse(data=data)


@router.get("/{application_id}/status")
async def stream_application_status(
    application_id: UUID,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> StreamingResponse:
    await ApplicationService(db, current_user).get_application(application_id)
    progress = ApplicationProgressService()
    return StreamingResponse(
        progress.stream_sse(application_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.patch("/{application_id}/status", response_model=APIResponse[ApplicationResponse])
async def update_application_status(
    application_id: UUID,
    payload: ApplicationStatusUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ApplicationResponse]:
    data = await ApplicationService(db, current_user).update_status(application_id, payload.status)
    return APIResponse(data=data)


@router.post("/{application_id}/schedule", response_model=APIResponse[AgentRunResponse], status_code=201)
async def rerun_scheduler(
    application_id: UUID,
    payload: ScheduleRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[AgentRunResponse]:
    """Rerun only the scheduler agent for an application."""
    await ApplicationService(db, current_user).get_application(application_id)
    agent_run = await ApplicationOrchestrator(db).run_single_agent(
        application_id,
        AgentName.SCHEDULER,
        availability_slots=payload.availability_slots,
    )
    if agent_run is None:
        raise RuntimeError("Application disappeared before scheduler rerun could start")
    await db.refresh(agent_run)
    return APIResponse(data=AgentRunResponse.model_validate(agent_run))


@router.post("/{application_id}/offer", response_model=APIResponse[AgentRunResponse], status_code=201)
async def rerun_offer_writer(
    application_id: UUID,
    payload: OfferRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[AgentRunResponse]:
    """Rerun only the offer writer agent for an application."""
    await ApplicationService(db, current_user).get_application(application_id)
    agent_run = await ApplicationOrchestrator(db).run_single_agent(
        application_id,
        AgentName.OFFER_WRITER,
        compensation_details=payload.compensation_details,
    )
    if agent_run is None:
        raise RuntimeError("Application disappeared before offer rerun could start")
    await db.refresh(agent_run)
    return APIResponse(data=AgentRunResponse.model_validate(agent_run))
