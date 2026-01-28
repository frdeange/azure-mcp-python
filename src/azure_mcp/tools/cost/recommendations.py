"""Cost recommendations tool using Azure Advisor.

Provides the cost_recommendations tool for getting cost optimization suggestions.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.cost.service import CostManagementService


class CostRecommendationsOptions(BaseModel):
    """Options for getting cost recommendations."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name to get recommendations for.",
    )
    category: Literal[
        "Cost", "Security", "Performance", "HighAvailability", "OperationalExcellence", ""
    ] = Field(
        default="Cost",
        description=(
            "Category of recommendations to retrieve. "
            "Use 'Cost' for cost optimization recommendations. "
            "Leave empty for all categories."
        ),
    )


@register_tool("cost", "recommendations")
class CostRecommendationsTool(AzureTool):
    """Tool for getting Azure Advisor cost recommendations."""

    @property
    def name(self) -> str:
        return "cost_recommendations"

    @property
    def description(self) -> str:
        return (
            "Get Azure Advisor recommendations for cost optimization. "
            "Returns actionable suggestions to reduce Azure spending, including "
            "underutilized resources, right-sizing opportunities, and reserved instance "
            "purchase recommendations. Each recommendation includes potential savings."
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
        return CostRecommendationsOptions

    async def execute(self, options: CostRecommendationsOptions) -> Any:
        """Execute the recommendations query."""
        service = CostManagementService()
        try:
            return await service.list_cost_recommendations(
                subscription=options.subscription,
                category=options.category,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Cost Recommendations") from e
