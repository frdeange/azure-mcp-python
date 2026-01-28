"""Cosmos DB tools.

Provides tools for interacting with Azure Cosmos DB:
- Account discovery via Resource Graph
- Database and container listing
- Item query, get, upsert, and delete operations
"""

from azure_mcp.tools.cosmos.account import CosmosAccountListTool
from azure_mcp.tools.cosmos.container import CosmosContainerListTool
from azure_mcp.tools.cosmos.database import CosmosDatabaseListTool
from azure_mcp.tools.cosmos.item import (
    CosmosItemDeleteTool,
    CosmosItemGetTool,
    CosmosItemQueryTool,
    CosmosItemUpsertTool,
)

__all__ = [
    "CosmosAccountListTool",
    "CosmosDatabaseListTool",
    "CosmosContainerListTool",
    "CosmosItemQueryTool",
    "CosmosItemGetTool",
    "CosmosItemUpsertTool",
    "CosmosItemDeleteTool",
]
