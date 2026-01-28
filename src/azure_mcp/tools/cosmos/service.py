"""Cosmos DB service layer.

Provides CosmosService for data plane operations using Azure Cosmos SDK.
Uses AAD authentication only (no connection strings) for security.
"""

from __future__ import annotations

from typing import Any

from azure_mcp.core.base import AzureService


class CosmosService(AzureService):
    """
    Service for Azure Cosmos DB data plane operations.

    Uses azure-cosmos SDK with AAD authentication via DefaultAzureCredential.
    Account discovery should be done via cosmos_account_list tool first.
    """

    async def list_databases(
        self,
        account_endpoint: str,
    ) -> list[dict[str, Any]]:
        """
        List all databases in a Cosmos DB account.

        Args:
            account_endpoint: The Cosmos DB account endpoint URL
                              (e.g., https://myaccount.documents.azure.com:443/).

        Returns:
            List of database information dictionaries.
        """
        from azure.cosmos import CosmosClient

        credential = self.get_credential()
        client = CosmosClient(url=account_endpoint, credential=credential)

        databases = []
        for db in client.list_databases():
            databases.append(
                {
                    "id": db.get("id"),
                    "self": db.get("_self"),
                    "etag": db.get("_etag"),
                    "collections": db.get("_colls"),
                    "users": db.get("_users"),
                }
            )

        return databases

    async def list_containers(
        self,
        account_endpoint: str,
        database_name: str,
    ) -> list[dict[str, Any]]:
        """
        List all containers in a Cosmos DB database.

        Args:
            account_endpoint: The Cosmos DB account endpoint URL.
            database_name: Name of the database.

        Returns:
            List of container information dictionaries.
        """
        from azure.cosmos import CosmosClient

        credential = self.get_credential()
        client = CosmosClient(url=account_endpoint, credential=credential)
        database = client.get_database_client(database_name)

        containers = []
        for container in database.list_containers():
            containers.append(
                {
                    "id": container.get("id"),
                    "self": container.get("_self"),
                    "etag": container.get("_etag"),
                    "partition_key": container.get("partitionKey", {}).get("paths", []),
                    "indexing_policy": container.get("indexingPolicy"),
                    "default_ttl": container.get("defaultTtl"),
                    "unique_key_policy": container.get("uniqueKeyPolicy"),
                }
            )

        return containers

    async def query_items(
        self,
        account_endpoint: str,
        database_name: str,
        container_name: str,
        query: str,
        parameters: list[dict[str, Any]] | None = None,
        max_items: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Query items in a container using SQL-like syntax.

        Args:
            account_endpoint: The Cosmos DB account endpoint URL.
            database_name: Name of the database.
            container_name: Name of the container.
            query: SQL-like query string (e.g., "SELECT * FROM c WHERE c.status = @status").
            parameters: Optional query parameters (e.g., [{"name": "@status", "value": "active"}]).
            max_items: Maximum number of items to return.

        Returns:
            List of matching items.
        """
        from azure.cosmos import CosmosClient

        credential = self.get_credential()
        client = CosmosClient(url=account_endpoint, credential=credential)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        items = []
        query_iterable = container.query_items(
            query=query,
            parameters=parameters,
            max_item_count=max_items,
        )

        for item in query_iterable:
            items.append(item)
            if len(items) >= max_items:
                break

        return items

    async def get_item(
        self,
        account_endpoint: str,
        database_name: str,
        container_name: str,
        item_id: str,
        partition_key: Any,
    ) -> dict[str, Any]:
        """
        Get a single item by ID and partition key.

        Args:
            account_endpoint: The Cosmos DB account endpoint URL.
            database_name: Name of the database.
            container_name: Name of the container.
            item_id: The item's unique ID.
            partition_key: The partition key value for the item.

        Returns:
            The item as a dictionary.
        """
        from azure.cosmos import CosmosClient

        credential = self.get_credential()
        client = CosmosClient(url=account_endpoint, credential=credential)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        item = container.read_item(item=item_id, partition_key=partition_key)
        return dict(item)

    async def upsert_item(
        self,
        account_endpoint: str,
        database_name: str,
        container_name: str,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Create or update an item in a container.

        Args:
            account_endpoint: The Cosmos DB account endpoint URL.
            database_name: Name of the database.
            container_name: Name of the container.
            item: The item to create or update (must include 'id' field).

        Returns:
            The upserted item as a dictionary.
        """
        from azure.cosmos import CosmosClient

        credential = self.get_credential()
        client = CosmosClient(url=account_endpoint, credential=credential)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        result = container.upsert_item(body=item)
        return dict(result)

    async def delete_item(
        self,
        account_endpoint: str,
        database_name: str,
        container_name: str,
        item_id: str,
        partition_key: Any,
    ) -> dict[str, Any]:
        """
        Delete an item by ID and partition key.

        Args:
            account_endpoint: The Cosmos DB account endpoint URL.
            database_name: Name of the database.
            container_name: Name of the container.
            item_id: The item's unique ID.
            partition_key: The partition key value for the item.

        Returns:
            Confirmation of deletion.
        """
        from azure.cosmos import CosmosClient

        credential = self.get_credential()
        client = CosmosClient(url=account_endpoint, credential=credential)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        container.delete_item(item=item_id, partition_key=partition_key)

        return {
            "deleted": True,
            "item_id": item_id,
            "partition_key": partition_key,
        }
