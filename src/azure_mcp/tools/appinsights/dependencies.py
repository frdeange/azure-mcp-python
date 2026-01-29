"""Application Insights dependencies query tool."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.appinsights.service import AppInsightsService


class AppInsightsDependenciesQueryOptions(BaseModel):
    """Options for querying dependency call telemetry."""

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
    dependency_type: str = Field(
        default="",
        description=(
            "Filter by dependency type. Common values: 'SQL', 'HTTP', 'Azure blob', "
            "'Azure table', 'Azure queue', 'Azure Service Bus'. Leave empty for all."
        ),
    )
    target: str = Field(
        default="",
        description="Filter where target contains this text (e.g., server name, URL). Leave empty for all.",
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
        description="Filter for calls slower than this duration in milliseconds. 0 for all.",
    )
    top: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum rows to return.",
    )


@register_tool("appinsights", "dependencies")
class AppInsightsDependenciesQueryTool(AzureTool):
    """Query dependency call telemetry."""

    @property
    def name(self) -> str:
        return "appinsights_dependencies_query"

    @property
    def description(self) -> str:
        return (
            "Query dependency calls from Application Insights. "
            "Dependencies are outgoing calls from your application to external services: "
            "SQL databases, HTTP APIs, Azure Storage, Service Bus, Redis, etc. "
            "Filter by type, target, success, or minimum duration. "
            "Use this to find slow external calls, analyze failure rates, or trace data flow."
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
        return AppInsightsDependenciesQueryOptions

    async def execute(self, options: AppInsightsDependenciesQueryOptions) -> Any:  # type: ignore[override]
        service = AppInsightsService()
        try:
            return await service.query_dependencies(
                resource_id=options.resource_id,
                timespan=options.timespan,
                dependency_type=options.dependency_type,
                target=options.target,
                success=options.success,
                min_duration_ms=options.min_duration_ms,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Application Insights Dependencies") from e
