"""Bing Video Search tool.

Provides:
- bing_video_search: Search for videos using Bing Video Search API v7
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.bing.service import BingService


class BingVideoSearchOptions(BaseModel):
    """Options for Bing Video Search."""

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
        description="Video search query string.",
    )
    market: str = Field(
        default="",
        description=(
            "BCP 47 market/locale code for the results, e.g. 'en-US'. "
            "Leave empty to use the Bing service default."
        ),
    )
    count: int = Field(
        default=10,
        ge=1,
        le=105,
        description="Number of video results to return (1-105).",
    )
    pricing: str = Field(
        default="",
        description=(
            "Filter by video pricing. "
            "Accepted values: 'Free', 'Paid'. "
            "Leave empty to return videos of any pricing."
        ),
    )
    resolution: str = Field(
        default="",
        description=(
            "Filter by video resolution. "
            "Accepted values: 'SD480p', 'HD720p', 'HD1080p'. "
            "Leave empty to return videos of any resolution."
        ),
    )


@register_tool("bing", "search")
class BingVideoSearchTool(AzureTool):
    """Tool for searching videos with Bing Video Search."""

    @property
    def name(self) -> str:
        return "bing_video_search"

    @property
    def description(self) -> str:
        return (
            "Search for videos using Bing Video Search API v7. "
            "Returns video titles, URLs, thumbnails, durations, view counts, and publisher info. "
            "Useful for finding tutorials, demonstrations, or multimedia content on a topic. "
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
        return BingVideoSearchOptions

    async def execute(self, options: BingVideoSearchOptions) -> Any:
        """Execute the Bing video search."""
        service = BingService()
        try:
            return await service.video_search(
                subscription=options.subscription,
                resource_name=options.resource_name,
                resource_group=options.resource_group,
                query=options.query,
                market=options.market,
                count=options.count,
                pricing=options.pricing,
                resolution=options.resolution,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
