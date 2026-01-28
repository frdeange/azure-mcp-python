"""Azure MCP Server - Module entry point.

Allows running the server with: python -m azure_mcp

Supports two modes:
    - stdio (default): For local MCP clients
    - http: For cloud deployment (Azure Container Apps, etc.)

Usage:
    python -m azure_mcp              # stdio mode
    python -m azure_mcp http         # HTTP mode (default port 8000)
    python -m azure_mcp http --port 3000  # HTTP mode with custom port

Environment variables (HTTP mode):
    HOST: Bind address (default: 0.0.0.0)
    PORT: Listen port (default: 8000)
"""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="azure-mcp",
        description="Azure MCP Server - Model Context Protocol tools for Azure services",
    )

    subparsers = parser.add_subparsers(dest="mode", help="Server mode")

    # stdio mode (default)
    subparsers.add_parser("stdio", help="Run in stdio mode (default)")

    # HTTP mode
    http_parser = subparsers.add_parser("http", help="Run in HTTP/SSE mode for cloud deployment")
    http_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    http_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    if args.mode == "http":
        from azure_mcp.server import run_http

        run_http(host=args.host, port=args.port)
    else:
        # Default to stdio mode
        from azure_mcp.server import main as run_stdio

        run_stdio()


if __name__ == "__main__":
    main()
