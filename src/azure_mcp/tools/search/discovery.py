"""Azure AI Search discovery tools.

Provides tools for discovering search services:
- search_service_list: List all search services in a subscription
- search_service_get: Get details of a specific search service
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.search.service import SearchService


# -----------------------------------------------------------------------------
# search_service_list
# -----------------------------------------------------------------------------


class SearchServiceListOptions(BaseModel):
    """Options for listing Azure AI Search services."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    resource_group: str = Field(
        default="",
        description="Filter by resource group. Leave empty for all resource groups.",
    )
    top: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of services to return.",
    )


@register_tool("search", "discovery")
class SearchServiceListTool(AzureTool):
    """Tool for listing Azure AI Search services in a subscription."""

    @property
    def name(self) -> str:
        return "search_service_list"

    @property
    def description(self) -> str:
        return (
            "List all Azure AI Search services in a subscription. "
            "Returns service names, endpoints, SKU, replica/partition counts, and status. "
            "Use the endpoint from this tool when calling search_index_list or search_query."
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
        return SearchServiceListOptions

    async def execute(self, options: SearchServiceListOptions) -> Any:
        """Execute the search service list operation."""
        service = SearchService()

        try:
            return await service.list_search_services(
                subscription=options.subscription,
                resource_group=options.resource_group,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# search_service_get
# -----------------------------------------------------------------------------


class SearchServiceGetOptions(BaseModel):
    """Options for getting a specific Azure AI Search service."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    service_name: str = Field(
        ...,
        description="Name of the Azure AI Search service.",
    )
    resource_group: str = Field(
        default="",
        description="Resource group containing the service. Leave empty to search all.",
    )


@register_tool("search", "discovery")
class SearchServiceGetTool(AzureTool):
    """Tool for getting details of a specific Azure AI Search service."""

    @property
    def name(self) -> str:
        return "search_service_get"

    @property
    def description(self) -> str:
        return (
            "Get detailed information about a specific Azure AI Search service. "
            "Returns endpoint URL, SKU, replica/partition counts, network settings, "
            "and authentication options. Use the endpoint for subsequent search operations."
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
        return SearchServiceGetOptions

    async def execute(self, options: SearchServiceGetOptions) -> Any:
        """Execute the search service get operation."""
        service = SearchService()

        try:
            result = await service.get_search_service(
                subscription=options.subscription,
                service_name=options.service_name,
                resource_group=options.resource_group,
            )
            if result is None:
                return {"error": f"Search service '{options.service_name}' not found."}
            return result
        except Exception as e:
            raise handle_azure_error(e) from e
