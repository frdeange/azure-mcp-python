"""Bing Image Search tool.

Provides:
- bing_image_search: Search for images using Bing Image Search API v7
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.bing.service import BingService


class BingImageSearchOptions(BaseModel):
    """Options for Bing Image Search."""

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
        description="Image search query string.",
    )
    market: str = Field(
        default="",
        description=(
            "BCP 47 market/locale code for the results, e.g. 'en-US'. "
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
        le=150,
        description="Number of image results to return (1-150).",
    )
    size: str = Field(
        default="",
        description=(
            "Filter by image size. "
            "Accepted values: 'Small', 'Medium', 'Large', 'Wallpaper'. "
            "Leave empty to return images of any size."
        ),
    )
    color: str = Field(
        default="",
        description=(
            "Filter by dominant color or color type. "
            "Examples: 'Red', 'Blue', 'Monochrome', 'ColorOnly'. "
            "Leave empty to return images of any color."
        ),
    )


@register_tool("bing", "search")
class BingImageSearchTool(AzureTool):
    """Tool for searching images with Bing Image Search."""

    @property
    def name(self) -> str:
        return "bing_image_search"

    @property
    def description(self) -> str:
        return (
            "Search for images using Bing Image Search API v7. "
            "Returns image URLs, thumbnails, dimensions, content URLs, and host page URLs. "
            "Useful for finding illustrative images, diagrams, or visual content for a topic. "
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
        return BingImageSearchOptions

    async def execute(self, options: BingImageSearchOptions) -> Any:
        """Execute the Bing image search."""
        service = BingService()
        try:
            return await service.image_search(
                subscription=options.subscription,
                resource_name=options.resource_name,
                resource_group=options.resource_group,
                query=options.query,
                market=options.market,
                safe_search=options.safe_search,
                count=options.count,
                size=options.size,
                color=options.color,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
