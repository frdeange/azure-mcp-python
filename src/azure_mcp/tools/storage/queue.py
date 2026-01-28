"""Storage queue tools.

Provides tools for listing queues in a storage account.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.storage.service import StorageService


class StorageQueueListOptions(BaseModel):
    """Options for listing queues."""

    account_name: str = Field(
        ...,
        description="Name of the storage account.",
    )
    prefix: str = Field(
        default="",
        description="Prefix to filter queue names. Leave empty for all queues.",
    )
    max_results: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of queues to return.",
    )


@register_tool("storage", "queue")
class StorageQueueListTool(AzureTool):
    """Tool for listing queues in a storage account."""

    @property
    def name(self) -> str:
        return "storage_queue_list"

    @property
    def description(self) -> str:
        return (
            "List queues in an Azure Storage account. "
            "Returns queue names and metadata. "
            "Can be filtered by prefix."
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
        return StorageQueueListOptions

    async def execute(self, options: BaseModel) -> Any:
        """Execute the queue list query."""
        opts = StorageQueueListOptions.model_validate(options.model_dump())
        service = StorageService()
        try:
            return await service.list_queues(
                account_name=opts.account_name,
                prefix=opts.prefix,
                max_results=opts.max_results,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Storage Queues") from e
