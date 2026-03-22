"""
Application schemas — create, update, and response models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.application import ApplicationStatus


class ApplicationCreate(BaseModel):
    """Request body for submitting an application."""

    job_id: str
    candidate_id: str


class ApplicationStatusUpdate(BaseModel):
    """Request body for manually updating application status."""

    status: ApplicationStatus


class ScheduleRequest(BaseModel):
    """Request body for triggering the scheduling agent."""

    availability_slots: list[str]


class OfferRequest(BaseModel):
    """Request body for triggering the offer writer agent."""

    compensation_details: str | None = None


class AgentRunResponse(BaseModel):
    """Agent execution log entry."""

    id: str
    agent_name: str
    status: str
    input: str | None
    output: dict[str, Any] | None
    error_message: str | None
    tokens_used: int | None
    duration_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationResponse(BaseModel):
    """Application detail response."""

    id: str
    job_id: str
    candidate_id: str
    status: str
    score: float | None
    screening_notes: str | None
    assessment_result: dict[str, Any] | None
    scheduled_at: datetime | None
    offer_text: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationDetailResponse(ApplicationResponse):
    """Application response with agent run history."""

    agent_runs: list[AgentRunResponse] = []


class ApplicationListResponse(BaseModel):
    """Paginated application list response."""

    applications: list[ApplicationResponse]
    total: int
    page: int
    limit: int
