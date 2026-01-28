"""Cosmos DB database tools.

Provides cosmos_database_list tool for listing databases in a Cosmos DB account.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.cosmos.service import CosmosService


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
