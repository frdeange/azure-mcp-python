"""Azure Monitor configuration tools - workspaces, action groups, diagnostics, etc."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.monitor.service import MonitorService


class WorkspaceListOptions(BaseModel):
    """Options for listing Log Analytics workspaces."""

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
        description="Maximum number of workspaces to return (1-1000).",
    )


class ActionGroupsListOptions(BaseModel):
    """Options for listing action groups."""

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
        description="Maximum number of groups to return (1-1000).",
    )


class DiagnosticSettingsListOptions(BaseModel):
    """Options for listing diagnostic settings."""

    resource_id: str = Field(
        ...,
        description="The full Azure resource ID to list diagnostic settings for.",
    )


class DataCollectionRulesListOptions(BaseModel):
    """Options for listing data collection rules."""

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


class ScheduledQueryRulesListOptions(BaseModel):
    """Options for listing scheduled query rules."""

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


@register_tool("monitor", "config")
class MonitorWorkspaceListTool(AzureTool):
    """List Log Analytics workspaces."""

    @property
    def name(self) -> str:
        return "monitor_workspace_list"

    @property
    def description(self) -> str:
        return (
            "List all Log Analytics workspaces in a subscription. "
            "Returns workspace IDs (needed for monitor_logs_query), names, locations, "
            "SKU, and retention settings. Use this to discover workspaces for log queries."
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
        return WorkspaceListOptions

    async def execute(self, options: WorkspaceListOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.list_workspaces(
                subscription=options.subscription,
                resource_group=options.resource_group,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Log Analytics Workspaces") from e


@register_tool("monitor", "config")
class MonitorActionGroupsListTool(AzureTool):
    """List notification action groups."""

    @property
    def name(self) -> str:
        return "monitor_action_groups_list"

    @property
    def description(self) -> str:
        return (
            "List all action groups in a subscription. "
            "Action groups define WHO gets notified when alerts fire. "
            "Shows email, SMS, webhook, and Azure app push notification receivers."
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
        return ActionGroupsListOptions

    async def execute(self, options: ActionGroupsListOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.list_action_groups(
                subscription=options.subscription,
                resource_group=options.resource_group,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Action Groups") from e


@register_tool("monitor", "config")
class MonitorDiagnosticSettingsListTool(AzureTool):
    """List diagnostic settings for a resource."""

    @property
    def name(self) -> str:
        return "monitor_diagnostic_settings_list"

    @property
    def description(self) -> str:
        return (
            "List diagnostic settings for a specific Azure resource. "
            "Shows what logs and metrics are being collected, and where they're sent "
            "(Log Analytics workspace, storage account, or Event Hub)."
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
        return DiagnosticSettingsListOptions

    async def execute(self, options: DiagnosticSettingsListOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.list_diagnostic_settings(
                resource_id=options.resource_id,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Diagnostic Settings") from e


@register_tool("monitor", "config")
class MonitorDataCollectionRulesListTool(AzureTool):
    """List data collection rules."""

    @property
    def name(self) -> str:
        return "monitor_data_collection_rules_list"

    @property
    def description(self) -> str:
        return (
            "List data collection rules (DCRs) in a subscription. "
            "DCRs define how data is collected and transformed before ingestion. "
            "Used for custom log collection, transformation, and routing."
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
        return DataCollectionRulesListOptions

    async def execute(self, options: DataCollectionRulesListOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.list_data_collection_rules(
                subscription=options.subscription,
                resource_group=options.resource_group,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Data Collection Rules") from e


@register_tool("monitor", "config")
class MonitorScheduledQueryRulesListTool(AzureTool):
    """List scheduled query (log-based) alert rules."""

    @property
    def name(self) -> str:
        return "monitor_scheduled_query_rules_list"

    @property
    def description(self) -> str:
        return (
            "List scheduled query rules (log-based alert rules) in a subscription. "
            "These are alert rules that run KQL queries on a schedule and fire alerts "
            "based on query results. Different from metric alerts which monitor metrics."
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
        return ScheduledQueryRulesListOptions

    async def execute(self, options: ScheduledQueryRulesListOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.list_scheduled_query_rules(
                subscription=options.subscription,
                resource_group=options.resource_group,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Scheduled Query Rules") from e
