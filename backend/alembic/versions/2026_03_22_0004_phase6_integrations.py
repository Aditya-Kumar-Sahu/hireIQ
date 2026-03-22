"""Add Phase 6 integration storage and webhook schema

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-22
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add company-scoped provider tokens, resume storage metadata, and ATS event logs."""
    op.add_column("companies", sa.Column("google_calendar_access_token", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("google_calendar_refresh_token", sa.Text(), nullable=True))
    op.add_column(
        "companies",
        sa.Column("google_calendar_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("google_calendar_connected_email", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "companies",
        sa.Column("google_calendar_calendar_id", sa.String(length=255), nullable=True),
    )

    op.add_column("candidates", sa.Column("resume_storage_key", sa.String(length=500), nullable=True))

    op.create_table(
        "ats_webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("external_event_id", sa.String(length=255), nullable=True),
        sa.Column("signature_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        op.f("ix_ats_webhook_events_provider"),
        "ats_webhook_events",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ats_webhook_events_event_type"),
        "ats_webhook_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ats_webhook_events_external_event_id"),
        "ats_webhook_events",
        ["external_event_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove Phase 6 integration schema objects."""
    op.drop_index(op.f("ix_ats_webhook_events_external_event_id"), table_name="ats_webhook_events")
    op.drop_index(op.f("ix_ats_webhook_events_event_type"), table_name="ats_webhook_events")
    op.drop_index(op.f("ix_ats_webhook_events_provider"), table_name="ats_webhook_events")
    op.drop_table("ats_webhook_events")

    op.drop_column("candidates", "resume_storage_key")

    op.drop_column("companies", "google_calendar_calendar_id")
    op.drop_column("companies", "google_calendar_connected_email")
    op.drop_column("companies", "google_calendar_token_expires_at")
    op.drop_column("companies", "google_calendar_refresh_token")
    op.drop_column("companies", "google_calendar_access_token")
