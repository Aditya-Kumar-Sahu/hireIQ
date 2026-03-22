"""Google OAuth flow for company-scoped calendar access."""

from __future__ import annotations

import inspect
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestException, UnauthorizedException
from app.core.security import create_access_token, decode_access_token
from app.models.company import Company
from app.models.user import User


async def _maybe_await(value: Any) -> Any:
    """Allow tests to monkeypatch async methods with sync callables."""
    if inspect.isawaitable(value):
        return await value
    return value


class GoogleOAuthService:
    """Generate OAuth URLs and exchange callback codes for company tokens."""

    scopes = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def is_configured(self) -> bool:
        return bool(
            settings.GOOGLE_CLIENT_ID
            and settings.GOOGLE_CLIENT_SECRET
            and settings.GOOGLE_REDIRECT_URI
        )

    def build_authorization_payload(self, user: User) -> dict[str, str]:
        """Return the signed state token and Google consent URL."""
        if not self.is_configured():
            raise BadRequestException("Google OAuth is not configured")

        state = create_access_token(
            {
                "sub": str(user.id),
                "company_id": str(user.company_id),
                "purpose": "google_calendar_oauth",
            },
            expires_delta=timedelta(minutes=10),
        )
        query = urlencode(
            {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "response_type": "code",
                "access_type": "offline",
                "prompt": "consent",
                "scope": " ".join(self.scopes),
                "state": state,
            }
        )
        return {
            "authorization_url": f"{settings.GOOGLE_OAUTH_AUTHORIZE_URI}?{query}",
            "state": state,
        }

    async def connect_company(
        self,
        *,
        company: Company,
        user: User,
        code: str,
        state: str,
    ) -> dict[str, object]:
        """Exchange the OAuth code and persist company calendar credentials."""
        self.validate_state(state=state, user=user)
        tokens = await _maybe_await(self.exchange_code(code, settings.GOOGLE_REDIRECT_URI))
        access_token = str(tokens["access_token"])
        refresh_token = tokens.get("refresh_token")
        expires_in = int(tokens.get("expires_in", 3600))
        identity = await _maybe_await(self.fetch_user_identity(access_token))

        company.google_calendar_access_token = access_token
        company.google_calendar_refresh_token = (
            str(refresh_token)
            if refresh_token is not None
            else company.google_calendar_refresh_token
        )
        company.google_calendar_token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=expires_in
        )
        company.google_calendar_connected_email = str(identity.get("email", "")) or None
        company.google_calendar_calendar_id = str(
            identity.get("calendar_id") or settings.GOOGLE_CALENDAR_ID or "primary"
        )
        await self.db.flush()
        return {
            "provider": "google_calendar",
            "connected": True,
            "connected_email": company.google_calendar_connected_email,
            "calendar_id": company.google_calendar_calendar_id,
        }

    async def disconnect_company(self, company: Company) -> dict[str, object]:
        """Clear company-scoped Google Calendar tokens."""
        company.google_calendar_access_token = None
        company.google_calendar_refresh_token = None
        company.google_calendar_token_expires_at = None
        company.google_calendar_connected_email = None
        company.google_calendar_calendar_id = None
        await self.db.flush()
        return {
            "provider": "google_calendar",
            "connected": False,
            "connected_email": None,
            "calendar_id": None,
        }

    def validate_state(self, *, state: str, user: User) -> None:
        """Ensure the callback state token belongs to the current user and company."""
        payload = decode_access_token(state)
        if payload is None:
            raise UnauthorizedException("Invalid Google OAuth state")
        if payload.get("purpose") != "google_calendar_oauth":
            raise UnauthorizedException("Invalid Google OAuth state")
        if payload.get("sub") != str(user.id):
            raise UnauthorizedException("Invalid Google OAuth state")
        if payload.get("company_id") != str(user.company_id):
            raise UnauthorizedException("Invalid Google OAuth state")

    async def exchange_code(self, code: str, redirect_uri: str) -> dict[str, Any]:
        """Exchange an OAuth authorization code for Google tokens."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                settings.GOOGLE_CALENDAR_TOKEN_URI,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
        return response.json()

    async def fetch_user_identity(self, access_token: str) -> dict[str, Any]:
        """Fetch the Google account identity bound to the granted access token."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
        payload = response.json()
        return {
            "email": payload.get("email"),
            "calendar_id": settings.GOOGLE_CALENDAR_ID or "primary",
        }
