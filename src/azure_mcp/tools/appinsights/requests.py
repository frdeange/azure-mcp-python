"""Application Insights HTTP requests query tool."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.appinsights.service import AppInsightsService


class AppInsightsRequestsQueryOptions(BaseModel):
    """Options for querying HTTP request telemetry."""

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
    url_filter: str = Field(
        default="",
        description="Filter requests where URL contains this text. Leave empty for all.",
    )
    result_code: str = Field(
        default="",
        description="Filter by HTTP status code (e.g., '500', '404'). Leave empty for all.",
    )
    success: str = Field(
        default="",
        description=(
            "Filter by success status. Values: 'true' for successful, 'false' for failed. "
            "Leave empty for all."
        ),
    )
    min_duration_ms: int = Field(
        default=0,
        ge=0,
        description="Filter for requests slower than this duration in milliseconds. 0 for all.",
    )
    top: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum rows to return.",
    )


@register_tool("appinsights", "requests")
class AppInsightsRequestsQueryTool(AzureTool):
    """Query HTTP request telemetry."""

    @property
    def name(self) -> str:
        return "appinsights_requests_query"

    @property
    def description(self) -> str:
        return (
            "Query HTTP request telemetry from Application Insights. "
            "Shows incoming requests to your application with URL, status code, "
            "duration, and success/failure status. "
            "Filter by URL pattern, HTTP status code, success, or minimum duration. "
            "Use this to analyze API performance, find slow endpoints, or investigate failures."
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
        return AppInsightsRequestsQueryOptions

    async def execute(self, options: AppInsightsRequestsQueryOptions) -> Any:  # type: ignore[override]
        service = AppInsightsService()
        try:
            return await service.query_requests(
                resource_id=options.resource_id,
                timespan=options.timespan,
                url_filter=options.url_filter,
                result_code=options.result_code,
                success=options.success,
                min_duration_ms=options.min_duration_ms,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Application Insights Requests") from e
