"""Azure MCP Core - Base classes and utilities."""

from azure_mcp.core.auth import CredentialProvider
from azure_mcp.core.base import AzureService, AzureTool
from azure_mcp.core.cache import cache
from azure_mcp.core.errors import (
    AuthenticationError,
    NotFoundError,
    ToolError,
    ValidationError,
    handle_azure_error,
)
from azure_mcp.core.models import ToolMetadata, ToolResponse
from azure_mcp.core.registry import register_tool, registry

__all__ = [
    # Auth
    "CredentialProvider",
    # Base classes
    "AzureService",
    "AzureTool",
    # Cache
    "cache",
    # Models
    "ToolMetadata",
    "ToolResponse",
    # Registry
    "registry",
    "register_tool",
    # Errors
    "ToolError",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "handle_azure_error",
]
