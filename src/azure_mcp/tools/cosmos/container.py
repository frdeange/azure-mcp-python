"""Cosmos DB container tools.

Provides tools for container operations:
- cosmos_container_list: List containers in a database
- cosmos_container_create: Create a container
- cosmos_container_delete: Delete a container
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool
from azure_mcp.tools.cosmos.service import CosmosService


# -----------------------------------------------------------------------------
# cosmos_container_list
# -----------------------------------------------------------------------------


class CosmosContainerListOptions(BaseModel):
    """Options for listing containers in a Cosmos DB database."""

    account_endpoint: str = Field(
        ...,
        description=(
            "The Cosmos DB account endpoint URL "
            "(e.g., 'https://myaccount.documents.azure.com:443/'). "
            "Obtain this from the cosmos_account_list tool's 'documentEndpoint' field."
        ),
    )
    database_name: str = Field(
        ...,
        description=(
            "Name of the database to list containers from. "
            "Obtain available database names from cosmos_database_list."
        ),
    )


@register_tool("cosmos", "container")
class CosmosContainerListTool(AzureTool):
    """Tool for listing containers in a Cosmos DB database."""

    @property
    def name(self) -> str:
        return "cosmos_container_list"

    @property
    def description(self) -> str:
        return (
            "List all containers in a Cosmos DB database. "
            "Requires account endpoint from cosmos_account_list and database name from cosmos_database_list. "
            "Returns container IDs and partition key paths needed for item operations."
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
        return CosmosContainerListOptions

    async def execute(self, options: CosmosContainerListOptions) -> Any:
        """Execute the container listing."""
        service = CosmosService()

        try:
            return await service.list_containers(
                account_endpoint=options.account_endpoint,
                database_name=options.database_name,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# cosmos_container_create
# -----------------------------------------------------------------------------


class CosmosContainerCreateOptions(BaseModel):
    """Options for creating a container in a Cosmos DB database."""

    account_endpoint: str = Field(
        ...,
        description=(
            "The Cosmos DB account endpoint URL "
            "(e.g., 'https://myaccount.documents.azure.com:443/'). "
            "Obtain this from the cosmos_account_list tool's 'documentEndpoint' field."
        ),
    )
    database_name: str = Field(
        ...,
        description=(
            "Name of the database to create the container in. "
            "Use cosmos_database_list to find available databases."
        ),
    )
    container_name: str = Field(
        ...,
        description="Name of the container to create.",
    )
    partition_key_path: str = Field(
        ...,
        description=(
            "Partition key path for the container (e.g., '/category', '/tenantId', '/id'). "
            "This determines how data is distributed. Cannot be changed after creation."
        ),
    )
    throughput: int = Field(
        default=0,
        ge=0,
        le=1000000,
        description=(
            "Provisioned throughput in RU/s. Use 0 for shared database throughput "
            "or serverless accounts. Minimum provisioned value is 400 RU/s."
        ),
    )


@register_tool("cosmos", "container")
class CosmosContainerCreateTool(AzureTool):
    """Tool for creating a container in a Cosmos DB database."""

    @property
    def name(self) -> str:
        return "cosmos_container_create"

    @property
    def description(self) -> str:
        return (
            "Create a container in a Cosmos DB database. "
            "Requires a partition key path that determines data distribution. "
            "This operation is idempotent - if the container already exists, "
            "it returns the existing container without error. "
            "WARNING: This is a write operation. The partition key path cannot be changed after creation."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=False,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return CosmosContainerCreateOptions

    async def execute(self, options: CosmosContainerCreateOptions) -> Any:
        """Execute the container creation."""
        service = CosmosService()

        try:
            return await service.create_container(
                account_endpoint=options.account_endpoint,
                database_name=options.database_name,
                container_name=options.container_name,
                partition_key_path=options.partition_key_path,
                throughput=options.throughput,
            )
        except Exception as e:
            raise handle_azure_error(e) from e


# -----------------------------------------------------------------------------
# cosmos_container_delete
# -----------------------------------------------------------------------------


class CosmosContainerDeleteOptions(BaseModel):
    """Options for deleting a container from a Cosmos DB database."""

    account_endpoint: str = Field(
        ...,
        description=(
            "The Cosmos DB account endpoint URL "
            "(e.g., 'https://myaccount.documents.azure.com:443/'). "
            "Obtain this from the cosmos_account_list tool's 'documentEndpoint' field."
        ),
    )
    database_name: str = Field(
        ...,
        description="Name of the database containing the container.",
    )
    container_name: str = Field(
        ...,
        description=(
            "Name of the container to delete. "
            "Use cosmos_container_list to find available containers."
        ),
    )


@register_tool("cosmos", "container")
class CosmosContainerDeleteTool(AzureTool):
    """Tool for deleting a container from a Cosmos DB database."""

    @property
    def name(self) -> str:
        return "cosmos_container_delete"

    @property
    def description(self) -> str:
        return (
            "Delete a container from a Cosmos DB database. "
            "WARNING: This is a destructive operation that permanently deletes "
            "the container and ALL its data. This cannot be undone."
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=False,
            destructive=True,
            idempotent=True,
        )

    @property
    def options_model(self) -> type[BaseModel]:
        return CosmosContainerDeleteOptions

    async def execute(self, options: CosmosContainerDeleteOptions) -> Any:
        """Execute the container deletion."""
        service = CosmosService()

        try:
            return await service.delete_container(
                account_endpoint=options.account_endpoint,
                database_name=options.database_name,
                container_name=options.container_name,
            )
        except Exception as e:
            raise handle_azure_error(e) from e
