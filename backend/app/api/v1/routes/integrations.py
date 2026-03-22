"""Integration-specific API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundException
from app.models.company import Company
from app.schemas.common import APIResponse
from app.schemas.integration import (
    ATSWebhookReceiptResponse,
    GoogleCalendarAuthorizationResponse,
    GoogleCalendarCallbackRequest,
    GoogleCalendarConnectionResponse,
)
from app.services.ats_webhooks import ATSWebhookService
from app.services.google_oauth import GoogleOAuthService

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get(
    "/google-calendar/authorize",
    response_model=APIResponse[GoogleCalendarAuthorizationResponse],
)
async def authorize_google_calendar(
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[GoogleCalendarAuthorizationResponse]:
    data = GoogleOAuthService(db).build_authorization_payload(current_user)
    return APIResponse(data=GoogleCalendarAuthorizationResponse(**data))


@router.post(
    "/google-calendar/callback",
    response_model=APIResponse[GoogleCalendarConnectionResponse],
)
async def connect_google_calendar(
    payload: GoogleCalendarCallbackRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[GoogleCalendarConnectionResponse]:
    company = await db.scalar(select(Company).where(Company.id == current_user.company_id))
    if company is None:
        raise NotFoundException("Company", str(current_user.company_id))

    data = await GoogleOAuthService(db).connect_company(
        company=company,
        user=current_user,
        code=payload.code,
        state=payload.state,
    )
    return APIResponse(data=GoogleCalendarConnectionResponse(**data))


@router.delete(
    "/google-calendar/connection",
    response_model=APIResponse[GoogleCalendarConnectionResponse],
)
async def disconnect_google_calendar(
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[GoogleCalendarConnectionResponse]:
    company = await db.scalar(select(Company).where(Company.id == current_user.company_id))
    if company is None:
        raise NotFoundException("Company", str(current_user.company_id))

    data = await GoogleOAuthService(db).disconnect_company(company)
    return APIResponse(data=GoogleCalendarConnectionResponse(**data))


@router.post("/ats/webhooks/{provider}", response_model=APIResponse[ATSWebhookReceiptResponse])
async def receive_ats_webhook(
    provider: str,
    request: Request,
    db: DBSession,
) -> APIResponse[ATSWebhookReceiptResponse]:
    body = await request.body()
    data = await ATSWebhookService(db).receive_event(
        provider=provider,
        body=body,
        signature=request.headers.get("X-HireIQ-Signature"),
    )
    return APIResponse(data=ATSWebhookReceiptResponse(**data))
