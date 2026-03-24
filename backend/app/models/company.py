"""Company ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Company(Base):
    """A hiring company registered on the platform."""

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    culture_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_calendar_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_calendar_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_calendar_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    google_calendar_connected_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    google_calendar_calendar_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    jobs: Mapped[list["Job"]] = relationship(  # noqa: F821
        "Job",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    candidates: Mapped[list["Candidate"]] = relationship(  # noqa: F821
        "Candidate",
        back_populates="company",
        lazy="selectin",
    )
    users: Mapped[list["User"]] = relationship(  # noqa: F821
        "User",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name!r}>"
