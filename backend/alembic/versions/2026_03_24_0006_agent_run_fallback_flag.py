"""Add used_fallback to agent runs

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-24
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add fallback visibility to persisted agent runs."""
    op.add_column(
        "agent_runs",
        sa.Column("used_fallback", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    """Remove the fallback visibility flag."""
    op.drop_column("agent_runs", "used_fallback")
