"""
Application schemas — create, update, and response models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.application import ApplicationStatus
from app.models.job import JobSeniority, JobStatus


class ApplicationJobSummary(BaseModel):
    """Job summary embedded on application responses."""

    id: UUID
    title: str
    status: JobStatus
    seniority: JobSeniority


class ApplicationCandidateSummary(BaseModel):
    """Candidate summary embedded on application responses."""

    id: UUID
    name: str
    email: str
    linkedin_url: str | None


class ApplicationCreate(BaseModel):
    """Request body for submitting an application."""

    job_id: UUID
    candidate_id: UUID


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

    id: UUID
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

    id: UUID
    job_id: UUID
    candidate_id: UUID
    status: ApplicationStatus
    score: float | None
    screening_notes: str | None
    assessment_result: dict[str, Any] | None
    scheduled_at: datetime | None
    offer_text: str | None
    created_at: datetime
    updated_at: datetime
    job: ApplicationJobSummary | None = None
    candidate: ApplicationCandidateSummary | None = None

    model_config = {"from_attributes": True}


class ApplicationDetailResponse(ApplicationResponse):
    """Application response with agent run history."""

    agent_runs: list[AgentRunResponse] = Field(default_factory=list)


class ApplicationListResponse(BaseModel):
    """Paginated application list response."""

    applications: list[ApplicationResponse]
    total: int
    page: int
    limit: int
