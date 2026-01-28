"""Storage table tools.

Provides tools for querying Azure Table Storage entities.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.storage.service import StorageService


class StorageTableQueryOptions(BaseModel):
    """Options for querying table entities."""

    account_name: str = Field(
        ...,
        description="Name of the storage account.",
    )
    table_name: str = Field(
        ...,
        description="Name of the table to query.",
    )
    filter_query: str = Field(
        default="",
        description=(
            "OData filter query. Examples: \"PartitionKey eq 'pk1'\", "
            "\"RowKey gt '100' and Status eq 'Active'\". Leave empty for all entities."
        ),
    )
    select: str = Field(
        default="",
        description="Comma-separated list of properties to return. Leave empty for all properties.",
    )
    max_results: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of entities to return.",
    )


@register_tool("storage", "table")
class StorageTableQueryTool(AzureTool):
    """Tool for querying Azure Table Storage entities."""

    @property
    def name(self) -> str:
        return "storage_table_query"

    @property
    def description(self) -> str:
        return (
            "Query entities from an Azure Table Storage table. "
            "Supports OData filter expressions for filtering by PartitionKey, RowKey, "
            "and custom properties. Can select specific properties to return."
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
        return StorageTableQueryOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the table query."""
        opts = StorageTableQueryOptions.model_validate(options.model_dump())
        service = StorageService()
        try:
            return await service.query_table_entities(
                account_name=opts.account_name,
                table_name=opts.table_name,
                filter_query=opts.filter_query,
                select=opts.select,
                max_results=opts.max_results,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Table Entities") from e
