"""Azure MCP Server - Main entry point."""

from __future__ import annotations

import os
from typing import Any

from fastmcp import FastMCP

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
        # Get the Pydantic options model for this tool
        options_model = tool.options_model

        # Create a handler function with explicit Pydantic model parameter
        # fastmcp 2.x requires explicit parameters, not **kwargs
        def make_handler(t: Any, model: type):
            async def handler(options) -> Any:
                return await t.execute(options)

            # Set function metadata for fastmcp - use __annotations__ for runtime type info
            handler.__annotations__ = {"options": model, "return": Any}
            handler.__name__ = t.name
            handler.__doc__ = t.description
            return handler

        mcp.tool(name=tool.name)(make_handler(tool, options_model))


def main() -> None:
    """Run the Azure MCP server (stdio mode)."""
    mcp = create_server()
    register_tools(mcp)
    mcp.run()


def run_http(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the Azure MCP server in HTTP mode for cloud deployment (AI Foundry compatible)."""
    import uvicorn

    mcp = create_server()
    register_tools(mcp)

    # Get the ASGI app for HTTP transport (stateless for AI Foundry compatibility)
    app = mcp.http_app(stateless_http=True)

    uvicorn.run(app, host=host, port=port)


def main_http() -> None:
    """Entry point for HTTP mode with environment configuration."""
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    run_http(host=host, port=port)


if __name__ == "__main__":
    main()
