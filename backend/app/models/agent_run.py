"""
AgentRun ORM model.

Logs every AI agent execution for observability, cost tracking, and debugging.
Each run records the agent name, input/output, token usage, and latency.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AgentName(str, enum.Enum):
    """Identifiers for each CrewAI agent."""

    CV_SCREENER = "cv_screener"
    ASSESSOR = "assessor"
    SCHEDULER = "scheduler"
    OFFER_WRITER = "offer_writer"


class AgentRunStatus(str, enum.Enum):
    """Execution status of an agent run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRun(Base):
    """An individual agent execution record with full observability data."""

    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[AgentName] = mapped_column(
        Enum(AgentName, name="agent_name", create_constraint=True),
        nullable=False,
        index=True,
    )
    status: Mapped[AgentRunStatus] = mapped_column(
        Enum(AgentRunStatus, name="agent_run_status", create_constraint=True),
        default=AgentRunStatus.PENDING,
        nullable=False,
    )
    input: Mapped[str | None] = mapped_column(Text, nullable=True)
    output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────
    application: Mapped["Application"] = relationship(  # noqa: F821
        "Application",
        back_populates="agent_runs",
    )

    def __repr__(self) -> str:
        return f"<AgentRun id={self.id} agent={self.agent_name} status={self.status}>"
