"""Enable pgvector extension

Revision ID: 0001
Revises: None
Create Date: 2025-03-22

"""
from __future__ import annotations

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable the pgvector extension for vector similarity search."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Remove the pgvector extension."""
    op.execute("DROP EXTENSION IF EXISTS vector")
