"""Azure MCP Server - Main entry point."""

from __future__ import annotations

import os
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from azure_mcp.core.registry import registry


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP(
        name="Azure MCP Server",
    )

    return mcp


def _get_field_description(field_info: FieldInfo) -> str:
    """Extract description from Pydantic FieldInfo."""
    return field_info.description or ""


def _create_flat_handler(tool: Any, options_model: type[BaseModel]):
    """
    Create a handler with individual Annotated parameters instead of a Pydantic model.

    This generates a flat JSON schema without $ref/$defs that AI Foundry requires.
    We use exec() to dynamically create a function with explicit parameters.
    """
    model_fields = options_model.model_fields
    field_names = list(model_fields.keys())

    # Build parameter strings for the function signature
    param_parts = []
    for field_name, field_info in model_fields.items():
        # Check if field has a default
        if field_info.default is not None and field_info.default is not ...:
            # Has default value
            param_parts.append(f"{field_name}={field_name}_default")
        elif field_info.default_factory is not None:
            # Has default_factory
            param_parts.append(f"{field_name}={field_name}_default")
        else:
            # Required field (no default)
            param_parts.append(field_name)

    params_str = ", ".join(param_parts)
    kwargs_items = ", ".join(f'"{fn}": {fn}' for fn in field_names)

    # Build the function code (use triple braces to escape dict braces in f-string)
    func_code = f"""
async def handler_func({params_str}) -> Any:
    kwargs = {{{kwargs_items}}}
    options = options_model(**kwargs)
    return await tool_instance.execute(options)
"""

    # Prepare the namespace with defaults and dependencies
    namespace = {
        "Any": Any,
        "Annotated": Annotated,
        "options_model": options_model,
        "tool_instance": tool,
    }

    # Add defaults to namespace
    for field_name, field_info in model_fields.items():
        if field_info.default is not None and field_info.default is not ...:
            namespace[f"{field_name}_default"] = field_info.default
        elif field_info.default_factory is not None:
            namespace[f"{field_name}_default"] = field_info.default_factory()

    # Execute to create the function
    exec(func_code, namespace)
    handler = namespace["handler_func"]

    # Set function name and docstring
    handler.__name__ = tool.name
    handler.__doc__ = tool.description

    # Set annotations with Annotated types for schema generation
    annotations = {}
    for field_name, field_info in model_fields.items():
        field_type = field_info.annotation
        description = _get_field_description(field_info)
        annotations[field_name] = Annotated[field_type, description]
    annotations["return"] = Any

    handler.__annotations__ = annotations

    return handler


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""
    # Import tools to trigger registration
    from azure_mcp import tools  # noqa: F401

    # Register all tools with MCP
    for tool in registry.list_tools():
        options_model = tool.options_model

        # Create handler with flat parameters (no $ref in schema)
        handler = _create_flat_handler(tool, options_model)

        # Register with fastmcp
        mcp.tool(name=tool.name)(handler)


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
