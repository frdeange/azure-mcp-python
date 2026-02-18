"""Cosmos DB tools.

Provides tools for interacting with Azure Cosmos DB:
- Account discovery and details via Resource Graph
- Database create, list, and delete operations
- Container create, list, and delete operations
- Item query, get, upsert, and delete operations
"""

from azure_mcp.tools.cosmos.account import CosmosAccountGetTool, CosmosAccountListTool
from azure_mcp.tools.cosmos.container import (
    CosmosContainerCreateTool,
    CosmosContainerDeleteTool,
    CosmosContainerListTool,
)
from azure_mcp.tools.cosmos.database import (
    CosmosDatabaseCreateTool,
    CosmosDatabaseDeleteTool,
    CosmosDatabaseListTool,
)
from azure_mcp.tools.cosmos.item import (
    CosmosItemDeleteTool,
    CosmosItemGetTool,
    CosmosItemQueryTool,
    CosmosItemUpsertTool,
)

__all__ = [
    "CosmosAccountListTool",
    "CosmosAccountGetTool",
    "CosmosDatabaseListTool",
    "CosmosDatabaseCreateTool",
    "CosmosDatabaseDeleteTool",
    "CosmosContainerListTool",
    "CosmosContainerCreateTool",
    "CosmosContainerDeleteTool",
    "CosmosItemQueryTool",
    "CosmosItemGetTool",
    "CosmosItemUpsertTool",
    "CosmosItemDeleteTool",
]
