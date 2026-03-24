"""CrewAI tool wrappers used by the application pipeline."""

from __future__ import annotations

import json
from typing import Any

from crewai.tools import BaseTool
from pydantic import PrivateAttr

from app.agents.crewai_runner import PipelineContext


class _ContextTool(BaseTool):
    """Base class for tools that operate over a precomputed pipeline context."""

    _context: PipelineContext = PrivateAttr()

    def __init__(self, context: PipelineContext, **data: Any) -> None:
        super().__init__(**data)
        self._context = context


class ApplicationContextTool(_ContextTool):
    """Expose normalized application context to CrewAI agents."""

    name: str = "application_context"
    description: str = "Return the normalized job and candidate context for the current application."

    def _run(self) -> str:
        return json.dumps(
            {
                "application_id": self._context.application_id,
                "company_name": self._context.company_name,
                "candidate_name": self._context.candidate_name,
                "candidate_email": self._context.candidate_email,
                "candidate_resume_text": self._context.candidate_resume_text,
                "job_title": self._context.job_title,
                "job_seniority": self._context.job_seniority,
                "job_description": self._context.job_description,
                "job_requirements": self._context.job_requirements,
            }
        )


class SimilarJobsTool(_ContextTool):
    """Expose top similar jobs for the candidate resume."""

    name: str = "similar_jobs_lookup"
    description: str = "Return the top similar jobs for the current candidate and their similarity scores."

    def _run(self) -> str:
        return json.dumps(self._context.similar_jobs)


class SimilarApplicationsTool(_ContextTool):
    """Expose historically similar applications."""

    name: str = "similar_applications_lookup"
    description: str = "Return past similar applications for the CV screener."

    def _run(self) -> str:
        return json.dumps(self._context.similar_applications)


class SkillGapTool(_ContextTool):
    """Expose matched and missing skills for the current application."""

    name: str = "skill_gap_analysis"
    description: str = "Return matched and missing skills between the resume and job requirements."

    def _run(self) -> str:
        return json.dumps(
            {
                "matched_skills": self._context.matched_skills,
                "missing_skills": self._context.missing_skills,
                "similarity_score": self._context.similarity_score,
                "strengths": self._context.screening_strengths,
                "risks": self._context.screening_risks,
                "evidence": self._context.screening_evidence,
            }
        )


class CalendarSlotsTool(_ContextTool):
    """Return deterministic interview slot suggestions."""

    name: str = "calendar_slot_suggestions"
    description: str = "Return candidate interview slot suggestions for the next few days."

    def _run(self) -> str:
        return json.dumps(self._context.scheduler_slots)


class OfferDraftTool(_ContextTool):
    """Return a structured starting point for offer drafting."""

    name: str = "offer_draft_context"
    description: str = "Return the current candidate, role, and recommendation context for the offer draft."

    def _run(self) -> str:
        return json.dumps(
            {
                "candidate_name": self._context.candidate_name,
                "job_title": self._context.job_title,
                "company_name": self._context.company_name,
                "recommendation": self._context.recommendation,
            }
        )


class EmailDeliveryTool(_ContextTool):
    """Expose active email-delivery configuration to the agent."""

    name: str = "email_delivery_context"
    description: str = "Return sender metadata and whether real email delivery is enabled."

    def _run(self) -> str:
        return json.dumps(
            {
                "delivery_mode": self._context.delivery_mode,
                "from_email": self._context.from_email,
            }
        )
