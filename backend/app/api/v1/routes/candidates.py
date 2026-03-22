"""Candidate management endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DBSession, Pagination
from app.schemas.candidate import (
    CandidateCreate,
    CandidateDetailResponse,
    CandidateResponse,
    CandidateSearchResult,
)
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.candidates import CandidateService

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post("", response_model=APIResponse[CandidateResponse])
async def create_candidate(
    payload: CandidateCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[CandidateResponse]:
    data = await CandidateService(db, current_user).create_candidate(payload)
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
    db: DBSession,
    current_user: CurrentUser,
    q: Annotated[str, Query(min_length=1)],
) -> APIResponse[list[CandidateSearchResult]]:
    data = await CandidateService(db, current_user).search_candidates(q)
    return APIResponse(data=data)


@router.get("/{candidate_id}", response_model=APIResponse[CandidateDetailResponse])
async def get_candidate(
    candidate_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[CandidateDetailResponse]:
    data = await CandidateService(db, current_user).get_candidate_response(candidate_id)
    return APIResponse(data=data)
