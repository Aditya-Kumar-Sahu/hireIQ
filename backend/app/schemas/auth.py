"""
Auth schemas — signup, login, and token responses.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Request body for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user profile."""

    id: str
    email: str
    role: str
    company_id: str
    created_at: str

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Combined user + token response for signup."""

    user: UserResponse
    access_token: str
    token_type: str = "bearer"
