"""Application management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DBSession, Pagination
from app.models.application import ApplicationStatus
from app.schemas.application import (
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationResponse,
    ApplicationStatusUpdate,
)
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.applications import ApplicationService

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=APIResponse[ApplicationResponse])
async def create_application(
    payload: ApplicationCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ApplicationResponse]:
    data = await ApplicationService(db, current_user).create_application(payload)
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


@router.patch("/{application_id}/status", response_model=APIResponse[ApplicationResponse])
async def update_application_status(
    application_id: UUID,
    payload: ApplicationStatusUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ApplicationResponse]:
    data = await ApplicationService(db, current_user).update_status(application_id, payload.status)
    return APIResponse(data=data)
