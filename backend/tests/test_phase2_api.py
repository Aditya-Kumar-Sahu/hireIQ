"""Integration tests for the Phase 2 API surface."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _signup_and_authenticate(client: TestClient, email: str) -> str:
    """Create a user and return a bearer token."""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "supersecure123",
            "company_name": "Test Company",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["user"]["email"] == email
    return payload["data"]["access_token"]


def test_auth_signup_login_and_me_flow(client: TestClient) -> None:
    """Users can sign up, log in, and fetch their profile."""
    email = "owner@example.com"
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "supersecure123",
            "company_name": "Acme Hiring",
        },
    )

    assert signup_response.status_code == 200
    signup_payload = signup_response.json()
    assert signup_payload["success"] is True
    assert signup_payload["data"]["user"]["role"] == "admin"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "supersecure123"},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["data"]["token_type"] == "bearer"

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_payload['data']['access_token']}"},
    )
    assert me_response.status_code == 200
    me_payload = me_response.json()
    assert me_payload["data"]["email"] == email
    assert me_payload["data"]["company_id"] == signup_payload["data"]["user"]["company_id"]


def test_jobs_candidates_and_applications_crud_flow(client: TestClient) -> None:
    """Core recruiter CRUD flow works end to end."""
    token = _signup_and_authenticate(client, "recruiter@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    job_response = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": "Backend Engineer",
            "description": "Build resilient APIs and hiring workflows.",
            "requirements": "FastAPI SQLAlchemy PostgreSQL Docker testing",
            "seniority": "mid",
        },
    )
    assert job_response.status_code == 200
    job_payload = job_response.json()["data"]
    assert job_payload["title"] == "Backend Engineer"
    assert job_payload["status"] == "draft"

    candidate_response = client.post(
        "/api/v1/candidates",
        headers=headers,
        json={
            "name": "Casey Candidate",
            "email": "casey@example.com",
            "linkedin_url": "https://linkedin.com/in/casey",
            "resume_text": "Backend engineer with FastAPI and PostgreSQL experience.",
        },
    )
    assert candidate_response.status_code == 200
    candidate_payload = candidate_response.json()["data"]
    assert candidate_payload["email"] == "casey@example.com"

    application_response = client.post(
        "/api/v1/applications",
        headers=headers,
        json={
            "job_id": job_payload["id"],
            "candidate_id": candidate_payload["id"],
        },
    )
    assert application_response.status_code == 200
    application_payload = application_response.json()["data"]
    assert application_payload["status"] == "submitted"

    jobs_list = client.get("/api/v1/jobs?page=1&limit=10", headers=headers)
    assert jobs_list.status_code == 200
    assert jobs_list.json()["data"]["total"] == 1

    candidate_search = client.get("/api/v1/candidates/search?q=FastAPI", headers=headers)
    assert candidate_search.status_code == 200
    assert len(candidate_search.json()["data"]) == 1

    application_detail = client.get(
        f"/api/v1/applications/{application_payload['id']}",
        headers=headers,
    )
    assert application_detail.status_code == 200
    assert application_detail.json()["data"]["agent_runs"] == []

    update_status = client.patch(
        f"/api/v1/applications/{application_payload['id']}/status",
        headers=headers,
        json={"status": "screening"},
    )
    assert update_status.status_code == 200
    assert update_status.json()["data"]["status"] == "screening"


def test_duplicate_application_is_rejected(client: TestClient) -> None:
    """The same candidate cannot apply to the same job twice."""
    token = _signup_and_authenticate(client, "duplicate@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    job_id = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": "Platform Engineer",
            "description": "Own platform reliability and delivery.",
            "requirements": "Python Docker CI PostgreSQL observability",
            "seniority": "senior",
        },
    ).json()["data"]["id"]

    candidate_id = client.post(
        "/api/v1/candidates",
        headers=headers,
        json={
            "name": "Taylor Candidate",
            "email": "taylor@example.com",
            "resume_text": "Platform engineer with CI and observability experience.",
        },
    ).json()["data"]["id"]

    first_response = client.post(
        "/api/v1/applications",
        headers=headers,
        json={"job_id": job_id, "candidate_id": candidate_id},
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/api/v1/applications",
        headers=headers,
        json={"job_id": job_id, "candidate_id": candidate_id},
    )
    assert second_response.status_code == 409
    assert "already applied" in second_response.json()["error"]


def test_job_update_soft_delete_and_status_filtering(client: TestClient) -> None:
    """Jobs can be updated, soft-deleted, and filtered by status."""
    token = _signup_and_authenticate(client, "jobs@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created_job = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": "Frontend Engineer",
            "description": "Build polished recruiter experiences.",
            "requirements": "React Next.js TypeScript testing",
            "seniority": "mid",
        },
    ).json()["data"]

    updated_job = client.put(
        f"/api/v1/jobs/{created_job['id']}",
        headers=headers,
        json={"status": "active", "title": "Senior Frontend Engineer"},
    )
    assert updated_job.status_code == 200
    assert updated_job.json()["data"]["status"] == "active"
    assert updated_job.json()["data"]["title"] == "Senior Frontend Engineer"

    active_jobs = client.get("/api/v1/jobs?page=1&limit=10&status=active", headers=headers)
    assert active_jobs.status_code == 200
    assert active_jobs.json()["data"]["total"] == 1

    deleted = client.delete(f"/api/v1/jobs/{created_job['id']}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True

    closed_jobs = client.get("/api/v1/jobs?page=1&limit=10&status=closed", headers=headers)
    assert closed_jobs.status_code == 200
    assert closed_jobs.json()["data"]["items"][0]["status"] == "closed"


def test_validation_errors_use_standard_envelope(client: TestClient) -> None:
    """Request validation failures stay inside the shared API envelope."""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "a",
            "password": "short",
            "company_name": "",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"] is None
    assert "password" in payload["error"]


def test_protected_endpoints_require_authentication(client: TestClient) -> None:
    """Protected endpoints reject missing credentials."""
    response = client.get("/api/v1/jobs?page=1&limit=10")

    assert response.status_code == 401
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"] == "Authentication credentials were not provided"
