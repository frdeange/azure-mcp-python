"""Error handling utilities.

Provides unified error types and Azure SDK error mapping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any

from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ResourceNotFoundError,
    ServiceRequestError,
)


@dataclass
class ToolError(Exception):
    """Base error for tool operations."""

    message: str
    status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "error": True,
            "status": self.status.value,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class ValidationError(ToolError):
    """Input validation failed."""

    message: str
    status: HTTPStatus = field(default=HTTPStatus.BAD_REQUEST)
    details: dict[str, Any] | None = None
    missing_fields: list[str] | None = None

    def __post_init__(self) -> None:
        if self.missing_fields:
            self.details = self.details or {}
            self.details["missing_fields"] = self.missing_fields


@dataclass
class NotFoundError(ToolError):
    """Resource not found."""

    message: str
    status: HTTPStatus = field(default=HTTPStatus.NOT_FOUND)
    details: dict[str, Any] | None = None


@dataclass
class AuthenticationError(ToolError):
    """Authentication failed."""

    message: str
    status: HTTPStatus = field(default=HTTPStatus.UNAUTHORIZED)
    details: dict[str, Any] | None = None


@dataclass
class PermissionError(ToolError):
    """Permission denied."""

    message: str
    status: HTTPStatus = field(default=HTTPStatus.FORBIDDEN)
    details: dict[str, Any] | None = None


def handle_azure_error(error: Exception) -> ToolError:
    """
    Convert Azure SDK errors to ToolError.

    Args:
        error: An exception from Azure SDK.

    Returns:
        A ToolError with appropriate status code and message.
    """
    if isinstance(error, ResourceNotFoundError):
        return NotFoundError(message=str(error))

    if isinstance(error, ClientAuthenticationError):
        return AuthenticationError(
            message=f"Authentication failed. Please run 'az login' to sign in. Details: {error}"
        )

    if isinstance(error, HttpResponseError):
        status = HTTPStatus.INTERNAL_SERVER_ERROR
        if error.status_code:
            try:
                status = HTTPStatus(error.status_code)
            except ValueError:
                pass

        return ToolError(
            message=str(error),
            status=status,
            details={"azure_error": error.error.code if error.error else None},
        )

    if isinstance(error, ServiceRequestError):
        return ToolError(
            message=f"Azure service unavailable: {error}",
            status=HTTPStatus.SERVICE_UNAVAILABLE,
        )

    # Unknown error
    return ToolError(message=str(error))
