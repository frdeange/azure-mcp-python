"""Tool registration and discovery.

Provides the registry for all Azure MCP tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from azure_mcp.core.base import AzureTool


@dataclass
class ToolDefinition:
    """Complete definition of a registered tool."""

    tool_class: type[AzureTool]
    group: str
    subgroup: str | None = None


class ToolRegistry:
    """
    Registry of all available MCP tools.

    Tools self-register using the @register_tool decorator.
    The registry provides tool discovery and schema generation for MCP.
    """

    _tools: dict[str, ToolDefinition] = {}
    _instance: ToolRegistry | None = None

    def __new__(cls) -> ToolRegistry:
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance

    def register(
        self,
        tool_class: type[AzureTool],
        group: str,
        subgroup: str | None = None,
    ) -> None:
        """
        Register a tool class.

        Args:
            tool_class: The tool class to register.
            group: Tool group (e.g., "storage", "cosmos").
            subgroup: Optional subgroup (e.g., "blob", "item").
        """
        instance = tool_class()
        self._tools[instance.name] = ToolDefinition(
            tool_class=tool_class,
            group=group,
            subgroup=subgroup,
        )

    def get_tool(self, name: str) -> AzureTool | None:
        """
        Get a tool instance by name.

        Args:
            name: Tool name (e.g., "storage_account_get").

        Returns:
            A new tool instance, or None if not found.
        """
        definition = self._tools.get(name)
        if definition:
            return definition.tool_class()
        return None

    def list_tools(self, group: str | None = None) -> list[AzureTool]:
        """
        List all registered tools.

        Args:
            group: Optional group to filter by.

        Returns:
            List of tool instances.
        """
        tools: list[AzureTool] = []
        for name, definition in self._tools.items():
            if group is None or definition.group == group:
                tools.append(definition.tool_class())
        return tools

    def list_tool_names(self, group: str | None = None) -> list[str]:
        """
        List all registered tool names.

        Args:
            group: Optional group to filter by.

        Returns:
            List of tool names.
        """
        names: list[str] = []
        for name, definition in self._tools.items():
            if group is None or definition.group == group:
                names.append(name)
        return sorted(names)

    def list_groups(self) -> list[str]:
        """List all registered tool groups."""
        groups = set(d.group for d in self._tools.values())
        return sorted(groups)

    def get_tool_schemas(self) -> dict[str, Any]:
        """
        Get MCP-compatible tool definitions for all tools.

        Returns:
            Dictionary mapping tool names to their schemas.
        """
        schemas: dict[str, Any] = {}
        for name, definition in self._tools.items():
            tool = definition.tool_class()
            schemas[name] = {
                "name": name,
                "description": tool.description,
                "inputSchema": tool.get_options_schema(),
                "metadata": tool.metadata.to_dict(),
            }
        return schemas

    def clear(self) -> None:
        """Clear all registered tools (for testing)."""
        self._tools.clear()

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# Global registry instance
registry = ToolRegistry()


def register_tool(
    group: str,
    subgroup: str | None = None,
):
    """
    Decorator to register a tool class.

    Usage:
        @register_tool("storage", "account")
        class StorageAccountGetTool(AzureTool):
            ...

    Args:
        group: Tool group (e.g., "storage", "cosmos").
        subgroup: Optional subgroup (e.g., "blob", "item").

    Returns:
        Decorator function.
    """

    def decorator(cls: type[AzureTool]) -> type[AzureTool]:
        registry.register(cls, group, subgroup)
        return cls

    return decorator
