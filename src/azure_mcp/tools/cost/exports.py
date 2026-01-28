"""Cost exports tool for Azure Cost Management.

Provides the cost_exports_list tool for listing configured cost exports.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.cost.service import CostManagementService


class CostExportsListOptions(BaseModel):
    """Options for listing cost exports."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name to list exports for.",
    )
    resource_group: str = Field(
        default="",
        description="Resource group to scope the query. Leave empty for subscription-level exports.",
    )


@register_tool("cost", "exports")
class CostExportsListTool(AzureTool):
    """Tool for listing Azure cost exports."""

    @property
    def name(self) -> str:
        return "cost_exports_list"

    @property
    def description(self) -> str:
        return (
            "List configured Azure cost exports for a subscription or resource group. "
            "Cost exports automatically deliver cost data to a storage account on a schedule. "
            "Returns export names, formats, schedules, and storage destinations."
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
        return CostExportsListOptions

    async def execute(self, options: CostExportsListOptions) -> Any:
        """Execute the exports list query."""
        service = CostManagementService()
        try:
            return await service.list_exports(
                subscription=options.subscription,
                resource_group=options.resource_group,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Cost Exports") from e
