"""Cosmos DB database tools.

Provides tools for database operations:
- cosmos_database_list: List databases in an account
- cosmos_database_create: Create a database
- cosmos_database_delete: Delete a database
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.cosmos.service import CosmosService


# -----------------------------------------------------------------------------
# cosmos_database_list
# -----------------------------------------------------------------------------


class CosmosDatabaseListOptions(BaseModel):
    """Options for listing databases in a Cosmos DB account."""

    account_endpoint: str = Field(
        ...,
        description=(
            "The Cosmos DB account endpoint URL "
            "(e.g., 'https://myaccount.documents.azure.com:443/'). "
            "Obtain this from the cosmos_account_list tool's 'documentEndpoint' field."
        ),
    )


@register_tool("cosmos", "database")
class CosmosDatabaseListTool(AzureTool):
    """Tool for listing databases in a Cosmos DB account."""

    @property
    def name(self) -> str:
        return "cosmos_database_list"

    @property
    def description(self) -> str:
        return (
            "List all databases in an Azure Cosmos DB account. "
            "Requires the account endpoint URL from cosmos_account_list. "
            "Returns database IDs that can be used with cosmos_container_list and item tools."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return CosmosDatabaseListOptions

    async def execute(self, options: CosmosDatabaseListOptions) -> Any:
        """Execute the database listing."""
        service = CosmosService()

        try:
            return await service.list_databases(
                account_endpoint=options.account_endpoint,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# cosmos_database_create
# -----------------------------------------------------------------------------


class CosmosDatabaseCreateOptions(BaseModel):
    """Options for creating a database in a Cosmos DB account."""

    account_endpoint: str = Field(
        ...,
        description=(
            "The Cosmos DB account endpoint URL "
            "(e.g., 'https://myaccount.documents.azure.com:443/'). "
            "Obtain this from the cosmos_account_list tool's 'documentEndpoint' field."
        ),
    )
    database_name: str = Field(
        ...,
        description="Name of the database to create.",
    )


@register_tool("cosmos", "database")
class CosmosDatabaseCreateTool(AzureTool):
    """Tool for creating a database in a Cosmos DB account."""

    @property
    def name(self) -> str:
        return "cosmos_database_create"

    @property
    def description(self) -> str:
        return (
            "Create a database in an Azure Cosmos DB account. "
            "This operation is idempotent - if the database already exists, "
            "it returns the existing database without error. "
            "WARNING: This is a write operation."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return CosmosDatabaseCreateOptions

    async def execute(self, options: CosmosDatabaseCreateOptions) -> Any:
        """Execute the database creation."""
        service = CosmosService()

        try:
            return await service.create_database(
                account_endpoint=options.account_endpoint,
                database_name=options.database_name,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# cosmos_database_delete
# -----------------------------------------------------------------------------


class CosmosDatabaseDeleteOptions(BaseModel):
    """Options for deleting a database from a Cosmos DB account."""

    account_endpoint: str = Field(
        ...,
        description=(
            "The Cosmos DB account endpoint URL "
            "(e.g., 'https://myaccount.documents.azure.com:443/'). "
            "Obtain this from the cosmos_account_list tool's 'documentEndpoint' field."
        ),
    )
    database_name: str = Field(
        ...,
        description=(
            "Name of the database to delete. Use cosmos_database_list to find available databases."
        ),
    )


@register_tool("cosmos", "database")
class CosmosDatabaseDeleteTool(AzureTool):
    """Tool for deleting a database from a Cosmos DB account."""

    @property
    def name(self) -> str:
        return "cosmos_database_delete"

    @property
    def description(self) -> str:
        return (
            "Delete a database from an Azure Cosmos DB account. "
            "WARNING: This is a destructive operation that permanently deletes "
            "the database and ALL its containers and data. This cannot be undone."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=True,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return CosmosDatabaseDeleteOptions

    async def execute(self, options: CosmosDatabaseDeleteOptions) -> Any:
        """Execute the database deletion."""
        service = CosmosService()

        try:
            return await service.delete_database(
                account_endpoint=options.account_endpoint,
                database_name=options.database_name,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
