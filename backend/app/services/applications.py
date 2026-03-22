"""CRUD service for applications."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.agent_run import AgentRun
from app.models.application import Application, ApplicationStatus
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.schemas.application import (
    AgentRunResponse,
    ApplicationCandidateSummary,
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationJobSummary,
    ApplicationResponse,
)
from app.schemas.common import PaginatedResponse, PaginationParams


def _to_application_response(application: Application) -> ApplicationResponse:
    job = application.__dict__.get("job")
    candidate = application.__dict__.get("candidate")
    return ApplicationResponse(
        id=application.id,
        job_id=application.job_id,
        candidate_id=application.candidate_id,
        status=application.status,
        score=application.score,
        screening_notes=application.screening_notes,
        assessment_result=application.assessment_result,
        scheduled_at=application.scheduled_at,
        offer_text=application.offer_text,
        created_at=application.created_at,
        updated_at=application.updated_at,
        job=(
            ApplicationJobSummary(
                id=job.id,
                title=job.title,
                status=job.status,
                seniority=job.seniority,
            )
            if job is not None
            else None
        ),
        candidate=(
            ApplicationCandidateSummary(
                id=candidate.id,
                name=candidate.name,
                email=candidate.email,
                linkedin_url=candidate.linkedin_url,
            )
            if candidate is not None
            else None
        ),
    )


class ApplicationService:
    """Business logic for application lifecycle management."""

    def __init__(self, db: AsyncSession, user: User) -> None:
        self.db = db
        self.user = user

    async def create_application(self, payload: ApplicationCreate) -> ApplicationResponse:
        job = await self.db.scalar(
            select(Job).where(Job.id == payload.job_id, Job.company_id == self.user.company_id)
        )
        if job is None:
            raise NotFoundException("Job", str(payload.job_id))

        candidate = await self.db.scalar(select(Candidate).where(Candidate.id == payload.candidate_id))
        if candidate is None:
            raise NotFoundException("Candidate", str(payload.candidate_id))

        existing = await self.db.scalar(
            select(Application).where(
                Application.job_id == payload.job_id,
                Application.candidate_id == payload.candidate_id,
            )
        )
        if existing is not None:
            raise ConflictException("This candidate has already applied for the selected job")

        application = Application(job_id=job.id, candidate_id=candidate.id)
        self.db.add(application)
        await self.db.flush()
        return _to_application_response(application)

    async def list_applications(
        self,
        pagination: PaginationParams,
        job_id: UUID | None = None,
        status: ApplicationStatus | None = None,
    ) -> PaginatedResponse[ApplicationResponse]:
        filters = [Job.company_id == self.user.company_id]
        if job_id is not None:
            filters.append(Application.job_id == job_id)
        if status is not None:
            filters.append(Application.status == status)

        query = (
            select(Application)
            .join(Job, Job.id == Application.job_id)
            .options(
                selectinload(Application.job),
                selectinload(Application.candidate),
            )
            .where(*filters)
        )
        total = await self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        result = await self.db.scalars(
            query.order_by(Application.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        items = [_to_application_response(application) for application in result.all()]
        return PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=(total + pagination.limit - 1) // pagination.limit if total else 0,
        )

    async def get_application(self, application_id: UUID) -> Application:
        application = await self.db.scalar(
            select(Application)
            .join(Job, Job.id == Application.job_id)
            .options(
                selectinload(Application.agent_runs),
                selectinload(Application.job).selectinload(Job.company),
                selectinload(Application.candidate),
            )
            .where(Application.id == application_id, Job.company_id == self.user.company_id)
        )
        if application is None:
            raise NotFoundException("Application", application_id)
        return application

    async def get_application_response(self, application_id: UUID) -> ApplicationDetailResponse:
        application = await self.get_application(application_id)
        return ApplicationDetailResponse(
            **_to_application_response(application).model_dump(),
            agent_runs=[AgentRunResponse.model_validate(agent_run) for agent_run in application.agent_runs],
        )

    async def update_status(
        self,
        application_id: UUID,
        status: ApplicationStatus,
    ) -> ApplicationResponse:
        application = await self.get_application(application_id)
        application.status = status
        await self.db.flush()
        return _to_application_response(application)
