"""Azure MCP Tools.

Each tool is organized by service family.
"""

# Import all tool modules here to trigger registration
# Tools use @register_tool decorator which auto-registers on import

from azure_mcp.tools import (
    appinsights,
    bing,
    communication,
    cosmos,
    cost,
    entraid,
    monitor,
    rbac,
    resourcegraph,
    search,
    storage,
)

__all__ = [
    "appinsights",
    "bing",
    "communication",
    "cosmos",
    "cost",
    "entraid",
    "monitor",
    "rbac",
    "resourcegraph",
    "search",
    "storage",
]
