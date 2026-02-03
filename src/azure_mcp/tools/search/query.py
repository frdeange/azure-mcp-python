"""Azure AI Search query tools.

Provides tools for searching and retrieving documents:
- search_query: Execute full-text and filtered searches
- search_document_get: Get a specific document by key
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
# search_query
# -----------------------------------------------------------------------------


class SearchQueryOptions(BaseModel):
    """Options for executing a search query."""

    endpoint: str = Field(
        ...,
        description=(
            "Azure AI Search service endpoint URL "
            "(e.g., 'https://myservice.search.windows.net'). "
            "Obtain from search_service_list."
        ),
    )
    index_name: str = Field(
        ...,
        description="Name of the search index to query. Obtain from search_index_list.",
    )
    search_text: str = Field(
        default="*",
        description=(
            "Search query text. Use '*' for all documents. "
            "Supports simple query syntax by default, or Lucene syntax if query_type='full'."
        ),
    )
    filter: str = Field(
        default="",
        description=(
            "OData filter expression to narrow results. "
            'Examples: "category eq \'Electronics\'", "price gt 100 and rating ge 4". '
            "Leave empty for no filter."
        ),
    )
    select: str = Field(
        default="",
        description=(
            "Comma-separated list of fields to return. Leave empty for all retrievable fields."
        ),
    )
    order_by: str = Field(
        default="",
        description=(
            "Comma-separated fields to sort by with optional direction. "
            "Example: 'rating desc, price asc'. Leave empty for relevance ranking."
        ),
    )
    top: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of documents to return.",
    )
    skip: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip for pagination.",
    )
    include_total_count: bool = Field(
        default=False,
        description="Include total count of matching documents (may impact performance).",
    )
    search_fields: str = Field(
        default="",
        description=(
            "Comma-separated fields to search in. Leave empty to search all searchable fields."
        ),
    )
    highlight_fields: str = Field(
        default="",
        description=(
            "Comma-separated fields to highlight matching terms in. "
            "Returns highlighted snippets in _highlights."
        ),
    )
    facets: list[str] = Field(
        default_factory=list,
        description=(
            "List of fields to facet on for aggregated counts. "
            "Example: ['category', 'brand']. Pass empty list for no facets."
        ),
    )
    query_type: str = Field(
        default="simple",
        description=(
            "Query syntax type: 'simple' (default) or 'full' (Lucene syntax). "
            "Use 'full' for advanced operators like AND, OR, NOT, wildcards, fuzzy."
        ),
    )
    search_mode: str = Field(
        default="any",
        description=(
            "Search mode: 'any' (match any term) or 'all' (match all terms). "
            "Use 'all' for stricter matching."
        ),
    )


@register_tool("search", "query")
class SearchQueryTool(AzureTool):
    """Tool for executing search queries against an Azure AI Search index."""

    @property
    def name(self) -> str:
        return "search_query"

    @property
    def description(self) -> str:
        return (
            "Execute a search query against an Azure AI Search index. "
            "Supports full-text search, OData filters, sorting, pagination, facets, and highlighting. "
            "Use search_index_get first to understand available fields and their types. "
            "Returns matching documents with optional search scores and highlights."
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
        return SearchQueryOptions

    async def execute(self, options: SearchQueryOptions) -> Any:
        """Execute the search query."""
        service = SearchService()

        try:
            return await service.search_documents(
                endpoint=options.endpoint,
                index_name=options.index_name,
                search_text=options.search_text,
                filter_expression=options.filter,
                select_fields=options.select,
                order_by=options.order_by,
                top=options.top,
                skip=options.skip,
                include_total_count=options.include_total_count,
                search_fields=options.search_fields,
                highlight_fields=options.highlight_fields,
                facets=options.facets if options.facets else None,
                query_type=options.query_type,
                search_mode=options.search_mode,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# search_document_get
# -----------------------------------------------------------------------------


class SearchDocumentGetOptions(BaseModel):
    """Options for getting a specific document by key."""

    endpoint: str = Field(
        ...,
        description="Azure AI Search service endpoint URL.",
    )
    index_name: str = Field(
        ...,
        description="Name of the search index.",
    )
    key: str = Field(
        ...,
        description=(
            "The document key value. This is the value of the field marked as 'key' in the index. "
            "Use search_index_get to identify the key field."
        ),
    )
    select: str = Field(
        default="",
        description="Comma-separated fields to return. Leave empty for all fields.",
    )


@register_tool("search", "query")
class SearchDocumentGetTool(AzureTool):
    """Tool for retrieving a specific document by its key."""

    @property
    def name(self) -> str:
        return "search_document_get"

    @property
    def description(self) -> str:
        return (
            "Get a specific document from a search index by its key. "
            "Faster than searching when you know the exact document key. "
            "The key field is defined in the index schema (use search_index_get to find it)."
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
        return SearchDocumentGetOptions

    async def execute(self, options: SearchDocumentGetOptions) -> Any:
        """Execute the document get operation."""
        service = SearchService()

        try:
            return await service.get_document(
                endpoint=options.endpoint,
                index_name=options.index_name,
                key=options.key,
                selected_fields=options.select,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
