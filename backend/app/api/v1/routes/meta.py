"""Metadata endpoints used by the frontend shell."""

from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DBSession
from app.core.config import settings
from app.models.company import Company
from app.schemas.common import APIResponse
from app.schemas.meta import IntegrationStatusResponse
from app.services.ats_webhooks import ATSWebhookService
from app.services.calendar import GoogleCalendarService
from app.services.storage import R2ResumeStorageService

router = APIRouter(prefix="/meta", tags=["Meta"])


@router.get("/integrations", response_model=APIResponse[IntegrationStatusResponse])
async def get_integrations(
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[IntegrationStatusResponse]:
    """Return which backend integrations are currently configured."""
    company = await db.scalar(select(Company).where(Company.id == current_user.company_id))
    calendar = GoogleCalendarService(db=db, company=company)
    storage = R2ResumeStorageService()
    ats = ATSWebhookService(db)
    data = IntegrationStatusResponse(
        gemini_enabled=bool(settings.resolved_gemini_api_key),
        google_calendar_enabled=calendar.is_configured(),
        google_calendar_connected_email=(
            company.google_calendar_connected_email if company is not None else None
        ),
        resend_enabled=bool(settings.RESEND_API_KEY),
        r2_enabled=storage.is_configured(),
        resume_storage_enabled=storage.is_configured(),
        ats_webhooks_enabled=ats.is_configured(),
        ats_webhook_url=ats.webhook_url(request),
    )
    return APIResponse(data=data)
