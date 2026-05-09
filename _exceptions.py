"""
All custom exceptions raised by the GreenPulse SDK.
"""

from typing import Any


class GreenPulseError(Exception):
    """Base exception for all GreenPulse SDK errors."""


class AuthenticationError(GreenPulseError):
    """Raised when login fails or the token has expired."""


class NotFoundError(GreenPulseError):
    """Raised on 404 responses."""


class ValidationError(GreenPulseError):
    """Raised on 400 responses."""

    def __init__(self, detail: Any) -> None:
        self.detail = detail
        super().__init__(f"Validation error: {detail}")


class APIError(GreenPulseError):
    """Raised for any unexpected non-2xx response."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {detail}")
