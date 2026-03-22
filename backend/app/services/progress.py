"""Progress event persistence and SSE formatting for application pipelines."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncIterator
from uuid import UUID

from fastapi import Request

from app.core.redis import redis_client


class ApplicationProgressService:
    """Store and stream application progress events via Redis."""

    key_prefix = "application_progress"
    ttl_seconds = 60 * 60 * 24
    terminal_events = {"complete", "failed"}

    def _key(self, application_id: UUID) -> str:
        return f"{self.key_prefix}:{application_id}"

    async def reset(self, application_id: UUID) -> None:
        """Clear any prior progress history for an application."""
        await redis_client.delete(self._key(application_id))

    async def publish(self, application_id: UUID, event: str, data: dict[str, object]) -> None:
        """Append a progress event to Redis history."""
        payload = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        key = self._key(application_id)
        await redis_client.rpush(key, json.dumps(payload))
        await redis_client.expire(key, self.ttl_seconds)

    async def list_events(self, application_id: UUID) -> list[dict[str, object]]:
        """Return the full Redis-backed event history for an application."""
        values = await redis_client.lrange(self._key(application_id), 0, -1)
        return [json.loads(value) for value in values]

    async def stream_sse(self, application_id: UUID, request: Request) -> AsyncIterator[str]:
        """Yield Redis-backed events as SSE frames until a terminal event is seen."""
        sent = 0
        while True:
            events = await self.list_events(application_id)
            while sent < len(events):
                payload = events[sent]
                sent += 1
                yield self._format_sse(payload)
                if payload["event"] in self.terminal_events:
                    return

            if await request.is_disconnected():
                return

            await asyncio.sleep(0.1)

    @staticmethod
    def _format_sse(payload: dict[str, object]) -> str:
        """Convert an event payload into SSE wire format."""
        return f"event: {payload['event']}\ndata: {json.dumps(payload, default=str)}\n\n"
