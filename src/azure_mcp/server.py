"""Azure MCP Server - Main entry point."""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from azure_mcp.core.registry import registry


def create_server(http_mode: bool = False) -> FastMCP:
    """Create and configure the MCP server.
    
    Args:
        http_mode: If True, configures server for HTTP/cloud deployment
                   with relaxed host validation (allows all hosts).
    """
    # For HTTP/cloud deployment, disable DNS rebinding protection
    # to allow requests from any host (Azure Container Apps, etc.)
    transport_security = None
    if http_mode:
        transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
        )
    
    mcp = FastMCP(
        name="Azure MCP Server",
        transport_security=transport_security,
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

    # Create server with HTTP mode enabled (disables DNS rebinding protection)
    mcp = create_server(http_mode=True)
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
