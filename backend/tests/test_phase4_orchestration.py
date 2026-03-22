"""Tests for initial Phase 4 orchestration and agent run logging."""

from __future__ import annotations

from typing import Any

import pytest
from crewai import Agent
from crewai.tools import BaseTool
from fastapi.testclient import TestClient

from app.agents.crewai_runner import CrewAIPipelineRunner, PipelineContext
from app.models.agent_run import AgentName
from app.rag.embeddings import EmbeddingService


def _auth_headers(client: TestClient, email: str = "phase4@example.com") -> dict[str, str]:
    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "supersecure123",
            "company_name": "Agents Co",
        },
    )
    token = signup.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _embedding_vector(x: float, y: float, z: float) -> list[float]:
    return [x, y, z] + [0.0] * 1533


def test_application_submission_triggers_agent_pipeline_and_logs_runs(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Submitting an application should orchestrate agent runs and persist their outputs."""

    async def fake_embed_job_text(self: EmbeddingService, text: str) -> list[float]:
        return _embedding_vector(1.0, 0.0, 0.0)

    async def fake_embed_text(self: EmbeddingService, text: str) -> list[float]:
        return _embedding_vector(0.98, 0.02, 0.0)

    monkeypatch.setattr(EmbeddingService, "embed_job_text", fake_embed_job_text)
    monkeypatch.setattr(EmbeddingService, "embed_text", fake_embed_text)

    headers = _auth_headers(client)

    job = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": "Backend Engineer",
            "description": "Build backend APIs and workflow tooling.",
            "requirements": "FastAPI PostgreSQL Docker communication",
            "seniority": "mid",
        },
    ).json()["data"]

    candidate = client.post(
        "/api/v1/candidates",
        headers=headers,
        json={
            "name": "Agent Casey",
            "email": "agent.casey@example.com",
            "resume_text": "Backend engineer with FastAPI and PostgreSQL experience.",
        },
    ).json()["data"]

    previous_candidate = client.post(
        "/api/v1/candidates",
        headers=headers,
        json={
            "name": "Earlier Casey",
            "email": "earlier.casey@example.com",
            "resume_text": "Backend engineer with FastAPI and PostgreSQL experience.",
        },
    ).json()["data"]

    previous_application = client.post(
        "/api/v1/applications",
        headers=headers,
        json={"job_id": job["id"], "candidate_id": previous_candidate["id"]},
    )
    assert previous_application.status_code == 200

    application_response = client.post(
        "/api/v1/applications",
        headers=headers,
        json={"job_id": job["id"], "candidate_id": candidate["id"]},
    )
    assert application_response.status_code == 200

    detail_response = client.get(
        f"/api/v1/applications/{application_response.json()['data']['id']}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    detail_payload: dict[str, Any] = detail_response.json()["data"]

    assert detail_payload["status"] == "offered"
    assert detail_payload["score"] is not None
    assert detail_payload["assessment_result"] is not None
    assert detail_payload["offer_text"]

    agent_runs = detail_payload["agent_runs"]
    assert len(agent_runs) == 4
    assert [agent_run["agent_name"] for agent_run in agent_runs] == [
        "cv_screener",
        "assessor",
        "scheduler",
        "offer_writer",
    ]
    assert all(agent_run["status"] == "completed" for agent_run in agent_runs)
    cv_screener_output = agent_runs[0]["output"]
    assert "matched_skills" in cv_screener_output
    assert "missing_skills" in cv_screener_output
    assert "similar_jobs" in cv_screener_output
    assert "similar_applications" in cv_screener_output
    assert len(cv_screener_output["similar_applications"]) >= 1


def test_application_status_sse_stream_replays_pipeline_events(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The SSE status endpoint should replay queued and agent progress events."""

    async def fake_embed_job_text(self: EmbeddingService, text: str) -> list[float]:
        return _embedding_vector(1.0, 0.0, 0.0)

    async def fake_embed_text(self: EmbeddingService, text: str) -> list[float]:
        return _embedding_vector(0.98, 0.02, 0.0)

    monkeypatch.setattr(EmbeddingService, "embed_job_text", fake_embed_job_text)
    monkeypatch.setattr(EmbeddingService, "embed_text", fake_embed_text)

    headers = _auth_headers(client, "sse@example.com")

    job = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": "Backend Engineer",
            "description": "Build backend APIs and workflow tooling.",
            "requirements": "FastAPI PostgreSQL Docker communication",
            "seniority": "mid",
        },
    ).json()["data"]

    candidate = client.post(
        "/api/v1/candidates",
        headers=headers,
        json={
            "name": "SSE Casey",
            "email": "sse.casey@example.com",
            "resume_text": "Backend engineer with FastAPI and PostgreSQL experience.",
        },
    ).json()["data"]

    application_id = client.post(
        "/api/v1/applications",
        headers=headers,
        json={"job_id": job["id"], "candidate_id": candidate["id"]},
    ).json()["data"]["id"]

    response = client.get(f"/api/v1/applications/{application_id}/status", headers=headers)
    assert response.status_code == 200
    body = response.text

    assert "event: queued" in body
    assert "event: stage" in body
    assert "cv_screener" in body
    assert "offer_writer" in body
    assert "event: complete" in body


def test_crewai_runner_builds_real_agents_and_tools() -> None:
    """CrewAI runner should expose real CrewAI agents wired with tool wrappers."""
    context = PipelineContext(
        application_id="app-123",
        company_name="HireIQ",
        candidate_name="Casey Candidate",
        candidate_email="casey@example.com",
        candidate_resume_text="FastAPI PostgreSQL Docker communication",
        job_title="Backend Engineer",
        job_description="Build backend APIs.",
        job_requirements="FastAPI PostgreSQL Docker",
        similarity_score=0.91,
        matched_skills=["FastAPI", "PostgreSQL"],
        missing_skills=["Docker"],
        similar_jobs=[],
        similar_applications=[],
    )

    agents = CrewAIPipelineRunner().build_agents(context)

    assert set(agents.keys()) == {
        AgentName.CV_SCREENER,
        AgentName.ASSESSOR,
        AgentName.SCHEDULER,
        AgentName.OFFER_WRITER,
    }
    assert all(isinstance(agent, Agent) for agent in agents.values())
    assert any(isinstance(tool, BaseTool) for tool in agents[AgentName.CV_SCREENER].tools)
