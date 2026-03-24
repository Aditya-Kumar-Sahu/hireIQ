"""Add updated_at tracking to jobs

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-24
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add updated_at to jobs and backfill existing rows."""
    op.add_column("jobs", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE jobs SET updated_at = created_at WHERE updated_at IS NULL")
    op.alter_column(
        "jobs",
        "updated_at",
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )


def downgrade() -> None:
    """Remove updated_at from jobs."""
    op.drop_column("jobs", "updated_at")
