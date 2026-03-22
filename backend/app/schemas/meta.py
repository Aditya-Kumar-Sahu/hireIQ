"""Schemas for frontend metadata and integration status pages."""

from __future__ import annotations

from pydantic import BaseModel


class IntegrationStatusResponse(BaseModel):
    """Expose whether key integrations are configured on the backend."""

    gemini_enabled: bool
    google_calendar_enabled: bool
    google_calendar_connected_email: str | None = None
    resend_enabled: bool
    r2_enabled: bool
    resume_storage_enabled: bool
    ats_webhooks_enabled: bool
    ats_webhook_url: str
    sse_enabled: bool = True
