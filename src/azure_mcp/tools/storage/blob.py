"""Storage blob tools.

Provides tools for listing, reading, and writing blobs.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.storage.service import StorageService


class StorageBlobListOptions(BaseModel):
    """Options for listing blobs."""

    account_name: str = Field(
        ...,
        description="Name of the storage account.",
    )
    container_name: str = Field(
        ...,
        description="Name of the container to list blobs from.",
    )
    prefix: str = Field(
        default="",
        description="Prefix to filter blob names. Leave empty for all blobs.",
    )
    max_results: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of blobs to return.",
    )
    include_metadata: bool = Field(
        default=False,
        description="Whether to include blob metadata in results.",
    )


@register_tool("storage", "blob")
class StorageBlobListTool(AzureTool):
    """Tool for listing blobs in a container."""

    @property
    def name(self) -> str:
        return "storage_blob_list"

    @property
    def description(self) -> str:
        return (
            "List blobs in an Azure Storage container. "
            "Returns blob names, sizes, content types, and last modified times. "
            "Can be filtered by prefix and optionally include metadata."
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
        return StorageBlobListOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the blob list query."""
        opts = StorageBlobListOptions.model_validate(options.model_dump())
        service = StorageService()
        try:
            return await service.list_blobs(
                account_name=opts.account_name,
                container_name=opts.container_name,
                prefix=opts.prefix,
                max_results=opts.max_results,
                include_metadata=opts.include_metadata,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Storage Blobs") from e


class StorageBlobReadOptions(BaseModel):
    """Options for reading blob content."""

    account_name: str = Field(
        ...,
        description="Name of the storage account.",
    )
    container_name: str = Field(
        ...,
        description="Name of the container.",
    )
    blob_name: str = Field(
        ...,
        description="Name of the blob to read.",
    )
    encoding: Literal["auto", "utf-8", "base64", "latin-1", "ascii"] = Field(
        default="auto",
        description=(
            "Encoding for content. 'auto' detects text vs binary automatically "
            "(returns base64 for binary). Use 'base64' to force base64 encoding."
        ),
    )
    max_size_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        ge=1,
        le=50 * 1024 * 1024,  # 50 MB max
        description="Maximum blob size to read in bytes. Default 10MB, max 50MB.",
    )


@register_tool("storage", "blob")
class StorageBlobReadTool(AzureTool):
    """Tool for reading blob content."""

    @property
    def name(self) -> str:
        return "storage_blob_read"

    @property
    def description(self) -> str:
        return (
            "Read content from an Azure Storage blob. "
            "Automatically detects text vs binary content. "
            "Returns text content as UTF-8 string, binary content as base64. "
            "Response includes content, encoding used, content_type, and size."
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
        return StorageBlobReadOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the blob read operation."""
        opts = StorageBlobReadOptions.model_validate(options.model_dump())
        service = StorageService()
        try:
            return await service.read_blob(
                account_name=opts.account_name,
                container_name=opts.container_name,
                blob_name=opts.blob_name,
                encoding=opts.encoding,
                max_size_bytes=opts.max_size_bytes,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Storage Blob") from e


class StorageBlobWriteOptions(BaseModel):
    """Options for writing blob content."""

    account_name: str = Field(
        ...,
        description="Name of the storage account.",
    )
    container_name: str = Field(
        ...,
        description="Name of the container.",
    )
    blob_name: str = Field(
        ...,
        description="Name of the blob to write.",
    )
    content: str = Field(
        ...,
        description="Content to write. Text for UTF-8, or base64 string if encoding='base64'.",
    )
    content_type: str = Field(
        default="",
        description="MIME content type (e.g., 'text/plain', 'application/json'). Leave empty for auto-detect.",
    )
    encoding: Literal["utf-8", "base64", "latin-1", "ascii"] = Field(
        default="utf-8",
        description="Encoding of the content. Use 'base64' for binary data.",
    )
    overwrite: bool = Field(
        default=True,
        description="Whether to overwrite existing blob. Set to false to fail if blob exists.",
    )


@register_tool("storage", "blob")
class StorageBlobWriteTool(AzureTool):
    """Tool for writing content to a blob."""

    @property
    def name(self) -> str:
        return "storage_blob_write"

    @property
    def description(self) -> str:
        return (
            "Write content to an Azure Storage blob. "
            "Supports text content (UTF-8) or binary content (base64 encoded). "
            "Can specify content type and whether to overwrite existing blobs."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=True,  # Can overwrite existing blobs
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return StorageBlobWriteOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the blob write operation."""
        opts = StorageBlobWriteOptions.model_validate(options.model_dump())
        service = StorageService()
        try:
            return await service.write_blob(
                account_name=opts.account_name,
                container_name=opts.container_name,
                blob_name=opts.blob_name,
                content=opts.content,
                content_type=opts.content_type,
                encoding=opts.encoding,
                overwrite=opts.overwrite,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Storage Blob") from e


class StorageBlobDeleteOptions(BaseModel):
    """Options for deleting a blob."""

    account_name: str = Field(
        ...,
        description="Name of the storage account.",
    )
    container_name: str = Field(
        ...,
        description="Name of the container.",
    )
    blob_name: str = Field(
        ...,
        description="Name of the blob to delete.",
    )


@register_tool("storage", "blob")
class StorageBlobDeleteTool(AzureTool):
    """Tool for deleting a blob."""

    @property
    def name(self) -> str:
        return "storage_blob_delete"

    @property
    def description(self) -> str:
        return (
            "Delete a blob from an Azure Storage container. "
            "This operation is destructive and cannot be undone "
            "(unless soft-delete is enabled on the storage account). "
            "Also deletes all snapshots of the blob."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=True,  # Requires confirmation
            idempotent=True,   # Safe to retry
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return StorageBlobDeleteOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the blob delete operation."""
        opts = StorageBlobDeleteOptions.model_validate(options.model_dump())
        service = StorageService()
        try:
            return await service.delete_blob(
                account_name=opts.account_name,
                container_name=opts.container_name,
                blob_name=opts.blob_name,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Storage Blob") from e
