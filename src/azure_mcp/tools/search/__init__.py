"""Azure AI Search tools.

Provides tools for interacting with Azure AI Search:
- Service discovery via Resource Graph
- Index listing and schema inspection
- Full-text and filtered search queries
- Suggestions and autocomplete
- Document upload, merge, and delete operations
"""

from azure_mcp.tools.search.discovery import (
    SearchServiceGetTool,
    SearchServiceListTool,
)
from azure_mcp.tools.search.document import (
    SearchDocumentDeleteTool,
    SearchDocumentMergeTool,
    SearchDocumentUploadTool,
)
from azure_mcp.tools.search.index import (
    SearchIndexGetTool,
    SearchIndexListTool,
    SearchIndexStatsTool,
)
from azure_mcp.tools.search.query import (
    SearchDocumentGetTool,
    SearchQueryTool,
)
from azure_mcp.tools.search.suggest import (
    SearchAutocompleteTool,
    SearchSuggestTool,
)

__all__ = [
    # Discovery
    "SearchServiceListTool",
    "SearchServiceGetTool",
    # Index management
    "SearchIndexListTool",
    "SearchIndexGetTool",
    "SearchIndexStatsTool",
    # Query operations
    "SearchQueryTool",
    "SearchDocumentGetTool",
    # Suggestions
    "SearchSuggestTool",
    "SearchAutocompleteTool",
    # Document management
    "SearchDocumentUploadTool",
    "SearchDocumentMergeTool",
    "SearchDocumentDeleteTool",
]
