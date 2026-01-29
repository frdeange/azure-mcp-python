"""Application Insights discovery tools - list and get App Insights resources."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.appinsights.service import AppInsightsService


class AppInsightsListOptions(BaseModel):
    """Options for listing Application Insights resources."""

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
        description="Maximum number of resources to return (1-1000).",
    )


class AppInsightsGetOptions(BaseModel):
    """Options for getting a specific Application Insights resource."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    resource_group: str = Field(
        ...,
        description="Resource group containing the Application Insights resource.",
    )
    name: str = Field(
        ...,
        description="Name of the Application Insights resource.",
    )


@register_tool("appinsights", "discovery")
class AppInsightsListTool(AzureTool):
    """List Application Insights resources."""

    @property
    def name(self) -> str:
        return "appinsights_list"

    @property
    def description(self) -> str:
        return (
            "List all Application Insights resources in a subscription. "
            "Returns resource IDs (needed for queries), names, locations, "
            "connection strings, instrumentation keys, and linked workspaces. "
            "Use this to discover App Insights resources before querying telemetry."
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
        return AppInsightsListOptions

    async def execute(self, options: AppInsightsListOptions) -> Any:  # type: ignore[override]
        service = AppInsightsService()
        try:
            return await service.list_app_insights(
                subscription=options.subscription,
                resource_group=options.resource_group,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Application Insights") from e


@register_tool("appinsights", "discovery")
class AppInsightsGetTool(AzureTool):
    """Get a specific Application Insights resource."""

    @property
    def name(self) -> str:
        return "appinsights_get"

    @property
    def description(self) -> str:
        return (
            "Get details of a specific Application Insights resource. "
            "Returns the resource ID (needed for queries), connection string, "
            "instrumentation key, linked Log Analytics workspace, retention settings, "
            "and other configuration. Use appinsights_list first to find resources."
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
        return AppInsightsGetOptions

    async def execute(self, options: AppInsightsGetOptions) -> Any:  # type: ignore[override]
        service = AppInsightsService()
        try:
            return await service.get_app_insights(
                subscription=options.subscription,
                resource_group=options.resource_group,
                name=options.name,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Application Insights") from e
