"""Dashboard aggregate and activity response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    """Aggregate metrics for the recruiter dashboard."""

    total_jobs: int
    active_jobs: int
    total_candidates: int
    total_applications: int
    average_score: float
    offered_count: int
    status_counts: dict[str, int] = Field(default_factory=dict)


class DashboardActivityItem(BaseModel):
    """A recent dashboard activity entry."""

    id: str
    type: Literal["application", "agent_run", "job"]
    title: str
    description: str
    status: str | None = None
    timestamp: datetime
    application_id: UUID | None = None
    job_id: UUID | None = None
    candidate_id: UUID | None = None
