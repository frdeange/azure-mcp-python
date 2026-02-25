"""Bing Search resource discovery tools.

Provides tools for discovering Microsoft.Bing/accounts resources in Azure:
- bing_resource_list: List all Bing Search resources in a subscription
- bing_resource_get:  Get details of a specific Bing Search resource
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.bing.service import BingService


# ---------------------------------------------------------------------------
# bing_resource_list
# ---------------------------------------------------------------------------


class BingResourceListOptions(BaseModel):
    """Options for listing Microsoft.Bing/accounts resources."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    resource_group: str = Field(
        default="",
        description=("Filter by resource group. Leave empty to list across all resource groups."),
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of resources to return.",
    )


@register_tool("bing", "discovery")
class BingResourceListTool(AzureTool):
    """Tool for listing Bing Search resources in a subscription."""

    @property
    def name(self) -> str:
        return "bing_resource_list"

    @property
    def description(self) -> str:
        return (
            "List all Microsoft.Bing/accounts (Bing Search) resources in an Azure subscription. "
            "Returns resource names, resource groups, locations, SKUs, and kinds. "
            "Use the name and resource_group from this tool when calling bing_web_search, "
            "bing_news_search, bing_image_search, bing_entity_search, or bing_video_search."
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
        return BingResourceListOptions

    async def execute(self, options: BingResourceListOptions) -> Any:
        """Execute the Bing resource list operation."""
        service = BingService()
        try:
            return await service.list_bing_resources(
                subscription=options.subscription,
                resource_group=options.resource_group,
                limit=options.limit,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# ---------------------------------------------------------------------------
# bing_resource_get
# ---------------------------------------------------------------------------


class BingResourceGetOptions(BaseModel):
    """Options for getting a specific Microsoft.Bing/accounts resource."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    resource_name: str = Field(
        ...,
        description="Name of the Microsoft.Bing/accounts resource.",
    )
    resource_group: str = Field(
        default="",
        description=(
            "Resource group containing the Bing resource. "
            "Leave empty to search across all resource groups."
        ),
    )


@register_tool("bing", "discovery")
class BingResourceGetTool(AzureTool):
    """Tool for getting details of a specific Bing Search resource."""

    @property
    def name(self) -> str:
        return "bing_resource_get"

    @property
    def description(self) -> str:
        return (
            "Get detailed information about a specific Microsoft.Bing/accounts resource. "
            "Returns the resource name, resource group, location, SKU, kind, and full properties. "
            "Use this to confirm a Bing resource exists before performing searches."
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
        return BingResourceGetOptions

    async def execute(self, options: BingResourceGetOptions) -> Any:
        """Execute the Bing resource get operation."""
        service = BingService()
        try:
            result = await service.get_bing_resource(
                subscription=options.subscription,
                name=options.resource_name,
                resource_group=options.resource_group,
            )
            if result is None:
                return {"error": f"Bing resource '{options.resource_name}' not found."}
            return result
        except Exception as e:
            raise handle_azure_error(e) from e
