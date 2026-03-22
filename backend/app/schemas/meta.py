"""Schemas for frontend metadata and integration status pages."""

from __future__ import annotations

from pydantic import BaseModel


class IntegrationStatusResponse(BaseModel):
    """Expose whether key integrations are configured on the backend."""

    openai_enabled: bool
    google_calendar_enabled: bool
    resend_enabled: bool
    sse_enabled: bool = True
