"""Cost forecast tool for Azure Cost Management.

Provides the cost_forecast tool for getting cost predictions.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.cost.service import CostManagementService


class CostForecastOptions(BaseModel):
    """Options for getting cost forecasts."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name to forecast costs for.",
    )
    resource_group: str = Field(
        default="",
        description="Resource group to scope the forecast. Leave empty for subscription-level.",
    )
    granularity: Literal["Daily", "Monthly"] = Field(
        default="Daily",
        description="Forecast data granularity.",
    )
    forecast_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Number of days to forecast into the future.",
    )
    include_actual_cost: bool = Field(
        default=True,
        description="Include actual costs from current period in the response.",
    )
    include_fresh_partial_cost: bool = Field(
        default=True,
        description="Include partial costs from the current day/period.",
    )


@register_tool("cost", "forecast")
class CostForecastTool(AzureTool):
    """Tool for getting Azure cost forecasts."""

    @property
    def name(self) -> str:
        return "cost_forecast"

    @property
    def description(self) -> str:
        return (
            "Get cost forecasts for an Azure subscription or resource group. "
            "Returns predicted costs for the specified number of days, with optional "
            "actual cost comparison. Useful for budget planning and anomaly detection."
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
        return CostForecastOptions

    async def execute(self, options: CostForecastOptions) -> Any:
        """Execute the cost forecast query."""
        service = CostManagementService()
        try:
            return await service.get_forecast(
                subscription=options.subscription,
                resource_group=options.resource_group,
                granularity=options.granularity,
                forecast_days=options.forecast_days,
                include_actual_cost=options.include_actual_cost,
                include_fresh_partial_cost=options.include_fresh_partial_cost,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Cost Forecast") from e
