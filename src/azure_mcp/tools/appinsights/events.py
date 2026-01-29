"""Application Insights custom events query tool."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.appinsights.service import AppInsightsService


class AppInsightsEventsQueryOptions(BaseModel):
    """Options for querying custom events."""

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
    event_name: str = Field(
        default="",
        description="Filter by specific event name. Leave empty for all events.",
    )
    top: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum rows to return.",
    )


@register_tool("appinsights", "events")
class AppInsightsEventsQueryTool(AzureTool):
    """Query custom events."""

    @property
    def name(self) -> str:
        return "appinsights_events_query"

    @property
    def description(self) -> str:
        return (
            "Query custom events from Application Insights. "
            "Custom events are user-defined telemetry sent via TrackEvent() "
            "to track business logic, feature usage, or custom metrics. "
            "Filter by event name. "
            "Returns event name, timestamp, custom dimensions, and measurements."
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
        return AppInsightsEventsQueryOptions

    async def execute(self, options: AppInsightsEventsQueryOptions) -> Any:  # type: ignore[override]
        service = AppInsightsService()
        try:
            return await service.query_events(
                resource_id=options.resource_id,
                timespan=options.timespan,
                event_name=options.event_name,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Application Insights Events") from e
