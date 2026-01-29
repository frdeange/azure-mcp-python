"""Azure Monitor activity log query tool."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.monitor.service import MonitorService


class ActivityLogQueryOptions(BaseModel):
    """Options for querying Activity Log."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    resource_group: str = Field(
        default="",
        description="Filter by resource group. Leave empty for subscription-wide.",
    )
    resource_id: str = Field(
        default="",
        description="Filter by specific resource ID. Leave empty for all resources.",
    )
    timespan_days: int = Field(
        default=7,
        ge=1,
        le=90,
        description="Time range in days (1-90, default 7).",
    )
    operation_name: str = Field(
        default="",
        description="Filter by operation (e.g., 'Microsoft.Compute/virtualMachines/write'). Leave empty for all.",
    )
    status: str = Field(
        default="",
        description="Filter by status: Succeeded, Failed, Started. Leave empty for all.",
    )
    top: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of events to return (1-1000).",
    )


@register_tool("monitor", "activity")
class MonitorActivityLogQueryTool(AzureTool):
    """Query Azure Activity Log for resource changes."""

    @property
    def name(self) -> str:
        return "monitor_activity_log_query"

    @property
    def description(self) -> str:
        return (
            "Query the Azure Activity Log to find WHO created, deleted, or modified Azure resources, "
            "WHEN changes happened, and WHAT operations were performed. "
            "Use this for auditing infrastructure changes, troubleshooting, and security investigations. "
            "Shows operations like VM creation, storage account deletion, network changes, etc. "
            "\n\n"
            "NOTE: For Entra ID (Azure AD) changes like user/group modifications, "
            "use entraid_audit_logs instead."
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
        return ActivityLogQueryOptions

    async def execute(self, options: ActivityLogQueryOptions) -> Any:  # type: ignore[override]
        service = MonitorService()
        try:
            return await service.query_activity_log(
                subscription=options.subscription,
                resource_group=options.resource_group,
                resource_id=options.resource_id,
                timespan=timedelta(days=options.timespan_days),
                operation_name=options.operation_name,
                status=options.status,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Activity Log") from e
