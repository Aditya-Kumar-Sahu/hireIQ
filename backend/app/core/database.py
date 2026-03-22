"""
Async SQLAlchemy engine and session factory.

Provides:
- `engine`: the async engine connected to PostgreSQL.
- `async_session_factory`: a sessionmaker bound to that engine.
- `get_db()`: FastAPI dependency that yields an `AsyncSession`.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ── Engine ─────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# ── Session Factory ────────────────────────────────────────────────────
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Declarative Base ───────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


# ── FastAPI Dependency ─────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, automatically closing on exit."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
