"""
Application ORM model.

Represents a candidate's application to a specific job.
Tracks the full pipeline status from submission through offer.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ApplicationStatus(str, enum.Enum):
    """Pipeline stages for an application."""

    SUBMITTED = "submitted"
    SCREENING = "screening"
    ASSESSED = "assessed"
    SCHEDULED = "scheduled"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"


class Application(Base):
    """A candidate's application to a job, tracking agent pipeline progress."""

    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("job_id", "candidate_id", name="uq_applications_job_candidate"),
        Index("ix_applications_job_status_created_at", "job_id", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(
            ApplicationStatus,
            name="application_status",
            create_constraint=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=ApplicationStatus.SUBMITTED,
        nullable=False,
        index=True,
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    screening_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessment_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    offer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────
    job: Mapped["Job"] = relationship(  # noqa: F821
        "Job",
        back_populates="applications",
    )
    candidate: Mapped["Candidate"] = relationship(  # noqa: F821
        "Candidate",
        back_populates="applications",
    )
    agent_runs: Mapped[list["AgentRun"]] = relationship(  # noqa: F821
        "AgentRun",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="AgentRun.created_at",
    )

    def __repr__(self) -> str:
        return f"<Application id={self.id} status={self.status}>"
