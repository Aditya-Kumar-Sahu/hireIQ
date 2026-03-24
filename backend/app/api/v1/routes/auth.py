"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.dependencies import CurrentUser, DBSession
from app.core.rate_limit import enforce_rate_limit
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, TokenResponse, UserResponse
from app.schemas.common import APIResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=APIResponse[AuthResponse], status_code=201)
async def signup(request: Request, payload: SignupRequest, db: DBSession) -> APIResponse[AuthResponse]:
    enforce_rate_limit(request, "25/minute", "auth:signup")
    service = AuthService(db)
    return APIResponse(data=await service.signup(payload))


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(request: Request, payload: LoginRequest, db: DBSession) -> APIResponse[TokenResponse]:
    enforce_rate_limit(request, "10/minute", "auth:login")
    service = AuthService(db)
    return APIResponse(data=await service.login(payload))


@router.get("/me", response_model=APIResponse[UserResponse])
async def me(current_user: CurrentUser) -> APIResponse[UserResponse]:
    return APIResponse(data=UserResponse.model_validate(current_user))
