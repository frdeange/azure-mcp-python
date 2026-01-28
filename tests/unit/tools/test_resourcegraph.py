"""Tests for Resource Graph query tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from azure_mcp.tools.resourcegraph.query import (
    ResourceGraphQueryOptions,
    ResourceGraphQueryTool,
    ResourceGraphService,
)


class TestResourceGraphQueryOptions:
    """Tests for ResourceGraphQueryOptions model."""

    def test_minimal_options(self):
        """Test creation with minimal required fields."""
        options = ResourceGraphQueryOptions(query="resources")
        assert options.query == "resources"
        assert options.subscriptions == []
        assert options.management_groups == []
        assert options.skip == 0
        assert options.top == 100

    def test_full_options(self):
        """Test creation with all fields."""
        options = ResourceGraphQueryOptions(
            query="resources | limit 10",
            subscriptions=["sub1", "sub2"],
            management_groups=["mg1"],
            skip=50,
            top=500,
        )
        assert options.query == "resources | limit 10"
        assert options.subscriptions == ["sub1", "sub2"]
        assert options.management_groups == ["mg1"]
        assert options.skip == 50
        assert options.top == 500

    def test_top_validation(self):
        """Test that top must be between 1 and 1000."""
        with pytest.raises(ValueError):
            ResourceGraphQueryOptions(query="resources", top=0)

        with pytest.raises(ValueError):
            ResourceGraphQueryOptions(query="resources", top=1001)


class TestResourceGraphQueryTool:
    """Tests for ResourceGraphQueryTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = ResourceGraphQueryTool()
        assert tool.name == "resourcegraph_query"
        assert "Resource Graph" in tool.description
        assert tool.metadata.read_only is True
        assert tool.metadata.idempotent is True

    def test_options_schema(self):
        """Test that options schema is valid JSON schema."""
        tool = ResourceGraphQueryTool()
        schema = tool.get_options_schema()

        assert "properties" in schema
        assert "query" in schema["properties"]
        assert schema["properties"]["query"]["type"] == "string"

    @pytest.mark.asyncio
    async def test_run_validates_options(self):
        """Test that run validates options."""
        tool = ResourceGraphQueryTool()

        # Missing required field should raise
        with pytest.raises(Exception):
            await tool.run({})

    @pytest.mark.asyncio
    async def test_execute_calls_service(self):
        """Test that execute calls the service."""
        tool = ResourceGraphQueryTool()
        options = ResourceGraphQueryOptions(query="resources | limit 1")

        with patch.object(ResourceGraphService, "query") as mock_query:
            mock_query.return_value = {
                "data": [{"id": "test"}],
                "count": 1,
                "total_records": 1,
                "skip_token": None,
                "result_truncated": False,
            }

            result = await tool.execute(options)

            mock_query.assert_called_once_with(
                query="resources | limit 1",
                subscriptions=None,
                management_groups=None,
                skip=0,
                top=100,
            )
            assert result["count"] == 1


class TestResourceGraphService:
    """Tests for ResourceGraphService."""

    @pytest.mark.asyncio
    async def test_query_with_subscriptions(self, mock_resourcegraph_client, patch_credential):
        """Test query with explicit subscriptions."""
        with patch("azure_mcp.tools.resourcegraph.query.ResourceGraphClient") as mock_cls:
            mock_cls.return_value = mock_resourcegraph_client

            service = ResourceGraphService()
            result = await service.query(
                query="resources",
                subscriptions=["sub-id"],
            )

            assert "data" in result
            assert "count" in result
