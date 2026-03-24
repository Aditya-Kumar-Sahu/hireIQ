#!/usr/bin/env python3
"""Seed a demo company with jobs and candidates via the public API.

The script creates a recruiter account, a small set of jobs, and several
candidates. It is intentionally API-driven so it exercises the same paths the
frontend uses without starting the application pipeline.

Example:
    python backend/scripts/seed_demo_company.py --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_PASSWORD = "DemoCompany123!"


@dataclass(slots=True)
class CreatedJob:
    id: str
    title: str


@dataclass(slots=True)
class CreatedCandidate:
    id: str
    name: str
    email: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Backend base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--company-name",
        default="HireIQ Demo Talent",
        help="Demo company name to register",
    )
    parser.add_argument(
        "--email",
        default=None,
        help="Recruiter email address. If omitted, a unique demo email is generated.",
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        help="Recruiter password used for the seeded account.",
    )
    return parser.parse_args()


def unique_email(prefix: str = "demo.recruiter") -> str:
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    token = uuid4().hex[:6]
    return f"{prefix}+{suffix}.{token}@example.com"


def api_request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    token: str | None = None,
    json_body: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = client.request(
        method,
        path,
        headers=headers,
        json=json_body,
        data=form_data,
    )

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"{method} {path} returned {response.status_code} with non-JSON body: {response.text}"
        ) from exc

    if response.status_code >= 400:
        raise RuntimeError(
            f"{method} {path} failed with HTTP {response.status_code}: {json.dumps(payload, indent=2)}"
        )

    if not isinstance(payload, dict) or "data" not in payload:
        raise RuntimeError(f"{method} {path} returned an unexpected payload: {payload!r}")

    return payload["data"]


def seed_jobs(client: httpx.Client, token: str) -> list[CreatedJob]:
    job_specs = [
        {
            "title": "Machine Learning Engineer - Talent Intelligence",
            "description": (
                "Build retrieval and recommendation systems that help recruiters surface "
                "the right candidate for the right role."
            ),
            "requirements": "Python, FastAPI, pgvector, embeddings, MLOps, data pipelines",
            "seniority": "senior",
        },
        {
            "title": "Backend Engineer - Platform",
            "description": (
                "Own core APIs, background jobs, and integration workflows for the recruiting platform."
            ),
            "requirements": "Python, FastAPI, PostgreSQL, Redis, async services, integration design",
            "seniority": "mid",
        },
        {
            "title": "Product Analyst - Recruiting Operations",
            "description": (
                "Analyze hiring funnels, recruiter throughput, and candidate quality signals."
            ),
            "requirements": "SQL, dashboards, experimentation, stakeholder communication",
            "seniority": "mid",
        },
        {
            "title": "Full Stack Engineer - Internal Tools",
            "description": "Build polished internal workflows for recruiters and hiring managers.",
            "requirements": "TypeScript, Next.js, React, UI systems, API integration",
            "seniority": "senior",
        },
    ]

    created: list[CreatedJob] = []
    for spec in job_specs:
        job = api_request(client, "POST", "/api/v1/jobs", token=token, json_body=spec)
        api_request(
            client,
            "PUT",
            f"/api/v1/jobs/{job['id']}",
            token=token,
            json_body={"status": "active"},
        )
        created.append(CreatedJob(id=str(job["id"]), title=str(job["title"])))
    return created


def seed_candidates(client: httpx.Client, token: str) -> list[CreatedCandidate]:
    candidate_specs = [
        {
            "name": "Aditya Sahu",
            "email": f"aditya.sahu+{uuid4().hex[:6]}@example.com",
            "linkedin_url": "https://www.linkedin.com/in/aditya-sahu/",
            "resume_text": (
                "Senior engineer with 6 years building Python APIs, recommendation systems, "
                "and vector search pipelines. Strong PostgreSQL, FastAPI, Redis, and MLOps background."
            ),
        },
        {
            "name": "Priya Nair",
            "email": f"priya.nair+{uuid4().hex[:6]}@example.com",
            "linkedin_url": "https://www.linkedin.com/in/priya-nair-analytics/",
            "resume_text": (
                "Product analyst with strong SQL, KPI design, experimentation, and hiring funnel analysis. "
                "Works closely with recruiting and operations stakeholders."
            ),
        },
        {
            "name": "Ethan Chen",
            "email": f"ethan.chen+{uuid4().hex[:6]}@example.com",
            "linkedin_url": "https://www.linkedin.com/in/ethan-chen-fullstack/",
            "resume_text": (
                "Full stack engineer focused on Next.js, TypeScript, React, and API integrations. "
                "Built internal tools and polished recruiter-facing workflows."
            ),
        },
        {
            "name": "Maria Gomez",
            "email": f"maria.gomez+{uuid4().hex[:6]}@example.com",
            "linkedin_url": "https://www.linkedin.com/in/maria-gomez-platform/",
            "resume_text": (
                "Backend engineer with experience in Python, async services, background jobs, "
                "and operational tooling for SaaS platforms."
            ),
        },
    ]

    created: list[CreatedCandidate] = []
    for spec in candidate_specs:
        candidate = api_request(client, "POST", "/api/v1/candidates", token=token, json_body=spec)
        created.append(
            CreatedCandidate(
                id=str(candidate["id"]),
                name=str(candidate["name"]),
                email=str(candidate["email"]),
            )
        )
    return created


def main() -> int:
    args = parse_args()
    email = args.email or unique_email()

    with httpx.Client(base_url=args.base_url, timeout=30.0) as client:
        signup = api_request(
            client,
            "POST",
            "/api/v1/auth/signup",
            json_body={
                "email": email,
                "password": args.password,
                "company_name": args.company_name,
            },
        )
        token = str(signup["access_token"])

        jobs = seed_jobs(client, token)
        candidates = seed_candidates(client, token)

    summary = {
        "company_name": args.company_name,
        "recruiter_email": email,
        "password": args.password,
        "jobs": [asdict(job) for job in jobs],
        "candidates": [asdict(candidate) for candidate in candidates],
    }

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
