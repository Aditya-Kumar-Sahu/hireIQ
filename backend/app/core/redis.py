"""
Redis client singleton.

Used for:
- Embedding cache (SHA-256 hashed text → vector, TTL 24h)
- Future job queue support (Celery/RQ upgrade path)
"""

from __future__ import annotations

import redis.asyncio as redis

from app.core.config import settings

# ── Redis Client ───────────────────────────────────────────────────────
redis_client: redis.Redis = redis.from_url(  # type: ignore[assignment]
    settings.REDIS_URL,
    decode_responses=True,
)


async def get_redis() -> redis.Redis:  # type: ignore[type-arg]
    """Return the shared Redis client instance."""
    return redis_client


async def close_redis() -> None:
    """Gracefully close the Redis connection."""
    await redis_client.close()
