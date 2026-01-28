"""Azure MCP Tools.

Each tool is organized by service family.
"""

# Import all tool modules here to trigger registration
# Tools use @register_tool decorator which auto-registers on import

from azure_mcp.tools import cosmos, cost, entraid, resourcegraph, storage

__all__ = [
    "cosmos",
    "cost",
    "entraid",
    "resourcegraph",
    "storage",
]
