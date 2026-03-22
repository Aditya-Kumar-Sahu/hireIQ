"""Add Phase 7 performance indexes

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-22
"""

from __future__ import annotations

from typing import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add compound indexes for the hottest list and observability queries."""
    op.create_index(
        "ix_jobs_company_status_created_at",
        "jobs",
        ["company_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_applications_job_status_created_at",
        "applications",
        ["job_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_agent_runs_application_created_at",
        "agent_runs",
        ["application_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_ats_webhook_events_provider_received_at",
        "ats_webhook_events",
        ["provider", "received_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the Phase 7 performance indexes."""
    op.drop_index("ix_ats_webhook_events_provider_received_at", table_name="ats_webhook_events")
    op.drop_index("ix_agent_runs_application_created_at", table_name="agent_runs")
    op.drop_index("ix_applications_job_status_created_at", table_name="applications")
    op.drop_index("ix_jobs_company_status_created_at", table_name="jobs")
