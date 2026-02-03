"""Azure AI Search index tools.

Provides tools for managing and exploring search indexes:
- search_index_list: List all indexes in a search service
- search_index_get: Get detailed index definition (schema, fields)
- search_index_stats: Get index statistics (document count, size)
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
# search_index_list
# -----------------------------------------------------------------------------


class SearchIndexListOptions(BaseModel):
    """Options for listing indexes in a search service."""

    endpoint: str = Field(
        ...,
        description=(
            "Azure AI Search service endpoint URL "
            "(e.g., 'https://myservice.search.windows.net'). "
            "Obtain this from search_service_list or search_service_get."
        ),
    )


@register_tool("search", "index")
class SearchIndexListTool(AzureTool):
    """Tool for listing all indexes in an Azure AI Search service."""

    @property
    def name(self) -> str:
        return "search_index_list"

    @property
    def description(self) -> str:
        return (
            "List all search indexes in an Azure AI Search service. "
            "Returns index names, field counts, suggester counts, and whether "
            "semantic search or vector search is configured. "
            "Use the index name with search_query to execute searches."
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
        return SearchIndexListOptions

    async def execute(self, options: SearchIndexListOptions) -> Any:
        """Execute the index list operation."""
        service = SearchService()

        try:
            return await service.list_indexes(endpoint=options.endpoint)
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# search_index_get
# -----------------------------------------------------------------------------


class SearchIndexGetOptions(BaseModel):
    """Options for getting index definition."""

    endpoint: str = Field(
        ...,
        description=(
            "Azure AI Search service endpoint URL (e.g., 'https://myservice.search.windows.net')."
        ),
    )
    index_name: str = Field(
        ...,
        description="Name of the search index to retrieve.",
    )


@register_tool("search", "index")
class SearchIndexGetTool(AzureTool):
    """Tool for getting detailed index definition and schema."""

    @property
    def name(self) -> str:
        return "search_index_get"

    @property
    def description(self) -> str:
        return (
            "Get the complete definition of a search index including all fields, "
            "their types, and properties (searchable, filterable, sortable, facetable). "
            "Also returns suggesters, scoring profiles, and semantic/vector search configuration. "
            "Use this to understand the index schema before querying."
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
        return SearchIndexGetOptions

    async def execute(self, options: SearchIndexGetOptions) -> Any:
        """Execute the index get operation."""
        service = SearchService()

        try:
            return await service.get_index(
                endpoint=options.endpoint,
                index_name=options.index_name,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# search_index_stats
# -----------------------------------------------------------------------------


class SearchIndexStatsOptions(BaseModel):
    """Options for getting index statistics."""

    endpoint: str = Field(
        ...,
        description=(
            "Azure AI Search service endpoint URL (e.g., 'https://myservice.search.windows.net')."
        ),
    )
    index_name: str = Field(
        ...,
        description="Name of the search index.",
    )


@register_tool("search", "index")
class SearchIndexStatsTool(AzureTool):
    """Tool for getting index statistics."""

    @property
    def name(self) -> str:
        return "search_index_stats"

    @property
    def description(self) -> str:
        return (
            "Get statistics for a search index including document count, "
            "storage size in bytes and MB, and vector index size if applicable. "
            "Useful for monitoring index growth and capacity planning."
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
        return SearchIndexStatsOptions

    async def execute(self, options: SearchIndexStatsOptions) -> Any:
        """Execute the index stats operation."""
        service = SearchService()

        try:
            return await service.get_index_statistics(
                endpoint=options.endpoint,
                index_name=options.index_name,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
