"""Tests for Cosmos DB tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from azure_mcp.tools.cosmos.account import (
    CosmosAccountGetOptions,
    CosmosAccountGetTool,
    CosmosAccountListOptions,
    CosmosAccountListTool,
    CosmosAccountService,
)
from azure_mcp.tools.cosmos.container import (
    CosmosContainerCreateOptions,
    CosmosContainerCreateTool,
    CosmosContainerDeleteOptions,
    CosmosContainerDeleteTool,
    CosmosContainerListOptions,
    CosmosContainerListTool,
)
from azure_mcp.tools.cosmos.database import (
    CosmosDatabaseCreateOptions,
    CosmosDatabaseCreateTool,
    CosmosDatabaseDeleteOptions,
    CosmosDatabaseDeleteTool,
    CosmosDatabaseListOptions,
    CosmosDatabaseListTool,
)
from azure_mcp.tools.cosmos.item import (
    CosmosItemDeleteOptions,
    CosmosItemDeleteTool,
    CosmosItemGetOptions,
    CosmosItemGetTool,
    CosmosItemQueryOptions,
    CosmosItemQueryTool,
    CosmosItemUpsertOptions,
    CosmosItemUpsertTool,
)
from azure_mcp.tools.cosmos.service import CosmosService


# =============================================================================
# Helper: Async iterator mock
# =============================================================================


class AsyncIteratorMock:
    """Helper to mock async iterators (async for)."""

    def __init__(self, items):
        self.items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.items)
        except StopIteration:
            raise StopAsyncIteration


# =============================================================================
# cosmos_account_list Tests
# =============================================================================


class TestCosmosAccountListOptions:
    """Tests for CosmosAccountListOptions model."""

    def test_minimal_options(self):
        """Test creation with minimal required fields."""
        options = CosmosAccountListOptions(subscription="my-sub")
        assert options.subscription == "my-sub"
        assert options.resource_group == ""  # Empty string, not None (AI Foundry compatibility)
        assert options.detail_level == "summary"
        assert options.limit == 50

    def test_full_options(self):
        """Test creation with all fields."""
        options = CosmosAccountListOptions(
            subscription="my-sub",
            resource_group="my-rg",
            detail_level="full",
            limit=100,
        )
        assert options.subscription == "my-sub"
        assert options.resource_group == "my-rg"
        assert options.detail_level == "full"
        assert options.limit == 100

    def test_detail_level_validation(self):
        """Test that detail_level only accepts valid values."""
        # Valid values should work
        CosmosAccountListOptions(subscription="sub", detail_level="summary")
        CosmosAccountListOptions(subscription="sub", detail_level="full")

        # Invalid value should raise
        with pytest.raises(ValueError):
            CosmosAccountListOptions(subscription="sub", detail_level="invalid")

    def test_limit_validation(self):
        """Test that limit must be between 1 and 200."""
        with pytest.raises(ValueError):
            CosmosAccountListOptions(subscription="sub", limit=0)

        with pytest.raises(ValueError):
            CosmosAccountListOptions(subscription="sub", limit=201)


class TestCosmosAccountListTool:
    """Tests for CosmosAccountListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CosmosAccountListTool()
        assert tool.name == "cosmos_account_list"
        assert "Cosmos DB" in tool.description
        assert "documentEndpoint" in tool.description
        assert tool.metadata.read_only is True
        assert tool.metadata.destructive is False
        assert tool.metadata.idempotent is True

    def test_options_schema(self):
        """Test that options schema is valid JSON schema."""
        tool = CosmosAccountListTool()
        schema = tool.get_options_schema()

        assert "properties" in schema
        assert "subscription" in schema["properties"]
        assert "detail_level" in schema["properties"]

    @pytest.mark.asyncio
    async def test_run_validates_options(self):
        """Test that run validates options."""
        tool = CosmosAccountListTool()

        # Missing required field should raise
        with pytest.raises(Exception):
            await tool.run({})

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CosmosAccountListTool()
        options = CosmosAccountListOptions(subscription="my-sub")

        with patch.object(CosmosAccountService, "list_accounts") as mock_list:
            mock_list.return_value = [
                {"name": "cosmos1", "documentEndpoint": "https://cosmos1.documents.azure.com:443/"}
            ]

            result = await tool.execute(options)

            mock_list.assert_called_once_with(
                subscription="my-sub",
                resource_group="",  # Empty string, not None (AI Foundry compatibility)
                detail_level="summary",
                limit=50,
            )
            assert len(result) == 1
            assert result[0]["name"] == "cosmos1"


# =============================================================================
# cosmos_account_get Tests
# =============================================================================


class TestCosmosAccountGetOptions:
    """Tests for CosmosAccountGetOptions model."""

    def test_minimal_options(self):
        """Test creation with minimal required fields."""
        options = CosmosAccountGetOptions(
            subscription="my-sub",
            account_name="mycosmosdb",
        )
        assert options.subscription == "my-sub"
        assert options.account_name == "mycosmosdb"
        assert options.resource_group == ""

    def test_full_options(self):
        """Test creation with all fields."""
        options = CosmosAccountGetOptions(
            subscription="my-sub",
            account_name="mycosmosdb",
            resource_group="my-rg",
        )
        assert options.resource_group == "my-rg"


class TestCosmosAccountGetTool:
    """Tests for CosmosAccountGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CosmosAccountGetTool()
        assert tool.name == "cosmos_account_get"
        assert "Cosmos DB" in tool.description
        assert "documentEndpoint" in tool.description
        assert tool.metadata.read_only is True
        assert tool.metadata.destructive is False
        assert tool.metadata.idempotent is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CosmosAccountGetTool()
        options = CosmosAccountGetOptions(
            subscription="my-sub",
            account_name="mycosmosdb",
        )

        with patch.object(CosmosService, "get_account") as mock_get:
            mock_get.return_value = {
                "name": "mycosmosdb",
                "documentEndpoint": "https://mycosmosdb.documents.azure.com:443/",
            }

            result = await tool.execute(options)

            mock_get.assert_called_once_with(
                subscription="my-sub",
                account_name="mycosmosdb",
                resource_group="",
            )
            assert result["name"] == "mycosmosdb"


# =============================================================================
# cosmos_database_list Tests
# =============================================================================


class TestCosmosDatabaseListOptions:
    """Tests for CosmosDatabaseListOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = CosmosDatabaseListOptions(
            account_endpoint="https://myaccount.documents.azure.com:443/"
        )
        assert options.account_endpoint == "https://myaccount.documents.azure.com:443/"


class TestCosmosDatabaseListTool:
    """Tests for CosmosDatabaseListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CosmosDatabaseListTool()
        assert tool.name == "cosmos_database_list"
        assert "database" in tool.description.lower()
        assert tool.metadata.read_only is True
        assert tool.metadata.idempotent is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CosmosDatabaseListTool()
        options = CosmosDatabaseListOptions(
            account_endpoint="https://test.documents.azure.com:443/"
        )

        with patch.object(CosmosService, "list_databases") as mock_list:
            mock_list.return_value = [{"id": "db1"}, {"id": "db2"}]

            result = await tool.execute(options)

            mock_list.assert_called_once_with(
                account_endpoint="https://test.documents.azure.com:443/"
            )
            assert len(result) == 2


# =============================================================================
# cosmos_database_create Tests
# =============================================================================


class TestCosmosDatabaseCreateOptions:
    """Tests for CosmosDatabaseCreateOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = CosmosDatabaseCreateOptions(
            account_endpoint="https://myaccount.documents.azure.com:443/",
            database_name="mydb",
        )
        assert options.account_endpoint == "https://myaccount.documents.azure.com:443/"
        assert options.database_name == "mydb"


class TestCosmosDatabaseCreateTool:
    """Tests for CosmosDatabaseCreateTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CosmosDatabaseCreateTool()
        assert tool.name == "cosmos_database_create"
        assert "create" in tool.description.lower()
        assert "idempotent" in tool.description.lower()
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is False
        assert tool.metadata.idempotent is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CosmosDatabaseCreateTool()
        options = CosmosDatabaseCreateOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="newdb",
        )

        with patch.object(CosmosService, "create_database") as mock_create:
            mock_create.return_value = {"id": "newdb", "self": "_self"}

            result = await tool.execute(options)

            mock_create.assert_called_once_with(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="newdb",
            )
            assert result["id"] == "newdb"


# =============================================================================
# cosmos_database_delete Tests
# =============================================================================


class TestCosmosDatabaseDeleteOptions:
    """Tests for CosmosDatabaseDeleteOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = CosmosDatabaseDeleteOptions(
            account_endpoint="https://myaccount.documents.azure.com:443/",
            database_name="mydb",
        )
        assert options.database_name == "mydb"


class TestCosmosDatabaseDeleteTool:
    """Tests for CosmosDatabaseDeleteTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CosmosDatabaseDeleteTool()
        assert tool.name == "cosmos_database_delete"
        assert "delete" in tool.description.lower()
        assert "destructive" in tool.description.lower()
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is True
        assert tool.metadata.idempotent is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CosmosDatabaseDeleteTool()
        options = CosmosDatabaseDeleteOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="olddb",
        )

        with patch.object(CosmosService, "delete_database") as mock_delete:
            mock_delete.return_value = {"deleted": True, "database_name": "olddb"}

            result = await tool.execute(options)

            mock_delete.assert_called_once_with(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="olddb",
            )
            assert result["deleted"] is True


# =============================================================================
# cosmos_container_list Tests
# =============================================================================


class TestCosmosContainerListOptions:
    """Tests for CosmosContainerListOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = CosmosContainerListOptions(
            account_endpoint="https://myaccount.documents.azure.com:443/",
            database_name="mydb",
        )
        assert options.account_endpoint == "https://myaccount.documents.azure.com:443/"
        assert options.database_name == "mydb"


class TestCosmosContainerListTool:
    """Tests for CosmosContainerListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CosmosContainerListTool()
        assert tool.name == "cosmos_container_list"
        assert "container" in tool.description.lower()
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CosmosContainerListTool()
        options = CosmosContainerListOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="mydb",
        )

        with patch.object(CosmosService, "list_containers") as mock_list:
            mock_list.return_value = [{"id": "container1", "partition_key": ["/pk"]}]

            result = await tool.execute(options)

            mock_list.assert_called_once_with(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
            )
            assert len(result) == 1


# =============================================================================
# cosmos_container_create Tests
# =============================================================================


class TestCosmosContainerCreateOptions:
    """Tests for CosmosContainerCreateOptions model."""

    def test_minimal_options(self):
        """Test creation with minimal required fields."""
        options = CosmosContainerCreateOptions(
            account_endpoint="https://myaccount.documents.azure.com:443/",
            database_name="mydb",
            container_name="mycontainer",
            partition_key_path="/category",
        )
        assert options.container_name == "mycontainer"
        assert options.partition_key_path == "/category"
        assert options.throughput == 0

    def test_full_options(self):
        """Test creation with all fields."""
        options = CosmosContainerCreateOptions(
            account_endpoint="https://myaccount.documents.azure.com:443/",
            database_name="mydb",
            container_name="mycontainer",
            partition_key_path="/tenantId",
            throughput=400,
        )
        assert options.throughput == 400


class TestCosmosContainerCreateTool:
    """Tests for CosmosContainerCreateTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CosmosContainerCreateTool()
        assert tool.name == "cosmos_container_create"
        assert "create" in tool.description.lower()
        assert "partition key" in tool.description.lower()
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is False
        assert tool.metadata.idempotent is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CosmosContainerCreateTool()
        options = CosmosContainerCreateOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="mydb",
            container_name="newcontainer",
            partition_key_path="/pk",
        )

        with patch.object(CosmosService, "create_container") as mock_create:
            mock_create.return_value = {
                "id": "newcontainer",
                "partition_key": ["/pk"],
            }

            result = await tool.execute(options)

            mock_create.assert_called_once_with(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="newcontainer",
                partition_key_path="/pk",
                throughput=0,
            )
            assert result["id"] == "newcontainer"


# =============================================================================
# cosmos_container_delete Tests
# =============================================================================


class TestCosmosContainerDeleteOptions:
    """Tests for CosmosContainerDeleteOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = CosmosContainerDeleteOptions(
            account_endpoint="https://myaccount.documents.azure.com:443/",
            database_name="mydb",
            container_name="mycontainer",
        )
        assert options.container_name == "mycontainer"


class TestCosmosContainerDeleteTool:
    """Tests for CosmosContainerDeleteTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CosmosContainerDeleteTool()
        assert tool.name == "cosmos_container_delete"
        assert "delete" in tool.description.lower()
        assert "destructive" in tool.description.lower()
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is True
        assert tool.metadata.idempotent is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CosmosContainerDeleteTool()
        options = CosmosContainerDeleteOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="mydb",
            container_name="oldcontainer",
        )

        with patch.object(CosmosService, "delete_container") as mock_delete:
            mock_delete.return_value = {
                "deleted": True,
                "database_name": "mydb",
                "container_name": "oldcontainer",
            }

            result = await tool.execute(options)

            mock_delete.assert_called_once_with(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="oldcontainer",
            )
            assert result["deleted"] is True


# =============================================================================
# cosmos_item_query Tests
# =============================================================================


class TestCosmosItemQueryOptions:
    """Tests for CosmosItemQueryOptions model."""

    def test_minimal_options(self):
        """Test creation with minimal required fields."""
        options = CosmosItemQueryOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="mydb",
            container_name="mycontainer",
            query="SELECT * FROM c",
        )
        assert options.query == "SELECT * FROM c"
        assert options.parameters == []  # Empty list, not None (AI Foundry compatibility)
        assert options.max_items == 100

    def test_full_options(self):
        """Test creation with all fields."""
        options = CosmosItemQueryOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="mydb",
            container_name="mycontainer",
            query="SELECT * FROM c WHERE c.status = @status",
            parameters=[{"name": "@status", "value": "active"}],
            max_items=50,
        )
        assert options.parameters == [{"name": "@status", "value": "active"}]
        assert options.max_items == 50

    def test_max_items_validation(self):
        """Test that max_items must be between 1 and 1000."""
        with pytest.raises(ValueError):
            CosmosItemQueryOptions(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="db",
                container_name="container",
                query="SELECT * FROM c",
                max_items=0,
            )


class TestCosmosItemQueryTool:
    """Tests for CosmosItemQueryTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CosmosItemQueryTool()
        assert tool.name == "cosmos_item_query"
        assert "SQL" in tool.description
        assert tool.metadata.read_only is True
        assert tool.metadata.idempotent is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CosmosItemQueryTool()
        options = CosmosItemQueryOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="mydb",
            container_name="mycontainer",
            query="SELECT * FROM c",
        )

        with patch.object(CosmosService, "query_items") as mock_query:
            mock_query.return_value = [{"id": "item1"}, {"id": "item2"}]

            result = await tool.execute(options)

            mock_query.assert_called_once_with(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="mycontainer",
                query="SELECT * FROM c",
                parameters=[],  # Empty list, not None (AI Foundry compatibility)
                max_items=100,
            )
            assert len(result) == 2


# =============================================================================
# cosmos_item_get Tests
# =============================================================================


class TestCosmosItemGetOptions:
    """Tests for CosmosItemGetOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = CosmosItemGetOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="mydb",
            container_name="mycontainer",
            item_id="item123",
            partition_key="pk-value",
        )
        assert options.item_id == "item123"
        assert options.partition_key == "pk-value"


class TestCosmosItemGetTool:
    """Tests for CosmosItemGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CosmosItemGetTool()
        assert tool.name == "cosmos_item_get"
        assert "partition key" in tool.description.lower()
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CosmosItemGetTool()
        options = CosmosItemGetOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="mydb",
            container_name="mycontainer",
            item_id="item123",
            partition_key="pk-value",
        )

        with patch.object(CosmosService, "get_item") as mock_get:
            mock_get.return_value = {"id": "item123", "data": "test"}

            result = await tool.execute(options)

            mock_get.assert_called_once_with(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="mycontainer",
                item_id="item123",
                partition_key="pk-value",
            )
            assert result["id"] == "item123"


# =============================================================================
# cosmos_item_upsert Tests
# =============================================================================


class TestCosmosItemUpsertOptions:
    """Tests for CosmosItemUpsertOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = CosmosItemUpsertOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="mydb",
            container_name="mycontainer",
            item={"id": "item123", "pk": "value", "data": "test"},
        )
        assert options.item["id"] == "item123"


class TestCosmosItemUpsertTool:
    """Tests for CosmosItemUpsertTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CosmosItemUpsertTool()
        assert tool.name == "cosmos_item_upsert"
        assert "upsert" in tool.description.lower()
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is True
        assert tool.metadata.idempotent is True  # Upsert is idempotent

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CosmosItemUpsertTool()
        item = {"id": "item123", "pk": "value", "data": "test"}
        options = CosmosItemUpsertOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="mydb",
            container_name="mycontainer",
            item=item,
        )

        with patch.object(CosmosService, "upsert_item") as mock_upsert:
            mock_upsert.return_value = item

            result = await tool.execute(options)

            mock_upsert.assert_called_once_with(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="mycontainer",
                item=item,
            )
            assert result["id"] == "item123"


# =============================================================================
# cosmos_item_delete Tests
# =============================================================================


class TestCosmosItemDeleteOptions:
    """Tests for CosmosItemDeleteOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = CosmosItemDeleteOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="mydb",
            container_name="mycontainer",
            item_id="item123",
            partition_key="pk-value",
        )
        assert options.item_id == "item123"
        assert options.partition_key == "pk-value"


class TestCosmosItemDeleteTool:
    """Tests for CosmosItemDeleteTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = CosmosItemDeleteTool()
        assert tool.name == "cosmos_item_delete"
        assert "delete" in tool.description.lower()
        assert "destructive" in tool.description.lower()
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = CosmosItemDeleteTool()
        options = CosmosItemDeleteOptions(
            account_endpoint="https://test.documents.azure.com:443/",
            database_name="mydb",
            container_name="mycontainer",
            item_id="item123",
            partition_key="pk-value",
        )

        with patch.object(CosmosService, "delete_item") as mock_delete:
            mock_delete.return_value = {
                "deleted": True,
                "item_id": "item123",
                "partition_key": "pk-value",
            }

            result = await tool.execute(options)

            mock_delete.assert_called_once_with(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="mycontainer",
                item_id="item123",
                partition_key="pk-value",
            )
            assert result["deleted"] is True


# =============================================================================
# CosmosService Tests (async SDK)
# =============================================================================


class TestCosmosService:
    """Tests for CosmosService data plane operations using async SDK."""

    @pytest.fixture
    def mock_cosmos_client(self):
        """Create a mock async Cosmos client with context manager support.

        In the azure.cosmos.aio SDK:
        - get_database_client() / get_container_client() are SYNC (return proxy objects)
        - list_databases() / list_containers() / query_items() are SYNC (return async iterables)
        - read_item() / upsert_item() / delete_item() / read() etc. are ASYNC (must be awaited)
        - create_database_if_not_exists() / delete_database() etc. are ASYNC
        """
        # Item-level mocks - use MagicMock so sync methods work correctly
        mock_container = MagicMock()
        mock_container.query_items.return_value = AsyncIteratorMock([{"id": "item1"}])
        mock_container.read_item = AsyncMock(return_value={"id": "item1", "data": "test"})
        mock_container.upsert_item = AsyncMock(return_value={"id": "item1", "data": "updated"})
        mock_container.delete_item = AsyncMock(return_value=None)
        mock_container.read = AsyncMock(
            return_value={
                "id": "container1",
                "_self": "_self",
                "_etag": "etag",
                "partitionKey": {"paths": ["/pk"]},
                "indexingPolicy": {},
                "defaultTtl": None,
                "uniqueKeyPolicy": {},
            }
        )

        # Database-level mocks - use MagicMock so sync methods work correctly
        mock_database = MagicMock()
        mock_database.list_containers.return_value = AsyncIteratorMock(
            [{"id": "container1", "partitionKey": {"paths": ["/pk"]}}]
        )
        mock_database.get_container_client.return_value = mock_container
        mock_database.delete_container = AsyncMock(return_value=None)
        mock_database.create_container_if_not_exists = AsyncMock(return_value=mock_container)
        mock_database.read = AsyncMock(
            return_value={
                "id": "db1",
                "_self": "_self",
                "_etag": "etag",
                "_colls": "colls",
                "_users": "users",
            }
        )

        # Client-level mocks - use MagicMock so sync methods work correctly
        mock_client = MagicMock()
        mock_client.list_databases.return_value = AsyncIteratorMock([{"id": "db1"}])
        mock_client.get_database_client.return_value = mock_database
        mock_client.create_database_if_not_exists = AsyncMock(return_value=mock_database)
        mock_client.delete_database = AsyncMock(return_value=None)

        # Context manager support
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        return mock_client

    @pytest.mark.asyncio
    async def test_list_databases(self, patch_credential, mock_cosmos_client):
        """Test listing databases with async SDK."""
        with patch("azure.cosmos.aio.CosmosClient") as mock_cls:
            mock_cls.return_value = mock_cosmos_client

            service = CosmosService()
            result = await service.list_databases(
                account_endpoint="https://test.documents.azure.com:443/"
            )

            assert len(result) == 1
            assert result[0]["id"] == "db1"

    @pytest.mark.asyncio
    async def test_list_containers(self, patch_credential, mock_cosmos_client):
        """Test listing containers with async SDK."""
        with patch("azure.cosmos.aio.CosmosClient") as mock_cls:
            mock_cls.return_value = mock_cosmos_client

            service = CosmosService()
            result = await service.list_containers(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
            )

            assert len(result) == 1
            assert result[0]["id"] == "container1"

    @pytest.mark.asyncio
    async def test_query_items(self, patch_credential, mock_cosmos_client):
        """Test querying items with async SDK."""
        with patch("azure.cosmos.aio.CosmosClient") as mock_cls:
            mock_cls.return_value = mock_cosmos_client

            service = CosmosService()
            result = await service.query_items(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="mycontainer",
                query="SELECT * FROM c",
            )

            assert len(result) == 1
            assert result[0]["id"] == "item1"

    @pytest.mark.asyncio
    async def test_get_item(self, patch_credential, mock_cosmos_client):
        """Test getting a single item with async SDK."""
        with patch("azure.cosmos.aio.CosmosClient") as mock_cls:
            mock_cls.return_value = mock_cosmos_client

            service = CosmosService()
            result = await service.get_item(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="mycontainer",
                item_id="item1",
                partition_key="pk",
            )

            assert result["id"] == "item1"

    @pytest.mark.asyncio
    async def test_upsert_item(self, patch_credential, mock_cosmos_client):
        """Test upserting an item with async SDK."""
        with patch("azure.cosmos.aio.CosmosClient") as mock_cls:
            mock_cls.return_value = mock_cosmos_client

            service = CosmosService()
            result = await service.upsert_item(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="mycontainer",
                item={"id": "item1", "data": "new"},
            )

            assert result["id"] == "item1"

    @pytest.mark.asyncio
    async def test_delete_item(self, patch_credential, mock_cosmos_client):
        """Test deleting an item with async SDK."""
        with patch("azure.cosmos.aio.CosmosClient") as mock_cls:
            mock_cls.return_value = mock_cosmos_client

            service = CosmosService()
            result = await service.delete_item(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="mycontainer",
                item_id="item1",
                partition_key="pk",
            )

            assert result["deleted"] is True
            assert result["item_id"] == "item1"

    @pytest.mark.asyncio
    async def test_create_database(self, patch_credential, mock_cosmos_client):
        """Test creating a database with async SDK."""
        with patch("azure.cosmos.aio.CosmosClient") as mock_cls:
            mock_cls.return_value = mock_cosmos_client

            service = CosmosService()
            result = await service.create_database(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="newdb",
            )

            assert result["id"] == "db1"
            mock_cosmos_client.create_database_if_not_exists.assert_called_once_with(id="newdb")

    @pytest.mark.asyncio
    async def test_delete_database(self, patch_credential, mock_cosmos_client):
        """Test deleting a database with async SDK."""
        with patch("azure.cosmos.aio.CosmosClient") as mock_cls:
            mock_cls.return_value = mock_cosmos_client

            service = CosmosService()
            result = await service.delete_database(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="olddb",
            )

            assert result["deleted"] is True
            assert result["database_name"] == "olddb"
            mock_cosmos_client.delete_database.assert_called_once_with("olddb")

    @pytest.mark.asyncio
    async def test_create_container(self, patch_credential, mock_cosmos_client):
        """Test creating a container with async SDK."""
        with (
            patch("azure.cosmos.aio.CosmosClient") as mock_cls,
            patch("azure.cosmos.PartitionKey") as mock_pk,
        ):
            mock_cls.return_value = mock_cosmos_client
            mock_pk_instance = MagicMock()
            mock_pk.return_value = mock_pk_instance

            service = CosmosService()
            result = await service.create_container(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="newcontainer",
                partition_key_path="/pk",
            )

            assert result["id"] == "container1"
            mock_pk.assert_called_once_with(path="/pk")

    @pytest.mark.asyncio
    async def test_create_container_with_throughput(self, patch_credential, mock_cosmos_client):
        """Test creating a container with provisioned throughput."""
        with (
            patch("azure.cosmos.aio.CosmosClient") as mock_cls,
            patch("azure.cosmos.PartitionKey") as mock_pk,
        ):
            mock_cls.return_value = mock_cosmos_client
            mock_pk_instance = MagicMock()
            mock_pk.return_value = mock_pk_instance

            mock_database = mock_cosmos_client.get_database_client.return_value

            service = CosmosService()
            await service.create_container(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="newcontainer",
                partition_key_path="/pk",
                throughput=400,
            )

            # Verify throughput was passed
            call_kwargs = mock_database.create_container_if_not_exists.call_args
            assert call_kwargs[1]["offer_throughput"] == 400

    @pytest.mark.asyncio
    async def test_delete_container(self, patch_credential, mock_cosmos_client):
        """Test deleting a container with async SDK."""
        with patch("azure.cosmos.aio.CosmosClient") as mock_cls:
            mock_cls.return_value = mock_cosmos_client

            service = CosmosService()
            result = await service.delete_container(
                account_endpoint="https://test.documents.azure.com:443/",
                database_name="mydb",
                container_name="oldcontainer",
            )

            assert result["deleted"] is True
            assert result["container_name"] == "oldcontainer"

    @pytest.mark.asyncio
    async def test_get_account(self, patch_credential):
        """Test getting a single account via Resource Graph."""
        service = CosmosService()

        with (
            patch.object(service, "resolve_subscription") as mock_resolve,
            patch.object(service, "execute_resource_graph_query") as mock_query,
        ):
            mock_resolve.return_value = "sub-id-123"
            mock_query.return_value = {
                "data": [
                    {
                        "name": "mycosmosdb",
                        "documentEndpoint": "https://mycosmosdb.documents.azure.com:443/",
                    }
                ]
            }

            result = await service.get_account(
                subscription="my-sub",
                account_name="mycosmosdb",
            )

            assert result["name"] == "mycosmosdb"
            mock_resolve.assert_called_once_with("my-sub")

    @pytest.mark.asyncio
    async def test_get_account_not_found(self, patch_credential):
        """Test getting a non-existent account raises ValueError."""
        service = CosmosService()

        with (
            patch.object(service, "resolve_subscription") as mock_resolve,
            patch.object(service, "execute_resource_graph_query") as mock_query,
        ):
            mock_resolve.return_value = "sub-id-123"
            mock_query.return_value = {"data": []}

            with pytest.raises(ValueError, match="not found"):
                await service.get_account(
                    subscription="my-sub",
                    account_name="nonexistent",
                )
