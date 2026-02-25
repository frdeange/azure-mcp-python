"""Bing Entity Search tool.

Provides:
- bing_entity_search: Search for entities (people, places, things) using Bing Entity Search API v7
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.bing.service import BingService


class BingEntitySearchOptions(BaseModel):
    """Options for Bing Entity Search."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    resource_name: str = Field(
        ...,
        description="Name of the Microsoft.Bing/accounts resource.",
    )
    resource_group: str = Field(
        ...,
        description="Resource group containing the Bing resource.",
    )
    query: str = Field(
        ...,
        description=(
            "Entity search query. Can be a person's name, a company, a place, "
            "a landmark, or any well-known entity."
        ),
    )
    market: str = Field(
        default="",
        description=(
            "BCP 47 market/locale code for the results, e.g. 'en-US'. "
            "Leave empty to use the Bing service default."
        ),
    )


@register_tool("bing", "search")
class BingEntitySearchTool(AzureTool):
    """Tool for searching named entities with Bing Entity Search."""

    @property
    def name(self) -> str:
        return "bing_entity_search"

    @property
    def description(self) -> str:
        return (
            "Search for entities such as people, places, organizations, and things "
            "using Bing Entity Search API v7. "
            "Returns structured entity facts, descriptions, Wikipedia links, and local business info. "
            "Useful for retrieving enriched knowledge about well-known subjects. "
            "Requires a Microsoft.Bing/accounts resource — use bing_resource_list to discover "
            "available resources. The managed identity automatically retrieves the API key."
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
        return BingEntitySearchOptions

    async def execute(self, options: BingEntitySearchOptions) -> Any:
        """Execute the Bing entity search."""
        service = BingService()
        try:
            return await service.entity_search(
                subscription=options.subscription,
                resource_name=options.resource_name,
                resource_group=options.resource_group,
                query=options.query,
                market=options.market,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
