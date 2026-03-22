"""Tests for Phase 3 resume parsing, embeddings, and semantic search."""

from __future__ import annotations

from typing import Any

import fitz
import pytest
from fastapi.testclient import TestClient

from app.rag.embeddings import EmbeddingService
from app.rag.parser import ResumeParser


def _auth_headers(client: TestClient, email: str = "rag@example.com") -> dict[str, str]:
    """Create an authenticated recruiter session."""
    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "supersecure123",
            "company_name": "RAG Co",
        },
    )
    token = signup.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_resume_parser_extracts_text_from_pdf() -> None:
    """Resume parser should extract normalized text from PDF bytes."""
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Casey Candidate\nFastAPI Engineer")
    pdf_bytes = document.tobytes()
    document.close()

    parsed_text = ResumeParser().extract_text(pdf_bytes)

    assert "Casey Candidate" in parsed_text
    assert "FastAPI Engineer" in parsed_text


@pytest.mark.asyncio
async def test_embedding_service_is_cached_and_stable() -> None:
    """Embedding results should be deterministic and cached in Redis."""
    class FakeRedis:
        def __init__(self) -> None:
            self.store: dict[str, str] = {}

        async def get(self, key: str) -> str | None:
            return self.store.get(key)

        async def set(self, key: str, value: str, ex: int | None = None) -> None:
            self.store[key] = value

        async def exists(self, key: str) -> int:
            return int(key in self.store)

    service = EmbeddingService()
    service.redis = FakeRedis()
    text = "fastapi postgres docker"

    first = await service.embed_text(text)
    second = await service.embed_text(text)
    cache_key = service.build_cache_key(text)

    assert len(first) == service.dimension
    assert first == second
    assert await service.redis.exists(cache_key) == 1


def test_phase3_embeddings_and_semantic_search_flow(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Jobs and candidates receive embeddings and semantic search ranks the closest resume first."""

    async def fake_embed_text(self: EmbeddingService, text: str) -> list[float]:
        mapping: dict[str, list[float]] = {
            "Backend Engineer Build backend hiring systems with FastAPI. FastAPI PostgreSQL APIs": [1.0, 0.0, 0.0] + [0.0] * 1533,
            "Python backend engineer with FastAPI and PostgreSQL.": [0.95, 0.05, 0.0] + [0.0] * 1533,
            "Frontend React engineer with design systems.": [0.0, 1.0, 0.0] + [0.0] * 1533,
            "fastapi backend engineer": [1.0, 0.0, 0.0] + [0.0] * 1533,
        }
        return mapping[text]

    monkeypatch.setattr(EmbeddingService, "embed_text", fake_embed_text)

    headers = _auth_headers(client)

    job_response = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": "Backend Engineer",
            "description": "Build backend hiring systems with FastAPI.",
            "requirements": "FastAPI PostgreSQL APIs",
            "seniority": "mid",
        },
    )
    assert job_response.status_code == 200
    assert job_response.json()["data"]["has_embedding"] is True

    backend_candidate = client.post(
        "/api/v1/candidates",
        headers=headers,
        json={
            "name": "Backend Casey",
            "email": "backend@example.com",
            "resume_text": "Python backend engineer with FastAPI and PostgreSQL.",
        },
    )
    assert backend_candidate.status_code == 200
    assert backend_candidate.json()["data"]["has_embedding"] is True

    frontend_candidate = client.post(
        "/api/v1/candidates",
        headers=headers,
        json={
            "name": "Frontend Taylor",
            "email": "frontend@example.com",
            "resume_text": "Frontend React engineer with design systems.",
        },
    )
    assert frontend_candidate.status_code == 200
    assert frontend_candidate.json()["data"]["has_embedding"] is True

    search_response = client.get(
        "/api/v1/candidates/search?q=fastapi backend engineer",
        headers=headers,
    )
    assert search_response.status_code == 200
    search_results: list[dict[str, Any]] = search_response.json()["data"]

    assert len(search_results) == 2
    assert search_results[0]["candidate"]["email"] == "backend@example.com"
    assert search_results[0]["similarity_score"] > search_results[1]["similarity_score"]
