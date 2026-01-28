"""Cost query tool for Azure Cost Management.

Provides the cost_query tool for querying cost data.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.cost.service import CostManagementService


class CostQueryOptions(BaseModel):
    """Options for querying cost data."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name to query costs for.",
    )
    resource_group: str = Field(
        default="",
        description="Resource group to scope the query. Leave empty for subscription-level.",
    )
    timeframe: Literal[
        "MonthToDate",
        "BillingMonthToDate",
        "TheLastMonth",
        "TheLastBillingMonth",
        "WeekToDate",
        "Custom",
    ] = Field(
        default="MonthToDate",
        description="Time period for cost data.",
    )
    granularity: Literal["None", "Daily", "Monthly"] = Field(
        default="None",
        description="Data granularity. Use 'Daily' or 'Monthly' for time-series data.",
    )
    group_by: str = Field(
        default="",
        description=(
            "Dimension to group costs by. Options: ResourceGroup, ResourceType, "
            "ServiceName, ResourceLocation, MeterCategory, MeterSubCategory, Meter, "
            "ResourceId, SubscriptionId, PublisherType. Leave empty for totals only."
        ),
    )
    metric_type: Literal["ActualCost", "AmortizedCost"] = Field(
        default="ActualCost",
        description="Type of cost metric. AmortizedCost spreads reservation costs.",
    )


@register_tool("cost", "query")
class CostQueryTool(AzureTool):
    """Tool for querying Azure cost data."""

    @property
    def name(self) -> str:
        return "cost_query"

    @property
    def description(self) -> str:
        return (
            "Query Azure cost data for a subscription or resource group. "
            "Returns cost aggregations with optional grouping by dimensions like "
            "ResourceGroup, ResourceType, or ServiceName. Supports different timeframes "
            "and granularities for trend analysis."
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
        return CostQueryOptions

    async def execute(self, options: CostQueryOptions) -> Any:
        """Execute the cost query."""
        service = CostManagementService()
        try:
            return await service.query_costs(
                subscription=options.subscription,
                resource_group=options.resource_group,
                timeframe=options.timeframe,
                granularity=options.granularity,
                group_by=options.group_by,
                metric_type=options.metric_type,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Cost Query") from e
