"""
Schemas package — re-export all request/response models.
"""

from app.schemas.application import (
    AgentRunResponse,
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationStatusUpdate,
    OfferRequest,
    ScheduleRequest,
)
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.candidate import (
    CandidateCreate,
    CandidateDetailResponse,
    CandidateListResponse,
    CandidateResponse,
    CandidateSearchResult,
)
from app.schemas.common import APIResponse, PaginatedResponse, PaginationParams
from app.schemas.job import JobCreate, JobListResponse, JobResponse, JobUpdate
from app.schemas.job import SimilarJobResult
from app.schemas.meta import IntegrationStatusResponse

__all__ = [
    "APIResponse",
    "AgentRunResponse",
    "ApplicationCreate",
    "ApplicationDetailResponse",
    "ApplicationListResponse",
    "ApplicationResponse",
    "ApplicationStatusUpdate",
    "AuthResponse",
    "CandidateCreate",
    "CandidateDetailResponse",
    "CandidateListResponse",
    "CandidateResponse",
    "CandidateSearchResult",
    "JobCreate",
    "JobListResponse",
    "JobResponse",
    "JobUpdate",
    "LoginRequest",
    "OfferRequest",
    "PaginatedResponse",
    "PaginationParams",
    "IntegrationStatusResponse",
    "ScheduleRequest",
    "SimilarJobResult",
    "SignupRequest",
    "TokenResponse",
    "UserResponse",
]
