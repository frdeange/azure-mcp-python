"""Cost budgets tools for Azure Consumption.

Provides tools for listing and getting budget details.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.cost.service import CostManagementService


class CostBudgetsListOptions(BaseModel):
    """Options for listing budgets."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name to list budgets for.",
    )
    resource_group: str = Field(
        default="",
        description="Resource group to scope the query. Leave empty for subscription-level budgets.",
    )


class CostBudgetsGetOptions(BaseModel):
    """Options for getting budget details."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name.",
    )
    budget_name: str = Field(
        ...,
        description="Name of the budget to retrieve.",
    )
    resource_group: str = Field(
        default="",
        description="Resource group scope if the budget is at resource group level.",
    )


@register_tool("cost", "budgets")
class CostBudgetsListTool(AzureTool):
    """Tool for listing Azure budgets."""

    @property
    def name(self) -> str:
        return "cost_budgets_list"

    @property
    def description(self) -> str:
        return (
            "List Azure budgets for a subscription or resource group. "
            "Returns budget names, amounts, time periods, and current spend. "
            "Useful for monitoring spending against defined limits."
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
        return CostBudgetsListOptions

    async def execute(self, options: CostBudgetsListOptions) -> Any:
        """Execute the budget list query."""
        service = CostManagementService()
        try:
            return await service.list_budgets(
                subscription=options.subscription,
                resource_group=options.resource_group,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Budgets") from e


@register_tool("cost", "budgets")
class CostBudgetsGetTool(AzureTool):
    """Tool for getting Azure budget details."""

    @property
    def name(self) -> str:
        return "cost_budgets_get"

    @property
    def description(self) -> str:
        return (
            "Get detailed information about a specific Azure budget. "
            "Returns budget amount, current spend, usage percentage, time period, "
            "and notification settings. Useful for understanding budget status and alerts."
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
        return CostBudgetsGetOptions

    async def execute(self, options: CostBudgetsGetOptions) -> Any:
        """Execute the budget get query."""
        service = CostManagementService()
        try:
            return await service.get_budget(
                subscription=options.subscription,
                budget_name=options.budget_name,
                resource_group=options.resource_group,
            )
        except Exception as e:
            raise handle_azure_error(e, resource=f"Budget '{options.budget_name}'") from e
