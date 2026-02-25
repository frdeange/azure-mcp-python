"""Bing News Search tool.

Provides:
- bing_news_search: Search for news articles using Bing News Search API v7
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.bing.service import BingService


class BingNewsSearchOptions(BaseModel):
    """Options for Bing News Search."""

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
        description="News search query string.",
    )
    market: str = Field(
        default="",
        description=(
            "BCP 47 market/locale code for the results, e.g. 'en-US', 'de-DE'. "
            "Leave empty to use the Bing service default."
        ),
    )
    count: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of news articles to return (1-100).",
    )
    freshness: str = Field(
        default="",
        description=(
            "Filter results by publication date. "
            "Accepted values: 'Day' (last 24 h), 'Week' (last 7 days), 'Month' (last 30 days). "
            "Leave empty to return results from any date."
        ),
    )


@register_tool("bing", "search")
class BingNewsSearchTool(AzureTool):
    """Tool for searching news articles with Bing News Search."""

    @property
    def name(self) -> str:
        return "bing_news_search"

    @property
    def description(self) -> str:
        return (
            "Search for news articles using Bing News Search API v7. "
            "Returns news articles with titles, URLs, descriptions, publication dates, and providers. "
            "Useful for retrieving current events, industry news, or topic-specific articles. "
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
        return BingNewsSearchOptions

    async def execute(self, options: BingNewsSearchOptions) -> Any:
        """Execute the Bing news search."""
        service = BingService()
        try:
            return await service.news_search(
                subscription=options.subscription,
                resource_name=options.resource_name,
                resource_group=options.resource_group,
                query=options.query,
                market=options.market,
                count=options.count,
                freshness=options.freshness,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
