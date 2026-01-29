"""Azure Monitor tools for querying logs, metrics, and managing alerts."""

from azure_mcp.tools.monitor.logs import (
    MonitorLogsQueryTool,
    MonitorLogsQueryResourceTool,
    MonitorLogsBatchQueryTool,
)
from azure_mcp.tools.monitor.metrics import (
    MonitorMetricsQueryTool,
    MonitorMetricDefinitionsListTool,
    MonitorMetricBaselinesGetTool,
)
from azure_mcp.tools.monitor.activity import MonitorActivityLogQueryTool
from azure_mcp.tools.monitor.alerts import (
    MonitorAlertsListTool,
    MonitorAlertRulesListTool,
    MonitorAlertRuleGetTool,
)
from azure_mcp.tools.monitor.autoscale import (
    MonitorAutoscaleSettingsListTool,
    MonitorAutoscaleSettingsGetTool,
)
from azure_mcp.tools.monitor.config import (
    MonitorWorkspaceListTool,
    MonitorActionGroupsListTool,
    MonitorDiagnosticSettingsListTool,
    MonitorDataCollectionRulesListTool,
    MonitorScheduledQueryRulesListTool,
)

__all__ = [
    # Logs
    "MonitorLogsQueryTool",
    "MonitorLogsQueryResourceTool",
    "MonitorLogsBatchQueryTool",
    # Metrics
    "MonitorMetricsQueryTool",
    "MonitorMetricDefinitionsListTool",
    "MonitorMetricBaselinesGetTool",
    # Activity
    "MonitorActivityLogQueryTool",
    # Alerts
    "MonitorAlertsListTool",
    "MonitorAlertRulesListTool",
    "MonitorAlertRuleGetTool",
    # Autoscale
    "MonitorAutoscaleSettingsListTool",
    "MonitorAutoscaleSettingsGetTool",
    # Config
    "MonitorWorkspaceListTool",
    "MonitorActionGroupsListTool",
    "MonitorDiagnosticSettingsListTool",
    "MonitorDataCollectionRulesListTool",
    "MonitorScheduledQueryRulesListTool",
]
