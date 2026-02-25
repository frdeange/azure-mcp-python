"""Bing Web Search tool.

Provides:
- bing_web_search: Search the web using Bing Search API v7
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.bing.service import BingService


class BingWebSearchOptions(BaseModel):
    """Options for Bing Web Search."""

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
        description="Web search query string.",
    )
    market: str = Field(
        default="",
        description=(
            "BCP 47 market/locale code for the search results, e.g. 'en-US', 'es-ES'. "
            "Leave empty to use the Bing service default."
        ),
    )
    safe_search: str = Field(
        default="",
        description=(
            "Safe search filter for adult content. "
            "Accepted values: 'Off', 'Moderate', 'Strict'. "
            "Leave empty to use the Bing service default."
        ),
    )
    count: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of web search results to return (1-50).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based page offset for pagination through results.",
    )


@register_tool("bing", "search")
class BingWebSearchTool(AzureTool):
    """Tool for performing Bing Web Search."""

    @property
    def name(self) -> str:
        return "bing_web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web using Bing Search API v7. "
            "Returns web pages, snippets, URLs, and metadata for the search query. "
            "Useful for retrieving up-to-date information, news, documentation, or any web content. "
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
        return BingWebSearchOptions

    async def execute(self, options: BingWebSearchOptions) -> Any:
        """Execute the Bing web search."""
        service = BingService()
        try:
            return await service.web_search(
                subscription=options.subscription,
                resource_name=options.resource_name,
                resource_group=options.resource_group,
                query=options.query,
                market=options.market,
                safe_search=options.safe_search,
                count=options.count,
                offset=options.offset,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
