"""Tests for error handling."""

from __future__ import annotations

import pytest

from azure_mcp.core.errors import (
    AuthenticationError,
    AuthorizationError,
    AzureResourceError,
    ConfigurationError,
    NetworkError,
    RateLimitError,
    ToolError,
    ValidationError,
    handle_azure_error,
)


class TestToolError:
    """Tests for ToolError base class."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = ToolError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.code is None
        assert error.details is None

    def test_error_with_code(self):
        """Test error with code."""
        error = ToolError("Test error", code="TEST001")
        assert error.code == "TEST001"

    def test_error_with_details(self):
        """Test error with details."""
        details = {"key": "value"}
        error = ToolError("Test error", details=details)
        assert error.details == details

    def test_to_dict(self):
        """Test error serialization."""
        error = ToolError("Test", code="CODE", details={"key": "val"})
        d = error.to_dict()
        assert d["error"] == "ToolError"
        assert d["message"] == "Test"
        assert d["code"] == "CODE"
        assert d["details"] == {"key": "val"}


class TestSpecificErrors:
    """Tests for specific error types."""

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid input", field="name")
        assert error.field == "name"
        d = error.to_dict()
        assert d["error"] == "ValidationError"
        assert d["field"] == "name"

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Auth failed")
        d = error.to_dict()
        assert d["error"] == "AuthenticationError"

    def test_authorization_error(self):
        """Test AuthorizationError."""
        error = AuthorizationError("Not allowed", permission="read")
        assert error.permission == "read"
        d = error.to_dict()
        assert d["permission"] == "read"

    def test_resource_error(self):
        """Test AzureResourceError."""
        error = AzureResourceError(
            "Not found",
            resource_type="Microsoft.Storage/storageAccounts",
            resource_name="myaccount",
        )
        assert error.resource_type == "Microsoft.Storage/storageAccounts"
        assert error.resource_name == "myaccount"

    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError("Connection failed", endpoint="https://example.com")
        assert error.endpoint == "https://example.com"

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Too many requests", retry_after=60)
        assert error.retry_after == 60


class TestHandleAzureError:
    """Tests for handle_azure_error function."""

    def test_passes_through_tool_error(self):
        """Test that ToolError passes through unchanged."""
        original = ValidationError("Test")
        result = handle_azure_error(original)
        assert result is original

    def test_converts_generic_exception(self):
        """Test that generic exceptions are converted."""
        original = Exception("Something went wrong")
        result = handle_azure_error(original)
        assert isinstance(result, ToolError)
        assert "Something went wrong" in str(result)

    def test_converts_with_resource_context(self):
        """Test conversion with resource context."""
        original = Exception("Not found")
        result = handle_azure_error(original, resource="Storage Account")
        assert isinstance(result, ToolError)
        assert "Storage Account" in str(result) or "Not found" in str(result)
