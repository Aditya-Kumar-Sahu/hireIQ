"""
Job schemas — create, update, and response models.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.job import JobSeniority, JobStatus


class JobCreate(BaseModel):
    """Request body for creating a job listing."""

    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=10)
    requirements: str = Field(min_length=10)
    seniority: JobSeniority = JobSeniority.MID


class JobUpdate(BaseModel):
    """Request body for updating a job listing. All fields optional."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=10)
    requirements: str | None = Field(default=None, min_length=10)
    seniority: JobSeniority | None = None
    status: JobStatus | None = None


class JobResponse(BaseModel):
    """Job listing response."""

    id: UUID
    company_id: UUID
    title: str
    description: str
    requirements: str
    seniority: JobSeniority
    status: JobStatus
    has_embedding: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class SimilarJobResult(BaseModel):
    """Job with a similarity score from vector search."""

    job: JobResponse
    similarity_score: float


class JobListResponse(BaseModel):
    """Paginated job list response."""

    jobs: list[JobResponse]
    total: int
    page: int
    limit: int
