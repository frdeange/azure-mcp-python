"""Application Insights exceptions query tool."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.appinsights.service import AppInsightsService


class AppInsightsExceptionsQueryOptions(BaseModel):
    """Options for querying exception telemetry."""

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
    exception_type: str = Field(
        default="",
        description=(
            "Filter by exception type name (e.g., 'NullReferenceException', 'ValueError'). "
            "Leave empty for all exception types."
        ),
    )
    problem_id: str = Field(
        default="",
        description="Filter by problem ID. Leave empty for all.",
    )
    top: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum rows to return.",
    )


@register_tool("appinsights", "exceptions")
class AppInsightsExceptionsQueryTool(AzureTool):
    """Query exception telemetry."""

    @property
    def name(self) -> str:
        return "appinsights_exceptions_query"

    @property
    def description(self) -> str:
        return (
            "Query exceptions from Application Insights. "
            "Shows unhandled and handled exceptions captured by your application. "
            "Filter by exception type or problem ID. "
            "Returns type, message, stack trace details, severity, and operation context. "
            "Use this to investigate application errors and crashes."
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
        return AppInsightsExceptionsQueryOptions

    async def execute(self, options: AppInsightsExceptionsQueryOptions) -> Any:  # type: ignore[override]
        service = AppInsightsService()
        try:
            return await service.query_exceptions(
                resource_id=options.resource_id,
                timespan=options.timespan,
                exception_type=options.exception_type,
                problem_id=options.problem_id,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Application Insights Exceptions") from e
