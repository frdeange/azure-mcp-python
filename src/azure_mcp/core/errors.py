"""Error handling utilities.

Provides unified error types and Azure SDK error mapping.
"""

from __future__ import annotations

from typing import Any

from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ResourceNotFoundError,
    ServiceRequestError,
)


class ToolError(Exception):
    """Base error for tool operations."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "error": self.__class__.__name__,
            "message": self.message,
        }
        if self.code:
            result["code"] = self.code
        if self.details:
            result["details"] = self.details
        return result


class ValidationError(ToolError):
    """Input validation failed."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)
        self.field = field

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        if self.field:
            result["field"] = self.field
        return result


class NotFoundError(ToolError):
    """Resource not found."""

    def __init__(
        self,
        message: str,
        resource: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)
        self.resource = resource


class AuthenticationError(ToolError):
    """Authentication failed."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


class AuthorizationError(ToolError):
    """Permission denied / authorization failed."""

    def __init__(
        self,
        message: str,
        permission: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)
        self.permission = permission

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        if self.permission:
            result["permission"] = self.permission
        return result


class AzureResourceError(ToolError):
    """Azure resource operation failed."""

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_name: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)
        self.resource_type = resource_type
        self.resource_name = resource_name

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        if self.resource_type:
            result["resource_type"] = self.resource_type
        if self.resource_name:
            result["resource_name"] = self.resource_name
        return result


class NetworkError(ToolError):
    """Network/connection error."""

    def __init__(
        self,
        message: str,
        endpoint: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)
        self.endpoint = endpoint

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        if self.endpoint:
            result["endpoint"] = self.endpoint
        return result


class RateLimitError(ToolError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)
        self.retry_after = retry_after

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        if self.retry_after:
            result["retry_after"] = self.retry_after
        return result


class ConfigurationError(ToolError):
    """Configuration error."""

    def __init__(
        self,
        message: str,
        setting: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)
        self.setting = setting


def handle_azure_error(
    error: Exception,
    resource: str | None = None,
) -> ToolError:
    """
    Convert Azure SDK errors to ToolError.

    Args:
        error: An exception from Azure SDK.
        resource: Optional resource context for error message.

    Returns:
        A ToolError with appropriate status code and message.
    """
    # Pass through existing ToolErrors
    if isinstance(error, ToolError):
        return error

    if isinstance(error, ResourceNotFoundError):
        msg = str(error)
        if resource:
            msg = f"{resource}: {msg}"
        return NotFoundError(message=msg)

    if isinstance(error, ClientAuthenticationError):
        return AuthenticationError(
            message=f"Authentication failed. Please run 'az login' to sign in. Details: {error}"
        )

    if isinstance(error, HttpResponseError):
        msg = str(error)
        if resource:
            msg = f"{resource}: {msg}"

        # Map specific status codes
        if error.status_code == 403:
            return AuthorizationError(message=msg)
        if error.status_code == 429:
            retry_after = None
            if hasattr(error, "headers") and error.headers:
                retry_after = error.headers.get("Retry-After")
                if retry_after:
                    try:
                        retry_after = int(retry_after)
                    except ValueError:
                        retry_after = None
            return RateLimitError(message=msg, retry_after=retry_after)

        return ToolError(
            message=msg,
            details={"azure_error": error.error.code if error.error else None},
        )

    if isinstance(error, ServiceRequestError):
        return NetworkError(message=f"Azure service unavailable: {error}")

    # Unknown error - include resource context if provided
    msg = str(error)
    if resource:
        msg = f"{resource}: {msg}"
    return ToolError(message=msg)
