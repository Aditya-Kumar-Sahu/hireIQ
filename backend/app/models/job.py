"""
Job ORM model.

Represents a job listing posted by a company. Includes a vector embedding
column for semantic similarity search via pgvector.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class JobStatus(str, enum.Enum):
    """Lifecycle status of a job listing."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class JobSeniority(str, enum.Enum):
    """Seniority level for a job."""

    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"


class Job(Base):
    """A job listing with an optional vector embedding for semantic search."""

    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_company_status_created_at", "company_id", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str] = mapped_column(Text, nullable=False)
    seniority: Mapped[JobSeniority] = mapped_column(
        Enum(
            JobSeniority,
            name="job_seniority",
            create_constraint=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=JobSeniority.MID,
        nullable=False,
    )
    embedding = mapped_column(Vector(1536), nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            name="job_status",
            create_constraint=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=JobStatus.DRAFT,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────
    company: Mapped["Company"] = relationship(  # noqa: F821
        "Company",
        back_populates="jobs",
    )
    applications: Mapped[list["Application"]] = relationship(  # noqa: F821
        "Application",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Job id={self.id} title={self.title!r} status={self.status}>"
