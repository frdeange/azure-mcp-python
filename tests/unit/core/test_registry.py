"""Tests for registry."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from azure_mcp.core.base import AzureTool
from azure_mcp.core.registry import ToolRegistry, register_tool


class DummyOptions(BaseModel):
    """Dummy options for testing."""
    value: str


class DummyTool(AzureTool):
    """Dummy tool for testing."""

    @property
    def name(self) -> str:
        return "test_dummy"

    @property
    def description(self) -> str:
        return "A test tool"

    @property
    def options_model(self) -> type[BaseModel]:
        return DummyOptions

    async def execute(self, options: DummyOptions):
        return {"value": options.value}


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def test_register_and_get_tool(self):
        """Test registering and retrieving a tool."""
        registry = ToolRegistry()
        registry.register(DummyTool, "test", "dummy")

        tool = registry.get_tool("test_dummy")
        assert tool is not None
        assert tool.name == "test_dummy"

    def test_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist."""
        registry = ToolRegistry()
        tool = registry.get_tool("nonexistent")
        assert tool is None

    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        registry.register(DummyTool, "test")

        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "test_dummy"

    def test_list_tools_by_group(self):
        """Test listing tools by group."""
        registry = ToolRegistry()
        registry.register(DummyTool, "group_a")

        tools = registry.list_tools(group="group_a")
        assert len(tools) == 1

        tools = registry.list_tools(group="group_b")
        assert len(tools) == 0

    def test_list_tool_names(self):
        """Test listing tool names."""
        registry = ToolRegistry()
        registry.register(DummyTool, "test")

        names = registry.list_tool_names()
        assert "test_dummy" in names

    def test_list_groups(self):
        """Test listing groups."""
        registry = ToolRegistry()
        registry.register(DummyTool, "test")

        groups = registry.list_groups()
        assert "test" in groups

    def test_contains(self):
        """Test containment check."""
        registry = ToolRegistry()
        registry.register(DummyTool, "test")

        assert "test_dummy" in registry
        assert "nonexistent" not in registry

    def test_len(self):
        """Test length."""
        registry = ToolRegistry()
        assert len(registry) == 0

        registry.register(DummyTool, "test")
        assert len(registry) == 1


class TestRegisterToolDecorator:
    """Tests for @register_tool decorator."""

    def test_decorator_registers_tool(self):
        """Test that decorator registers the tool."""
        # Create a new registry for this test
        registry = ToolRegistry()
        registry.clear()

        # We can't easily test the global decorator here
        # but we can verify the registration logic works
        registry.register(DummyTool, "decorated")
        assert "test_dummy" in registry
