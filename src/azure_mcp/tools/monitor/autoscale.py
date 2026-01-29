"""Azure Monitor autoscale tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.monitor.service import MonitorService


class AutoscaleSettingsListOptions(BaseModel):
    """Options for listing autoscale settings."""

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
        description="Maximum number of settings to return (1-1000).",
    )


class AutoscaleSettingsGetOptions(BaseModel):
    """Options for getting an autoscale setting."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    resource_group: str = Field(
        ...,
        description="Resource group containing the autoscale setting.",
    )
    setting_name: str = Field(
        ...,
        description="Name of the autoscale setting.",
    )


@register_tool("monitor", "autoscale")
class MonitorAutoscaleSettingsListTool(AzureTool):
    """List autoscale settings."""

    @property
    def name(self) -> str:
        return "monitor_autoscale_settings_list"

    @property
    def description(self) -> str:
        return (
            "List all autoscale configurations in a subscription. "
            "Shows target resources, capacity settings (min/max/default instances), "
            "and scaling rules. Useful for capacity planning and troubleshooting scaling issues."
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
        return AutoscaleSettingsListOptions

    async def execute(self, options: AutoscaleSettingsListOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.list_autoscale_settings(
                subscription=options.subscription,
                resource_group=options.resource_group,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Autoscale Settings") from e


@register_tool("monitor", "autoscale")
class MonitorAutoscaleSettingsGetTool(AzureTool):
    """Get details of a specific autoscale setting."""

    @property
    def name(self) -> str:
        return "monitor_autoscale_settings_get"

    @property
    def description(self) -> str:
        return (
            "Get detailed configuration of a specific autoscale setting. "
            "Shows complete profile definitions including scale-out and scale-in rules, "
            "metric triggers, thresholds, and cooldown periods."
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
        return AutoscaleSettingsGetOptions

    async def execute(self, options: AutoscaleSettingsGetOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.get_autoscale_setting(
                subscription=options.subscription,
                resource_group=options.resource_group,
                setting_name=options.setting_name,
            )
        except Exception as e:
            raise handle_azure_error(
                e, resource=f"Autoscale Setting '{options.setting_name}'"
            ) from e
