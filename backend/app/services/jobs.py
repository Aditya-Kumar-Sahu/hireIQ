"""CRUD service for job listings."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.job import Job, JobStatus
from app.models.user import User
from app.rag.embeddings import EmbeddingService
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.job import JobCreate, JobResponse, JobUpdate


def _to_job_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        company_id=job.company_id,
        title=job.title,
        description=job.description,
        requirements=job.requirements,
        seniority=job.seniority,
        status=job.status,
        has_embedding=job.embedding is not None,
        created_at=job.created_at,
    )


class JobService:
    """Business logic for job management."""

    def __init__(self, db: AsyncSession, user: User) -> None:
        self.db = db
        self.user = user
        self.embedding_service = EmbeddingService()

    @staticmethod
    def build_embedding_text(title: str, description: str, requirements: str) -> str:
        """Build the canonical text used for job embeddings."""
        return "\n".join([title.strip(), description.strip(), requirements.strip()])

    async def create_job(self, payload: JobCreate) -> JobResponse:
        job = Job(
            company_id=self.user.company_id,
            embedding=await self.embedding_service.embed_job_text(
                self.build_embedding_text(
                    payload.title,
                    payload.description,
                    payload.requirements,
                )
            ),
            **payload.model_dump(),
        )
        self.db.add(job)
        await self.db.flush()
        return _to_job_response(job)

    async def list_jobs(
        self,
        pagination: PaginationParams,
        status: JobStatus | None = None,
    ) -> PaginatedResponse[JobResponse]:
        filters = [Job.company_id == self.user.company_id]
        if status is not None:
            filters.append(Job.status == status)

        total = await self.db.scalar(select(func.count()).select_from(Job).where(*filters)) or 0
        result = await self.db.scalars(
            select(Job)
            .where(*filters)
            .order_by(Job.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        jobs = [_to_job_response(job) for job in result.all()]
        return PaginatedResponse(
            items=jobs,
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=(total + pagination.limit - 1) // pagination.limit if total else 0,
        )

    async def get_job(self, job_id: UUID) -> Job:
        job = await self.db.scalar(
            select(Job).where(Job.id == job_id, Job.company_id == self.user.company_id)
        )
        if job is None:
            raise NotFoundException("Job", job_id)
        return job

    async def get_job_response(self, job_id: UUID) -> JobResponse:
        return _to_job_response(await self.get_job(job_id))

    async def update_job(self, job_id: UUID, payload: JobUpdate) -> JobResponse:
        job = await self.get_job(job_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)
        if {"title", "description", "requirements"} & set(update_data):
            job.embedding = await self.embedding_service.embed_job_text(
                self.build_embedding_text(job.title, job.description, job.requirements)
            )
        await self.db.flush()
        return _to_job_response(job)

    async def delete_job(self, job_id: UUID) -> None:
        job = await self.get_job(job_id)
        job.status = JobStatus.CLOSED
        await self.db.flush()
