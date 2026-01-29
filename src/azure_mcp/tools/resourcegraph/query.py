"""Resource Graph query tool."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureService, AzureTool
from azure_mcp.core.errors import AzureResourceError, handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool


class ResourceGraphQueryOptions(BaseModel):
    """Options for Resource Graph query tool."""

    query: str = Field(
        ...,
        description="Kusto Query Language (KQL) query to execute against Azure Resource Graph",
    )
    subscriptions: list[str] = Field(
        default_factory=list,
        description="List of subscription IDs to query. If empty, queries all accessible subscriptions.",
    )
    management_groups: list[str] = Field(
        default_factory=list,
        description="List of management group IDs to query. Takes precedence over subscriptions.",
    )
    skip: int = Field(
        default=0,
        ge=0,
        description="Number of rows to skip for pagination.",
    )
    top: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of rows to return.",
    )


class ResourceGraphService(AzureService):
    """Service for Azure Resource Graph operations."""

    async def query(
        self,
        query: str,
        subscriptions: list[str] | None = None,
        management_groups: list[str] | None = None,
        skip: int = 0,
        top: int = 100,
    ) -> dict[str, Any]:
        """
        Execute a Resource Graph query.

        Args:
            query: KQL query string.
            subscriptions: List of subscription IDs.
            management_groups: List of management group IDs.
            skip: Number of rows to skip.
            top: Maximum rows to return.

        Returns:
            Query results with data and metadata.
        """
        # Use the base class method for consistency
        return await self.execute_resource_graph_query(
            query=query,
            subscriptions=subscriptions,
            management_groups=management_groups,
            skip=skip,
            top=top,
        )


@register_tool("resourcegraph")
class ResourceGraphQueryTool(AzureTool):
    """Tool for executing Azure Resource Graph queries."""

    @property
    def name(self) -> str:
        return "resourcegraph_query"

    @property
    def description(self) -> str:
        return (
            "Execute an Azure Resource Graph query using Kusto Query Language (KQL). "
            "Resource Graph provides efficient exploration of Azure resources across "
            "multiple subscriptions. Use this tool to query resource properties, "
            "analyze configurations, and find resources matching specific criteria."
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
        return ResourceGraphQueryOptions

    async def execute(self, options: ResourceGraphQueryOptions) -> Any:
        """Execute the Resource Graph query."""
        service = ResourceGraphService()

        try:
            result = await service.query(
                query=options.query,
                subscriptions=options.subscriptions or None,
                management_groups=options.management_groups or None,
                skip=options.skip,
                top=options.top,
            )
            return result

        except Exception as e:
            raise handle_azure_error(e, resource="Resource Graph")
