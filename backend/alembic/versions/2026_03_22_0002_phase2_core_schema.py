"""Create Phase 2 core schema

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-22
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

job_seniority = postgresql.ENUM(
    "junior",
    "mid",
    "senior",
    "lead",
    name="job_seniority",
    create_type=False,
)
job_status = postgresql.ENUM("draft", "active", "closed", name="job_status", create_type=False)
application_status = postgresql.ENUM(
    "submitted",
    "screening",
    "assessed",
    "scheduled",
    "offered",
    "hired",
    "rejected",
    name="application_status",
    create_type=False,
)
agent_name = postgresql.ENUM(
    "cv_screener",
    "assessor",
    "scheduler",
    "offer_writer",
    name="agent_name",
    create_type=False,
)
agent_run_status = postgresql.ENUM(
    "pending",
    "running",
    "completed",
    "failed",
    name="agent_run_status",
    create_type=False,
)
user_role = postgresql.ENUM("recruiter", "admin", name="user_role", create_type=False)


def upgrade() -> None:
    """Create the relational schema used by the core Phase 2 API."""
    bind = op.get_bind()
    job_seniority.create(bind, checkfirst=True)
    job_status.create(bind, checkfirst=True)
    application_status.create(bind, checkfirst=True)
    agent_name.create(bind, checkfirst=True)
    agent_run_status.create(bind, checkfirst=True)
    user_role.create(bind, checkfirst=True)

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("culture_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_companies_name"), "companies", ["name"], unique=False)

    op.create_table(
        "candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("resume_embedding", Vector(1536), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("resume_file_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_candidates_email"),
    )
    op.create_index(op.f("ix_candidates_email"), "candidates", ["email"], unique=True)
    op.create_index(op.f("ix_candidates_name"), "candidates", ["name"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=False),
        sa.Column("seniority", job_seniority, nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("status", job_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_jobs_company_id"), "jobs", ["company_id"], unique=False)
    op.create_index(op.f("ix_jobs_status"), "jobs", ["status"], unique=False)
    op.create_index(op.f("ix_jobs_title"), "jobs", ["title"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index(op.f("ix_users_company_id"), "users", ["company_id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", application_status, nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("screening_notes", sa.Text(), nullable=True),
        sa.Column("assessment_result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("offer_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("job_id", "candidate_id", name="uq_applications_job_candidate"),
    )
    op.create_index(op.f("ix_applications_candidate_id"), "applications", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_applications_job_id"), "applications", ["job_id"], unique=False)
    op.create_index(op.f("ix_applications_status"), "applications", ["status"], unique=False)

    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_name", agent_name, nullable=False),
        sa.Column("status", agent_run_status, nullable=False),
        sa.Column("input", sa.Text(), nullable=True),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_agent_runs_agent_name"), "agent_runs", ["agent_name"], unique=False)
    op.create_index(op.f("ix_agent_runs_application_id"), "agent_runs", ["application_id"], unique=False)


def downgrade() -> None:
    """Drop the Phase 2 schema objects in reverse dependency order."""
    op.drop_index(op.f("ix_agent_runs_application_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_agent_name"), table_name="agent_runs")
    op.drop_table("agent_runs")

    op.drop_index(op.f("ix_applications_status"), table_name="applications")
    op.drop_index(op.f("ix_applications_job_id"), table_name="applications")
    op.drop_index(op.f("ix_applications_candidate_id"), table_name="applications")
    op.drop_table("applications")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_company_id"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_jobs_title"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_status"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_company_id"), table_name="jobs")
    op.drop_table("jobs")

    op.drop_index(op.f("ix_candidates_name"), table_name="candidates")
    op.drop_index(op.f("ix_candidates_email"), table_name="candidates")
    op.drop_table("candidates")

    op.drop_index(op.f("ix_companies_name"), table_name="companies")
    op.drop_table("companies")

    bind = op.get_bind()
    agent_run_status.drop(bind, checkfirst=True)
    agent_name.drop(bind, checkfirst=True)
    application_status.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
    job_status.drop(bind, checkfirst=True)
    job_seniority.drop(bind, checkfirst=True)
