"""Inbound ATS webhook verification and persistence."""

from __future__ import annotations

import hashlib
import hmac
import json

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.models.ats_webhook_event import ATSWebhookEvent


class ATSWebhookService:
    """Verify ATS webhook signatures and persist deliveries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def is_configured(self) -> bool:
        return bool(settings.ATS_WEBHOOK_SECRET)

    def webhook_url(self, request: Request, provider: str | None = None) -> str:
        provider_name = provider or settings.ATS_WEBHOOK_PROVIDER
        base_url = settings.BACKEND_PUBLIC_URL.rstrip("/") or str(request.base_url).rstrip("/")
        return f"{base_url}/api/v1/integrations/ats/webhooks/{provider_name}"

    async def receive_event(
        self,
        *,
        provider: str,
        body: bytes,
        signature: str | None,
    ) -> dict[str, object]:
        """Validate and persist an ATS webhook payload."""
        if not self.verify_signature(signature=signature, body=body):
            raise UnauthorizedException("Invalid webhook signature")

        payload = json.loads(body.decode("utf-8"))
        event = ATSWebhookEvent(
            provider=provider,
            event_type=str(payload.get("event_type", "unknown")),
            external_event_id=(
                str(payload["event_id"])
                if payload.get("event_id") is not None
                else None
            ),
            signature_verified=True,
            payload=payload,
        )
        self.db.add(event)
        await self.db.flush()
        return {
            "accepted": True,
            "provider": provider,
            "event_type": event.event_type,
            "event_id": event.external_event_id,
        }

    def verify_signature(self, *, signature: str | None, body: bytes) -> bool:
        """Return whether the incoming signature matches the configured secret."""
        if not self.is_configured() or not signature:
            return False
        expected = hmac.new(
            settings.ATS_WEBHOOK_SECRET.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, f"sha256={expected}")
