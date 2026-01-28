"""Azure MCP Server - Model Context Protocol tools for Azure services."""

from azure_mcp.core.auth import CredentialProvider
from azure_mcp.core.base import AzureService, AzureTool
from azure_mcp.core.errors import (
    AuthenticationError,
    NotFoundError,
    ToolError,
    ValidationError,
    handle_azure_error,
)
from azure_mcp.core.models import ToolMetadata, ToolResponse
from azure_mcp.core.registry import register_tool, registry

__version__ = "0.1.0"

__all__ = [
    # Auth
    "CredentialProvider",
    # Base classes
    "AzureService",
    "AzureTool",
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
