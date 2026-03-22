"""
Auth schemas — signup, login, and token responses.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.user import UserRole


class SignupRequest(BaseModel):
    """Request body for user registration."""

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: str = Field(min_length=3, max_length=255)
    password: str


class TokenResponse(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user profile."""

    id: UUID
    email: str
    role: UserRole
    company_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Combined user + token response for signup."""

    user: UserResponse
    access_token: str
    token_type: str = "bearer"
