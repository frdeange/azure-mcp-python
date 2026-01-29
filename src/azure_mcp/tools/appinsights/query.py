"""Application Insights custom query tool."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.appinsights.service import AppInsightsService


class AppInsightsQueryOptions(BaseModel):
    """Options for running custom KQL queries on Application Insights."""

    resource_id: str = Field(
        ...,
        description=(
            "Full Azure resource ID of the Application Insights resource. "
            "Get this from appinsights_list or appinsights_get. "
            "Format: /subscriptions/{sub}/resourceGroups/{rg}/providers/microsoft.insights/components/{name}"
        ),
    )
    query: str = Field(
        ...,
        description=(
            "KQL (Kusto Query Language) query to execute. "
            "Common tables: traces, exceptions, requests, dependencies, customEvents, pageViews, availabilityResults. "
            "Example: 'requests | where success == false | summarize count() by name'"
        ),
    )
    timespan: str = Field(
        default="P1D",
        description=(
            "Time range in ISO 8601 duration format. "
            "Examples: PT1H (1 hour), P1D (1 day), P7D (7 days), P30D (30 days)."
        ),
    )
    top: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum rows to return. Added as '| take N' if not in query.",
    )


@register_tool("appinsights", "query")
class AppInsightsQueryTool(AzureTool):
    """Run custom KQL queries on Application Insights."""

    @property
    def name(self) -> str:
        return "appinsights_query"

    @property
    def description(self) -> str:
        return (
            "Run a custom KQL query against Application Insights telemetry data. "
            "Supports all App Insights tables: traces, exceptions, requests, dependencies, "
            "customEvents, pageViews, availabilityResults, customMetrics, performanceCounters. "
            "Use this for advanced analytics not covered by specialized tools. "
            "Requires the full resource ID from appinsights_list or appinsights_get."
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
        return AppInsightsQueryOptions

    async def execute(self, options: AppInsightsQueryOptions) -> Any:  # type: ignore[override]
        service = AppInsightsService()
        try:
            return await service.query(
                resource_id=options.resource_id,
                query=options.query,
                timespan=options.timespan,
                top=options.top,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Application Insights Query") from e
