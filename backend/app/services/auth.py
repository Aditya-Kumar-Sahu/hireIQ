"""Authentication service for signup, login, and current-user helpers."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.company import Company
from app.models.user import User, UserRole
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, TokenResponse, UserResponse


class AuthService:
    """Encapsulates auth-related database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def signup(self, payload: SignupRequest) -> AuthResponse:
        """Create a company and its first recruiter account."""
        existing_user = await self.db.scalar(
            select(User).where(func.lower(User.email) == payload.email.lower())
        )
        if existing_user is not None:
            raise ConflictException("A user with this email already exists")

        company = Company(name=payload.company_name.strip())
        user = User(
            email=payload.email.lower(),
            hashed_password=hash_password(payload.password),
            role=UserRole.ADMIN,
            company=company,
        )
        self.db.add_all([company, user])
        await self.db.flush()

        token = create_access_token({"sub": str(user.id)})
        return AuthResponse(user=UserResponse.model_validate(user), access_token=token)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        """Authenticate a user and mint a bearer token."""
        user = await self.db.scalar(select(User).where(func.lower(User.email) == payload.email.lower()))
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=token)
