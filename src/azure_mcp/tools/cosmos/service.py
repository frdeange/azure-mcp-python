"""Cosmos DB service layer.

Provides CosmosService for data plane operations using Azure Cosmos SDK.
Uses AAD authentication only (no connection strings) for security.
Uses async SDK (azure.cosmos.aio) for non-blocking I/O.
"""

from __future__ import annotations

from typing import Any

from azure_mcp.core.base import AzureService


class CosmosService(AzureService):
    """
    Service for Azure Cosmos DB data plane operations.

    Uses azure-cosmos async SDK with AAD authentication via DefaultAzureCredential.
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
        from azure.cosmos.aio import CosmosClient

        credential = self.get_credential()

        async with CosmosClient(url=account_endpoint, credential=credential) as client:
            databases = []
            async for db in client.list_databases():
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
        from azure.cosmos.aio import CosmosClient

        credential = self.get_credential()

        async with CosmosClient(url=account_endpoint, credential=credential) as client:
            database = client.get_database_client(database_name)

            containers = []
            async for container in database.list_containers():
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
        from azure.cosmos.aio import CosmosClient

        credential = self.get_credential()

        async with CosmosClient(url=account_endpoint, credential=credential) as client:
            database = client.get_database_client(database_name)
            container = database.get_container_client(container_name)

            items = []
            async for item in container.query_items(
                query=query,
                parameters=parameters,
                max_item_count=max_items,
            ):
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
        from azure.cosmos.aio import CosmosClient

        credential = self.get_credential()

        async with CosmosClient(url=account_endpoint, credential=credential) as client:
            database = client.get_database_client(database_name)
            container = database.get_container_client(container_name)

            item = await container.read_item(item=item_id, partition_key=partition_key)
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
        from azure.cosmos.aio import CosmosClient

        credential = self.get_credential()

        async with CosmosClient(url=account_endpoint, credential=credential) as client:
            database = client.get_database_client(database_name)
            container = database.get_container_client(container_name)

            result = await container.upsert_item(body=item)
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
        from azure.cosmos.aio import CosmosClient

        credential = self.get_credential()

        async with CosmosClient(url=account_endpoint, credential=credential) as client:
            database = client.get_database_client(database_name)
            container = database.get_container_client(container_name)

            await container.delete_item(item=item_id, partition_key=partition_key)

        return {
            "deleted": True,
            "item_id": item_id,
            "partition_key": partition_key,
        }

    async def create_database(
        self,
        account_endpoint: str,
        database_name: str,
    ) -> dict[str, Any]:
        """
        Create a database in a Cosmos DB account (idempotent).

        Uses create_database_if_not_exists for safe, idempotent operation.

        Args:
            account_endpoint: The Cosmos DB account endpoint URL.
            database_name: Name of the database to create.

        Returns:
            Database information dictionary.
        """
        from azure.cosmos.aio import CosmosClient

        credential = self.get_credential()

        async with CosmosClient(url=account_endpoint, credential=credential) as client:
            db = await client.create_database_if_not_exists(id=database_name)
            properties = await db.read()

            return {
                "id": properties.get("id"),
                "self": properties.get("_self"),
                "etag": properties.get("_etag"),
                "collections": properties.get("_colls"),
                "users": properties.get("_users"),
            }

    async def delete_database(
        self,
        account_endpoint: str,
        database_name: str,
    ) -> dict[str, Any]:
        """
        Delete a database from a Cosmos DB account.

        WARNING: This permanently deletes the database and ALL its containers and data.

        Args:
            account_endpoint: The Cosmos DB account endpoint URL.
            database_name: Name of the database to delete.

        Returns:
            Confirmation of deletion.
        """
        from azure.cosmos.aio import CosmosClient

        credential = self.get_credential()

        async with CosmosClient(url=account_endpoint, credential=credential) as client:
            await client.delete_database(database_name)

        return {
            "deleted": True,
            "database_name": database_name,
        }

    async def create_container(
        self,
        account_endpoint: str,
        database_name: str,
        container_name: str,
        partition_key_path: str,
        throughput: int = 0,
    ) -> dict[str, Any]:
        """
        Create a container in a Cosmos DB database (idempotent).

        Uses create_container_if_not_exists for safe, idempotent operation.

        Args:
            account_endpoint: The Cosmos DB account endpoint URL.
            database_name: Name of the database.
            container_name: Name of the container to create.
            partition_key_path: Partition key path (e.g., '/category', '/id').
            throughput: Provisioned throughput in RU/s. 0 for shared/serverless.

        Returns:
            Container information dictionary.
        """
        from azure.cosmos import PartitionKey
        from azure.cosmos.aio import CosmosClient

        credential = self.get_credential()

        async with CosmosClient(url=account_endpoint, credential=credential) as client:
            database = client.get_database_client(database_name)

            kwargs: dict[str, Any] = {
                "id": container_name,
                "partition_key": PartitionKey(path=partition_key_path),
            }
            if throughput > 0:
                kwargs["offer_throughput"] = throughput

            container = await database.create_container_if_not_exists(**kwargs)
            properties = await container.read()

            return {
                "id": properties.get("id"),
                "self": properties.get("_self"),
                "etag": properties.get("_etag"),
                "partition_key": properties.get("partitionKey", {}).get("paths", []),
                "indexing_policy": properties.get("indexingPolicy"),
                "default_ttl": properties.get("defaultTtl"),
                "unique_key_policy": properties.get("uniqueKeyPolicy"),
            }

    async def delete_container(
        self,
        account_endpoint: str,
        database_name: str,
        container_name: str,
    ) -> dict[str, Any]:
        """
        Delete a container from a Cosmos DB database.

        WARNING: This permanently deletes the container and ALL its data.

        Args:
            account_endpoint: The Cosmos DB account endpoint URL.
            database_name: Name of the database.
            container_name: Name of the container to delete.

        Returns:
            Confirmation of deletion.
        """
        from azure.cosmos.aio import CosmosClient

        credential = self.get_credential()

        async with CosmosClient(url=account_endpoint, credential=credential) as client:
            database = client.get_database_client(database_name)
            await database.delete_container(container_name)

        return {
            "deleted": True,
            "database_name": database_name,
            "container_name": container_name,
        }

    async def get_account(
        self,
        subscription: str,
        account_name: str,
        resource_group: str = "",
    ) -> dict[str, Any]:
        """
        Get a single Cosmos DB account by name via Resource Graph.

        Args:
            subscription: Subscription ID or name.
            account_name: Name of the Cosmos DB account.
            resource_group: Optional resource group filter.

        Returns:
            Cosmos DB account details dictionary.
        """
        sub_id = await self.resolve_subscription(subscription)

        query = (
            "resources "
            "| where type =~ 'microsoft.documentdb/databaseaccounts' "
            f"| where name =~ '{account_name}'"
        )

        if resource_group:
            query += f" | where resourceGroup =~ '{resource_group}'"

        query += (
            " | project id, name, location, resourceGroup, subscriptionId, kind, tags, "
            "documentEndpoint = properties.documentEndpoint, "
            "consistencyLevel = properties.consistencyPolicy.defaultConsistencyLevel, "
            "provisioningState = properties.provisioningState, "
            "enableFreeTier = properties.enableFreeTier, "
            "capacityMode = properties.capacity.mode, "
            "writeLocations = properties.writeLocations, "
            "readLocations = properties.readLocations"
        )

        result = await self.execute_resource_graph_query(
            query=query,
            subscriptions=[sub_id],
        )

        data = result.get("data", [])
        if not data:
            msg = f"Cosmos DB account '{account_name}' not found"
            raise ValueError(msg)

        return data[0]
