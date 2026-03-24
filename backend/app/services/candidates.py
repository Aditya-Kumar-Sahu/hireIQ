"""CRUD service for candidates."""

from __future__ import annotations

import asyncio
import inspect
from uuid import UUID

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.rag import ResumeParser
from app.rag.embeddings import EmbeddingService
from app.schemas.candidate import (
    CandidateCreate,
    CandidateDetailResponse,
    CandidateResponse,
    CandidateSearchResult,
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.storage import R2ResumeStorageService


async def _maybe_await(value: object) -> object:
    if inspect.isawaitable(value):
        return await value
    return value


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
        self.embedding_service = EmbeddingService()
        self.resume_parser = ResumeParser()
        self.storage_service = R2ResumeStorageService()

    async def create_candidate(self, payload: CandidateCreate) -> CandidateResponse:
        candidate = await self._create_candidate_model(
            name=payload.name,
            email=payload.email,
            linkedin_url=payload.linkedin_url,
            resume_text=payload.resume_text,
        )
        return _to_candidate_response(candidate)

    async def create_candidate_from_pdf(
        self,
        *,
        name: str,
        email: str,
        linkedin_url: str | None,
        filename: str,
        file_bytes: bytes,
    ) -> CandidateResponse:
        """Parse a resume PDF, store the original file, and create a candidate."""
        if not filename.lower().endswith(".pdf"):
            raise BadRequestException("Resume upload must be a PDF")

        resume_text = self.resume_parser.extract_text(file_bytes)
        await self._ensure_email_is_available(email)

        embedding_task = (
            asyncio.create_task(self.embedding_service.embed_text(resume_text))
            if resume_text
            else None
        )
        upload_task = asyncio.create_task(
            _maybe_await(
                self.storage_service.upload_resume(
                    company_id=self.user.company_id,
                    filename=filename,
                    file_bytes=file_bytes,
                )
            )
        )

        resume_embedding = await embedding_task if embedding_task is not None else None
        upload_result = await upload_task

        candidate = Candidate(
            name=name.strip(),
            email=email.lower(),
            linkedin_url=linkedin_url,
            resume_text=resume_text,
            resume_embedding=resume_embedding,
        )
        self.db.add(candidate)
        await self.db.flush()
        if isinstance(upload_result, dict) and upload_result.get("storage_key"):
            candidate.resume_storage_key = str(upload_result["storage_key"])
            candidate.resume_file_url = f"/api/v1/candidates/{candidate.id}/resume"
            await self.db.flush()

        return _to_candidate_response(candidate)

    async def get_candidate_resume(self, candidate_id: UUID) -> dict[str, object]:
        """Return stored resume bytes and metadata for download."""
        candidate = await self.get_candidate(candidate_id)
        if not candidate.resume_storage_key:
            raise NotFoundException("Resume", str(candidate_id))

        payload = await _maybe_await(
            self.storage_service.download_resume(candidate.resume_storage_key)
        )
        if not isinstance(payload, dict):
            raise NotFoundException("Resume", str(candidate_id))
        return payload

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

        query_embedding = await self.embedding_service.embed_text(term)
        similarity_score = (1 - Candidate.resume_embedding.cosine_distance(query_embedding)).label(
            "similarity_score"
        )
        result = await self.db.execute(
            select(Candidate, similarity_score)
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
                Candidate.resume_embedding.is_not(None),
            )
            .order_by(Candidate.resume_embedding.cosine_distance(query_embedding))
            .limit(20)
        )

        return [
            CandidateSearchResult(
                candidate=_to_candidate_response(candidate),
                similarity_score=float(score),
            )
            for candidate, score in result.all()
        ]

    async def _create_candidate_model(
        self,
        *,
        name: str,
        email: str,
        linkedin_url: str | None,
        resume_text: str | None,
    ) -> Candidate:
        await self._ensure_email_is_available(email)
        candidate = Candidate(
            name=name.strip(),
            email=email.lower(),
            linkedin_url=linkedin_url,
            resume_text=resume_text,
            resume_embedding=(
                await self.embedding_service.embed_text(resume_text)
                if resume_text
                else None
            ),
        )
        self.db.add(candidate)
        await self.db.flush()
        return candidate

    async def _ensure_email_is_available(self, email: str) -> None:
        existing = await self.db.scalar(
            select(Candidate).where(func.lower(Candidate.email) == email.lower())
        )
        if existing is not None:
            raise ConflictException("A candidate with this email already exists")
