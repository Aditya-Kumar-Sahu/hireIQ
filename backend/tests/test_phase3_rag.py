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


def _embedding_vector(x: float, y: float, z: float) -> list[float]:
    """Build a 1536-dim test vector with the first 3 dimensions populated."""
    return [x, y, z] + [0.0] * 1533


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

    async def fake_embed_job_text(self: EmbeddingService, text: str) -> list[float]:
        mapping: dict[str, list[float]] = {
            "Backend Engineer\nBuild backend hiring systems with FastAPI.\nFastAPI PostgreSQL APIs": _embedding_vector(1.0, 0.0, 0.0),
        }
        return mapping[text]

    async def fake_embed_text(self: EmbeddingService, text: str) -> list[float]:
        mapping: dict[str, list[float]] = {
            "Python backend engineer with FastAPI and PostgreSQL.": _embedding_vector(0.95, 0.05, 0.0),
            "Frontend React engineer with design systems.": _embedding_vector(0.0, 1.0, 0.0),
            "fastapi backend engineer": _embedding_vector(1.0, 0.0, 0.0),
        }
        return mapping[text]

    monkeypatch.setattr(EmbeddingService, "embed_job_text", fake_embed_job_text)
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
    assert job_response.status_code == 201
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
    assert backend_candidate.status_code == 201
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
    assert frontend_candidate.status_code == 201
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


def test_candidate_pdf_upload_parses_resume_and_generates_embedding(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Multipart candidate ingest should parse PDF text and embed the extracted resume."""

    async def fake_embed_text(self: EmbeddingService, text: str) -> list[float]:
        assert "Casey Candidate" in text
        return _embedding_vector(1.0, 0.0, 0.0)

    monkeypatch.setattr(EmbeddingService, "embed_text", fake_embed_text)

    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Casey Candidate\nFastAPI Engineer")
    pdf_bytes = document.tobytes()
    document.close()

    headers = _auth_headers(client, "pdf-upload@example.com")
    response = client.post(
        "/api/v1/candidates",
        headers=headers,
        files={"resume": ("resume.pdf", pdf_bytes, "application/pdf")},
        data={
            "name": "Casey Candidate",
            "email": "pdf.candidate@example.com",
            "linkedin_url": "https://linkedin.com/in/pdf-candidate",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["has_embedding"] is True

    detail = client.get(f"/api/v1/candidates/{payload['id']}", headers=headers)
    assert detail.status_code == 200
    assert "Casey Candidate" in detail.json()["data"]["resume_text"]


def test_similar_jobs_for_candidate_and_application(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Candidates and applications should be able to retrieve similar jobs by vector score."""

    async def fake_embed_job_text(self: EmbeddingService, text: str) -> list[float]:
        mapping: dict[str, list[float]] = {
            "Backend Engineer\nBuild backend APIs with FastAPI.\nFastAPI PostgreSQL APIs": _embedding_vector(1.0, 0.0, 0.0),
            "Frontend Engineer\nBuild UI workflows with React.\nReact TypeScript Design Systems": _embedding_vector(0.0, 1.0, 0.0),
        }
        return mapping[text]

    async def fake_embed_text(self: EmbeddingService, text: str) -> list[float]:
        mapping: dict[str, list[float]] = {
            "Python backend engineer with FastAPI.": _embedding_vector(0.98, 0.02, 0.0),
        }
        return mapping[text]

    monkeypatch.setattr(EmbeddingService, "embed_job_text", fake_embed_job_text)
    monkeypatch.setattr(EmbeddingService, "embed_text", fake_embed_text)

    headers = _auth_headers(client, "similar-jobs@example.com")

    backend_job = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": "Backend Engineer",
            "description": "Build backend APIs with FastAPI.",
            "requirements": "FastAPI PostgreSQL APIs",
            "seniority": "mid",
        },
    ).json()["data"]

    client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": "Frontend Engineer",
            "description": "Build UI workflows with React.",
            "requirements": "React TypeScript Design Systems",
            "seniority": "mid",
        },
    )

    candidate = client.post(
        "/api/v1/candidates",
        headers=headers,
        json={
            "name": "Sam Search",
            "email": "sam.search@example.com",
            "resume_text": "Python backend engineer with FastAPI.",
        },
    ).json()["data"]

    candidate_matches = client.get(
        f"/api/v1/candidates/{candidate['id']}/similar-jobs",
        headers=headers,
    )
    assert candidate_matches.status_code == 200
    candidate_results: list[dict[str, Any]] = candidate_matches.json()["data"]
    assert candidate_results[0]["job"]["id"] == backend_job["id"]

    application = client.post(
        "/api/v1/applications",
        headers=headers,
        json={"job_id": backend_job["id"], "candidate_id": candidate["id"]},
    ).json()["data"]

    application_matches = client.get(
        f"/api/v1/applications/{application['id']}/similar-jobs",
        headers=headers,
    )
    assert application_matches.status_code == 200
    application_results: list[dict[str, Any]] = application_matches.json()["data"]
    assert application_results[0]["job"]["id"] == backend_job["id"]
