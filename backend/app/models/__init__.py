"""Models package for Alembic discovery."""

from app.models.agent_run import AgentName, AgentRun, AgentRunStatus
from app.models.application import Application, ApplicationStatus
from app.models.ats_webhook_event import ATSWebhookEvent
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
    "ATSWebhookEvent",
    "Candidate",
    "Company",
    "Job",
    "JobSeniority",
    "JobStatus",
    "User",
    "UserRole",
]
