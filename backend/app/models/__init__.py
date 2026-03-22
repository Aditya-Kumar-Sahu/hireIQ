"""
Models package — import all ORM models here for Alembic discovery.

Alembic's env.py imports Base.metadata, and these imports ensure
all models are registered on the metadata before autogenerate runs.
"""

from app.models.agent_run import AgentName, AgentRun, AgentRunStatus
from app.models.application import Application, ApplicationStatus
from app.models.candidate import Candidate
from app.models.company import Company
from app.models.job import Job, JobSeniority, JobStatus
from app.models.user import User, UserRole

__all__ = [
    "AgentName",
    "AgentRun",
    "AgentRunStatus",
    "Application",
    "ApplicationStatus",
    "Candidate",
    "Company",
    "Job",
    "JobSeniority",
    "JobStatus",
    "User",
    "UserRole",
]
