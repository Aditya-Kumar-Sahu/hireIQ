"""Dashboard aggregate endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DBSession
from app.schemas.common import APIResponse
from app.schemas.dashboard import DashboardActivityItem, DashboardStatsResponse
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=APIResponse[DashboardStatsResponse])
async def get_dashboard_stats(
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[DashboardStatsResponse]:
    """Return aggregate dashboard metrics for the current company."""
    data = await DashboardService(db, current_user).get_stats()
    return APIResponse(data=data)


@router.get("/activity", response_model=APIResponse[list[DashboardActivityItem]])
async def get_dashboard_activity(
    db: DBSession,
    current_user: CurrentUser,
    limit: int = Query(default=12, ge=1, le=50),
) -> APIResponse[list[DashboardActivityItem]]:
    """Return recent recruiter activity for the current company."""
    data = await DashboardService(db, current_user).get_activity(limit)
    return APIResponse(data=data)
