"""
Common schemas — API response envelope and pagination.

Every API response uses the `APIResponse[T]` envelope for consistency.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""

    success: bool = True
    data: T | None = None
    error: str | None = None


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate the SQL OFFSET from page and limit."""
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response with total count."""

    items: list[T]
    total: int
    page: int
    limit: int
    pages: int
