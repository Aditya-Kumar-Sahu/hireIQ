"""Shared pytest fixtures for backend integration tests."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Point the app at reachable services before importing app modules.
# On the host we use localhost; inside Docker Compose the existing env vars use service names.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://hireiq:hireiq_secret@127.0.0.1:5432/hireiq",
)
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ["GEMINI_API_KEY"] = ""
os.environ["GOOGLE_API_KEY"] = ""

from app.main import app  # noqa: E402


TEST_DATABASE_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create a dedicated event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_session_factory() -> async_sessionmaker[AsyncSession]:
    """Provide an async session factory bound to the local Postgres test database."""
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


@pytest.fixture(autouse=True)
async def reset_database(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Truncate mutable tables before each test for deterministic assertions."""
    async with db_session_factory() as session:
        await session.execute(
            text(
                "TRUNCATE TABLE "
                "ats_webhook_events, agent_runs, applications, users, jobs, candidates, companies "
                "RESTART IDENTITY CASCADE"
            )
        )
        await session.commit()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Yield a synchronous test client backed by the ASGI app."""
    with TestClient(app) as test_client:
        yield test_client
