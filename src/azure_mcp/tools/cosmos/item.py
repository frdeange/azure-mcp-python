"""Cosmos DB item tools.

Provides tools for item operations:
- cosmos_item_query: SQL-like query
- cosmos_item_get: Get by ID and partition key
- cosmos_item_upsert: Create or update
- cosmos_item_delete: Delete by ID and partition key
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
# cosmos_item_query (Issue #24, P0)
# -----------------------------------------------------------------------------


class CosmosItemQueryOptions(BaseModel):
    """Options for querying items in a Cosmos DB container."""

    account_endpoint: str = Field(
        ...,
        description=(
            "The Cosmos DB account endpoint URL "
            "(e.g., 'https://myaccount.documents.azure.com:443/'). "
            "Obtain this from the cosmos_account_list tool."
        ),
    )
    database_name: str = Field(
        ...,
        description="Name of the database. Obtain from cosmos_database_list.",
    )
    container_name: str = Field(
        ...,
        description="Name of the container. Obtain from cosmos_container_list.",
    )
    query: str = Field(
        ...,
        description=(
            "SQL-like query string (e.g., 'SELECT * FROM c WHERE c.status = @status'). "
            "Use parameterized queries with @param placeholders for safety."
        ),
    )
    parameters: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Query parameters as a list of objects with 'name' and 'value' keys "
            "(e.g., [{'name': '@status', 'value': 'active'}]). "
            "Use parameters instead of string concatenation for safety."
        ),
    )
    max_items: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of items to return.",
    )


@register_tool("cosmos", "item")
class CosmosItemQueryTool(AzureTool):
    """Tool for querying items in a Cosmos DB container."""

    @property
    def name(self) -> str:
        return "cosmos_item_query"

    @property
    def description(self) -> str:
        return (
            "Query items in a Cosmos DB container using SQL-like syntax. "
            "Supports parameterized queries for safe value substitution. "
            "Use cosmos_account_list, cosmos_database_list, and cosmos_container_list "
            "to obtain the required endpoint, database, and container names."
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
        return CosmosItemQueryOptions

    async def execute(self, options: CosmosItemQueryOptions) -> Any:
        """Execute the item query."""
        service = CosmosService()

        try:
            return await service.query_items(
                account_endpoint=options.account_endpoint,
                database_name=options.database_name,
                container_name=options.container_name,
                query=options.query,
                parameters=options.parameters,
                max_items=options.max_items,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# cosmos_item_get (Issue #25, P1)
# -----------------------------------------------------------------------------


class CosmosItemGetOptions(BaseModel):
    """Options for getting a single item from a Cosmos DB container."""

    account_endpoint: str = Field(
        ...,
        description=(
            "The Cosmos DB account endpoint URL. Obtain this from the cosmos_account_list tool."
        ),
    )
    database_name: str = Field(
        ...,
        description="Name of the database.",
    )
    container_name: str = Field(
        ...,
        description="Name of the container.",
    )
    item_id: str = Field(
        ...,
        description="The unique ID of the item to retrieve.",
    )
    partition_key: Any = Field(
        ...,
        description=(
            "The partition key value for the item. "
            "Check cosmos_container_list for the container's partition key path."
        ),
    )


@register_tool("cosmos", "item")
class CosmosItemGetTool(AzureTool):
    """Tool for getting a single item from a Cosmos DB container."""

    @property
    def name(self) -> str:
        return "cosmos_item_get"

    @property
    def description(self) -> str:
        return (
            "Get a single item from a Cosmos DB container by its ID and partition key. "
            "Requires both values for efficient point read. "
            "Use cosmos_container_list to find the partition key path for the container."
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
        return CosmosItemGetOptions

    async def execute(self, options: CosmosItemGetOptions) -> Any:
        """Execute the item get."""
        service = CosmosService()

        try:
            return await service.get_item(
                account_endpoint=options.account_endpoint,
                database_name=options.database_name,
                container_name=options.container_name,
                item_id=options.item_id,
                partition_key=options.partition_key,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# cosmos_item_upsert (Issue #26, P2)
# -----------------------------------------------------------------------------


class CosmosItemUpsertOptions(BaseModel):
    """Options for creating or updating an item in a Cosmos DB container."""

    account_endpoint: str = Field(
        ...,
        description=(
            "The Cosmos DB account endpoint URL. Obtain this from the cosmos_account_list tool."
        ),
    )
    database_name: str = Field(
        ...,
        description="Name of the database.",
    )
    container_name: str = Field(
        ...,
        description="Name of the container.",
    )
    item: dict[str, Any] = Field(
        ...,
        description=(
            "The item to create or update. Must include an 'id' field. "
            "Must also include the partition key field as defined by the container."
        ),
    )


@register_tool("cosmos", "item")
class CosmosItemUpsertTool(AzureTool):
    """Tool for creating or updating an item in a Cosmos DB container."""

    @property
    def name(self) -> str:
        return "cosmos_item_upsert"

    @property
    def description(self) -> str:
        return (
            "Create or update (upsert) an item in a Cosmos DB container. "
            "If an item with the same ID and partition key exists, it will be replaced. "
            "The item must include an 'id' field and the partition key field. "
            "WARNING: This is a write operation that modifies data."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=True,
            idempotent=True,  # Upsert is idempotent - same input = same result
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return CosmosItemUpsertOptions

    async def execute(self, options: CosmosItemUpsertOptions) -> Any:
        """Execute the item upsert."""
        service = CosmosService()

        try:
            return await service.upsert_item(
                account_endpoint=options.account_endpoint,
                database_name=options.database_name,
                container_name=options.container_name,
                item=options.item,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# cosmos_item_delete (Issue #27, P2)
# -----------------------------------------------------------------------------


class CosmosItemDeleteOptions(BaseModel):
    """Options for deleting an item from a Cosmos DB container."""

    account_endpoint: str = Field(
        ...,
        description=(
            "The Cosmos DB account endpoint URL. Obtain this from the cosmos_account_list tool."
        ),
    )
    database_name: str = Field(
        ...,
        description="Name of the database.",
    )
    container_name: str = Field(
        ...,
        description="Name of the container.",
    )
    item_id: str = Field(
        ...,
        description="The unique ID of the item to delete.",
    )
    partition_key: Any = Field(
        ...,
        description=("The partition key value for the item. Required for efficient deletion."),
    )


@register_tool("cosmos", "item")
class CosmosItemDeleteTool(AzureTool):
    """Tool for deleting an item from a Cosmos DB container."""

    @property
    def name(self) -> str:
        return "cosmos_item_delete"

    @property
    def description(self) -> str:
        return (
            "Delete an item from a Cosmos DB container by its ID and partition key. "
            "WARNING: This is a destructive operation that permanently removes data. "
            "The deletion cannot be undone."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=True,
            idempotent=True,  # Deleting same item twice has same effect
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return CosmosItemDeleteOptions

    async def execute(self, options: CosmosItemDeleteOptions) -> Any:
        """Execute the item deletion."""
        service = CosmosService()

        try:
            return await service.delete_item(
                account_endpoint=options.account_endpoint,
                database_name=options.database_name,
                container_name=options.container_name,
                item_id=options.item_id,
                partition_key=options.partition_key,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
