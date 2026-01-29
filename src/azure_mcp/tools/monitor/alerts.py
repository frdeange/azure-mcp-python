"""Azure Monitor alerts tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.monitor.service import MonitorService


class AlertsListOptions(BaseModel):
    """Options for listing fired alerts."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    resource_group: str = Field(
        default="",
        description="Filter by resource group. Leave empty for all.",
    )
    severity: str = Field(
        default="",
        description="Filter by severity: Sev0, Sev1, Sev2, Sev3, Sev4. Leave empty for all.",
    )
    state: str = Field(
        default="",
        description="Filter by state: New, Acknowledged, Closed. Leave empty for all.",
    )
    top: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of alerts to return (1-1000).",
    )


class AlertRulesListOptions(BaseModel):
    """Options for listing alert rules."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    resource_group: str = Field(
        default="",
        description="Filter by resource group. Leave empty for all.",
    )
    top: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of rules to return (1-1000).",
    )


class AlertRuleGetOptions(BaseModel):
    """Options for getting an alert rule."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    resource_group: str = Field(
        ...,
        description="Resource group containing the alert rule.",
    )
    rule_name: str = Field(
        ...,
        description="Name of the alert rule.",
    )


@register_tool("monitor", "alerts")
class MonitorAlertsListTool(AzureTool):
    """List fired alerts in a subscription."""

    @property
    def name(self) -> str:
        return "monitor_alerts_list"

    @property
    def description(self) -> str:
        return (
            "List all fired/active alerts in a subscription. "
            "First step in incident investigation - shows alerts that need attention. "
            "Can filter by severity (Sev0=Critical to Sev4=Verbose) and state (New, Acknowledged, Closed)."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return AlertsListOptions

    async def execute(self, options: AlertsListOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.list_alerts(
                subscription=options.subscription,
                resource_group=options.resource_group,
                severity=options.severity,
                state=options.state,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Alerts") from e


@register_tool("monitor", "alerts")
class MonitorAlertRulesListTool(AzureTool):
    """List configured alert rules."""

    @property
    def name(self) -> str:
        return "monitor_alert_rules_list"

    @property
    def description(self) -> str:
        return (
            "List all configured metric alert rules in a subscription. "
            "Shows rule configuration including conditions, severity, scopes, and enabled status. "
            "Useful for auditing alerting coverage and configuration."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return AlertRulesListOptions

    async def execute(self, options: AlertRulesListOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.list_alert_rules(
                subscription=options.subscription,
                resource_group=options.resource_group,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Alert Rules") from e


@register_tool("monitor", "alerts")
class MonitorAlertRuleGetTool(AzureTool):
    """Get details of a specific alert rule."""

    @property
    def name(self) -> str:
        return "monitor_alert_rule_get"

    @property
    def description(self) -> str:
        return (
            "Get detailed configuration of a specific metric alert rule. "
            "Shows complete rule definition including metric conditions, thresholds, "
            "evaluation frequency, and action groups."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return AlertRuleGetOptions

    async def execute(self, options: AlertRuleGetOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.get_alert_rule(
                subscription=options.subscription,
                resource_group=options.resource_group,
                rule_name=options.rule_name,
            )
        except Exception as e:
            raise handle_azure_error(e, resource=f"Alert Rule '{options.rule_name}'") from e
