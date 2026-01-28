"""Storage service for Azure operations.

Provides methods for managing storage accounts, blobs, containers, tables, and queues.
"""

from __future__ import annotations

import base64
from typing import Any

from azure_mcp.core.base import AzureService


# Binary content types that should be returned as base64
BINARY_CONTENT_TYPES = {
    "application/octet-stream",
    "application/pdf",
    "application/zip",
    "application/x-zip-compressed",
    "application/gzip",
    "application/x-tar",
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/svg+xml",
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "video/mp4",
    "video/mpeg",
    "video/webm",
}

# Magic bytes for common binary formats
MAGIC_BYTES = {
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"PK\x03\x04": "application/zip",
    b"%PDF": "application/pdf",
    b"\x1f\x8b": "application/gzip",
}


class StorageService(AzureService):
    """Service for Azure Storage operations."""

    def _get_account_url(self, account_name: str, service: str = "blob") -> str:
        """Build the storage account URL for a specific service."""
        return f"https://{account_name}.{service}.core.windows.net"

    def _is_binary_content(self, content_type: str | None, data: bytes) -> bool:
        """Detect if content is binary based on content-type and magic bytes."""
        # Check content type
        if content_type:
            base_type = content_type.split(";")[0].strip().lower()
            if base_type in BINARY_CONTENT_TYPES:
                return True
            if base_type.startswith("text/"):
                return False

        # Check magic bytes
        for magic, _ in MAGIC_BYTES.items():
            if data.startswith(magic):
                return True

        # Try to decode as UTF-8
        try:
            data[:1024].decode("utf-8")
        except UnicodeDecodeError:
            return True

        return False

    async def list_accounts(
        self,
        subscription: str,
        resource_group: str = "",
    ) -> list[dict[str, Any]]:
        """
        List storage accounts using Resource Graph.

        Args:
            subscription: Subscription ID or name.
            resource_group: Optional resource group filter.

        Returns:
            List of storage account summaries.
        """
        from azure.mgmt.resourcegraph import ResourceGraphClient
        from azure.mgmt.resourcegraph.models import QueryRequest

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()

        query = """
        resources
        | where type =~ 'Microsoft.Storage/storageAccounts'
        | project
            id,
            name,
            location,
            resourceGroup,
            kind,
            sku = sku.name,
            accessTier = properties.accessTier,
            primaryEndpoints = properties.primaryEndpoints,
            creationTime = properties.creationTime,
            provisioningState = properties.provisioningState
        """

        if resource_group:
            query += f"\n| where resourceGroup =~ '{resource_group}'"

        client = ResourceGraphClient(credential)
        request = QueryRequest(subscriptions=[sub_id], query=query)
        result = client.resources(request)

        return list(result.data) if result.data else []

    async def get_account(
        self,
        subscription: str,
        account_name: str,
        resource_group: str = "",
    ) -> dict[str, Any]:
        """
        Get detailed information about a storage account.

        Args:
            subscription: Subscription ID or name.
            account_name: Name of the storage account.
            resource_group: Optional resource group (speeds up lookup).

        Returns:
            Storage account details.
        """
        from azure.mgmt.resourcegraph import ResourceGraphClient
        from azure.mgmt.resourcegraph.models import QueryRequest

        sub_id = await self.resolve_subscription(subscription)
        credential = self.get_credential()

        query = f"""
        resources
        | where type =~ 'Microsoft.Storage/storageAccounts'
        | where name =~ '{account_name}'
        | project
            id,
            name,
            location,
            resourceGroup,
            kind,
            sku = sku.name,
            tags,
            accessTier = properties.accessTier,
            primaryEndpoints = properties.primaryEndpoints,
            primaryLocation = properties.primaryLocation,
            secondaryLocation = properties.secondaryLocation,
            creationTime = properties.creationTime,
            provisioningState = properties.provisioningState,
            allowBlobPublicAccess = properties.allowBlobPublicAccess,
            minimumTlsVersion = properties.minimumTlsVersion,
            supportsHttpsTrafficOnly = properties.supportsHttpsTrafficOnly,
            networkAcls = properties.networkAcls,
            encryption = properties.encryption
        """

        if resource_group:
            query += f"\n| where resourceGroup =~ '{resource_group}'"

        client = ResourceGraphClient(credential)
        request = QueryRequest(subscriptions=[sub_id], query=query)
        result = client.resources(request)

        if not result.data:
            raise ValueError(f"Storage account '{account_name}' not found")

        return result.data[0]

    async def list_containers(
        self,
        account_name: str,
        prefix: str = "",
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List containers in a storage account.

        Args:
            account_name: Name of the storage account.
            prefix: Optional prefix to filter containers.
            max_results: Maximum number of results.

        Returns:
            List of container information.
        """
        from azure.storage.blob.aio import BlobServiceClient

        credential = self.get_credential()
        account_url = self._get_account_url(account_name, "blob")

        async with BlobServiceClient(account_url, credential=credential) as client:
            containers = []
            count = 0

            async for container in client.list_containers(
                name_starts_with=prefix if prefix else None,
                include_metadata=True,
            ):
                if count >= max_results:
                    break

                containers.append(
                    {
                        "name": container.name,
                        "last_modified": container.last_modified.isoformat()
                        if container.last_modified
                        else None,
                        "etag": container.etag,
                        "lease_status": container.lease.status if container.lease else None,
                        "lease_state": container.lease.state if container.lease else None,
                        "public_access": container.public_access,
                        "metadata": dict(container.metadata) if container.metadata else {},
                    }
                )
                count += 1

            return containers

    async def list_blobs(
        self,
        account_name: str,
        container_name: str,
        prefix: str = "",
        max_results: int = 100,
        include_metadata: bool = False,
    ) -> list[dict[str, Any]]:
        """
        List blobs in a container.

        Args:
            account_name: Name of the storage account.
            container_name: Name of the container.
            prefix: Optional prefix to filter blobs.
            max_results: Maximum number of results.
            include_metadata: Whether to include blob metadata.

        Returns:
            List of blob information.
        """
        from azure.storage.blob.aio import ContainerClient

        credential = self.get_credential()
        account_url = self._get_account_url(account_name, "blob")

        async with ContainerClient(account_url, container_name, credential=credential) as client:
            blobs = []
            count = 0

            async for blob in client.list_blobs(
                name_starts_with=prefix if prefix else None,
                include=["metadata"] if include_metadata else None,
            ):
                if count >= max_results:
                    break

                blobs.append(
                    {
                        "name": blob.name,
                        "size": blob.size,
                        "content_type": blob.content_settings.content_type
                        if blob.content_settings
                        else None,
                        "last_modified": blob.last_modified.isoformat()
                        if blob.last_modified
                        else None,
                        "etag": blob.etag,
                        "blob_type": blob.blob_type,
                        "lease_status": blob.lease.status if blob.lease else None,
                        "metadata": dict(blob.metadata)
                        if include_metadata and blob.metadata
                        else {},
                    }
                )
                count += 1

            return blobs

    async def read_blob(
        self,
        account_name: str,
        container_name: str,
        blob_name: str,
        encoding: str = "auto",
        max_size_bytes: int = 10 * 1024 * 1024,  # 10 MB default
    ) -> dict[str, Any]:
        """
        Read blob content with auto-detection of text vs binary.

        Args:
            account_name: Name of the storage account.
            container_name: Name of the container.
            blob_name: Name of the blob.
            encoding: Encoding to use ('auto', 'utf-8', 'base64', etc.)
            max_size_bytes: Maximum size to read (default 10MB).

        Returns:
            Dict with content, encoding, content_type, and size.
        """
        from azure.storage.blob.aio import BlobClient

        credential = self.get_credential()
        account_url = self._get_account_url(account_name, "blob")

        async with BlobClient(
            account_url, container_name, blob_name, credential=credential
        ) as client:
            # Get blob properties first
            properties = await client.get_blob_properties()
            blob_size = properties.size

            if blob_size > max_size_bytes:
                raise ValueError(
                    f"Blob size ({blob_size} bytes) exceeds maximum "
                    f"({max_size_bytes} bytes). Use a smaller blob or increase limit."
                )

            # Download content
            download = await client.download_blob()
            data = await download.readall()
            content_type = properties.content_settings.content_type

            # Determine encoding
            if encoding == "auto":
                is_binary = self._is_binary_content(content_type, data)
                if is_binary:
                    return {
                        "content": base64.b64encode(data).decode("ascii"),
                        "encoding": "base64",
                        "content_type": content_type or "application/octet-stream",
                        "size": blob_size,
                    }
                else:
                    return {
                        "content": data.decode("utf-8"),
                        "encoding": "utf-8",
                        "content_type": content_type or "text/plain",
                        "size": blob_size,
                    }
            elif encoding == "base64":
                return {
                    "content": base64.b64encode(data).decode("ascii"),
                    "encoding": "base64",
                    "content_type": content_type or "application/octet-stream",
                    "size": blob_size,
                }
            else:
                # Try specified encoding
                return {
                    "content": data.decode(encoding),
                    "encoding": encoding,
                    "content_type": content_type or "text/plain",
                    "size": blob_size,
                }

    async def write_blob(
        self,
        account_name: str,
        container_name: str,
        blob_name: str,
        content: str,
        content_type: str = "",
        encoding: str = "utf-8",
        overwrite: bool = True,
    ) -> dict[str, Any]:
        """
        Write content to a blob.

        Args:
            account_name: Name of the storage account.
            container_name: Name of the container.
            blob_name: Name of the blob.
            content: Content to write (string, or base64 if encoding='base64').
            content_type: MIME type of the content.
            encoding: Encoding of content ('utf-8', 'base64', etc.)
            overwrite: Whether to overwrite existing blob.

        Returns:
            Dict with blob info after write.
        """
        from azure.storage.blob import ContentSettings
        from azure.storage.blob.aio import BlobClient

        credential = self.get_credential()
        account_url = self._get_account_url(account_name, "blob")

        # Prepare data
        data = base64.b64decode(content) if encoding == "base64" else content.encode(encoding)

        # Set content settings
        content_settings = None
        if content_type:
            content_settings = ContentSettings(content_type=content_type)

        async with BlobClient(
            account_url, container_name, blob_name, credential=credential
        ) as client:
            result = await client.upload_blob(
                data,
                overwrite=overwrite,
                content_settings=content_settings,
            )

            return {
                "blob_name": blob_name,
                "container": container_name,
                "account": account_name,
                "etag": result.get("etag"),
                "last_modified": result.get("last_modified").isoformat()
                if result.get("last_modified")
                else None,
                "size": len(data),
                "content_type": content_type or "application/octet-stream",
            }

    async def query_table_entities(
        self,
        account_name: str,
        table_name: str,
        filter_query: str = "",
        select: str = "",
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Query entities from a table.

        Args:
            account_name: Name of the storage account.
            table_name: Name of the table.
            filter_query: OData filter query (e.g., "PartitionKey eq 'pk1'").
            select: Comma-separated list of properties to return.
            max_results: Maximum number of results.

        Returns:
            List of entity dictionaries.
        """
        from azure.data.tables.aio import TableClient

        credential = self.get_credential()
        account_url = self._get_account_url(account_name, "table")

        async with TableClient(
            endpoint=account_url,
            table_name=table_name,
            credential=credential,
        ) as client:
            entities = []
            count = 0

            # Build query parameters
            query_params = {}
            if filter_query:
                query_params["query_filter"] = filter_query
            if select:
                query_params["select"] = [s.strip() for s in select.split(",")]

            async for entity in client.query_entities(**query_params):
                if count >= max_results:
                    break

                # Convert entity to plain dict, handling special types
                entity_dict = {}
                for key, value in entity.items():
                    if hasattr(value, "isoformat"):
                        entity_dict[key] = value.isoformat()
                    else:
                        entity_dict[key] = value

                entities.append(entity_dict)
                count += 1

            return entities

    async def list_queues(
        self,
        account_name: str,
        prefix: str = "",
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List queues in a storage account.

        Args:
            account_name: Name of the storage account.
            prefix: Optional prefix to filter queues.
            max_results: Maximum number of results.

        Returns:
            List of queue information.
        """
        from azure.storage.queue.aio import QueueServiceClient

        credential = self.get_credential()
        account_url = self._get_account_url(account_name, "queue")

        async with QueueServiceClient(account_url, credential=credential) as client:
            queues = []
            count = 0

            async for queue in client.list_queues(
                name_starts_with=prefix if prefix else None,
                include_metadata=True,
            ):
                if count >= max_results:
                    break

                queues.append(
                    {
                        "name": queue.name,
                        "metadata": dict(queue.metadata) if queue.metadata else {},
                    }
                )
                count += 1

            return queues
