"""CrewAI-backed application pipeline runner with deterministic local fallback."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task
from pydantic import BaseModel, Field

from app.models.agent_run import AgentName
from app.services.screening import ScreeningInsightsService


class PipelineContext(BaseModel):
    """Normalized application context passed into agents and tools."""

    application_id: str
    company_name: str
    candidate_name: str
    candidate_email: str
    candidate_resume_text: str
    job_title: str
    job_description: str
    job_requirements: str
    similarity_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    screening_strengths: list[str]
    screening_risks: list[str]
    screening_evidence: list[str]
    similar_jobs: list[dict[str, object]]
    similar_applications: list[dict[str, object]]
    recommendation: str = "review"
    scheduler_slots: list[str] = Field(default_factory=list)
    delivery_mode: str = "preview"
    from_email: str = "noreply@hireiq.dev"


class CVScreenerOutput(BaseModel):
    score: float
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    risks: list[str]
    evidence: list[str]
    similar_jobs: list[dict[str, object]]
    similar_applications: list[dict[str, object]]
    recommendation: str
    summary: str
    experience_years: int


class AssessorOutput(BaseModel):
    questions: list[str]
    focus_areas: list[str]
    question_provenance: list[dict[str, object]]


class SchedulerOutput(BaseModel):
    scheduled_at: str
    proposed_slots: list[str]
    email_draft: str


class OfferWriterOutput(BaseModel):
    offer_text: str
    summary: str


class AgentTaskResult(BaseModel):
    """Normalized output from a single agent execution."""

    output: dict[str, object]
    tokens_used: int = 0


class CrewAIPipelineRunner:
    """Build and execute real CrewAI agents, with a safe deterministic fallback."""

    model = "gpt-4o-mini"

    def build_agents(self, context: PipelineContext) -> dict[AgentName, Agent]:
        """Return the four CrewAI agents used in the application pipeline."""
        llm = self._build_llm()

        from app.tools.recruitment_tools import (
            ApplicationContextTool,
            CalendarSlotsTool,
            EmailDeliveryTool,
            OfferDraftTool,
            SimilarApplicationsTool,
            SimilarJobsTool,
            SkillGapTool,
        )

        return {
            AgentName.CV_SCREENER: Agent(
                role="Senior Talent Acquisition Analyst",
                goal="Evaluate resume fit, identify skill gaps, and produce an auditable recommendation.",
                backstory="You specialize in technical recruiting and structured candidate screening.",
                llm=llm,
                verbose=False,
                allow_delegation=False,
                tools=[
                    ApplicationContextTool(context),
                    SimilarJobsTool(context),
                    SimilarApplicationsTool(context),
                    SkillGapTool(context),
                ],
            ),
            AgentName.ASSESSOR: Agent(
                role="Technical Interview Assessor",
                goal="Create sharp, role-specific interview questions from the job context and skill gaps.",
                backstory="You translate role requirements into focused technical assessment questions.",
                llm=llm,
                verbose=False,
                allow_delegation=False,
                tools=[
                    ApplicationContextTool(context),
                    SkillGapTool(context),
                ],
            ),
            AgentName.SCHEDULER: Agent(
                role="Interview Scheduling Coordinator",
                goal="Propose polished interview slots and a draft outreach message.",
                backstory="You coordinate interviews with speed and clarity.",
                llm=llm,
                verbose=False,
                allow_delegation=False,
                tools=[
                    ApplicationContextTool(context),
                    CalendarSlotsTool(context),
                    EmailDeliveryTool(context),
                ],
            ),
            AgentName.OFFER_WRITER: Agent(
                role="Offer Communications Specialist",
                goal="Draft a personalized offer note grounded in the role and screening outcome.",
                backstory="You write warm, structured recruiting communications.",
                llm=llm,
                verbose=False,
                allow_delegation=False,
                tools=[
                    ApplicationContextTool(context),
                    OfferDraftTool(context),
                    EmailDeliveryTool(context),
                ],
            ),
        }

    async def run_task(self, agent_name: AgentName, context: PipelineContext) -> AgentTaskResult:
        """Execute one pipeline task using CrewAI when configured, else a deterministic fallback."""
        if self._build_llm() is None:
            return AgentTaskResult(output=self._fallback_output(agent_name, context), tokens_used=0)

        agents = self.build_agents(context)
        agent = agents[agent_name]
        task = self._build_task(agent_name, agent)
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )
        crew_output = crew.kickoff(inputs=context.model_dump())
        parsed_output = self._parse_output(crew_output)
        tokens = 0
        if crew_output.token_usage is not None:
            tokens = int(getattr(crew_output.token_usage, "total_tokens", 0) or 0)
        return AgentTaskResult(output=parsed_output, tokens_used=tokens)

    def _build_task(self, agent_name: AgentName, agent: Agent) -> Task:
        """Build the CrewAI task definition for a single agent."""
        if agent_name == AgentName.CV_SCREENER:
            return Task(
                description=(
                    "Evaluate the candidate against the job. Use the tools to inspect application context, "
                    "similar jobs, past similar applications, and skill gaps. Return a structured JSON "
                    "screening report with score, matched_skills, missing_skills, strengths, risks, "
                    "evidence, similar_jobs, similar_applications, recommendation, summary, "
                    "and experience_years."
                ),
                expected_output="Structured JSON screening report.",
                output_json=CVScreenerOutput,
                agent=agent,
            )
        if agent_name == AgentName.ASSESSOR:
            return Task(
                description=(
                    "Generate focused interview questions for this candidate and role. "
                    "Return JSON with questions, focus_areas, and question_provenance."
                ),
                expected_output="Structured JSON assessment plan.",
                output_json=AssessorOutput,
                agent=agent,
            )
        if agent_name == AgentName.SCHEDULER:
            return Task(
                description=(
                    "Propose interview slots and a concise outreach email draft. "
                    "Return JSON with scheduled_at, proposed_slots, and email_draft."
                ),
                expected_output="Structured JSON scheduling plan.",
                output_json=SchedulerOutput,
                agent=agent,
            )
        return Task(
            description=(
                "Draft a personalized offer note for this candidate and role. "
                "Return JSON with offer_text and summary."
            ),
            expected_output="Structured JSON offer draft.",
            output_json=OfferWriterOutput,
            agent=agent,
        )

    def _parse_output(self, crew_output: Any) -> dict[str, object]:
        """Normalize CrewAI output into a plain dict."""
        task_output = crew_output.tasks_output[0] if crew_output.tasks_output else None
        if task_output and task_output.json_dict:
            return dict(task_output.json_dict)
        if crew_output.json_dict:
            return dict(crew_output.json_dict)
        if task_output and task_output.pydantic:
            return task_output.pydantic.model_dump()
        if crew_output.pydantic:
            return crew_output.pydantic.model_dump()
        return json.loads(crew_output.raw)

    def _build_llm(self) -> LLM | None:
        """Return the configured CrewAI LLM, or None when local fallback should be used."""
        from app.core.config import settings

        if not settings.OPENAI_API_KEY:
            return None
        return LLM(
            model=self.model,
            api_key=settings.OPENAI_API_KEY,
            temperature=0,
            response_format={"type": "json_object"},
        )

    def _fallback_output(self, agent_name: AgentName, context: PipelineContext) -> dict[str, object]:
        """Produce deterministic outputs for local development and tests."""
        if agent_name == AgentName.CV_SCREENER:
            experience_years = ScreeningInsightsService.estimate_experience_years(
                context.candidate_resume_text
            )
            summary = (
                f"{context.candidate_name} matches {len(context.matched_skills)} tracked skills for "
                f"{context.job_title} with a similarity score of {context.similarity_score:.2f}."
            )
            return CVScreenerOutput(
                score=round(context.similarity_score, 4),
                matched_skills=context.matched_skills,
                missing_skills=context.missing_skills,
                strengths=context.screening_strengths,
                risks=context.screening_risks,
                evidence=context.screening_evidence,
                similar_jobs=context.similar_jobs,
                similar_applications=context.similar_applications,
                recommendation=self.recommendation(context),
                summary=summary,
                experience_years=experience_years,
            ).model_dump()
        if agent_name == AgentName.ASSESSOR:
            focus_areas = context.missing_skills or context.matched_skills[:2] or ["Problem Solving"]
            questions = [
                f"Walk through a project where you used {context.job_title}.",
                f"How would you approach a challenge involving {focus_areas[0]}?",
                "How do you balance delivery speed with maintainability in production systems?",
            ]
            question_provenance = [
                {
                    "question": questions[0],
                    "derived_from": "job_title",
                    "source_value": context.job_title,
                },
                {
                    "question": questions[1],
                    "derived_from": "skill_gap",
                    "source_value": focus_areas[0],
                },
                {
                    "question": questions[2],
                    "derived_from": "screening_risk",
                    "source_value": context.screening_risks[0]
                    if context.screening_risks
                    else "general engineering judgment",
                },
            ]
            return AssessorOutput(
                questions=questions,
                focus_areas=focus_areas,
                question_provenance=question_provenance,
            ).model_dump()
        if agent_name == AgentName.SCHEDULER:
            scheduled_at = context.scheduler_slots[0]
            return SchedulerOutput(
                scheduled_at=scheduled_at,
                proposed_slots=context.scheduler_slots,
                email_draft=(
                    f"Hi {context.candidate_name}, we'd love to schedule an interview for the "
                    f"{context.job_title} role."
                ),
            ).model_dump()
        return OfferWriterOutput(
            offer_text=(
                f"{context.candidate_name}, we're excited to move you forward for the "
                f"{context.job_title} role at {context.company_name}."
            ),
            summary="Personalized offer draft generated from role and screening context.",
        ).model_dump()

    @staticmethod
    def recommendation(context: PipelineContext) -> str:
        """Return a screening recommendation from the current context."""
        if context.similarity_score >= 0.8 and len(context.missing_skills) <= 2:
            return "proceed"
        if context.similarity_score >= 0.55:
            return "review"
        return "hold"

    @staticmethod
    def default_scheduler_slots() -> list[str]:
        """Return deterministic upcoming interview slots."""
        base = datetime.now(timezone.utc) + timedelta(days=3)
        return [
            base.isoformat(),
            (base + timedelta(hours=2)).isoformat(),
            (base + timedelta(days=1)).isoformat(),
        ]
