"""
Candidate ORM model.

Represents a job applicant. Includes a vector embedding of their resume
for semantic similarity search via pgvector.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Candidate(Base):
    """A candidate whose resume is embedded for semantic matching."""

    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_embedding = mapped_column(Vector(1536), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resume_file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────
    applications: Mapped[list["Application"]] = relationship(  # noqa: F821
        "Application",
        back_populates="candidate",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Candidate id={self.id} name={self.name!r} email={self.email!r}>"
