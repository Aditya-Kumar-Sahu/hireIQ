"""Integration tests for Phase 6 provider flows and external ingestion."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.company import Company


def _auth_headers(client: TestClient, email: str = "phase6@example.com") -> dict[str, str]:
    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "supersecure123",
            "company_name": "Phase 6 Co",
        },
    )
    token = signup.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _sign_webhook(secret: str, payload: dict[str, Any]) -> str:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_google_calendar_oauth_flow_persists_company_connection(
    client: TestClient,
    event_loop,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A recruiter can generate an auth URL and complete the Google OAuth token exchange."""
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "google-client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "google-client-secret")
    monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost:3000/api/auth/google/callback")

    headers = _auth_headers(client, "calendar@example.com")

    authorize_response = client.get(
        "/api/v1/integrations/google-calendar/authorize",
        headers=headers,
    )

    assert authorize_response.status_code == 200
    authorize_payload = authorize_response.json()["data"]
    assert "accounts.google.com" in authorize_payload["authorization_url"]
    assert authorize_payload["state"]

    monkeypatch.setattr(
        "app.services.google_oauth.GoogleOAuthService.exchange_code",
        lambda self, code, redirect_uri: {
            "access_token": "access-token-123",
            "refresh_token": "refresh-token-123",
            "expires_in": 3600,
            "scope": "openid email https://www.googleapis.com/auth/calendar.events",
            "token_type": "Bearer",
            "id_token": "stub-id-token",
        },
    )
    monkeypatch.setattr(
        "app.services.google_oauth.GoogleOAuthService.fetch_user_identity",
        lambda self, access_token: {
            "email": "recruiter@phase6.example",
            "calendar_id": "primary",
        },
    )

    callback_response = client.post(
        "/api/v1/integrations/google-calendar/callback",
        headers=headers,
        json={
            "code": "google-code-123",
            "state": authorize_payload["state"],
        },
    )
    assert callback_response.status_code == 200
    callback_payload = callback_response.json()["data"]
    assert callback_payload["connected"] is True
    assert callback_payload["provider"] == "google_calendar"
    assert callback_payload["calendar_id"] == "primary"
    assert callback_payload["connected_email"] == "recruiter@phase6.example"

    meta_response = client.get("/api/v1/meta/integrations", headers=headers)
    assert meta_response.status_code == 200
    assert meta_response.json()["data"]["google_calendar_enabled"] is True
    assert (
        meta_response.json()["data"]["google_calendar_connected_email"]
        == "recruiter@phase6.example"
    )

    async def verify_company_tokens() -> None:
        engine = create_async_engine(settings.DATABASE_URL, future=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            company = await session.scalar(select(Company))
            assert company is not None
            assert company.google_calendar_refresh_token == "refresh-token-123"
            assert company.google_calendar_access_token == "access-token-123"
            assert company.google_calendar_calendar_id == "primary"
            assert company.google_calendar_connected_email == "recruiter@phase6.example"
        await engine.dispose()

    event_loop.run_until_complete(verify_company_tokens())


def test_resume_pdf_upload_stores_file_and_exposes_download_url(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PDF ingest should parse text, store the original file, and expose a download route."""
    headers = _auth_headers(client, "storage@example.com")

    monkeypatch.setattr(
        "app.rag.parser.ResumeParser.extract_text",
        lambda self, file_bytes: "Parsed PDF resume text with FastAPI and PostgreSQL experience.",
    )
    monkeypatch.setattr(
        "app.services.storage.R2ResumeStorageService.upload_resume",
        lambda self, *, company_id, filename, file_bytes: {
            "storage_key": f"companies/{company_id}/resumes/casey-resume.pdf",
            "content_type": "application/pdf",
            "size_bytes": len(file_bytes),
        },
    )
    monkeypatch.setattr(
        "app.services.storage.R2ResumeStorageService.download_resume",
        lambda self, storage_key: {
            "filename": "casey-resume.pdf",
            "content_type": "application/pdf",
            "file_bytes": b"%PDF-1.4 fake resume bytes",
        },
    )

    response = client.post(
        "/api/v1/candidates",
        headers=headers,
        files={
            "resume": ("casey-resume.pdf", b"%PDF-1.4 fake resume bytes", "application/pdf"),
        },
        data={
            "name": "Casey Resume",
            "email": "casey.resume@example.com",
            "linkedin_url": "https://linkedin.com/in/casey-resume",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["resume_file_url"] == f"/api/v1/candidates/{payload['id']}/resume"
    assert payload["has_embedding"] is True

    detail_response = client.get(
        f"/api/v1/candidates/{payload['id']}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    assert "Parsed PDF resume text" in detail_response.json()["data"]["resume_text"]

    download_response = client.get(payload["resume_file_url"], headers=headers)
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"
    assert download_response.content == b"%PDF-1.4 fake resume bytes"


def test_ats_webhook_requires_valid_signature_and_persists_event(
    client: TestClient,
    event_loop,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ATS webhook deliveries are signature-verified before being persisted."""
    secret = "ats-secret-value"
    monkeypatch.setattr(settings, "ATS_WEBHOOK_SECRET", secret)

    invalid_response = client.post(
        "/api/v1/integrations/ats/webhooks/greenhouse",
        headers={"X-HireIQ-Signature": "sha256=invalid"},
        json={"event_type": "application.created", "data": {"external_id": "app_123"}},
    )
    assert invalid_response.status_code == 401

    payload = {
        "event_type": "application.created",
        "event_id": "evt_123",
        "data": {
            "application_id": "app_123",
            "candidate_email": "webhook@example.com",
        },
    }
    response = client.post(
        "/api/v1/integrations/ats/webhooks/greenhouse",
        headers={"X-HireIQ-Signature": _sign_webhook(secret, payload)},
        content=json.dumps(payload, separators=(",", ":"), sort_keys=True),
    )

    assert response.status_code == 200
    response_payload = response.json()["data"]
    assert response_payload["accepted"] is True
    assert response_payload["provider"] == "greenhouse"
    assert response_payload["event_type"] == "application.created"

    async def verify_webhook_event() -> None:
        from app.models.ats_webhook_event import ATSWebhookEvent

        engine = create_async_engine(settings.DATABASE_URL, future=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            event = await session.scalar(select(ATSWebhookEvent))
            assert event is not None
            assert event.provider == "greenhouse"
            assert event.event_type == "application.created"
            assert event.external_event_id == "evt_123"
            assert event.payload["data"]["candidate_email"] == "webhook@example.com"
        await engine.dispose()

    event_loop.run_until_complete(verify_webhook_event())
