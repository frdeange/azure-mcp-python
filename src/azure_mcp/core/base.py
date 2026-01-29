"""Base classes for Azure services and tools.

Provides AzureService and AzureTool base classes.
"""

from __future__ import annotations

import re
import uuid
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from azure_mcp.core.auth import CredentialProvider
from azure_mcp.core.cache import cache
from azure_mcp.core.models import ToolMetadata

if TYPE_CHECKING:
    from azure.core.credentials import TokenCredential

# Cache TTL for subscription resolution
SUBSCRIPTION_CACHE_TTL = timedelta(hours=12)


class AzureService:
    """
    Base class for Azure service operations.

    Provides:
    - Credential management with tenant support
    - Subscription resolution (name → ID)
    - Resource Graph query helpers
    """

    def __init__(self, credential: TokenCredential | None = None) -> None:
        """
        Initialize the service.

        Args:
            credential: Optional credential override.
        """
        self._credential = credential

    def get_credential(self, tenant: str | None = None) -> TokenCredential:
        """
        Get credential, using provided or creating from chain.

        Args:
            tenant: Optional tenant ID.

        Returns:
            TokenCredential for Azure authentication.
        """
        if self._credential:
            return self._credential
        return CredentialProvider.get_credential(tenant)

    async def resolve_subscription(
        self,
        subscription: str,
        tenant: str | None = None,
    ) -> str:
        """
        Resolve subscription name or ID to subscription ID.

        Args:
            subscription: Subscription ID (GUID) or display name.
            tenant: Optional tenant ID.

        Returns:
            Subscription ID (GUID string).

        Raises:
            ValueError: If subscription is not found.
        """
        # If it's already a GUID, return it
        if self._is_guid(subscription):
            return subscription

        # Look up by name with caching
        cache_key = f"subscription:{subscription}:{tenant or 'default'}"

        async def fetch_subscription() -> str:
            from azure.mgmt.resource import SubscriptionClient

            credential = self.get_credential(tenant)
            client = SubscriptionClient(credential)

            for sub in client.subscriptions.list():
                if sub.display_name and sub.display_name.lower() == subscription.lower():
                    return sub.subscription_id

            raise ValueError(f"Subscription '{subscription}' not found")

        return await cache.get_or_set(cache_key, fetch_subscription, SUBSCRIPTION_CACHE_TTL)

    async def list_subscriptions(self, tenant: str | None = None) -> list[dict[str, Any]]:
        """
        List all accessible subscriptions.

        Args:
            tenant: Optional tenant ID.

        Returns:
            List of subscription dictionaries.
        """
        cache_key = f"subscriptions:{tenant or 'default'}"

        async def fetch_subscriptions() -> list[dict[str, Any]]:
            from azure.mgmt.resource import SubscriptionClient

            credential = self.get_credential(tenant)
            client = SubscriptionClient(credential)

            return [
                {
                    "id": sub.subscription_id,
                    "name": sub.display_name,
                    "state": sub.state.value if hasattr(sub.state, "value") else sub.state,
                    "tenant_id": sub.tenant_id,
                }
                for sub in client.subscriptions.list()
            ]

        return await cache.get_or_set(cache_key, fetch_subscriptions, SUBSCRIPTION_CACHE_TTL)

    async def execute_resource_graph_query(
        self,
        query: str,
        subscriptions: list[str] | None = None,
        management_groups: list[str] | None = None,
        skip: int = 0,
        top: int = 1000,
    ) -> dict[str, Any]:
        """
        Execute a custom Resource Graph KQL query.

        This is the central method for all Resource Graph queries. Use this for
        custom KQL queries with projections, aggregations, or complex filters.
        For simple resource listings, prefer list_resources() instead.

        Args:
            query: Full KQL query string.
            subscriptions: List of subscription IDs. If empty and no management_groups,
                          queries all accessible subscriptions.
            management_groups: List of management group IDs. Takes precedence over subscriptions.
            skip: Number of rows to skip for pagination.
            top: Maximum rows to return.

        Returns:
            Dict with 'data', 'count', 'total_records', 'skip_token', 'result_truncated'.
        """
        from azure.mgmt.resourcegraph import ResourceGraphClient
        from azure.mgmt.resourcegraph.models import QueryRequest, QueryRequestOptions

        credential = self.get_credential()
        client = ResourceGraphClient(credential)

        # Build request options
        options = QueryRequestOptions(skip=skip, top=top)

        # Build request - use management groups if provided, else subscriptions
        if management_groups:
            request = QueryRequest(
                management_groups=management_groups,
                query=query,
                options=options,
            )
        else:
            # If no subscriptions provided, get all accessible
            if not subscriptions:
                subs = await self.list_subscriptions()
                subscriptions = [s["id"] for s in subs]

            request = QueryRequest(
                subscriptions=subscriptions,
                query=query,
                options=options,
            )

        # Execute query
        result = client.resources(request)

        # Return structured result
        return {
            "data": list(result.data) if result.data else [],
            "count": result.count,
            "total_records": result.total_records,
            "skip_token": result.skip_token,
            "result_truncated": result.result_truncated,
        }

    async def list_resources(
        self,
        resource_type: str,
        subscription: str,
        resource_group: str | None = None,
        name_filter: str | None = None,
        additional_filter: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List resources using Azure Resource Graph.

        This is a convenience wrapper around execute_resource_graph_query() for
        simple resource listings by type. For custom KQL queries with projections
        or complex logic, use execute_resource_graph_query() directly.

        Args:
            resource_type: Azure resource type (e.g., "Microsoft.Storage/storageAccounts").
            subscription: Subscription ID or name.
            resource_group: Optional resource group filter.
            name_filter: Optional name filter (exact match).
            additional_filter: Optional additional KQL filter.
            limit: Maximum number of results.

        Returns:
            List of resources as dictionaries.
        """
        sub_id = await self.resolve_subscription(subscription)

        # Build KQL query
        query = f"resources | where type =~ '{self._escape_kql(resource_type)}'"

        if resource_group:
            query += f" | where resourceGroup =~ '{self._escape_kql(resource_group)}'"

        if name_filter:
            query += f" | where name =~ '{self._escape_kql(name_filter)}'"

        if additional_filter:
            query += f" | where {additional_filter}"

        query += f" | limit {limit}"

        # Use the central Resource Graph query method
        result = await self.execute_resource_graph_query(
            query=query,
            subscriptions=[sub_id],
            top=limit,
        )

        return result.get("data", [])

    async def get_resource(
        self,
        resource_type: str,
        subscription: str,
        name: str,
        resource_group: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Get a single resource by name.

        Args:
            resource_type: Azure resource type.
            subscription: Subscription ID or name.
            name: Resource name.
            resource_group: Optional resource group.

        Returns:
            Resource dictionary, or None if not found.
        """
        results = await self.list_resources(
            resource_type=resource_type,
            subscription=subscription,
            resource_group=resource_group,
            name_filter=name,
            limit=1,
        )
        return results[0] if results else None

    @staticmethod
    def _is_guid(value: str) -> bool:
        """Check if a string is a valid GUID."""
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _escape_kql(value: str) -> str:
        """Escape a string for use in KQL queries."""
        # Escape single quotes by doubling them
        return value.replace("'", "''")


class AzureTool(ABC):
    """
    Base class for all Azure MCP tools.

    Tools are the MCP-facing interface. They:
    1. Define their name, description, and metadata
    2. Define their input parameters (options schema)
    3. Validate inputs using Pydantic
    4. Call services to perform operations
    5. Format and return results

    Subclasses must define:
    - name: Tool identifier
    - description: Human-readable description
    - options_model: Pydantic model for options
    - execute(): Async implementation method
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Tool name.

        Format: {family}_{resource}_{action}
        Example: "storage_account_get", "cosmos_item_query"
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description for LLM context.

        Should describe:
        - What the tool does
        - When to use it
        - What it returns
        """
        pass

    @property
    def metadata(self) -> ToolMetadata:
        """
        Tool behavioral metadata.

        Override to customize. Default assumes destructive, non-idempotent operation.
        """
        return ToolMetadata()

    @property
    @abstractmethod
    def options_model(self) -> type[BaseModel]:
        """
        Pydantic model class for tool options.

        Used for:
        - Input validation
        - JSON schema generation for MCP
        """
        pass

    def get_options_schema(self) -> dict[str, Any]:
        """
        Get JSON Schema for tool parameters.

        Returns:
            JSON Schema dictionary.
        """
        return self.options_model.model_json_schema()

    @abstractmethod
    async def execute(self, options: BaseModel) -> Any:
        """
        Execute the tool with validated options.

        Args:
            options: Validated Pydantic model instance.

        Returns:
            Result data (will be JSON serialized).

        Raises:
            ToolError: On any error during execution.
        """
        pass

    async def run(self, raw_options: dict[str, Any]) -> Any:
        """
        Run the tool with raw options dictionary.

        Validates options using the Pydantic model before execution.

        Args:
            raw_options: Dictionary of option values.

        Returns:
            Result from execute().

        Raises:
            ValidationError: If options are invalid.
            ToolError: If execution fails.
        """
        from azure_mcp.core.errors import ValidationError

        try:
            options = self.options_model(**raw_options)
        except Exception as e:
            raise ValidationError(message=f"Invalid options: {e}")

        return await self.execute(options)
