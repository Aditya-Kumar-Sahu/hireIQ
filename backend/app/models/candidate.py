"""Candidate ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Candidate(Base):
    """A candidate whose resume is embedded for semantic matching."""

    __tablename__ = "candidates"
    __table_args__ = (
        UniqueConstraint("company_id", "email", name="uq_candidates_company_email"),
        Index("ix_candidates_company_created_at", "company_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_embedding = mapped_column(Vector(1536), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resume_file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resume_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    applications: Mapped[list["Application"]] = relationship(  # noqa: F821
        "Application",
        back_populates="candidate",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    company: Mapped["Company | None"] = relationship(  # noqa: F821
        "Company",
        back_populates="candidates",
    )

    def __repr__(self) -> str:
        return f"<Candidate id={self.id} name={self.name!r} email={self.email!r}>"
