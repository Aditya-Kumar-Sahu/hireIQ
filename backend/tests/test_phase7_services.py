"""Unit tests for Phase 7 service, tool, and deployment-facing polish."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import fitz
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.agents.crewai_runner import CVScreenerOutput, CrewAIPipelineRunner, PipelineContext
from app.core.config import Settings, settings
from app.core.exceptions import ServiceUnavailableException
from app.rag.embeddings import EmbeddingService
from app.services.ats_webhooks import ATSWebhookService
from app.services.calendar import BusyWindow, GoogleCalendarService
from app.services.email import ResendEmailService
from app.services.progress import ApplicationProgressService
from app.services.storage import R2ResumeStorageService
from app.tools.recruitment_tools import (
    ApplicationContextTool,
    CalendarSlotsTool,
    EmailDeliveryTool,
    OfferDraftTool,
    SimilarApplicationsTool,
    SimilarJobsTool,
    SkillGapTool,
)


class FakeRedis:
    """Minimal async Redis stub for progress-service unit tests."""

    def __init__(self) -> None:
        self.store: dict[str, list[str]] = {}

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)

    async def rpush(self, key: str, value: str) -> None:
        self.store.setdefault(key, []).append(value)

    async def expire(self, key: str, ttl_seconds: int) -> None:
        self.store.setdefault(key, [])

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        values = self.store.get(key, [])
        if end == -1:
            return values[start:]
        return values[start : end + 1]


def _build_context() -> PipelineContext:
    """Return a representative pipeline context for tool and runner tests."""
    return PipelineContext(
        application_id="app-123",
        company_name="HireIQ",
        candidate_name="Casey Candidate",
        candidate_email="casey@example.com",
        candidate_resume_text="Python FastAPI PostgreSQL Redis",
        job_title="Platform Engineer",
        job_description="Build APIs and delivery workflows.",
        job_requirements="Python FastAPI PostgreSQL Redis",
        similarity_score=0.82,
        matched_skills=["Python", "FastAPI"],
        missing_skills=["Redis"],
        screening_strengths=["Strong API background"],
        screening_risks=["Redis depth needs validation"],
        screening_evidence=["Similarity score: 0.82"],
        similar_jobs=[
            {"job_id": "job-1", "title": "Backend Engineer", "similarity_score": 0.91},
        ],
        similar_applications=[
            {
                "application_id": "app-prev",
                "candidate_name": "Earlier Casey",
                "job_title": "Backend Engineer",
                "similarity_score": 0.88,
            }
        ],
        recommendation="proceed",
        scheduler_slots=["2026-03-25T10:00:00+00:00"],
        delivery_mode="preview",
        from_email="noreply@hireiq.dev",
    )


@pytest.mark.asyncio
async def test_progress_service_publishes_lists_and_formats_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Progress events should round-trip through Redis and SSE formatting."""
    from app.services import progress as progress_module

    fake_redis = FakeRedis()
    monkeypatch.setattr(progress_module, "redis_client", fake_redis)

    service = ApplicationProgressService()
    application_id = uuid4()

    await service.reset(application_id)
    await service.publish(application_id, "queued", {"status": "submitted"})
    await service.publish(application_id, "complete", {"status": "offered"})

    events = await service.list_events(application_id)

    assert [event["event"] for event in events] == ["queued", "complete"]
    formatted = service._format_sse(events[0])
    assert formatted.startswith("event: queued")
    assert '"status": "submitted"' in formatted


def test_recruitment_tools_serialize_pipeline_context() -> None:
    """CrewAI tools should expose stable JSON payloads from the shared pipeline context."""
    context = _build_context()

    application_context = json.loads(ApplicationContextTool(context)._run())
    similar_jobs = json.loads(SimilarJobsTool(context)._run())
    similar_applications = json.loads(SimilarApplicationsTool(context)._run())
    skill_gap = json.loads(SkillGapTool(context)._run())
    calendar_slots = json.loads(CalendarSlotsTool(context)._run())
    offer_context = json.loads(OfferDraftTool(context)._run())
    delivery_context = json.loads(EmailDeliveryTool(context)._run())

    assert application_context["job_title"] == "Platform Engineer"
    assert similar_jobs[0]["title"] == "Backend Engineer"
    assert similar_applications[0]["candidate_name"] == "Earlier Casey"
    assert skill_gap["matched_skills"] == ["Python", "FastAPI"]
    assert calendar_slots == ["2026-03-25T10:00:00+00:00"]
    assert offer_context["recommendation"] == "proceed"
    assert delivery_context["delivery_mode"] == "preview"


def test_calendar_service_builds_non_overlapping_business_hour_slots() -> None:
    """Calendar slot generation should avoid busy windows and stay within business hours."""
    service = GoogleCalendarService()
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    busy_start = now + timedelta(hours=3)
    busy_end = busy_start + timedelta(minutes=service.event_duration_minutes)

    slots = service._build_free_slots(
        [BusyWindow(start=busy_start, end=busy_end)]
    )

    assert len(slots) == service.slot_count
    assert busy_start.isoformat() not in slots
    assert all(datetime.fromisoformat(slot).hour >= 9 for slot in slots)


def test_email_service_preview_mode_and_html_rendering(monkeypatch: pytest.MonkeyPatch) -> None:
    """Email service should degrade to preview mode and render HTML safely."""
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    service = ResendEmailService()

    assert service.is_configured() is False
    assert service.delivery_mode() == "preview"
    interview_html = service.render_interview_email(
        candidate_name="Casey <Candidate>",
        job_title="Platform Engineer",
        scheduled_at="2026-03-25T10:00:00+00:00",
        calendar_link="https://calendar.example/event",
    )
    offer_html = service.render_offer_email(
        candidate_name="Casey Candidate",
        company_name="HireIQ",
        offer_text="We'd love to move forward.",
    )

    assert "&lt;Candidate&gt;" in interview_html
    assert "Open calendar event" in interview_html
    assert "HireIQ" in offer_html


@pytest.mark.asyncio
async def test_email_service_preview_send_returns_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    """Preview email sends should return stable metadata without calling Resend."""
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    service = ResendEmailService()

    response = await service.send_email(
        to_email="casey@example.com",
        subject="Interview invite",
        html="<p>Preview only</p>",
    )

    assert response["mode"] == "preview"
    assert response["email_id"] is None
    assert response["to_email"] == "casey@example.com"


def test_ats_webhook_signature_and_url_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Webhook helper methods should verify signatures and build public URLs."""
    monkeypatch.setattr(settings, "ATS_WEBHOOK_SECRET", "phase7-secret")
    monkeypatch.setattr(settings, "BACKEND_PUBLIC_URL", "https://hireiq.example")
    service = ATSWebhookService(SimpleNamespace())

    body = b'{"event_type":"application.created"}'
    digest = hmac.new(b"phase7-secret", body, hashlib.sha256).hexdigest()
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": "https",
            "server": ("hireiq.example", 443),
            "path": "/api/v1/integrations/ats/webhooks/greenhouse",
            "headers": [],
        }
    )

    assert service.verify_signature(signature=f"sha256={digest}", body=body) is True
    assert service.verify_signature(signature="sha256=bad", body=body) is False
    assert service.webhook_url(request) == "https://hireiq.example/api/v1/integrations/ats/webhooks/greenhouse"


def test_storage_service_slugifies_filename_and_prefers_custom_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """R2 storage helpers should sanitize filenames and honor explicit endpoints."""
    monkeypatch.setattr(settings, "R2_ENDPOINT_URL", "https://r2.example")
    monkeypatch.setattr(settings, "R2_ACCOUNT_ID", "")
    monkeypatch.setattr(settings, "R2_ACCESS_KEY_ID", "key")
    monkeypatch.setattr(settings, "R2_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setattr(settings, "R2_BUCKET_NAME", "hireiq-resumes")
    service = R2ResumeStorageService()

    assert service.endpoint_url == "https://r2.example"
    assert service._slugify_filename("Casey Candidate Resume (Final).pdf") == "Casey-Candidate-Resume-Final-.pdf"


def test_storage_service_rejects_invalid_account_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    """R2 readiness should fail when the account id is not hostname-safe."""
    monkeypatch.setattr(settings, "R2_ENDPOINT_URL", "")
    monkeypatch.setattr(settings, "R2_ACCOUNT_ID", "recruiter@example.com")
    monkeypatch.setattr(settings, "R2_ACCESS_KEY_ID", "key")
    monkeypatch.setattr(settings, "R2_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setattr(settings, "R2_BUCKET_NAME", "hireiq-resumes")
    service = R2ResumeStorageService()

    assert service.is_configured() is False
    assert "Cloudflare account ID" in str(service.configuration_error())


@pytest.mark.asyncio
async def test_storage_service_raises_on_runtime_upload_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configured R2 uploads should surface provider failures instead of failing silently."""
    monkeypatch.setattr(settings, "R2_ENDPOINT_URL", "https://example.r2.cloudflarestorage.com")
    monkeypatch.setattr(settings, "R2_ACCOUNT_ID", "abcdef123456")
    monkeypatch.setattr(settings, "R2_ACCESS_KEY_ID", "key")
    monkeypatch.setattr(settings, "R2_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setattr(settings, "R2_BUCKET_NAME", "hireiq-resumes")
    service = R2ResumeStorageService()

    class FailingClient:
        def put_object(self, **kwargs: object) -> None:
            raise RuntimeError("tls handshake failed")

    monkeypatch.setattr(service, "_client", lambda: FailingClient())

    with pytest.raises(ServiceUnavailableException):
        await service.upload_resume(
            company_id=uuid4(),
            filename="resume.pdf",
            file_bytes=b"%PDF-1.4",
        )


@pytest.mark.asyncio
async def test_storage_service_upload_and_download_round_trip_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The storage service should pass the expected bucket, key, and content metadata to boto3."""
    monkeypatch.setattr(settings, "R2_ENDPOINT_URL", "https://example.r2.cloudflarestorage.com")
    monkeypatch.setattr(settings, "R2_ACCOUNT_ID", "abcdef123456")
    monkeypatch.setattr(settings, "R2_ACCESS_KEY_ID", "key")
    monkeypatch.setattr(settings, "R2_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setattr(settings, "R2_BUCKET_NAME", "hireiq-resumes")
    service = R2ResumeStorageService()
    captured: dict[str, object] = {}

    class FakeBody:
        def read(self) -> bytes:
            return b"%PDF-1.4"

    class FakeClient:
        def put_object(self, **kwargs: object) -> None:
            captured.update(kwargs)

        def get_object(self, **kwargs: object) -> dict[str, object]:
            captured.update({f"download_{key}": value for key, value in kwargs.items()})
            return {
                "ContentType": "application/pdf",
                "Body": FakeBody(),
            }

    monkeypatch.setattr(service, "_client", lambda: FakeClient())
    upload = await service.upload_resume(
        company_id=uuid4(),
        filename="Casey Candidate Resume.pdf",
        file_bytes=b"%PDF-1.4",
    )

    assert upload is not None
    assert upload["content_type"] == "application/pdf"
    assert str(upload["storage_key"]).startswith("companies/")
    assert str(upload["storage_key"]).endswith("Casey-Candidate-Resume.pdf")
    assert captured["Bucket"] == "hireiq-resumes"
    assert captured["ContentType"] == "application/pdf"
    assert captured["Body"] == b"%PDF-1.4"

    download = await service.download_resume(str(upload["storage_key"]))

    assert download["content_type"] == "application/pdf"
    assert download["file_bytes"] == b"%PDF-1.4"
    assert captured["download_Bucket"] == "hireiq-resumes"
    assert captured["download_Key"] == upload["storage_key"]


def test_pdf_candidate_upload_returns_503_when_r2_is_invalid(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Multipart resume ingest should fail loudly when R2 is configured incorrectly."""

    async def fake_embed_text(self: EmbeddingService, text: str) -> list[float]:
        return [0.0] * 1536

    monkeypatch.setattr(EmbeddingService, "embed_text", fake_embed_text)
    monkeypatch.setattr(settings, "R2_ENDPOINT_URL", "")
    monkeypatch.setattr(settings, "R2_ACCOUNT_ID", "recruiter@example.com")
    monkeypatch.setattr(settings, "R2_ACCESS_KEY_ID", "key")
    monkeypatch.setattr(settings, "R2_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setattr(settings, "R2_BUCKET_NAME", "hireiq-resumes")

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "pdf-storage@example.com",
            "password": "supersecure123",
            "company_name": "Storage Co",
        },
    )
    token = signup.json()["data"]["access_token"]

    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Casey Candidate\nFastAPI Engineer")
    pdf_bytes = document.tobytes()
    document.close()

    response = client.post(
        "/api/v1/candidates",
        headers={"Authorization": f"Bearer {token}"},
        files={"resume": ("resume.pdf", pdf_bytes, "application/pdf")},
        data={
            "name": "Casey Candidate",
            "email": "casey.storage@example.com",
        },
    )

    assert response.status_code == 503
    payload = response.json()
    assert payload["success"] is False
    assert "R2_ACCOUNT_ID" in payload["error"]


def test_pdf_candidate_upload_rejects_invalid_magic_bytes(client: TestClient) -> None:
    """Multipart resume ingest should reject renamed non-PDF files."""
    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "invalid-pdf@example.com",
            "password": "supersecure123",
            "company_name": "Validation Co",
        },
    )
    token = signup.json()["data"]["access_token"]

    response = client.post(
        "/api/v1/candidates",
        headers={"Authorization": f"Bearer {token}"},
        files={"resume": ("resume.pdf", b"not really a pdf", "application/pdf")},
        data={
            "name": "Casey Candidate",
            "email": "casey.invalid@example.com",
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert "valid PDF" in payload["error"]


def test_crewai_runner_parse_output_and_recommendation_logic() -> None:
    """Runner helpers should normalize CrewAI output and expose deterministic recommendations."""
    runner = CrewAIPipelineRunner()
    context = _build_context()

    fake_output = SimpleNamespace(
        tasks_output=[SimpleNamespace(json_dict={"score": 0.91})],
        json_dict=None,
        pydantic=None,
        raw='{"score": 0.1}',
    )

    parsed = runner._parse_output(fake_output)

    assert parsed == {"score": 0.91}
    assert runner.recommendation(context) == "proceed"
    assert runner.default_scheduler_slots()
    assert CVScreenerOutput.__annotations__["score"] is float
    assert runner._extract_token_usage(SimpleNamespace(token_usage=SimpleNamespace(total_tokens=123, prompt_tokens=100, completion_tokens=23, successful_requests=1))) == 123
    assert runner._extract_token_usage(SimpleNamespace(token_usage=SimpleNamespace(total_tokens=0, prompt_tokens=0, completion_tokens=0, successful_requests=0))) is None


def test_settings_require_a_strong_jwt_secret() -> None:
    """Settings should reject JWT secrets that are too short."""
    with pytest.raises(ValidationError):
        Settings(JWT_SECRET_KEY="too-short")


@pytest.mark.asyncio
async def test_crewai_runner_uses_to_thread_for_kickoff(monkeypatch: pytest.MonkeyPatch) -> None:
    """Crew kickoff should be dispatched through asyncio.to_thread."""
    from app.agents import crewai_runner as crewai_runner_module
    from app.models.agent_run import AgentName

    runner = CrewAIPipelineRunner()
    context = _build_context()
    captured: dict[str, object] = {}

    class FakeCrew:
        def __init__(self, **_: object) -> None:
            pass

        def kickoff(self, *, inputs: dict[str, object]) -> SimpleNamespace:
            captured["inputs"] = inputs
            return SimpleNamespace(
                tasks_output=[SimpleNamespace(json_dict={"score": 0.77})],
                json_dict=None,
                pydantic=None,
                raw='{"score": 0.1}',
                token_usage=SimpleNamespace(
                    total_tokens=9,
                    prompt_tokens=4,
                    completion_tokens=5,
                    successful_requests=1,
                ),
            )

    async def fake_to_thread(fn, *args, **kwargs):  # type: ignore[no-untyped-def]
        captured["fn"] = fn
        captured["kwargs"] = kwargs
        return fn(*args, **kwargs)

    monkeypatch.setattr(runner, "_build_llm", lambda: object())
    monkeypatch.setattr(runner, "build_agents", lambda context: {AgentName.CV_SCREENER: object()})
    monkeypatch.setattr(runner, "_build_task", lambda agent_name, agent: object())
    monkeypatch.setattr(crewai_runner_module, "Crew", FakeCrew)
    monkeypatch.setattr(crewai_runner_module.asyncio, "to_thread", fake_to_thread)

    result = await runner.run_task(AgentName.CV_SCREENER, context)

    assert callable(captured["fn"])
    assert captured["kwargs"] == {"inputs": context.model_dump()}
    assert captured["inputs"] == context.model_dump()
    assert result.output == {"score": 0.77}
    assert result.used_fallback is False
    assert result.tokens_used == 9


@pytest.mark.asyncio
async def test_crewai_runner_returns_fallback_metadata_on_provider_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider failures should be captured while still returning deterministic fallback output."""
    from app.agents import crewai_runner as crewai_runner_module
    from app.models.agent_run import AgentName

    runner = CrewAIPipelineRunner()
    context = _build_context()

    class FailingCrew:
        def __init__(self, **_: object) -> None:
            pass

        def kickoff(self, *, inputs: dict[str, object]) -> SimpleNamespace:
            raise RuntimeError("provider timeout")

    async def fake_to_thread(fn, *args, **kwargs):  # type: ignore[no-untyped-def]
        return fn(*args, **kwargs)

    monkeypatch.setattr(runner, "_build_llm", lambda: object())
    monkeypatch.setattr(runner, "build_agents", lambda context: {AgentName.CV_SCREENER: object()})
    monkeypatch.setattr(runner, "_build_task", lambda agent_name, agent: object())
    monkeypatch.setattr(crewai_runner_module, "Crew", FailingCrew)
    monkeypatch.setattr(crewai_runner_module.asyncio, "to_thread", fake_to_thread)

    result = await runner.run_task(AgentName.CV_SCREENER, context)

    assert result.used_fallback is True
    assert result.error_message == "provider timeout"
    assert "summary" in result.output


@pytest.mark.asyncio
async def test_ats_webhook_receive_event_persists_expected_metadata() -> None:
    """Receiving a verified event should enqueue the normalized webhook record."""
    captured: list[object] = []

    async def flush() -> None:
        return None

    payload = {
        "event_type": "application.created",
        "event_id": "evt-123",
        "data": {"candidate_email": "candidate@example.com"},
    }
    body = json.dumps(payload).encode("utf-8")
    service = ATSWebhookService(SimpleNamespace(add=lambda event: captured.append(event), flush=flush))
    service.verify_signature = lambda **_: True  # type: ignore[method-assign]

    accepted = await service.receive_event(
        provider="greenhouse",
        body=body,
        signature="sha256=verified",
    )

    assert accepted["accepted"] is True
    assert captured[0].event_type == "application.created"
    assert captured[0].external_event_id == "evt-123"
