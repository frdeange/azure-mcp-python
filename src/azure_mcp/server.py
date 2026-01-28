"""Azure MCP Server - Main entry point."""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from azure_mcp.core.registry import registry


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP(
        name="Azure MCP Server",
    )

    return mcp


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""
    # Import tools to trigger registration
    from azure_mcp import tools  # noqa: F401

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


def main() -> None:
    """Run the Azure MCP server (stdio mode)."""
    mcp = create_server()
    register_tools(mcp)
    mcp.run()


def run_http(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the Azure MCP server in HTTP/SSE mode for cloud deployment."""
    import uvicorn

    mcp = create_server()
    register_tools(mcp)

    # Get the ASGI app for SSE transport (HTTP-based)
    app = mcp.sse_app()

    uvicorn.run(app, host=host, port=port)


def main_http() -> None:
    """Entry point for HTTP mode with environment configuration."""
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    run_http(host=host, port=port)


if __name__ == "__main__":
    main()
