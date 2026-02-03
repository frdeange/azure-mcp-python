"""Azure AI Search suggestion tools.

Provides tools for search suggestions and autocomplete:
- search_suggest: Get suggestions based on partial text
- search_autocomplete: Get autocomplete completions for partial terms
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
# search_suggest
# -----------------------------------------------------------------------------


class SearchSuggestOptions(BaseModel):
    """Options for getting search suggestions."""

    endpoint: str = Field(
        ...,
        description="Azure AI Search service endpoint URL.",
    )
    index_name: str = Field(
        ...,
        description="Name of the search index.",
    )
    search_text: str = Field(
        ...,
        description="Partial search text to get suggestions for (e.g., 'micro' for 'microsoft').",
    )
    suggester_name: str = Field(
        ...,
        description=(
            "Name of the suggester configured in the index. "
            "Use search_index_get to find available suggesters."
        ),
    )
    filter: str = Field(
        default="",
        description="OData filter expression to narrow suggestions. Leave empty for no filter.",
    )
    select: str = Field(
        default="",
        description="Comma-separated fields to return with each suggestion.",
    )
    top: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of suggestions to return.",
    )
    use_fuzzy_matching: bool = Field(
        default=False,
        description="Enable fuzzy matching to handle typos and spelling variations.",
    )
    highlight_pre_tag: str = Field(
        default="",
        description="HTML tag to insert before highlighted text (e.g., '<b>').",
    )
    highlight_post_tag: str = Field(
        default="",
        description="HTML tag to insert after highlighted text (e.g., '</b>').",
    )


@register_tool("search", "suggest")
class SearchSuggestTool(AzureTool):
    """Tool for getting search suggestions based on partial text."""

    @property
    def name(self) -> str:
        return "search_suggest"

    @property
    def description(self) -> str:
        return (
            "Get search suggestions based on partial query text. "
            "Requires a suggester to be configured in the index. "
            "Returns suggested text completions along with matching document fields. "
            "Useful for implementing search-as-you-type experiences."
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
        return SearchSuggestOptions

    async def execute(self, options: SearchSuggestOptions) -> Any:
        """Execute the suggest operation."""
        service = SearchService()

        try:
            return await service.suggest(
                endpoint=options.endpoint,
                index_name=options.index_name,
                search_text=options.search_text,
                suggester_name=options.suggester_name,
                filter_expression=options.filter,
                select_fields=options.select,
                top=options.top,
                use_fuzzy_matching=options.use_fuzzy_matching,
                highlight_pre_tag=options.highlight_pre_tag,
                highlight_post_tag=options.highlight_post_tag,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# search_autocomplete
# -----------------------------------------------------------------------------


class SearchAutocompleteOptions(BaseModel):
    """Options for getting autocomplete suggestions."""

    endpoint: str = Field(
        ...,
        description="Azure AI Search service endpoint URL.",
    )
    index_name: str = Field(
        ...,
        description="Name of the search index.",
    )
    search_text: str = Field(
        ...,
        description="Partial search text to autocomplete (e.g., 'wash' for 'washington').",
    )
    suggester_name: str = Field(
        ...,
        description=(
            "Name of the suggester configured in the index. "
            "Use search_index_get to find available suggesters."
        ),
    )
    mode: str = Field(
        default="oneTerm",
        description=(
            "Autocomplete mode: "
            "'oneTerm' - complete the last term only, "
            "'twoTerms' - complete last two terms, "
            "'oneTermWithContext' - complete with preceding context."
        ),
    )
    filter: str = Field(
        default="",
        description="OData filter expression to narrow results. Leave empty for no filter.",
    )
    top: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of completions to return.",
    )
    use_fuzzy_matching: bool = Field(
        default=False,
        description="Enable fuzzy matching to handle typos.",
    )
    highlight_pre_tag: str = Field(
        default="",
        description="Tag to insert before the completed text portion.",
    )
    highlight_post_tag: str = Field(
        default="",
        description="Tag to insert after the completed text portion.",
    )


@register_tool("search", "suggest")
class SearchAutocompleteTool(AzureTool):
    """Tool for getting autocomplete suggestions for partial terms."""

    @property
    def name(self) -> str:
        return "search_autocomplete"

    @property
    def description(self) -> str:
        return (
            "Get autocomplete suggestions for partial search terms. "
            "Completes partial words to full terms that exist in the index. "
            "Requires a suggester to be configured in the index. "
            "Returns the completed text and the full query string."
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
        return SearchAutocompleteOptions

    async def execute(self, options: SearchAutocompleteOptions) -> Any:
        """Execute the autocomplete operation."""
        service = SearchService()

        try:
            return await service.autocomplete(
                endpoint=options.endpoint,
                index_name=options.index_name,
                search_text=options.search_text,
                suggester_name=options.suggester_name,
                mode=options.mode,
                filter_expression=options.filter,
                top=options.top,
                use_fuzzy_matching=options.use_fuzzy_matching,
                highlight_pre_tag=options.highlight_pre_tag,
                highlight_post_tag=options.highlight_post_tag,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
