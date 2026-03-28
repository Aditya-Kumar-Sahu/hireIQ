"""Shared pytest fixtures for backend integration tests."""

from __future__ import annotations

import asyncio
import fcntl
import os
from collections.abc import Generator
from pathlib import Path

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
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-at-least-32-chars")
os.environ["GEMINI_API_KEY"] = ""
os.environ["GOOGLE_API_KEY"] = ""
os.environ["R2_ACCOUNT_ID"] = ""
os.environ["R2_ACCESS_KEY_ID"] = ""
os.environ["R2_SECRET_ACCESS_KEY"] = ""
os.environ["R2_ENDPOINT_URL"] = ""

from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402


TEST_DATABASE_URL = os.environ["DATABASE_URL"]
TEST_STATE_LOCK_PATH = Path("/tmp/hireiq-test-state.lock")


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
    """Reset database state before each test under a cross-process lock."""
    TEST_STATE_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TEST_STATE_LOCK_PATH.open("w", encoding="utf-8") as lock_file:
        # Multiple pytest processes can run in parallel; serialize state resets.
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            async with db_session_factory() as session:
                await session.execute(
                    text(
                        "TRUNCATE TABLE "
                        "ats_webhook_events, agent_runs, applications, users, jobs, candidates, companies "
                        "RESTART IDENTITY CASCADE"
                    )
                )
                await session.commit()

            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


@pytest.fixture(autouse=True)
def reset_runtime_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep tests isolated from locally configured third-party credentials."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "")
    monkeypatch.setattr(settings, "R2_ACCOUNT_ID", "")
    monkeypatch.setattr(settings, "R2_ACCESS_KEY_ID", "")
    monkeypatch.setattr(settings, "R2_SECRET_ACCESS_KEY", "")
    monkeypatch.setattr(settings, "R2_ENDPOINT_URL", "")
    monkeypatch.setattr(settings, "R2_BUCKET_NAME", "hireiq-resumes")


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Yield a synchronous test client backed by the ASGI app."""
    with TestClient(app) as test_client:
        yield test_client
