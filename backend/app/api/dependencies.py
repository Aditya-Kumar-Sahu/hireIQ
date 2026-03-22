"""Shared FastAPI dependencies used across route modules."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.common import PaginationParams

bearer_scheme = HTTPBearer(auto_error=False)

DBSession = Annotated[AsyncSession, Depends(get_db)]
Pagination = Annotated[PaginationParams, Depends()]


async def get_current_user(
    db: DBSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    """Return the authenticated user from the bearer token."""
    if credentials is None:
        raise UnauthorizedException("Authentication credentials were not provided")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedException()

    user_id_raw = payload.get("sub")
    if not isinstance(user_id_raw, str):
        raise UnauthorizedException()
    try:
        user_id = UUID(user_id_raw)
    except ValueError as exc:
        raise UnauthorizedException() from exc

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise UnauthorizedException()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
