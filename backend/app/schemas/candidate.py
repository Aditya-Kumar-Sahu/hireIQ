"""
Candidate schemas — create and response models.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CandidateCreate(BaseModel):
    """Request body for adding a candidate."""

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    linkedin_url: str | None = Field(default=None, max_length=500)
    resume_text: str | None = None


class CandidateResponse(BaseModel):
    """Candidate profile response."""

    id: str
    name: str
    email: str
    linkedin_url: str | None
    resume_file_url: str | None
    has_embedding: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class CandidateDetailResponse(CandidateResponse):
    """Candidate profile with resume text included."""

    resume_text: str | None


class CandidateSearchResult(BaseModel):
    """Candidate with similarity score from semantic search."""

    candidate: CandidateResponse
    similarity_score: float


class CandidateListResponse(BaseModel):
    """Paginated candidate list response."""

    candidates: list[CandidateResponse]
    total: int
    page: int
    limit: int
