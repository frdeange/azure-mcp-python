"""Cost usage by resource tool.

Provides the cost_usage_by_resource tool for getting cost breakdown by resource.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.cost.service import CostManagementService


class CostUsageByResourceOptions(BaseModel):
    """Options for getting cost breakdown by resource."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name to query costs for.",
    )
    resource_group: str = Field(
        default="",
        description="Resource group to filter resources. Leave empty for all resources.",
    )
    timeframe: Literal[
        "MonthToDate",
        "BillingMonthToDate",
        "TheLastMonth",
        "TheLastBillingMonth",
        "WeekToDate",
    ] = Field(
        default="MonthToDate",
        description="Time period for cost data.",
    )
    top: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of top-cost resources to return.",
    )
    metric_type: Literal["ActualCost", "AmortizedCost"] = Field(
        default="ActualCost",
        description="Type of cost metric.",
    )


@register_tool("cost", "usage")
class CostUsageByResourceTool(AzureTool):
    """Tool for getting cost breakdown by individual resources."""

    @property
    def name(self) -> str:
        return "cost_usage_by_resource"

    @property
    def description(self) -> str:
        return (
            "Get cost breakdown by individual Azure resources. Returns the top "
            "cost-generating resources in a subscription or resource group, "
            "sorted by cost descending. Useful for identifying expensive resources "
            "and optimization opportunities."
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
        return CostUsageByResourceOptions

    async def execute(self, options: CostUsageByResourceOptions) -> Any:
        """Execute the cost by resource query."""
        service = CostManagementService()
        try:
            return await service.query_costs_by_resource(
                subscription=options.subscription,
                resource_group=options.resource_group,
                timeframe=options.timeframe,
                top=options.top,
                metric_type=options.metric_type,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Cost Usage") from e
