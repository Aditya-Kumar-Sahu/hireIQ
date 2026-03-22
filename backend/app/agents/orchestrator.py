"""CrewAI-backed application orchestration and agent-run logging."""

from __future__ import annotations

from datetime import datetime
from time import perf_counter
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.crewai_runner import CrewAIPipelineRunner, PipelineContext
from app.core.database import async_session_factory
from app.models.agent_run import AgentName, AgentRun, AgentRunStatus
from app.models.application import Application, ApplicationStatus
from app.models.job import Job
from app.services.progress import ApplicationProgressService
from app.services.screening import ScreeningInsightsService


class ApplicationOrchestrator:
    """Run the application pipeline and persist agent logs/progress."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.progress = ApplicationProgressService()
        self.runner = CrewAIPipelineRunner()
        self.screening = ScreeningInsightsService(db)

    async def run(self, application_id: UUID) -> None:
        """Run the full application pipeline and persist agent logs."""
        application = await self.db.scalar(
            select(Application)
            .options(
                selectinload(Application.job).selectinload(Job.company),
                selectinload(Application.candidate),
                selectinload(Application.agent_runs),
            )
            .where(Application.id == application_id)
        )
        if application is None:
            return

        await self.progress.publish(
            application.id,
            "pipeline_started",
            {"application_id": str(application.id), "status": application.status.value},
        )
        context = await self._build_context(application)

        await self._run_agent(application, AgentName.CV_SCREENER, ApplicationStatus.SCREENING, context)
        await self._run_agent(application, AgentName.ASSESSOR, ApplicationStatus.ASSESSED, context)
        await self._run_agent(application, AgentName.SCHEDULER, ApplicationStatus.SCHEDULED, context)
        await self._run_agent(application, AgentName.OFFER_WRITER, ApplicationStatus.OFFERED, context)

        await self.progress.publish(
            application.id,
            "complete",
            {"application_id": str(application.id), "status": application.status.value},
        )

    async def _build_context(self, application: Application) -> PipelineContext:
        """Assemble the shared pipeline context for all four agents."""
        insights = await self.screening.build_insights(application)
        context = PipelineContext(
            application_id=str(application.id),
            company_name=application.job.company.name if application.job.company else "HireIQ",
            candidate_name=application.candidate.name,
            candidate_email=application.candidate.email,
            candidate_resume_text=application.candidate.resume_text or "",
            job_title=application.job.title,
            job_description=application.job.description,
            job_requirements=application.job.requirements,
            similarity_score=insights.similarity_score,
            matched_skills=insights.matched_skills,
            missing_skills=insights.missing_skills,
            similar_jobs=insights.similar_jobs,
            similar_applications=insights.similar_applications,
            scheduler_slots=self.runner.default_scheduler_slots(),
        )
        context.recommendation = self.runner.recommendation(context)
        return context

    async def _run_agent(
        self,
        application: Application,
        agent_name: AgentName,
        target_status: ApplicationStatus,
        context: PipelineContext,
    ) -> None:
        """Execute one agent, persist its run, and publish progress events."""
        stage_name = {
            AgentName.CV_SCREENER: "screening",
            AgentName.ASSESSOR: "assessing",
            AgentName.SCHEDULER: "scheduling",
            AgentName.OFFER_WRITER: "writing_offer",
        }[agent_name]

        application.status = target_status
        agent_run = AgentRun(
            application_id=application.id,
            agent_name=agent_name,
            status=AgentRunStatus.RUNNING,
            input=context.model_dump_json(),
        )
        self.db.add(agent_run)
        await self.db.commit()
        await self.progress.publish(
            application.id,
            "stage",
            {
                "stage": stage_name,
                "agent_name": agent_name.value,
                "status": "running",
            },
        )

        started_at = perf_counter()
        try:
            result = await self.runner.run_task(agent_name, context)
            agent_run.status = AgentRunStatus.COMPLETED
            agent_run.output = result.output
            agent_run.tokens_used = result.tokens_used
            agent_run.duration_ms = max(int((perf_counter() - started_at) * 1000), 1)
            self._apply_output(application, agent_name, result.output)
            await self.db.commit()
            await self.progress.publish(
                application.id,
                "stage",
                {
                    "stage": stage_name,
                    "agent_name": agent_name.value,
                    "status": "completed",
                    "application_status": application.status.value,
                },
            )
        except Exception as exc:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error_message = str(exc)
            agent_run.duration_ms = max(int((perf_counter() - started_at) * 1000), 1)
            await self.db.commit()
            await self.progress.publish(
                application.id,
                "failed",
                {
                    "stage": stage_name,
                    "agent_name": agent_name.value,
                    "status": "failed",
                    "error": str(exc),
                },
            )
            raise

    @staticmethod
    def _apply_output(
        application: Application,
        agent_name: AgentName,
        output: dict[str, object],
    ) -> None:
        """Apply structured agent outputs back onto the application row."""
        if agent_name == AgentName.CV_SCREENER:
            application.score = float(output.get("score", 0.0))
            application.screening_notes = str(output.get("summary", ""))
            return
        if agent_name == AgentName.ASSESSOR:
            application.assessment_result = output
            return
        if agent_name == AgentName.SCHEDULER:
            scheduled_at = output.get("scheduled_at")
            if isinstance(scheduled_at, str):
                application.scheduled_at = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
            return
        if agent_name == AgentName.OFFER_WRITER:
            application.offer_text = str(output.get("offer_text", ""))


async def run_application_pipeline(application_id: UUID) -> None:
    """Entry point used by FastAPI background tasks."""
    async with async_session_factory() as session:
        orchestrator = ApplicationOrchestrator(session)
        await orchestrator.run(application_id)
