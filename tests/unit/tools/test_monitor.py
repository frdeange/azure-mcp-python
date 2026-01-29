"""Unit tests for Azure Monitor tools."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from azure_mcp.tools.monitor.logs import (
    MonitorLogsBatchQueryTool,
    MonitorLogsQueryResourceTool,
    MonitorLogsQueryTool,
)
from azure_mcp.tools.monitor.metrics import (
    MonitorMetricBaselinesGetTool,
    MonitorMetricDefinitionsListTool,
    MonitorMetricsQueryTool,
)
from azure_mcp.tools.monitor.activity import MonitorActivityLogQueryTool
from azure_mcp.tools.monitor.alerts import (
    MonitorAlertRuleGetTool,
    MonitorAlertRulesListTool,
    MonitorAlertsListTool,
)
from azure_mcp.tools.monitor.autoscale import (
    MonitorAutoscaleSettingsGetTool,
    MonitorAutoscaleSettingsListTool,
)
from azure_mcp.tools.monitor.config import (
    MonitorActionGroupsListTool,
    MonitorDataCollectionRulesListTool,
    MonitorDiagnosticSettingsListTool,
    MonitorScheduledQueryRulesListTool,
    MonitorWorkspaceListTool,
)


class TestMonitorToolRegistration:
    """Test that all Monitor tools are properly registered."""

    def test_logs_query_tool_metadata(self):
        """Test logs query tool metadata."""
        tool = MonitorLogsQueryTool()
        assert tool.name == "monitor_logs_query"
        assert "KQL" in tool.description
        assert tool.metadata.read_only is True
        assert tool.metadata.idempotent is True

    def test_logs_query_resource_tool_metadata(self):
        """Test logs query resource tool metadata."""
        tool = MonitorLogsQueryResourceTool()
        assert tool.name == "monitor_logs_query_resource"
        assert "resource" in tool.description.lower()

    def test_logs_batch_query_tool_metadata(self):
        """Test logs batch query tool metadata."""
        tool = MonitorLogsBatchQueryTool()
        assert tool.name == "monitor_logs_batch_query"
        assert "batch" in tool.description.lower()

    def test_metrics_query_tool_metadata(self):
        """Test metrics query tool metadata."""
        tool = MonitorMetricsQueryTool()
        assert tool.name == "monitor_metrics_query"
        assert "metric" in tool.description.lower()

    def test_metric_definitions_list_tool_metadata(self):
        """Test metric definitions list tool metadata."""
        tool = MonitorMetricDefinitionsListTool()
        assert tool.name == "monitor_metric_definitions_list"

    def test_metric_baselines_get_tool_metadata(self):
        """Test metric baselines get tool metadata."""
        tool = MonitorMetricBaselinesGetTool()
        assert tool.name == "monitor_metric_baselines_get"

    def test_activity_log_query_tool_metadata(self):
        """Test activity log query tool metadata."""
        tool = MonitorActivityLogQueryTool()
        assert tool.name == "monitor_activity_log_query"
        assert "entraid" in tool.description.lower()  # Should mention Entra ID

    def test_alerts_list_tool_metadata(self):
        """Test alerts list tool metadata."""
        tool = MonitorAlertsListTool()
        assert tool.name == "monitor_alerts_list"
        assert "fired" in tool.description.lower()

    def test_alert_rules_list_tool_metadata(self):
        """Test alert rules list tool metadata."""
        tool = MonitorAlertRulesListTool()
        assert tool.name == "monitor_alert_rules_list"

    def test_alert_rule_get_tool_metadata(self):
        """Test alert rule get tool metadata."""
        tool = MonitorAlertRuleGetTool()
        assert tool.name == "monitor_alert_rule_get"

    def test_autoscale_settings_list_tool_metadata(self):
        """Test autoscale settings list tool metadata."""
        tool = MonitorAutoscaleSettingsListTool()
        assert tool.name == "monitor_autoscale_settings_list"

    def test_autoscale_settings_get_tool_metadata(self):
        """Test autoscale settings get tool metadata."""
        tool = MonitorAutoscaleSettingsGetTool()
        assert tool.name == "monitor_autoscale_settings_get"

    def test_workspace_list_tool_metadata(self):
        """Test workspace list tool metadata."""
        tool = MonitorWorkspaceListTool()
        assert tool.name == "monitor_workspace_list"
        assert "Log Analytics" in tool.description

    def test_action_groups_list_tool_metadata(self):
        """Test action groups list tool metadata."""
        tool = MonitorActionGroupsListTool()
        assert tool.name == "monitor_action_groups_list"

    def test_diagnostic_settings_list_tool_metadata(self):
        """Test diagnostic settings list tool metadata."""
        tool = MonitorDiagnosticSettingsListTool()
        assert tool.name == "monitor_diagnostic_settings_list"

    def test_data_collection_rules_list_tool_metadata(self):
        """Test data collection rules list tool metadata."""
        tool = MonitorDataCollectionRulesListTool()
        assert tool.name == "monitor_data_collection_rules_list"

    def test_scheduled_query_rules_list_tool_metadata(self):
        """Test scheduled query rules list tool metadata."""
        tool = MonitorScheduledQueryRulesListTool()
        assert tool.name == "monitor_scheduled_query_rules_list"


class TestMonitorOptionsValidation:
    """Test Pydantic options validation for Monitor tools."""

    def test_logs_query_options_required_fields(self):
        """Test logs query requires workspace_id and query."""
        from azure_mcp.tools.monitor.logs import LogsQueryOptions

        with pytest.raises(Exception):  # Pydantic ValidationError
            LogsQueryOptions()

        # Valid options
        options = LogsQueryOptions(
            workspace_id="test-workspace-id",
            query="AzureActivity | take 10",
        )
        assert options.workspace_id == "test-workspace-id"
        assert options.timespan_hours == 24  # Default
        assert options.include_statistics is False  # Default

    def test_logs_query_options_timespan_default(self):
        """Test logs query timespan defaults to 24 hours."""
        from azure_mcp.tools.monitor.logs import LogsQueryOptions

        options = LogsQueryOptions(
            workspace_id="ws",
            query="query",
        )
        assert options.timespan_hours == 24

    def test_metrics_query_options_validation(self):
        """Test metrics query options validation."""
        from azure_mcp.tools.monitor.metrics import MetricsQueryOptions

        options = MetricsQueryOptions(
            resource_id="/subscriptions/sub/providers/test",
            metric_names="CpuPercentage,MemoryPercentage",
        )
        assert "CpuPercentage" in options.metric_names
        assert options.interval == "PT1M"  # Default

    def test_activity_log_query_options(self):
        """Test activity log query options."""
        from azure_mcp.tools.monitor.activity import ActivityLogQueryOptions

        options = ActivityLogQueryOptions(
            subscription="my-subscription",
            timespan_days=3,
            resource_group="my-rg",
        )
        assert options.subscription == "my-subscription"
        assert options.timespan_days == 3
        assert options.resource_group == "my-rg"


class TestMonitorServiceMethods:
    """Test MonitorService methods with mocks."""

    @pytest.mark.asyncio
    async def test_query_logs_service_instantiation(self):
        """Test MonitorService can be instantiated."""
        from azure_mcp.tools.monitor.service import MonitorService

        service = MonitorService()

        # Verify the service has the expected methods
        assert hasattr(service, "query_logs")
        assert hasattr(service, "list_workspaces")
        assert hasattr(service, "list_alerts")
        assert hasattr(service, "execute_resource_graph_query")

    @pytest.mark.asyncio
    async def test_list_workspaces_uses_resource_graph(self):
        """Test that list_workspaces uses Resource Graph."""
        from azure_mcp.tools.monitor.service import MonitorService

        service = MonitorService()

        with patch.object(service, "resolve_subscription", new_callable=AsyncMock) as mock_resolve:
            mock_resolve.return_value = "sub-123"

            with patch.object(
                service, "execute_resource_graph_query", new_callable=AsyncMock
            ) as mock_rg:
                mock_rg.return_value = {"data": [{"name": "workspace1"}], "count": 1}

                result = await service.list_workspaces(
                    subscription="my-sub",
                    resource_group="",
                    top=100,
                )

                assert mock_rg.called
                assert "operationalinsights/workspaces" in mock_rg.call_args[1]["query"].lower()


class TestMonitorSchemaCompatibility:
    """Test that Monitor tool schemas are AI Foundry compatible."""

    def test_no_optional_types_in_logs_query_options(self):
        """Verify LogsQueryOptions doesn't use Optional types."""
        from azure_mcp.tools.monitor.logs import LogsQueryOptions

        schema = LogsQueryOptions.model_json_schema()

        # Check no anyOf (which would come from Optional types)
        schema_str = str(schema)
        assert "anyOf" not in schema_str, "Schema contains anyOf (likely from Optional type)"

    def test_no_optional_types_in_metrics_query_options(self):
        """Verify MetricsQueryOptions doesn't use Optional types."""
        from azure_mcp.tools.monitor.metrics import MetricsQueryOptions

        schema = MetricsQueryOptions.model_json_schema()
        schema_str = str(schema)
        assert "anyOf" not in schema_str

    def test_all_monitor_tools_have_valid_schemas(self):
        """Verify all Monitor tool options have AI Foundry compatible schemas."""
        from azure_mcp.tools.monitor.logs import (
            LogsQueryOptions,
            LogsQueryResourceOptions,
            LogsBatchQueryOptions,
        )
        from azure_mcp.tools.monitor.metrics import (
            MetricsQueryOptions,
            MetricDefinitionsListOptions,
            MetricBaselinesGetOptions,
        )
        from azure_mcp.tools.monitor.activity import ActivityLogQueryOptions
        from azure_mcp.tools.monitor.alerts import (
            AlertsListOptions,
            AlertRulesListOptions,
            AlertRuleGetOptions,
        )
        from azure_mcp.tools.monitor.autoscale import (
            AutoscaleSettingsListOptions,
            AutoscaleSettingsGetOptions,
        )
        from azure_mcp.tools.monitor.config import (
            WorkspaceListOptions,
            ActionGroupsListOptions,
            DiagnosticSettingsListOptions,
            DataCollectionRulesListOptions,
            ScheduledQueryRulesListOptions,
        )

        all_options = [
            LogsQueryOptions,
            LogsQueryResourceOptions,
            LogsBatchQueryOptions,
            MetricsQueryOptions,
            MetricDefinitionsListOptions,
            MetricBaselinesGetOptions,
            ActivityLogQueryOptions,
            AlertsListOptions,
            AlertRulesListOptions,
            AlertRuleGetOptions,
            AutoscaleSettingsListOptions,
            AutoscaleSettingsGetOptions,
            WorkspaceListOptions,
            ActionGroupsListOptions,
            DiagnosticSettingsListOptions,
            DataCollectionRulesListOptions,
            ScheduledQueryRulesListOptions,
        ]

        for options_class in all_options:
            schema = options_class.model_json_schema()
            schema_str = str(schema)
            assert "anyOf" not in schema_str, f"{options_class.__name__} contains anyOf"
            assert "$ref" not in schema_str or "$defs" not in schema_str, (
                f"{options_class.__name__} contains complex references"
            )
