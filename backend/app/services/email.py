"""Transactional email delivery via Resend with safe local preview fallbacks."""

from __future__ import annotations

from html import escape

import httpx

from app.core.config import settings


class ResendEmailService:
    """Send transactional emails through Resend or return preview metadata."""

    api_url = "https://api.resend.com/emails"

    @property
    def from_email(self) -> str:
        return settings.FROM_EMAIL

    def is_configured(self) -> bool:
        """Return whether live email delivery can be attempted."""
        return bool(settings.RESEND_API_KEY)

    def delivery_mode(self) -> str:
        """Expose whether live or preview delivery is active."""
        return "live" if self.is_configured() else "preview"

    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        html: str,
    ) -> dict[str, object]:
        """Send an email when configured, else return preview metadata."""
        if not self.is_configured():
            return {
                "mode": "preview",
                "email_id": None,
                "to_email": to_email,
                "from_email": self.from_email,
                "subject": subject,
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": self.from_email,
                    "to": [to_email],
                    "subject": subject,
                    "html": html,
                },
            )
            response.raise_for_status()

        payload = response.json()
        return {
            "mode": "live",
            "email_id": payload.get("id"),
            "to_email": to_email,
            "from_email": self.from_email,
            "subject": subject,
        }

    @staticmethod
    def render_interview_email(
        *,
        candidate_name: str,
        job_title: str,
        scheduled_at: str,
        calendar_link: str | None,
    ) -> str:
        """Render the interview scheduling email body."""
        calendar_line = (
            f'<p><a href="{escape(calendar_link)}">Open calendar event</a></p>'
            if calendar_link
            else ""
        )
        return (
            f"<p>Hi {escape(candidate_name)},</p>"
            f"<p>We'd love to meet with you for the {escape(job_title)} role.</p>"
            f"<p>Your interview is tentatively scheduled for <strong>{escape(scheduled_at)}</strong>.</p>"
            f"{calendar_line}"
            "<p>Reply if you need an alternate slot.</p>"
        )

    @staticmethod
    def render_offer_email(
        *,
        candidate_name: str,
        company_name: str,
        offer_text: str,
    ) -> str:
        """Render the offer delivery email body."""
        return (
            f"<p>Hi {escape(candidate_name)},</p>"
            f"<p>{escape(company_name)} is excited to share the next step in your hiring process.</p>"
            f"<p>{escape(offer_text)}</p>"
            "<p>Please reply with any questions and we’ll keep things moving.</p>"
        )
