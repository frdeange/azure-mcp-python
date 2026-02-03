"""Azure Storage tools.

Provides tools for managing Azure Storage accounts, blobs, containers, tables, and queues.
"""

from azure_mcp.tools.storage.account import StorageAccountGetTool, StorageAccountListTool
from azure_mcp.tools.storage.blob import (
    StorageBlobDeleteTool,
    StorageBlobListTool,
    StorageBlobReadTool,
    StorageBlobWriteTool,
)
from azure_mcp.tools.storage.container import StorageContainerListTool
from azure_mcp.tools.storage.queue import StorageQueueListTool
from azure_mcp.tools.storage.table import StorageTableQueryTool

__all__ = [
    "StorageAccountListTool",
    "StorageAccountGetTool",
    "StorageContainerListTool",
    "StorageBlobListTool",
    "StorageBlobReadTool",
    "StorageBlobWriteTool",
    "StorageBlobDeleteTool",
    "StorageTableQueryTool",
    "StorageQueueListTool",
]
