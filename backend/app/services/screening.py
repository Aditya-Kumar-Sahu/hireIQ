"""Richer retrieval and skill analysis for CV screening."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass

from google import genai
from google.genai import types
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.config import settings
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job, JobStatus

logger = logging.getLogger(__name__)

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python", "py"),
    "FastAPI": ("fastapi",),
    "Django": ("django",),
    "Flask": ("flask",),
    "SQLAlchemy": ("sqlalchemy",),
    "PostgreSQL": ("postgresql", "postgres"),
    "MySQL": ("mysql",),
    "SQLite": ("sqlite",),
    "MongoDB": ("mongodb", "mongo db", "mongo"),
    "Redis": ("redis",),
    "Docker": ("docker", "containerization"),
    "Kubernetes": ("kubernetes", "k8s"),
    "AWS": ("aws", "amazon web services"),
    "GCP": ("gcp", "google cloud platform", "google cloud"),
    "Azure": ("azure",),
    "Terraform": ("terraform",),
    "CI/CD": ("ci/cd", "cicd", "continuous integration", "continuous delivery"),
    "GitHub Actions": ("github actions",),
    "React": ("react",),
    "Next.js": ("next.js", "nextjs"),
    "TypeScript": ("typescript", "type script"),
    "JavaScript": ("javascript", "js"),
    "HTML": ("html",),
    "CSS": ("css",),
    "Tailwind CSS": ("tailwind", "tailwindcss", "tailwind css"),
    "Node.js": ("node.js", "nodejs", "node"),
    "Express": ("express", "expressjs"),
    "GraphQL": ("graphql",),
    "REST APIs": ("rest api", "restful api", "apis"),
    "Microservices": ("microservices", "microservice"),
    "System Design": ("system design",),
    "Testing": ("pytest", "jest", "testing", "test automation", "unit testing"),
    "Pytest": ("pytest",),
    "Playwright": ("playwright",),
    "Pandas": ("pandas",),
    "NumPy": ("numpy",),
    "Machine Learning": ("machine learning", "ml"),
    "LLMs": ("llm", "llms", "large language models"),
    "OpenAI": ("openai",),
    "Gemini": ("gemini", "google genai", "google ai studio"),
    "CrewAI": ("crewai",),
    "LangChain": ("langchain",),
    "Data Pipelines": ("etl", "elt", "data pipeline", "data pipelines"),
    "Airflow": ("airflow", "apache airflow"),
    "Spark": ("spark", "apache spark"),
    "Linux": ("linux",),
    "Agile": ("agile", "scrum", "kanban"),
    "Communication": ("communication", "stakeholder management"),
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


class SkillExtractionOutput(BaseModel):
    """Structured skill extraction payload returned by Gemini."""

    skills: list[str]


class SkillExtractionService:
    """Extract canonical skills from free text using Gemini with deterministic fallback."""

    def __init__(self) -> None:
        self._client = (
            genai.Client(api_key=settings.resolved_gemini_api_key)
            if settings.resolved_gemini_api_key
            else None
        )

    async def extract_skills(self, text: str) -> list[str]:
        """Return canonical skills found in the provided text."""
        fallback = self.extract_skills_fallback(text)
        normalized = self.normalize_text(text)
        if not normalized or self._client is None:
            return fallback

        try:
            remote_skills = await asyncio.to_thread(self._remote_extract_skills, normalized)
        except Exception:
            logger.exception("Gemini skill extraction failed; using deterministic fallback")
            return fallback

        return self._merge_skills(remote_skills, fallback)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize whitespace before extraction."""
        return " ".join(text.split()).strip()

    @staticmethod
    def canonical_skills() -> list[str]:
        """Return the supported canonical taxonomy."""
        return list(SKILL_ALIASES.keys())

    @classmethod
    def normalize_skill_name(cls, raw_skill: str) -> str | None:
        """Map a raw skill label back into the supported canonical taxonomy."""
        candidate = raw_skill.strip().lower()
        if not candidate:
            return None

        for canonical, aliases in SKILL_ALIASES.items():
            known_values = {canonical.lower(), *(alias.lower() for alias in aliases)}
            if candidate in known_values:
                return canonical
        return None

    @classmethod
    def extract_skills_fallback(cls, text: str) -> list[str]:
        """Extract canonical skills using deterministic alias matching."""
        haystack = cls.normalize_text(text).lower()
        found: list[str] = []
        for canonical, aliases in SKILL_ALIASES.items():
            if canonical.lower() in haystack or any(alias in haystack for alias in aliases):
                found.append(canonical)
        return found

    @classmethod
    def _merge_skills(cls, primary: list[str], secondary: list[str]) -> list[str]:
        """Deduplicate while preserving the higher-quality extractor ordering first."""
        merged: list[str] = []
        seen: set[str] = set()
        for skill in [*primary, *secondary]:
            canonical = cls.normalize_skill_name(skill) or skill
            if canonical not in SKILL_ALIASES or canonical in seen:
                continue
            seen.add(canonical)
            merged.append(canonical)
        return merged

    def _remote_extract_skills(self, text: str) -> list[str]:
        """Ask Gemini to extract skills using the supported canonical taxonomy."""
        assert self._client is not None
        response = self._client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=(
                "Extract only the relevant hard skills, frameworks, cloud platforms, tools, and "
                "seniority-relevant competencies from the text. Return strict JSON with a single "
                f"'skills' array using only these canonical values: {', '.join(self.canonical_skills())}.\n\n"
                f"TEXT:\n{text}"
            ),
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )
        payload = SkillExtractionOutput.model_validate(json.loads(response.text or "{}"))
        return [skill for skill in payload.skills if self.normalize_skill_name(skill)]


class ScreeningInsightsService:
    """Compute similarity, skill gaps, and historical context for CV screening."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.skill_extractor = SkillExtractionService()

    async def build_insights(self, application: Application) -> ScreeningInsights:
        """Compute the full CV-screener context for an application."""
        matched_skills, missing_skills = await self.analyze_skill_gap(
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

    async def analyze_skill_gap(self, *, job_text: str, resume_text: str) -> tuple[list[str], list[str]]:
        """Return matched and missing canonical skills."""
        job_skills = await self.skill_extractor.extract_skills(job_text)
        resume_skills = await self.skill_extractor.extract_skills(resume_text)
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
