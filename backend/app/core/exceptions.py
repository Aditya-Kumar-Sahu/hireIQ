"""
Custom exception classes for consistent error handling.

All exceptions raised from services/agents are caught by the global
exception handler middleware in `main.py` and returned as structured
JSON with the standard API envelope.
"""

from __future__ import annotations


class HireIQException(Exception):
    """Base exception for all HireIQ application errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(HireIQException):
    """Resource not found (404)."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            status_code=404,
        )


class UnauthorizedException(HireIQException):
    """Authentication failure (401)."""

    def __init__(self, message: str = "Invalid or expired credentials") -> None:
        super().__init__(message=message, status_code=401)


class ForbiddenException(HireIQException):
    """Authorisation failure (403)."""

    def __init__(self, message: str = "You do not have permission to perform this action") -> None:
        super().__init__(message=message, status_code=403)


class BadRequestException(HireIQException):
    """Client-side validation error (400)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=400)


class ConflictException(HireIQException):
    """Resource conflict — duplicate entry, etc. (409)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=409)
