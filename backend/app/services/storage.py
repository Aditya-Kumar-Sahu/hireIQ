"""Cloudflare R2 resume storage service."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import boto3

from app.core.config import settings


class R2ResumeStorageService:
    """Upload and download candidate resume files from Cloudflare R2."""

    def is_configured(self) -> bool:
        return bool(
            settings.R2_ACCOUNT_ID
            and settings.R2_ACCESS_KEY_ID
            and settings.R2_SECRET_ACCESS_KEY
            and settings.R2_BUCKET_NAME
        )

    @property
    def endpoint_url(self) -> str:
        if settings.R2_ENDPOINT_URL:
            return settings.R2_ENDPOINT_URL
        return f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

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
        if not self.is_configured():
            return None

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
        except Exception:
            return None

    async def download_resume(self, storage_key: str) -> dict[str, object]:
        """Fetch a stored resume object."""

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
        except Exception:
            return {}

    @staticmethod
    def _slugify_filename(filename: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", filename.strip())
        return cleaned or "resume.pdf"
