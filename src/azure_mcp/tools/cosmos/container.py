"""Cosmos DB container tools.

Provides cosmos_container_list tool for listing containers in a database.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.cosmos.service import CosmosService


class CosmosContainerListOptions(BaseModel):
    """Options for listing containers in a Cosmos DB database."""

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
            "Name of the database to list containers from. "
            "Obtain available database names from cosmos_database_list."
        ),
    )


@register_tool("cosmos", "container")
class CosmosContainerListTool(AzureTool):
    """Tool for listing containers in a Cosmos DB database."""

    @property
    def name(self) -> str:
        return "cosmos_container_list"

    @property
    def description(self) -> str:
        return (
            "List all containers in a Cosmos DB database. "
            "Requires account endpoint from cosmos_account_list and database name from cosmos_database_list. "
            "Returns container IDs and partition key paths needed for item operations."
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
        return CosmosContainerListOptions

    async def execute(self, options: CosmosContainerListOptions) -> Any:
        """Execute the container listing."""
        service = CosmosService()

        try:
            return await service.list_containers(
                account_endpoint=options.account_endpoint,
                database_name=options.database_name,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
