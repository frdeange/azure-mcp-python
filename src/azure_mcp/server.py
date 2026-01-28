"""Azure MCP Server - Main entry point."""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from azure_mcp.core.registry import registry


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP(
        name="Azure MCP Server",
    )

    return mcp


def main() -> None:
    """Run the Azure MCP server."""
    # Import tools to trigger registration
    from azure_mcp import tools  # noqa: F401

    mcp = create_server()

    # Register all tools with MCP
    for tool in registry.list_tools():
        # Create a closure to capture the tool
        def make_handler(t: Any):
            async def handler(**kwargs: Any) -> Any:
                return await t.run(kwargs)
            return handler

        mcp.tool(
            name=tool.name,
            description=tool.description,
        )(make_handler(tool))

    # Run server
    mcp.run()


if __name__ == "__main__":
    main()
