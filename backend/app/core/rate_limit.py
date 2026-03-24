"""Shared rate-limiter helpers."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Request
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import FixedWindowRateLimiter

from app.core.exceptions import TooManyRequestsException


def rate_limit_key(request: Request) -> str:
    """Prefer forwarded client IPs when present, else fall back to the socket address."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        first_hop = forwarded_for.split(",", 1)[0].strip()
        if first_hop:
            return first_hop
    client = getattr(request, "client", None)
    return client.host if client is not None else "anonymous"


_storage = MemoryStorage()
_limiter = FixedWindowRateLimiter(_storage)


@lru_cache(maxsize=32)
def _parsed_limit(limit_value: str):
    return parse(limit_value)


def enforce_rate_limit(request: Request, limit_value: str, scope: str) -> None:
    """Enforce a fixed-window rate limit for the current request."""
    rate_limit_item = _parsed_limit(limit_value)
    key = f"{scope}:{rate_limit_key(request)}"
    if _limiter.hit(rate_limit_item, key):
        return
    raise TooManyRequestsException(f"Rate limit exceeded: {limit_value}")
