"""Create Phase 3 vector indexes

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-22
"""

from __future__ import annotations

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create HNSW indexes for cosine similarity search."""
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_jobs_embedding_hnsw "
        "ON jobs USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_candidates_resume_embedding_hnsw "
        "ON candidates USING hnsw (resume_embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Remove the Phase 3 vector indexes."""
    op.execute("DROP INDEX IF EXISTS ix_candidates_resume_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_jobs_embedding_hnsw")
