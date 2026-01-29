"""Azure MCP Tools.

Each tool is organized by service family.
"""

# Import all tool modules here to trigger registration
# Tools use @register_tool decorator which auto-registers on import

from azure_mcp.tools import (
    appinsights,
    cosmos,
    cost,
    entraid,
    monitor,
    rbac,
    resourcegraph,
    storage,
)

__all__ = [
    "appinsights",
    "cosmos",
    "cost",
    "entraid",
    "monitor",
    "rbac",
    "resourcegraph",
    "storage",
]
