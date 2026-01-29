"""Cosmos DB account tools.

Provides cosmos_account_list tool for discovering Cosmos DB accounts via Resource Graph.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureService, AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool


# Summary fields for Resource Graph projection
SUMMARY_PROJECTION = """
| project
    id,
    name,
    location,
    resourceGroup,
    subscriptionId,
    kind,
    tags,
    documentEndpoint = properties.documentEndpoint,
    consistencyLevel = properties.consistencyPolicy.defaultConsistencyLevel,
    provisioningState = properties.provisioningState,
    enableFreeTier = properties.enableFreeTier,
    capacityMode = properties.capacity.mode,
    writeLocations = properties.writeLocations,
    readLocations = properties.readLocations
"""


class CosmosAccountListOptions(BaseModel):
    """Options for listing Cosmos DB accounts."""

    subscription: str = Field(
        ...,
        description="Azure subscription ID or display name to query.",
    )
    resource_group: str = Field(
        default="",
        description="Resource group name to filter accounts. Leave empty for all resource groups.",
    )
    detail_level: Literal["summary", "full"] = Field(
        default="summary",
        description=(
            "Level of detail in response: "
            "'summary' returns essential fields (name, endpoint, location, kind, consistency, locations); "
            "'full' returns all account properties including networking, backup, and security configuration."
        ),
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of accounts to return.",
    )


class CosmosAccountService(AzureService):
    """Service for Cosmos DB account discovery via Resource Graph."""

    async def list_accounts(
        self,
        subscription: str,
        resource_group: str = "",
        detail_level: str = "summary",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List Cosmos DB accounts using Azure Resource Graph.

        Args:
            subscription: Subscription ID or name.
            resource_group: Optional resource group filter.
            detail_level: 'summary' for essential fields, 'full' for all properties.
            limit: Maximum number of results.

        Returns:
            List of Cosmos DB account dictionaries.
        """
        sub_id = await self.resolve_subscription(subscription)

        # Build KQL query
        query = "resources | where type =~ 'microsoft.documentdb/databaseaccounts'"

        if resource_group:
            query += f" | where resourceGroup =~ '{resource_group}'"

        if detail_level == "summary":
            query += SUMMARY_PROJECTION
        # For 'full', we don't project - return all fields

        query += f" | limit {limit}"

        # Use the base class method
        result = await self.execute_resource_graph_query(
            query=query,
            subscriptions=[sub_id],
        )

        return result.get("data", [])


@register_tool("cosmos", "account")
class CosmosAccountListTool(AzureTool):
    """Tool for listing Cosmos DB accounts."""

    @property
    def name(self) -> str:
        return "cosmos_account_list"

    @property
    def description(self) -> str:
        return (
            "List Azure Cosmos DB accounts in a subscription using Resource Graph. "
            "Returns account information including the documentEndpoint URL needed "
            "for data plane operations (database/container/item tools). "
            "Use 'summary' detail_level for quick discovery, 'full' for complete configuration details."
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
        return CosmosAccountListOptions

    async def execute(self, options: CosmosAccountListOptions) -> Any:
        """Execute the account listing."""
        service = CosmosAccountService()

        try:
            return await service.list_accounts(
                subscription=options.subscription,
                resource_group=options.resource_group,
                detail_level=options.detail_level,
                limit=options.limit,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
