"""Tests for Cosmos DB tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from azure_mcp.tools.cosmos.account import (
    CosmosAccountListOptions,
    CosmosAccountListTool,
    CosmosAccountService,
)
from azure_mcp.tools.cosmos.container import (
    CosmosContainerListOptions,
    CosmosContainerListTool,
)
from azure_mcp.tools.cosmos.database import (
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
# CosmosService Tests
# =============================================================================


class TestCosmosService:
    """Tests for CosmosService data plane operations."""

    @pytest.fixture
    def mock_cosmos_client(self):
        """Create a mock Cosmos client."""
        mock_container = MagicMock()
        mock_container.query_items.return_value = [{"id": "item1"}]
        mock_container.read_item.return_value = {"id": "item1", "data": "test"}
        mock_container.upsert_item.return_value = {"id": "item1", "data": "updated"}
        mock_container.delete_item.return_value = None

        mock_database = MagicMock()
        mock_database.list_containers.return_value = [{"id": "container1"}]
        mock_database.get_container_client.return_value = mock_container

        mock_client = MagicMock()
        mock_client.list_databases.return_value = [{"id": "db1"}]
        mock_client.get_database_client.return_value = mock_database

        return mock_client

    @pytest.mark.asyncio
    async def test_list_databases(self, patch_credential, mock_cosmos_client):
        """Test listing databases."""
        with patch("azure.cosmos.CosmosClient") as mock_cls:
            mock_cls.return_value = mock_cosmos_client

            service = CosmosService()
            result = await service.list_databases(
                account_endpoint="https://test.documents.azure.com:443/"
            )

            assert len(result) == 1
            assert result[0]["id"] == "db1"

    @pytest.mark.asyncio
    async def test_list_containers(self, patch_credential, mock_cosmos_client):
        """Test listing containers."""
        with patch("azure.cosmos.CosmosClient") as mock_cls:
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
        """Test querying items."""
        with patch("azure.cosmos.CosmosClient") as mock_cls:
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
        """Test getting a single item."""
        with patch("azure.cosmos.CosmosClient") as mock_cls:
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
        """Test upserting an item."""
        with patch("azure.cosmos.CosmosClient") as mock_cls:
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
        """Test deleting an item."""
        with patch("azure.cosmos.CosmosClient") as mock_cls:
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
