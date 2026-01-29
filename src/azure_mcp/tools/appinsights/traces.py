"""Application Insights traces query tool."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.appinsights.service import AppInsightsService


class AppInsightsTracesQueryOptions(BaseModel):
    """Options for querying application traces."""

    resource_id: str = Field(
        ...,
        description=(
            "Full Azure resource ID of the Application Insights resource. "
            "Get this from appinsights_list or appinsights_get."
        ),
    )
    timespan: str = Field(
        default="P1D",
        description=(
            "Time range in ISO 8601 duration format. "
            "Examples: PT1H (1 hour), P1D (1 day), P7D (7 days)."
        ),
    )
    severity_level: str = Field(
        default="",
        description=(
            "Filter by severity level. Values: Verbose, Information, Warning, Error, Critical. "
            "Leave empty for all severity levels."
        ),
    )
    message_filter: str = Field(
        default="",
        description="Filter traces where message contains this text. Leave empty for all.",
    )
    top: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum rows to return.",
    )


@register_tool("appinsights", "traces")
class AppInsightsTracesQueryTool(AzureTool):
    """Query application traces and logs."""

    @property
    def name(self) -> str:
        return "appinsights_traces_query"

    @property
    def description(self) -> str:
        return (
            "Query application traces (logs) from Application Insights. "
            "Traces are log messages emitted by your application using ILogger, "
            "TrackTrace, or similar logging frameworks. "
            "Filter by severity level (Verbose, Information, Warning, Error, Critical) "
            "or by message content. Returns timestamp, message, severity, and context."
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
        return AppInsightsTracesQueryOptions

    async def execute(self, options: AppInsightsTracesQueryOptions) -> Any:  # type: ignore[override]
        service = AppInsightsService()
        try:
            return await service.query_traces(
                resource_id=options.resource_id,
                timespan=options.timespan,
                severity_level=options.severity_level,
                message_filter=options.message_filter,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Application Insights Traces") from e
