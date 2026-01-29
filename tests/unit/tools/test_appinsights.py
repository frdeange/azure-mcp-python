"""Unit tests for Application Insights tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from azure_mcp.tools.appinsights.dependencies import AppInsightsDependenciesQueryTool
from azure_mcp.tools.appinsights.discovery import AppInsightsGetTool, AppInsightsListTool
from azure_mcp.tools.appinsights.events import AppInsightsEventsQueryTool
from azure_mcp.tools.appinsights.exceptions import AppInsightsExceptionsQueryTool
from azure_mcp.tools.appinsights.query import AppInsightsQueryTool
from azure_mcp.tools.appinsights.requests import AppInsightsRequestsQueryTool
from azure_mcp.tools.appinsights.traces import AppInsightsTracesQueryTool


class TestAppInsightsToolRegistration:
    """Test that all Application Insights tools are properly registered."""

    def test_appinsights_list_tool_metadata(self):
        """Test appinsights list tool metadata."""
        tool = AppInsightsListTool()
        assert tool.name == "appinsights_list"
        assert "Application Insights" in tool.description
        assert tool.metadata.read_only is True
        assert tool.metadata.idempotent is True

    def test_appinsights_get_tool_metadata(self):
        """Test appinsights get tool metadata."""
        tool = AppInsightsGetTool()
        assert tool.name == "appinsights_get"
        assert "resource ID" in tool.description.lower()

    def test_appinsights_query_tool_metadata(self):
        """Test appinsights query tool metadata."""
        tool = AppInsightsQueryTool()
        assert tool.name == "appinsights_query"
        assert "KQL" in tool.description

    def test_appinsights_traces_query_tool_metadata(self):
        """Test appinsights traces query tool metadata."""
        tool = AppInsightsTracesQueryTool()
        assert tool.name == "appinsights_traces_query"
        assert "traces" in tool.description.lower()
        assert "log" in tool.description.lower()

    def test_appinsights_exceptions_query_tool_metadata(self):
        """Test appinsights exceptions query tool metadata."""
        tool = AppInsightsExceptionsQueryTool()
        assert tool.name == "appinsights_exceptions_query"
        assert "exception" in tool.description.lower()

    def test_appinsights_requests_query_tool_metadata(self):
        """Test appinsights requests query tool metadata."""
        tool = AppInsightsRequestsQueryTool()
        assert tool.name == "appinsights_requests_query"
        assert "HTTP" in tool.description

    def test_appinsights_dependencies_query_tool_metadata(self):
        """Test appinsights dependencies query tool metadata."""
        tool = AppInsightsDependenciesQueryTool()
        assert tool.name == "appinsights_dependencies_query"
        assert "SQL" in tool.description

    def test_appinsights_events_query_tool_metadata(self):
        """Test appinsights events query tool metadata."""
        tool = AppInsightsEventsQueryTool()
        assert tool.name == "appinsights_events_query"
        assert "custom event" in tool.description.lower()


class TestAppInsightsOptionsValidation:
    """Test Pydantic options validation for Application Insights tools."""

    def test_appinsights_list_options_required_fields(self):
        """Test appinsights list requires subscription."""
        from azure_mcp.tools.appinsights.discovery import AppInsightsListOptions

        with pytest.raises(Exception):
            AppInsightsListOptions()

        # Valid options
        options = AppInsightsListOptions(subscription="my-sub")
        assert options.subscription == "my-sub"
        assert options.resource_group == ""  # Default
        assert options.top == 100  # Default

    def test_appinsights_get_options_required_fields(self):
        """Test appinsights get requires all fields."""
        from azure_mcp.tools.appinsights.discovery import AppInsightsGetOptions

        with pytest.raises(Exception):
            AppInsightsGetOptions()

        options = AppInsightsGetOptions(
            subscription="sub",
            resource_group="rg",
            name="my-ai",
        )
        assert options.name == "my-ai"

    def test_appinsights_query_options(self):
        """Test appinsights query options."""
        from azure_mcp.tools.appinsights.query import AppInsightsQueryOptions

        options = AppInsightsQueryOptions(
            resource_id="/subscriptions/sub/resourceGroups/rg/providers/microsoft.insights/components/ai",
            query="traces | take 10",
        )
        assert options.timespan == "P1D"  # Default
        assert options.top == 100  # Default

    def test_appinsights_traces_query_options(self):
        """Test appinsights traces query options."""
        from azure_mcp.tools.appinsights.traces import AppInsightsTracesQueryOptions

        options = AppInsightsTracesQueryOptions(
            resource_id="/subscriptions/sub/...",
            severity_level="Error",
            message_filter="timeout",
        )
        assert options.severity_level == "Error"
        assert options.message_filter == "timeout"

    def test_appinsights_requests_query_options(self):
        """Test appinsights requests query options."""
        from azure_mcp.tools.appinsights.requests import AppInsightsRequestsQueryOptions

        options = AppInsightsRequestsQueryOptions(
            resource_id="/subscriptions/sub/...",
            url_filter="/api/",
            result_code="500",
            success="false",
            min_duration_ms=1000,
        )
        assert options.min_duration_ms == 1000
        assert options.success == "false"

    def test_appinsights_dependencies_query_options(self):
        """Test appinsights dependencies query options."""
        from azure_mcp.tools.appinsights.dependencies import (
            AppInsightsDependenciesQueryOptions,
        )

        options = AppInsightsDependenciesQueryOptions(
            resource_id="/subscriptions/sub/...",
            dependency_type="SQL",
            target="myserver.database.windows.net",
        )
        assert options.dependency_type == "SQL"


class TestAppInsightsServiceMethods:
    """Test AppInsightsService methods with mocks."""

    @pytest.mark.asyncio
    async def test_list_app_insights_uses_resource_graph(self):
        """Test that list_app_insights uses Resource Graph."""
        from azure_mcp.tools.appinsights.service import AppInsightsService

        service = AppInsightsService()

        with patch.object(
            service, "resolve_subscription", new_callable=AsyncMock
        ) as mock_resolve:
            mock_resolve.return_value = "sub-123"

            with patch.object(
                service, "run_resource_graph_query", new_callable=AsyncMock
            ) as mock_rg:
                mock_rg.return_value = [{"name": "app-insights-1"}]

                await service.list_app_insights(
                    subscription="my-sub",
                    resource_group="",
                    top=100,
                )

                assert mock_rg.called
                # Should query for microsoft.insights/components
                query = mock_rg.call_args[0][0].lower()
                assert "microsoft.insights/components" in query

    @pytest.mark.asyncio
    async def test_get_app_insights_not_found(self):
        """Test get_app_insights raises error when not found."""
        from azure_mcp.tools.appinsights.service import AppInsightsService
        from azure_mcp.core.errors import ResourceNotFoundError

        service = AppInsightsService()

        with patch.object(
            service, "resolve_subscription", new_callable=AsyncMock
        ) as mock_resolve:
            mock_resolve.return_value = "sub-123"

            with patch.object(
                service, "run_resource_graph_query", new_callable=AsyncMock
            ) as mock_rg:
                mock_rg.return_value = []  # Not found

                with pytest.raises(ResourceNotFoundError):
                    await service.get_app_insights(
                        subscription="sub",
                        resource_group="rg",
                        name="nonexistent",
                    )

    def test_parse_iso_duration(self):
        """Test ISO 8601 duration parsing."""
        from azure_mcp.tools.appinsights.service import AppInsightsService
        from datetime import timedelta

        service = AppInsightsService()

        assert service._parse_iso_duration("PT1H") == timedelta(hours=1)
        assert service._parse_iso_duration("PT30M") == timedelta(minutes=30)
        assert service._parse_iso_duration("P1D") == timedelta(days=1)
        assert service._parse_iso_duration("P7D") == timedelta(days=7)
        assert service._parse_iso_duration("P1W") == timedelta(weeks=1)
        assert service._parse_iso_duration("P1M") == timedelta(days=30)
        # Invalid format defaults to 1 day
        assert service._parse_iso_duration("invalid") == timedelta(days=1)


class TestAppInsightsSchemaCompatibility:
    """Test that App Insights tool schemas are AI Foundry compatible."""

    def test_no_optional_types_in_appinsights_options(self):
        """Verify AppInsights options don't use Optional types."""
        from azure_mcp.tools.appinsights.discovery import (
            AppInsightsGetOptions,
            AppInsightsListOptions,
        )
        from azure_mcp.tools.appinsights.query import AppInsightsQueryOptions
        from azure_mcp.tools.appinsights.traces import AppInsightsTracesQueryOptions
        from azure_mcp.tools.appinsights.exceptions import (
            AppInsightsExceptionsQueryOptions,
        )
        from azure_mcp.tools.appinsights.requests import AppInsightsRequestsQueryOptions
        from azure_mcp.tools.appinsights.dependencies import (
            AppInsightsDependenciesQueryOptions,
        )
        from azure_mcp.tools.appinsights.events import AppInsightsEventsQueryOptions

        all_options = [
            AppInsightsListOptions,
            AppInsightsGetOptions,
            AppInsightsQueryOptions,
            AppInsightsTracesQueryOptions,
            AppInsightsExceptionsQueryOptions,
            AppInsightsRequestsQueryOptions,
            AppInsightsDependenciesQueryOptions,
            AppInsightsEventsQueryOptions,
        ]

        for options_class in all_options:
            schema = options_class.model_json_schema()
            schema_str = str(schema)
            assert "anyOf" not in schema_str, f"{options_class.__name__} contains anyOf"

    def test_all_required_fields_are_required(self):
        """Verify required fields are marked as required in schema."""
        from azure_mcp.tools.appinsights.query import AppInsightsQueryOptions

        schema = AppInsightsQueryOptions.model_json_schema()
        required = schema.get("required", [])

        assert "resource_id" in required
        assert "query" in required
        # Optional fields should not be in required
        assert "timespan" not in required
        assert "top" not in required
