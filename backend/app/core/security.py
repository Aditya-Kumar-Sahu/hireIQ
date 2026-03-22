"""
Security utilities — JWT token management and password hashing.

Provides:
- `hash_password()` / `verify_password()` for bcrypt password hashing.
- `create_access_token()` / `decode_access_token()` for JWT lifecycle.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password Hashing ──────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Tokens ─────────────────────────────────────────────────────────
def create_access_token(
    data: dict[str, str | int],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        data: Claims to encode (must include "sub" with the user ID).
        expires_delta: Optional custom expiry. Defaults to config value.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = int(expire.timestamp())
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, str | int] | None:
    """Decode and validate a JWT access token.

    Returns:
        The decoded claims dict, or None if the token is invalid/expired.
    """
    try:
        payload: dict[str, str | int] = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None
