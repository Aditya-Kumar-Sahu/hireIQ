"""Richer retrieval and skill analysis for CV screening."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job, JobStatus

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "FastAPI": ("fastapi",),
    "SQLAlchemy": ("sqlalchemy",),
    "PostgreSQL": ("postgresql", "postgres"),
    "Docker": ("docker",),
    "Redis": ("redis",),
    "React": ("react",),
    "TypeScript": ("typescript", "type script"),
    "GraphQL": ("graphql",),
    "Kubernetes": ("kubernetes", "k8s"),
    "CrewAI": ("crewai",),
    "OpenAI": ("openai",),
    "Gemini": ("gemini", "google genai", "google ai studio"),
    "Next.js": ("next.js", "nextjs"),
}


@dataclass(slots=True)
class ScreeningInsights:
    """Screening-specific retrieval and skill gap context."""

    similarity_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    risks: list[str]
    evidence: list[str]
    similar_jobs: list[dict[str, object]]
    similar_applications: list[dict[str, object]]


class ScreeningInsightsService:
    """Compute similarity, skill gaps, and historical context for CV screening."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def build_insights(self, application: Application) -> ScreeningInsights:
        """Compute the full CV-screener context for an application."""
        matched_skills, missing_skills = self.analyze_skill_gap(
            job_text=f"{application.job.description}\n{application.job.requirements}",
            resume_text=application.candidate.resume_text or "",
        )
        similar_jobs = await self._similar_jobs(application)
        similar_applications = await self._similar_applications(application)
        similarity_score = self.cosine_similarity(
            application.job.embedding,
            application.candidate.resume_embedding,
        )
        strengths = self.build_strengths(
            similarity_score=similarity_score,
            matched_skills=matched_skills,
            similar_jobs=similar_jobs,
        )
        risks = self.build_risks(
            similarity_score=similarity_score,
            missing_skills=missing_skills,
            similar_applications=similar_applications,
        )
        evidence = self.build_evidence(
            similarity_score=similarity_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            similar_applications=similar_applications,
        )
        return ScreeningInsights(
            similarity_score=similarity_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            strengths=strengths,
            risks=risks,
            evidence=evidence,
            similar_jobs=similar_jobs,
            similar_applications=similar_applications,
        )

    @staticmethod
    def analyze_skill_gap(*, job_text: str, resume_text: str) -> tuple[list[str], list[str]]:
        """Return matched and missing canonical skills."""
        job_skills = ScreeningInsightsService.extract_skills(job_text)
        resume_skills = ScreeningInsightsService.extract_skills(resume_text)
        matched = [skill for skill in job_skills if skill in resume_skills]
        missing = [skill for skill in job_skills if skill not in resume_skills]
        return matched, missing

    async def _similar_jobs(self, application: Application) -> list[dict[str, object]]:
        """Return top similar jobs for the candidate within the same company."""
        if application.candidate.resume_embedding is None:
            return []

        similarity_score = (1 - Job.embedding.cosine_distance(application.candidate.resume_embedding)).label(
            "similarity_score"
        )
        result = await self.db.execute(
            select(Job, similarity_score)
            .where(
                Job.company_id == application.job.company_id,
                Job.embedding.is_not(None),
                Job.status != JobStatus.CLOSED,
            )
            .order_by(Job.embedding.cosine_distance(application.candidate.resume_embedding))
            .limit(3)
        )
        return [
            {
                "job_id": str(job.id),
                "title": job.title,
                "similarity_score": float(score),
            }
            for job, score in result.all()
        ]

    async def _similar_applications(self, application: Application) -> list[dict[str, object]]:
        """Return top historical applications with similar resume embeddings."""
        if application.candidate.resume_embedding is None:
            return []

        other_candidate = aliased(Candidate)
        other_job = aliased(Job)
        similarity_score = (
            1 - other_candidate.resume_embedding.cosine_distance(application.candidate.resume_embedding)
        ).label("similarity_score")
        result = await self.db.execute(
            select(Application, other_candidate.name, other_job.title, similarity_score)
            .join(other_candidate, Application.candidate_id == other_candidate.id)
            .join(other_job, Application.job_id == other_job.id)
            .where(
                Application.id != application.id,
                other_job.company_id == application.job.company_id,
                other_candidate.resume_embedding.is_not(None),
            )
            .order_by(other_candidate.resume_embedding.cosine_distance(application.candidate.resume_embedding))
            .limit(3)
        )
        return [
            {
                "application_id": str(other_application.id),
                "candidate_name": candidate_name,
                "job_title": job_title,
                "status": other_application.status.value,
                "score": other_application.score,
                "similarity_score": float(score),
            }
            for other_application, candidate_name, job_title, score in result.all()
        ]

    @staticmethod
    def extract_skills(text: str) -> list[str]:
        """Extract canonical skills from free text."""
        haystack = text.lower()
        found: list[str] = []
        for canonical, aliases in SKILL_ALIASES.items():
            if any(alias in haystack for alias in aliases):
                found.append(canonical)
        return found

    @staticmethod
    def estimate_experience_years(text: str) -> int:
        """Estimate years of experience from resume text using simple regexes."""
        matches = re.findall(r"(\d+)\+?\s+years?", text.lower())
        if not matches:
            return 0
        return max(int(value) for value in matches)

    @staticmethod
    def build_strengths(
        *,
        similarity_score: float,
        matched_skills: list[str],
        similar_jobs: list[dict[str, object]],
    ) -> list[str]:
        """Summarize the strongest positive fit signals."""
        strengths: list[str] = []
        if matched_skills:
            strengths.append(f"Matched skills: {', '.join(matched_skills[:4])}")
        if similarity_score >= 0.8:
            strengths.append(f"High semantic fit score ({similarity_score:.2f})")
        if similar_jobs:
            strengths.append(f"Closest internal role match: {similar_jobs[0]['title']}")
        return strengths or ["Resume provides enough signal for recruiter review"]

    @staticmethod
    def build_risks(
        *,
        similarity_score: float,
        missing_skills: list[str],
        similar_applications: list[dict[str, object]],
    ) -> list[str]:
        """Summarize the main candidate risks."""
        risks: list[str] = []
        if missing_skills:
            risks.append(f"Missing tracked skills: {', '.join(missing_skills[:4])}")
        if similarity_score < 0.6:
            risks.append(f"Lower semantic fit score ({similarity_score:.2f})")
        if similar_applications and similar_applications[0].get("score") is not None:
            risks.append("Historical matches should be reviewed before making a final decision")
        return risks or ["No major structured risks detected from the current screening heuristics"]

    @staticmethod
    def build_evidence(
        *,
        similarity_score: float,
        matched_skills: list[str],
        missing_skills: list[str],
        similar_applications: list[dict[str, object]],
    ) -> list[str]:
        """Return short evidence points used by the screener."""
        evidence = [
            f"Similarity score: {similarity_score:.2f}",
            f"Matched skill count: {len(matched_skills)}",
            f"Missing skill count: {len(missing_skills)}",
        ]
        if similar_applications:
            evidence.append(
                "Most similar past application: "
                f"{similar_applications[0]['candidate_name']} for {similar_applications[0]['job_title']}"
            )
        return evidence

    @staticmethod
    def cosine_similarity(job_embedding: list[float] | None, resume_embedding: list[float] | None) -> float:
        """Compute cosine similarity for generic numeric sequences."""
        if job_embedding is None or resume_embedding is None:
            return 0.0

        job_values = [float(value) for value in job_embedding]
        resume_values = [float(value) for value in resume_embedding]
        if not job_values or not resume_values:
            return 0.0

        dot = sum(a * b for a, b in zip(job_values, resume_values, strict=True))
        job_norm = sum(value * value for value in job_values) ** 0.5
        resume_norm = sum(value * value for value in resume_values) ** 0.5
        if job_norm == 0 or resume_norm == 0:
            return 0.0
        return max(min(dot / (job_norm * resume_norm), 1.0), -1.0)
