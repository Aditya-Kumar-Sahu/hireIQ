"""Job management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DBSession, Pagination
from app.models.job import JobStatus
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.job import JobCreate, JobResponse, JobUpdate
from app.services.jobs import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=APIResponse[JobResponse], status_code=201)
async def create_job(
    payload: JobCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[JobResponse]:
    return APIResponse(data=await JobService(db, current_user).create_job(payload))


@router.get("", response_model=APIResponse[PaginatedResponse[JobResponse]])
async def list_jobs(
    db: DBSession,
    current_user: CurrentUser,
    pagination: Pagination,
    status: JobStatus | None = Query(default=None),
) -> APIResponse[PaginatedResponse[JobResponse]]:
    data = await JobService(db, current_user).list_jobs(pagination, status)
    return APIResponse(data=data)


@router.get("/{job_id}", response_model=APIResponse[JobResponse])
async def get_job(
    job_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[JobResponse]:
    return APIResponse(data=await JobService(db, current_user).get_job_response(job_id))


@router.put("/{job_id}", response_model=APIResponse[JobResponse])
async def update_job(
    job_id: UUID,
    payload: JobUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[JobResponse]:
    data = await JobService(db, current_user).update_job(job_id, payload)
    return APIResponse(data=data)


@router.delete("/{job_id}", response_model=APIResponse[dict[str, bool]])
async def delete_job(
    job_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict[str, bool]]:
    await JobService(db, current_user).delete_job(job_id)
    return APIResponse(data={"deleted": True})
