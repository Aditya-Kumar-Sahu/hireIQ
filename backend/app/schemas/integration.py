"""Schemas for external integration flows."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GoogleCalendarAuthorizationResponse(BaseModel):
    """Authorization payload returned before redirecting to Google."""

    authorization_url: str
    state: str


class GoogleCalendarCallbackRequest(BaseModel):
    """OAuth callback payload forwarded from the frontend route."""

    code: str = Field(min_length=1)
    state: str = Field(min_length=1)


class GoogleCalendarConnectionResponse(BaseModel):
    """Connected Google Calendar metadata."""

    provider: str = "google_calendar"
    connected: bool
    connected_email: str | None = None
    calendar_id: str | None = None


class ATSWebhookReceiptResponse(BaseModel):
    """Inbound webhook acknowledgement."""

    accepted: bool
    provider: str
    event_type: str
    event_id: str | None = None
