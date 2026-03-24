"""Scope candidates to companies

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-24
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add company ownership to candidates and backfill inferable rows."""
    op.add_column(
        "candidates",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_candidates_company_id_companies",
        "candidates",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_candidates_company_id"), "candidates", ["company_id"], unique=False)
    op.create_index(
        "ix_candidates_company_created_at",
        "candidates",
        ["company_id", "created_at"],
        unique=False,
    )

    op.execute(
        """
        UPDATE candidates
        SET company_id = scoped.company_id
        FROM (
            SELECT DISTINCT ON (applications.candidate_id)
                applications.candidate_id AS candidate_id,
                jobs.company_id AS company_id
            FROM applications
            JOIN jobs ON jobs.id = applications.job_id
            ORDER BY applications.candidate_id, jobs.company_id
        ) AS scoped
        WHERE candidates.id = scoped.candidate_id
          AND candidates.company_id IS NULL
        """
    )

    op.drop_constraint("uq_candidates_email", "candidates", type_="unique")
    op.drop_index(op.f("ix_candidates_email"), table_name="candidates")
    op.create_index(op.f("ix_candidates_email"), "candidates", ["email"], unique=False)
    op.create_unique_constraint(
        "uq_candidates_company_email",
        "candidates",
        ["company_id", "email"],
    )


def downgrade() -> None:
    """Remove company-scoped candidate ownership."""
    op.drop_constraint("uq_candidates_company_email", "candidates", type_="unique")
    op.drop_index("ix_candidates_company_created_at", table_name="candidates")
    op.drop_index(op.f("ix_candidates_company_id"), table_name="candidates")
    op.drop_constraint("fk_candidates_company_id_companies", "candidates", type_="foreignkey")
    op.drop_index(op.f("ix_candidates_email"), table_name="candidates")
    op.create_index(op.f("ix_candidates_email"), "candidates", ["email"], unique=True)
    op.create_unique_constraint("uq_candidates_email", "candidates", ["email"])
    op.drop_column("candidates", "company_id")
