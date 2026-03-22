"""Utilities for extracting normalized text from uploaded resume PDFs."""

from __future__ import annotations

import re

import fitz

from app.core.exceptions import BadRequestException


class ResumeParser:
    """Parse PDF resumes into normalized plain text."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Collapse excess whitespace while preserving readable spacing."""
        return re.sub(r"\s+", " ", text).strip()

    def extract_text(self, file_bytes: bytes) -> str:
        """Extract text from a PDF payload."""
        try:
            document = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:  # pragma: no cover - fitz error types vary
            raise BadRequestException("Unable to parse resume PDF") from exc

        try:
            raw_text = "\n".join(page.get_text("text") for page in document)
        finally:
            document.close()

        normalized = self.normalize_text(raw_text)
        if not normalized:
            raise BadRequestException("Resume PDF did not contain readable text")
        return normalized
