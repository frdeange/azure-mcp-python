"""Bing Search service layer.

Provides BingService for interacting with:
- Azure Resource Manager (to discover Microsoft.Bing/accounts resources and retrieve API keys)
- Bing Search API v7 (web, news, images, entities, video)

Authentication flow:
1. Resource discovery uses DefaultAzureCredential + Resource Graph (consistent with project).
2. API key retrieval uses DefaultAzureCredential to call the ARM listKeys endpoint for the
   Microsoft.Bing/accounts resource. The result is cached for 12 hours.
3. Search calls use aiohttp with the key in the 'Ocp-Apim-Subscription-Key' header.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

try:
    import aiohttp
except ImportError:  # pragma: no cover
    aiohttp = None  # type: ignore[assignment]

from azure_mcp.core.base import AzureService
from azure_mcp.core.cache import cache

logger = logging.getLogger(__name__)

# Bing Search API v7 base URL
BING_API_BASE = "https://api.bing.microsoft.com/v7.0"

# ARM API version for Microsoft.Bing/accounts
BING_ARM_API_VERSION = "2020-06-10"

# Cache TTL for Bing API keys (12 hours, same as subscription resolution)
BING_KEY_CACHE_TTL = timedelta(hours=12)


class BingService(AzureService):
    """
    Service for Azure Bing Search resources and the Bing Search API v7.

    Provides:
    - Resource discovery via Azure Resource Graph (Microsoft.Bing/accounts)
    - API key retrieval via ARM REST (POST .../listKeys) authenticated with
      DefaultAzureCredential — no environment variables needed.
    - Async search operations via aiohttp using the retrieved key.
    """

    # ------------------------------------------------------------------
    # Resource discovery
    # ------------------------------------------------------------------

    async def list_bing_resources(
        self,
        subscription: str,
        resource_group: str = "",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List Microsoft.Bing/accounts resources in a subscription.

        Args:
            subscription: Subscription ID or display name.
            resource_group: Optional resource group filter. Leave empty for all.
            limit: Maximum number of results.

        Returns:
            List of Bing resource dictionaries with name, resourceGroup,
            location, sku, kind, and properties.
        """
        return await self.list_resources(
            resource_type="Microsoft.Bing/accounts",
            subscription=subscription,
            resource_group=resource_group if resource_group else None,
            limit=limit,
        )

    async def get_bing_resource(
        self,
        subscription: str,
        name: str,
        resource_group: str = "",
    ) -> dict[str, Any] | None:
        """
        Get details of a specific Microsoft.Bing/accounts resource.

        Args:
            subscription: Subscription ID or display name.
            name: Bing resource name.
            resource_group: Optional resource group filter.

        Returns:
            Resource dictionary, or None if not found.
        """
        return await self.get_resource(
            resource_type="Microsoft.Bing/accounts",
            subscription=subscription,
            name=name,
            resource_group=resource_group if resource_group else None,
        )

    # ------------------------------------------------------------------
    # API key retrieval via ARM (new pattern: ARM key retrieval)
    # ------------------------------------------------------------------

    async def _get_api_key(
        self,
        subscription_id: str,
        resource_group: str,
        resource_name: str,
    ) -> str:
        """
        Retrieve a Bing Search API key from ARM using DefaultAzureCredential.

        Calls POST .../Microsoft.Bing/accounts/{name}/listKeys on the ARM REST API,
        authenticated with the managed identity (or developer credential).
        The key is cached for 12 hours to avoid redundant ARM calls.

        Args:
            subscription_id: Resolved subscription GUID.
            resource_group: Resource group containing the Bing resource.
            resource_name: Name of the Microsoft.Bing/accounts resource.

        Returns:
            The first (key1) Bing Search API key.

        Raises:
            ValueError: If the resource is not found or has no keys.
            Exception: On ARM authentication or network errors.
        """
        cache_key = f"bing:key:{subscription_id}:{resource_group}:{resource_name}"

        async def fetch_key() -> str:
            if aiohttp is None:  # pragma: no cover
                raise ImportError(
                    "aiohttp is required for Bing Search tools. "
                    "Install with: pip install 'azure-mcp[bing]'"
                )

            credential = self.get_credential()

            # get_token() is synchronous — wrap with asyncio.to_thread to avoid
            # blocking the event loop (architecture rule: async-first)
            token = await asyncio.to_thread(
                credential.get_token,
                "https://management.azure.com/.default",
            )

            url = (
                f"https://management.azure.com/subscriptions/{subscription_id}"
                f"/resourceGroups/{resource_group}"
                f"/providers/Microsoft.Bing/accounts/{resource_name}"
                f"/listKeys?api-version={BING_ARM_API_VERSION}"
            )

            async with aiohttp.ClientSession() as session, session.post(
                url,
                headers={
                    "Authorization": f"Bearer {token.token}",
                    "Content-Type": "application/json",
                },
            ) as response:
                if response.status == 401:
                    raise PermissionError(
                        "Unauthorized: the managed identity lacks permission to call "
                        f"Microsoft.Bing/accounts/listKeys on resource '{resource_name}'. "
                        "Assign the 'Contributor' role (or a custom role with "
                        "Microsoft.Bing/accounts/listKeys/action) to the managed identity "
                        "on the Bing resource."
                    )
                if response.status == 403:
                    raise PermissionError(
                        "Forbidden: the managed identity lacks permission to call "
                        f"Microsoft.Bing/accounts/listKeys on resource '{resource_name}'. "
                        "Assign the 'Contributor' role (or a custom role with "
                        "Microsoft.Bing/accounts/listKeys/action) to the managed identity."
                    )
                if response.status == 404:
                    raise ValueError(
                        f"Bing resource '{resource_name}' not found in "
                        f"resource group '{resource_group}' "
                        f"(subscription: {subscription_id})."
                    )
                response.raise_for_status()
                data = await response.json()

            key1 = data.get("key1") or data.get("Key1")
            if not key1:
                raise ValueError(
                    f"Bing resource '{resource_name}' returned no API keys. "
                    "Verify the resource is provisioned and has valid keys."
                )
            return key1

        return await cache.get_or_set(cache_key, fetch_key, BING_KEY_CACHE_TTL)

    # ------------------------------------------------------------------
    # Search operations
    # ------------------------------------------------------------------

    async def _search(
        self,
        endpoint: str,
        api_key: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a Bing Search API v7 GET request.

        Args:
            endpoint: Relative endpoint path (e.g. '/search', '/news/search').
            api_key: Bing Search subscription key.
            params: Query parameters to include in the request.

        Returns:
            Parsed JSON response as a dictionary.
        """
        if aiohttp is None:  # pragma: no cover
            raise ImportError(
                "aiohttp is required for Bing Search tools. "
                "Install with: pip install 'azure-mcp[bing]'"
            )

        # Remove empty params to keep the request clean
        clean_params = {k: v for k, v in params.items() if v not in ("", None)}

        async with aiohttp.ClientSession() as session, session.get(
            f"{BING_API_BASE}{endpoint}",
            headers={"Ocp-Apim-Subscription-Key": api_key},
            params=clean_params,
        ) as response:
            if response.status == 401:
                raise PermissionError(
                    "Bing Search API returned 401 Unauthorized. "
                    "The API key may be invalid or expired."
                )
            if response.status == 403:
                raise PermissionError(
                    "Bing Search API returned 403 Forbidden. "
                    "The API key does not have access to this endpoint. "
                    "Verify the Bing resource SKU supports this search type."
                )
            if response.status == 429:
                raise RuntimeError(
                    "Bing Search API rate limit exceeded (429). "
                    "Reduce the request frequency or upgrade the SKU."
                )
            response.raise_for_status()
            return await response.json()

    async def web_search(
        self,
        subscription: str,
        resource_name: str,
        resource_group: str,
        query: str,
        market: str = "",
        safe_search: str = "",
        count: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Perform a Bing Web Search.

        Args:
            subscription: Subscription ID or display name.
            resource_name: Name of the Microsoft.Bing/accounts resource.
            resource_group: Resource group of the Bing resource.
            query: Search query string.
            market: BCP 47 market code, e.g. 'en-US'. Leave empty for default.
            safe_search: SafeSearch setting: 'Off', 'Moderate', or 'Strict'. Leave empty for default.
            count: Number of results to return (1-50).
            offset: Zero-based offset for pagination.

        Returns:
            Bing Web Search API v7 response.
        """
        sub_id = await self.resolve_subscription(subscription)
        api_key = await self._get_api_key(sub_id, resource_group, resource_name)
        params: dict[str, Any] = {
            "q": query,
            "count": count,
            "offset": offset,
            "mkt": market,
            "safeSearch": safe_search,
        }
        return await self._search("/search", api_key, params)

    async def news_search(
        self,
        subscription: str,
        resource_name: str,
        resource_group: str,
        query: str,
        market: str = "",
        count: int = 10,
        freshness: str = "",
    ) -> dict[str, Any]:
        """
        Perform a Bing News Search.

        Args:
            subscription: Subscription ID or display name.
            resource_name: Name of the Microsoft.Bing/accounts resource.
            resource_group: Resource group of the Bing resource.
            query: Search query string.
            market: BCP 47 market code, e.g. 'en-US'. Leave empty for default.
            count: Number of results to return (1-100).
            freshness: Freshness filter: 'Day', 'Week', 'Month'. Leave empty for all.

        Returns:
            Bing News Search API v7 response.
        """
        sub_id = await self.resolve_subscription(subscription)
        api_key = await self._get_api_key(sub_id, resource_group, resource_name)
        params: dict[str, Any] = {
            "q": query,
            "count": count,
            "mkt": market,
            "freshness": freshness,
        }
        return await self._search("/news/search", api_key, params)

    async def image_search(
        self,
        subscription: str,
        resource_name: str,
        resource_group: str,
        query: str,
        market: str = "",
        safe_search: str = "",
        count: int = 10,
        size: str = "",
        color: str = "",
    ) -> dict[str, Any]:
        """
        Perform a Bing Image Search.

        Args:
            subscription: Subscription ID or display name.
            resource_name: Name of the Microsoft.Bing/accounts resource.
            resource_group: Resource group of the Bing resource.
            query: Search query string.
            market: BCP 47 market code, e.g. 'en-US'. Leave empty for default.
            safe_search: SafeSearch: 'Off', 'Moderate', 'Strict'. Leave empty for default.
            count: Number of results (1-150).
            size: Image size filter: 'Small', 'Medium', 'Large', 'Wallpaper'. Leave empty for all.
            color: Color filter, e.g. 'Red', 'Monochrome'. Leave empty for all.

        Returns:
            Bing Image Search API v7 response.
        """
        sub_id = await self.resolve_subscription(subscription)
        api_key = await self._get_api_key(sub_id, resource_group, resource_name)
        params: dict[str, Any] = {
            "q": query,
            "count": count,
            "mkt": market,
            "safeSearch": safe_search,
            "size": size,
            "color": color,
        }
        return await self._search("/images/search", api_key, params)

    async def entity_search(
        self,
        subscription: str,
        resource_name: str,
        resource_group: str,
        query: str,
        market: str = "",
    ) -> dict[str, Any]:
        """
        Perform a Bing Entity Search.

        Args:
            subscription: Subscription ID or display name.
            resource_name: Name of the Microsoft.Bing/accounts resource.
            resource_group: Resource group of the Bing resource.
            query: Entity name or description to search for.
            market: BCP 47 market code, e.g. 'en-US'. Leave empty for default.

        Returns:
            Bing Entity Search API v7 response, including entity facts and
            local business information.
        """
        sub_id = await self.resolve_subscription(subscription)
        api_key = await self._get_api_key(sub_id, resource_group, resource_name)
        params: dict[str, Any] = {
            "q": query,
            "mkt": market,
        }
        return await self._search("/entities", api_key, params)

    async def video_search(
        self,
        subscription: str,
        resource_name: str,
        resource_group: str,
        query: str,
        market: str = "",
        count: int = 10,
        pricing: str = "",
        resolution: str = "",
    ) -> dict[str, Any]:
        """
        Perform a Bing Video Search.

        Args:
            subscription: Subscription ID or display name.
            resource_name: Name of the Microsoft.Bing/accounts resource.
            resource_group: Resource group of the Bing resource.
            query: Search query string.
            market: BCP 47 market code, e.g. 'en-US'. Leave empty for default.
            count: Number of results (1-105).
            pricing: Pricing filter: 'Free', 'Paid'. Leave empty for all.
            resolution: Resolution filter: 'SD480p', 'HD720p', 'HD1080p'. Leave empty for all.

        Returns:
            Bing Video Search API v7 response.
        """
        sub_id = await self.resolve_subscription(subscription)
        api_key = await self._get_api_key(sub_id, resource_group, resource_name)
        params: dict[str, Any] = {
            "q": query,
            "count": count,
            "mkt": market,
            "pricing": pricing,
            "resolution": resolution,
        }
        return await self._search("/videos/search", api_key, params)
