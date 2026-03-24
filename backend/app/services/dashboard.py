"""Dashboard aggregate and activity queries."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_run import AgentRun
from app.models.application import Application, ApplicationStatus
from app.models.candidate import Candidate
from app.models.job import Job, JobStatus
from app.models.user import User
from app.schemas.dashboard import DashboardActivityItem, DashboardStatsResponse


class DashboardService:
    """Compute server-side dashboard metrics and recent activity."""

    def __init__(self, db: AsyncSession, user: User) -> None:
        self.db = db
        self.user = user

    async def get_stats(self) -> DashboardStatsResponse:
        """Return aggregate recruiter metrics for the current company."""
        total_jobs = await self.db.scalar(
            select(func.count()).select_from(Job).where(Job.company_id == self.user.company_id)
        ) or 0
        active_jobs = await self.db.scalar(
            select(func.count())
            .select_from(Job)
            .where(Job.company_id == self.user.company_id, Job.status == JobStatus.ACTIVE)
        ) or 0
        total_candidates = await self.db.scalar(
            select(func.count())
            .select_from(Candidate)
            .where(Candidate.company_id == self.user.company_id)
        ) or 0
        total_applications = await self.db.scalar(
            select(func.count())
            .select_from(Application)
            .join(Job, Job.id == Application.job_id)
            .where(Job.company_id == self.user.company_id)
        ) or 0
        average_score = await self.db.scalar(
            select(func.avg(Application.score))
            .select_from(Application)
            .join(Job, Job.id == Application.job_id)
            .where(Job.company_id == self.user.company_id, Application.score.is_not(None))
        )
        offered_count = await self.db.scalar(
            select(func.count())
            .select_from(Application)
            .join(Job, Job.id == Application.job_id)
            .where(
                Job.company_id == self.user.company_id,
                Application.status.in_([ApplicationStatus.OFFERED, ApplicationStatus.HIRED]),
            )
        ) or 0

        status_counts = {status.value: 0 for status in ApplicationStatus}
        grouped_statuses = await self.db.execute(
            select(Application.status, func.count())
            .join(Job, Job.id == Application.job_id)
            .where(Job.company_id == self.user.company_id)
            .group_by(Application.status)
        )
        for status, count in grouped_statuses.all():
            status_counts[status.value] = int(count)

        return DashboardStatsResponse(
            total_jobs=int(total_jobs),
            active_jobs=int(active_jobs),
            total_candidates=int(total_candidates),
            total_applications=int(total_applications),
            average_score=float(average_score or 0.0),
            offered_count=int(offered_count),
            status_counts=status_counts,
        )

    async def get_activity(self, limit: int = 12) -> list[DashboardActivityItem]:
        """Return recent application, agent-run, and job activity merged by timestamp."""
        application_rows = await self.db.execute(
            select(Application, Candidate, Job)
            .join(Job, Job.id == Application.job_id)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .where(Job.company_id == self.user.company_id)
            .order_by(Application.updated_at.desc())
            .limit(limit)
        )
        job_rows = await self.db.execute(
            select(Job)
            .where(Job.company_id == self.user.company_id)
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        agent_run_rows = await self.db.execute(
            select(AgentRun, Application, Candidate, Job)
            .join(Application, Application.id == AgentRun.application_id)
            .join(Job, Job.id == Application.job_id)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .where(Job.company_id == self.user.company_id)
            .order_by(AgentRun.created_at.desc())
            .limit(limit)
        )

        activity: list[DashboardActivityItem] = [
            DashboardActivityItem(
                id=str(application.id),
                type="application",
                title=f"{candidate.name} applied to {job.title}",
                description=f"Application moved to {application.status.value}.",
                status=application.status.value,
                timestamp=application.updated_at,
                application_id=application.id,
                job_id=job.id,
                candidate_id=candidate.id,
            )
            for application, candidate, job in application_rows.all()
        ]
        activity.extend(
            DashboardActivityItem(
                id=str(job.id),
                type="job",
                title=f"Job posted: {job.title}",
                description=f"{job.seniority.value} role is currently {job.status.value}.",
                status=job.status.value,
                timestamp=job.created_at,
                job_id=job.id,
            )
            for job in job_rows.scalars().all()
        )
        activity.extend(
            DashboardActivityItem(
                id=str(agent_run.id),
                type="agent_run",
                title=f"{agent_run.agent_name.value} ran for {candidate.name}",
                description=(
                    "Fallback output used."
                    if agent_run.used_fallback
                    else f"Completed for {job.title}."
                ),
                status=agent_run.status.value,
                timestamp=agent_run.created_at,
                application_id=application.id,
                job_id=job.id,
                candidate_id=candidate.id,
            )
            for agent_run, application, candidate, job in agent_run_rows.all()
        )

        activity.sort(key=lambda item: item.timestamp, reverse=True)
        return activity[:limit]
