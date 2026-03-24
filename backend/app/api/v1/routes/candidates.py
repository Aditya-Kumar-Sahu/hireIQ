"""Candidate management endpoints."""

from __future__ import annotations

import re
from pathlib import PurePath
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from app.api.dependencies import CurrentUser, DBSession, Pagination
from app.core.exceptions import BadRequestException
from app.core.rate_limit import enforce_rate_limit
from app.schemas.candidate import (
    CandidateCreate,
    CandidateDetailResponse,
    CandidateResponse,
    CandidateSearchResult,
)
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.job import SimilarJobResult
from app.services.candidates import CandidateService
from app.services.jobs import JobService

router = APIRouter(prefix="/candidates", tags=["Candidates"])


def _safe_attachment_filename(filename: str) -> str:
    """Return a header-safe filename for resume downloads."""
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", PurePath(filename).name).strip("._")
    return sanitized or "resume.pdf"


@router.post("", response_model=APIResponse[CandidateResponse], status_code=201)
async def create_candidate(
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[CandidateResponse]:
    enforce_rate_limit(request, "30/minute", "candidates:create")
    service = CandidateService(db, current_user)
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        resume = form.get("resume")
        if resume is None or not hasattr(resume, "read") or not hasattr(resume, "filename"):
            raise BadRequestException("Resume upload is required for multipart candidate ingest")
        data = await service.create_candidate_from_pdf(
            name=str(form.get("name", "")),
            email=str(form.get("email", "")),
            linkedin_url=(
                str(form.get("linkedin_url"))
                if form.get("linkedin_url") is not None
                else None
            ),
            filename=str(resume.filename),
            content_type=getattr(resume, "content_type", None),
            file_bytes=await resume.read(),
        )
    else:
        payload = CandidateCreate.model_validate(await request.json())
        data = await service.create_candidate(payload)
    return APIResponse(data=data)


@router.get("", response_model=APIResponse[PaginatedResponse[CandidateResponse]])
async def list_candidates(
    db: DBSession,
    current_user: CurrentUser,
    pagination: Pagination,
    search: str | None = Query(default=None),
) -> APIResponse[PaginatedResponse[CandidateResponse]]:
    data = await CandidateService(db, current_user).list_candidates(pagination, search)
    return APIResponse(data=data)


@router.get("/search", response_model=APIResponse[list[CandidateSearchResult]])
async def search_candidates(
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    q: Annotated[str, Query(min_length=1)],
) -> APIResponse[list[CandidateSearchResult]]:
    enforce_rate_limit(request, "120/minute", "candidates:search")
    data = await CandidateService(db, current_user).search_candidates(q)
    return APIResponse(data=data)


@router.get("/{candidate_id}/similar-jobs", response_model=APIResponse[list[SimilarJobResult]])
async def similar_jobs_for_candidate(
    candidate_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[list[SimilarJobResult]]:
    candidate = await CandidateService(db, current_user).get_candidate(candidate_id)
    data = await JobService(db, current_user).find_similar_jobs_for_candidate(candidate)
    return APIResponse(data=data)


@router.get("/{candidate_id}/resume")
async def download_candidate_resume(
    candidate_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> Response:
    payload = await CandidateService(db, current_user).get_candidate_resume(candidate_id)
    filename = _safe_attachment_filename(str(payload.get("filename", "resume.pdf")))
    return Response(
        content=payload["file_bytes"],
        media_type=str(payload.get("content_type", "application/pdf")),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{candidate_id}", response_model=APIResponse[CandidateDetailResponse])
async def get_candidate(
    candidate_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[CandidateDetailResponse]:
    data = await CandidateService(db, current_user).get_candidate_response(candidate_id)
    return APIResponse(data=data)
