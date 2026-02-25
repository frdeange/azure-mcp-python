"""Bing Search tools for Azure MCP.

Tools for discovering Microsoft.Bing/accounts resources and performing
web, news, image, entity, and video searches via the Bing Search API v7.

All tools authenticate using DefaultAzureCredential. The API key is
automatically retrieved from the ARM listKeys endpoint and cached for 12 hours
— no environment variables or manual key management required.

Available tools:
- bing_resource_list:  List Microsoft.Bing/accounts resources in a subscription
- bing_resource_get:   Get details of a specific Bing resource
- bing_web_search:     Search the web
- bing_news_search:    Search for news articles
- bing_image_search:   Search for images
- bing_entity_search:  Search for named entities (people, places, organizations)
- bing_video_search:   Search for videos
"""

from azure_mcp.tools.bing.discovery import BingResourceGetTool, BingResourceListTool
from azure_mcp.tools.bing.entities import BingEntitySearchTool
from azure_mcp.tools.bing.images import BingImageSearchTool
from azure_mcp.tools.bing.news import BingNewsSearchTool
from azure_mcp.tools.bing.service import BingService
from azure_mcp.tools.bing.videos import BingVideoSearchTool
from azure_mcp.tools.bing.web import BingWebSearchTool

__all__ = [
    "BingService",
    "BingResourceListTool",
    "BingResourceGetTool",
    "BingWebSearchTool",
    "BingNewsSearchTool",
    "BingImageSearchTool",
    "BingEntitySearchTool",
    "BingVideoSearchTool",
]
