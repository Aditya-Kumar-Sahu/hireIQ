"""Cloudflare R2 resume storage service."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

import boto3

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException

logger = logging.getLogger(__name__)


class R2ResumeStorageService:
    """Upload and download candidate resume files from Cloudflare R2."""

    REQUIRED_SETTINGS = (
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME",
    )
    OPTIONAL_TRIGGER_SETTINGS = (
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
    )

    def has_any_configuration(self) -> bool:
        return any(bool(getattr(settings, field)) for field in self.OPTIONAL_TRIGGER_SETTINGS) or bool(
            settings.R2_ENDPOINT_URL
        )

    def missing_settings(self) -> list[str]:
        return [
            field
            for field in self.REQUIRED_SETTINGS
            if not bool(getattr(settings, field))
        ]

    def is_configured(self) -> bool:
        return not self.missing_settings() and self.configuration_error() is None

    def configuration_error(self) -> str | None:
        missing = self.missing_settings()
        if missing:
            if self.has_any_configuration():
                missing_names = ", ".join(missing)
                return f"R2 storage is partially configured. Missing: {missing_names}"
            return None

        endpoint_url = self.endpoint_url
        parsed = urlparse(endpoint_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return "R2 endpoint URL is invalid. Provide a full https:// endpoint URL."

        if not settings.R2_ENDPOINT_URL and not self._looks_like_account_id(settings.R2_ACCOUNT_ID):
            return (
                "R2_ACCOUNT_ID must be your Cloudflare account ID. "
                "If you already have the full endpoint URL, set R2_ENDPOINT_URL instead."
            )

        return None

    @property
    def endpoint_url(self) -> str:
        if settings.R2_ENDPOINT_URL:
            return settings.R2_ENDPOINT_URL.rstrip("/")
        if settings.R2_ACCOUNT_ID.startswith(("http://", "https://")):
            return settings.R2_ACCOUNT_ID.rstrip("/")
        return f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

    def _ensure_runtime_ready(self) -> None:
        error = self.configuration_error()
        if error is None:
            return

        logger.error(
            "R2 storage is misconfigured",
            extra={
                "missing_settings": self.missing_settings(),
                "endpoint_host": urlparse(self.endpoint_url).netloc,
            },
        )
        raise ServiceUnavailableException(error)

    def _client(self) -> Any:
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name=settings.R2_REGION,
        )

    async def upload_resume(
        self,
        *,
        company_id: UUID,
        filename: str,
        file_bytes: bytes,
    ) -> dict[str, object] | None:
        """Persist a PDF resume and return storage metadata when configured."""
        if not self.has_any_configuration():
            return None
        self._ensure_runtime_ready()

        safe_filename = self._slugify_filename(filename)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        storage_key = f"companies/{company_id}/resumes/{timestamp}-{safe_filename}"

        def _upload() -> None:
            client = self._client()
            client.put_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=storage_key,
                Body=file_bytes,
                ContentType="application/pdf",
            )

        try:
            await asyncio.to_thread(_upload)
            return {
                "storage_key": storage_key,
                "content_type": "application/pdf",
                "size_bytes": len(file_bytes),
            }
        except Exception as exc:
            logger.exception(
                "R2 resume upload failed",
                extra={
                    "bucket_name": settings.R2_BUCKET_NAME,
                    "endpoint_host": urlparse(self.endpoint_url).netloc,
                    "storage_key": storage_key,
                    "resume_filename": safe_filename,
                    "error_type": type(exc).__name__,
                },
            )
            raise ServiceUnavailableException(
                "Resume storage is configured but the upload failed. "
                "Check your R2 endpoint, account ID, bucket, and credentials."
            ) from exc

    async def download_resume(self, storage_key: str) -> dict[str, object]:
        """Fetch a stored resume object."""
        if not self.has_any_configuration():
            return {}
        self._ensure_runtime_ready()

        def _download() -> dict[str, object]:
            client = self._client()
            response = client.get_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=storage_key,
            )
            filename = storage_key.rsplit("/", 1)[-1]
            return {
                "filename": filename,
                "content_type": response.get("ContentType", "application/pdf"),
                "file_bytes": response["Body"].read(),
            }

        try:
            return await asyncio.to_thread(_download)
        except Exception as exc:
            logger.exception(
                "R2 resume download failed",
                extra={
                    "bucket_name": settings.R2_BUCKET_NAME,
                    "endpoint_host": urlparse(self.endpoint_url).netloc,
                    "storage_key": storage_key,
                    "error_type": type(exc).__name__,
                },
            )
            raise ServiceUnavailableException(
                "Resume storage is configured but the download failed. "
                "Check your R2 endpoint, bucket, and credentials."
            ) from exc

    @staticmethod
    def _slugify_filename(filename: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", filename.strip())
        return cleaned or "resume.pdf"

    @staticmethod
    def _looks_like_account_id(value: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-z0-9]{6,64}", value.strip()))
