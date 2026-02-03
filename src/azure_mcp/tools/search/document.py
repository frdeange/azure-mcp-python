"""Azure AI Search document management tools.

Provides tools for document CRUD operations:
- search_document_upload: Upload/index new documents
- search_document_merge: Merge/update existing documents
- search_document_delete: Delete documents from the index

WARNING: These are write operations that modify data.
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
# search_document_upload
# -----------------------------------------------------------------------------


class SearchDocumentUploadOptions(BaseModel):
    """Options for uploading documents to a search index."""

    endpoint: str = Field(
        ...,
        description="Azure AI Search service endpoint URL.",
    )
    index_name: str = Field(
        ...,
        description="Name of the search index to upload documents to.",
    )
    documents: list[dict[str, Any]] = Field(
        ...,
        min_length=1,
        description=(
            "List of documents to upload. Each document must include the key field "
            "defined in the index schema. Existing documents with the same key will be replaced."
        ),
    )


@register_tool("search", "document")
class SearchDocumentUploadTool(AzureTool):
    """Tool for uploading documents to a search index."""

    @property
    def name(self) -> str:
        return "search_document_upload"

    @property
    def description(self) -> str:
        return (
            "Upload documents to an Azure AI Search index. "
            "New documents are added, and existing documents with the same key are replaced. "
            "Each document must include the key field defined in the index schema. "
            "Use search_index_get to find the key field. "
            "WARNING: This is a write operation that modifies data."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=False,
            idempotent=True,  # Upload is idempotent (same doc = same result)
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return SearchDocumentUploadOptions

    async def execute(self, options: SearchDocumentUploadOptions) -> Any:
        """Execute the document upload operation."""
        service = SearchService()

        try:
            return await service.upload_documents(
                endpoint=options.endpoint,
                index_name=options.index_name,
                documents=options.documents,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# search_document_merge
# -----------------------------------------------------------------------------


class SearchDocumentMergeOptions(BaseModel):
    """Options for merging/updating documents in a search index."""

    endpoint: str = Field(
        ...,
        description="Azure AI Search service endpoint URL.",
    )
    index_name: str = Field(
        ...,
        description="Name of the search index.",
    )
    documents: list[dict[str, Any]] = Field(
        ...,
        min_length=1,
        description=(
            "List of partial documents to merge. Each document must include the key field. "
            "Only the fields provided will be updated; other fields remain unchanged. "
            "If a document with the key doesn't exist, the merge will fail for that document."
        ),
    )


@register_tool("search", "document")
class SearchDocumentMergeTool(AzureTool):
    """Tool for merging/updating existing documents in a search index."""

    @property
    def name(self) -> str:
        return "search_document_merge"

    @property
    def description(self) -> str:
        return (
            "Merge updates into existing documents in an Azure AI Search index. "
            "Only the fields specified in the document are updated; other fields remain unchanged. "
            "Each document must include the key field. The document must already exist. "
            "WARNING: This is a write operation that modifies data."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=False,
            idempotent=True,  # Merge is idempotent (same update = same result)
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return SearchDocumentMergeOptions

    async def execute(self, options: SearchDocumentMergeOptions) -> Any:
        """Execute the document merge operation."""
        service = SearchService()

        try:
            return await service.merge_documents(
                endpoint=options.endpoint,
                index_name=options.index_name,
                documents=options.documents,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# search_document_delete
# -----------------------------------------------------------------------------


class SearchDocumentDeleteOptions(BaseModel):
    """Options for deleting documents from a search index."""

    endpoint: str = Field(
        ...,
        description="Azure AI Search service endpoint URL.",
    )
    index_name: str = Field(
        ...,
        description="Name of the search index.",
    )
    documents: list[dict[str, Any]] = Field(
        ...,
        min_length=1,
        description=(
            "List of documents to delete. Each document only needs to contain the key field. "
            "Example: [{'id': 'doc1'}, {'id': 'doc2'}] where 'id' is the key field."
        ),
    )


@register_tool("search", "document")
class SearchDocumentDeleteTool(AzureTool):
    """Tool for deleting documents from a search index."""

    @property
    def name(self) -> str:
        return "search_document_delete"

    @property
    def description(self) -> str:
        return (
            "Delete documents from an Azure AI Search index by their keys. "
            "Each document in the list only needs to contain the key field. "
            "Use search_index_get to find the key field name. "
            "WARNING: This is a destructive operation that permanently removes data."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=True,
            idempotent=True,  # Delete is idempotent (deleting non-existent = no-op)
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return SearchDocumentDeleteOptions

    async def execute(self, options: SearchDocumentDeleteOptions) -> Any:
        """Execute the document delete operation."""
        service = SearchService()

        try:
            return await service.delete_documents(
                endpoint=options.endpoint,
                index_name=options.index_name,
                documents=options.documents,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
