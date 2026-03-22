"""Metadata endpoints used by the frontend shell."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import CurrentUser
from app.core.config import settings
from app.schemas.common import APIResponse
from app.schemas.meta import IntegrationStatusResponse

router = APIRouter(prefix="/meta", tags=["Meta"])


@router.get("/integrations", response_model=APIResponse[IntegrationStatusResponse])
async def get_integrations(current_user: CurrentUser) -> APIResponse[IntegrationStatusResponse]:
    """Return which backend integrations are currently configured."""
    data = IntegrationStatusResponse(
        openai_enabled=bool(settings.OPENAI_API_KEY),
        google_calendar_enabled=bool(
            settings.GOOGLE_CALENDAR_ACCESS_TOKEN
            or (
                settings.GOOGLE_CLIENT_ID
                and settings.GOOGLE_CLIENT_SECRET
                and settings.GOOGLE_CALENDAR_REFRESH_TOKEN
            )
        ),
        resend_enabled=bool(settings.RESEND_API_KEY),
    )
    return APIResponse(data=data)
