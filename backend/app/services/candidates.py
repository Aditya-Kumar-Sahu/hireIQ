"""CRUD service for candidates."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.schemas.candidate import (
    CandidateCreate,
    CandidateDetailResponse,
    CandidateResponse,
    CandidateSearchResult,
)
from app.schemas.common import PaginatedResponse, PaginationParams


def _to_candidate_response(candidate: Candidate) -> CandidateResponse:
    return CandidateResponse(
        id=candidate.id,
        name=candidate.name,
        email=candidate.email,
        linkedin_url=candidate.linkedin_url,
        resume_file_url=candidate.resume_file_url,
        has_embedding=candidate.resume_embedding is not None,
        created_at=candidate.created_at,
    )


class CandidateService:
    """Business logic for candidate management."""

    def __init__(self, db: AsyncSession, user: User) -> None:
        self.db = db
        self.user = user

    async def create_candidate(self, payload: CandidateCreate) -> CandidateResponse:
        existing = await self.db.scalar(
            select(Candidate).where(func.lower(Candidate.email) == payload.email.lower())
        )
        if existing is not None:
            raise ConflictException("A candidate with this email already exists")

        candidate = Candidate(
            name=payload.name.strip(),
            email=payload.email.lower(),
            linkedin_url=payload.linkedin_url,
            resume_text=payload.resume_text,
        )
        self.db.add(candidate)
        await self.db.flush()
        return _to_candidate_response(candidate)

    async def list_candidates(
        self,
        pagination: PaginationParams,
        search: str | None = None,
    ) -> PaginatedResponse[CandidateResponse]:
        accessible_ids = (
            select(Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .where(Job.company_id == self.user.company_id)
        )
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    Candidate.name.ilike(term),
                    Candidate.email.ilike(term),
                    Candidate.resume_text.ilike(term),
                )
            )

        base_query = (
            select(Candidate)
            .where(or_(Candidate.id.in_(accessible_ids), ~Candidate.applications.any()))
            .where(*filters)
        )
        total = await self.db.scalar(
            select(func.count()).select_from(base_query.subquery())
        ) or 0
        result = await self.db.scalars(
            base_query.order_by(Candidate.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        items = [_to_candidate_response(candidate) for candidate in result.all()]
        return PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=(total + pagination.limit - 1) // pagination.limit if total else 0,
        )

    async def get_candidate(self, candidate_id: UUID) -> Candidate:
        access_query = (
            select(Candidate)
            .where(Candidate.id == candidate_id)
            .where(
                or_(
                    ~Candidate.applications.any(),
                    exists(
                        select(Application.id)
                        .join(Job, Job.id == Application.job_id)
                        .where(
                            Application.candidate_id == Candidate.id,
                            Job.company_id == self.user.company_id,
                        )
                    ),
                )
            )
        )
        candidate = await self.db.scalar(access_query)
        if candidate is None:
            raise NotFoundException("Candidate", candidate_id)
        return candidate

    async def get_candidate_response(self, candidate_id: UUID) -> CandidateDetailResponse:
        candidate = await self.get_candidate(candidate_id)
        return CandidateDetailResponse(
            **_to_candidate_response(candidate).model_dump(),
            resume_text=candidate.resume_text,
        )

    async def search_candidates(self, query: str) -> list[CandidateSearchResult]:
        term = query.strip()
        if not term:
            return []

        result = await self.db.scalars(
            select(Candidate)
            .where(
                or_(
                    ~Candidate.applications.any(),
                    exists(
                        select(Application.id)
                        .join(Job, Job.id == Application.job_id)
                        .where(
                            Application.candidate_id == Candidate.id,
                            Job.company_id == self.user.company_id,
                        )
                    ),
                ),
                or_(
                    Candidate.name.ilike(f"%{term}%"),
                    Candidate.email.ilike(f"%{term}%"),
                    Candidate.resume_text.ilike(f"%{term}%"),
                )
            )
            .order_by(Candidate.created_at.desc())
            .limit(20)
        )

        return [
            CandidateSearchResult(
                candidate=_to_candidate_response(candidate),
                similarity_score=1.0,
            )
            for candidate in result.all()
        ]
