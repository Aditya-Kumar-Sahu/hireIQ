"""Google Calendar integration used by the scheduling stage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings


@dataclass(slots=True)
class BusyWindow:
    """A busy time range returned by Google Calendar."""

    start: datetime
    end: datetime


class GoogleCalendarService:
    """Suggest interview slots and optionally create a real calendar event."""

    event_duration_minutes = 45
    search_window_days = 5
    slot_count = 3

    @property
    def calendar_id(self) -> str:
        return settings.GOOGLE_CALENDAR_ID or "primary"

    def is_configured(self) -> bool:
        """Return whether live Google Calendar calls can be made."""
        has_access_token = bool(settings.GOOGLE_CALENDAR_ACCESS_TOKEN)
        has_refresh_flow = bool(
            settings.GOOGLE_CLIENT_ID
            and settings.GOOGLE_CLIENT_SECRET
            and settings.GOOGLE_CALENDAR_REFRESH_TOKEN
        )
        return has_access_token or has_refresh_flow

    async def suggest_slots(self) -> list[str]:
        """Return upcoming interview slots from Google Calendar or a local fallback."""
        if not self.is_configured():
            return self._fallback_slots()

        try:
            access_token = await self._get_access_token()
            busy_windows = await self._fetch_busy_windows(access_token)
            slots = self._build_free_slots(busy_windows)
            return slots or self._fallback_slots()
        except Exception:
            return self._fallback_slots()

    async def schedule_interview(
        self,
        *,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        scheduled_at: str,
    ) -> dict[str, object]:
        """Create a calendar event when configured, else return a preview payload."""
        if not self.is_configured():
            return {
                "mode": "preview",
                "calendar_id": self.calendar_id,
                "event_id": None,
                "html_link": None,
                "scheduled_at": scheduled_at,
                "candidate_email": candidate_email,
                "candidate_name": candidate_name,
                "job_title": job_title,
            }

        start_at = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00")).astimezone(timezone.utc)
        end_at = start_at + timedelta(minutes=self.event_duration_minutes)
        payload = {
            "summary": f"HireIQ interview: {job_title}",
            "description": (
                f"Interview with {candidate_name} for the {job_title} role. "
                "Created by HireIQ's scheduling agent."
            ),
            "start": {"dateTime": start_at.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_at.isoformat(), "timeZone": "UTC"},
            "attendees": [{"email": candidate_email}],
        }

        access_token = await self._get_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"https://www.googleapis.com/calendar/v3/calendars/{quote(self.calendar_id, safe='')}/events",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        return {
            "mode": "live",
            "calendar_id": self.calendar_id,
            "event_id": data.get("id"),
            "html_link": data.get("htmlLink"),
            "scheduled_at": start_at.isoformat(),
            "candidate_email": candidate_email,
            "candidate_name": candidate_name,
            "job_title": job_title,
        }

    async def _get_access_token(self) -> str:
        """Return a live Google access token."""
        if settings.GOOGLE_CALENDAR_ACCESS_TOKEN:
            return settings.GOOGLE_CALENDAR_ACCESS_TOKEN

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                settings.GOOGLE_CALENDAR_TOKEN_URI,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "refresh_token": settings.GOOGLE_CALENDAR_REFRESH_TOKEN,
                    "grant_type": "refresh_token",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
        token_payload = response.json()
        return str(token_payload["access_token"])

    async def _fetch_busy_windows(self, access_token: str) -> list[BusyWindow]:
        """Query Google Calendar free/busy data for the next few business days."""
        now = datetime.now(timezone.utc)
        window_end = now + timedelta(days=self.search_window_days)
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://www.googleapis.com/calendar/v3/freeBusy",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "timeMin": now.isoformat(),
                    "timeMax": window_end.isoformat(),
                    "items": [{"id": self.calendar_id}],
                },
            )
            response.raise_for_status()

        payload = response.json()
        busy_ranges = payload.get("calendars", {}).get(self.calendar_id, {}).get("busy", [])
        return [
            BusyWindow(
                start=datetime.fromisoformat(item["start"].replace("Z", "+00:00")),
                end=datetime.fromisoformat(item["end"].replace("Z", "+00:00")),
            )
            for item in busy_ranges
        ]

    def _build_free_slots(self, busy_windows: list[BusyWindow]) -> list[str]:
        """Build candidate interview slots inside business hours."""
        slots: list[str] = []
        cursor = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)
        window_end = cursor + timedelta(days=self.search_window_days)
        duration = timedelta(minutes=self.event_duration_minutes)

        while cursor < window_end and len(slots) < self.slot_count:
            if cursor.weekday() >= 5:
                cursor = self._next_business_day(cursor)
                continue

            if cursor.time() < time(hour=9):
                cursor = cursor.replace(hour=9, minute=0)
            if cursor.time() >= time(hour=17):
                cursor = self._next_business_day(cursor)
                continue

            candidate_end = cursor + duration
            overlaps_busy = any(
                busy.start < candidate_end and busy.end > cursor
                for busy in busy_windows
            )
            if not overlaps_busy:
                slots.append(cursor.isoformat())
            cursor += timedelta(hours=1)

        return slots

    def _fallback_slots(self) -> list[str]:
        """Return deterministic local interview slots."""
        base = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(days=2)
        if base.weekday() >= 5:
            base = self._next_business_day(base)
        base = base.replace(hour=10)
        return [
            base.isoformat(),
            (base + timedelta(hours=2)).isoformat(),
            (base + timedelta(days=1)).isoformat(),
        ]

    @staticmethod
    def _next_business_day(moment: datetime) -> datetime:
        """Move to the next business day at 09:00 UTC."""
        cursor = moment + timedelta(days=1)
        while cursor.weekday() >= 5:
            cursor += timedelta(days=1)
        return cursor.replace(hour=9, minute=0, second=0, microsecond=0)
