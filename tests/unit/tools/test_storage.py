"""Unit tests for Storage tools.

Tests all 8 Storage tools:
- storage_account_list
- storage_account_get
- storage_container_list
- storage_blob_list
- storage_blob_read
- storage_blob_write
- storage_table_query
- storage_queue_list
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from azure_mcp.tools.storage.account import (
    StorageAccountGetOptions,
    StorageAccountGetTool,
    StorageAccountListOptions,
    StorageAccountListTool,
)
from azure_mcp.tools.storage.blob import (
    StorageBlobListOptions,
    StorageBlobListTool,
    StorageBlobReadOptions,
    StorageBlobReadTool,
    StorageBlobWriteOptions,
    StorageBlobWriteTool,
)
from azure_mcp.tools.storage.container import (
    StorageContainerListOptions,
    StorageContainerListTool,
)
from azure_mcp.tools.storage.queue import StorageQueueListOptions, StorageQueueListTool
from azure_mcp.tools.storage.table import StorageTableQueryOptions, StorageTableQueryTool


# =============================================================================
# StorageAccountListOptions Tests
# =============================================================================


class TestStorageAccountListOptions:
    """Tests for StorageAccountListOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = StorageAccountListOptions(subscription="my-sub")
        assert options.subscription == "my-sub"
        assert options.resource_group == ""

    def test_full_options(self):
        """Test with all fields specified."""
        options = StorageAccountListOptions(
            subscription="my-sub",
            resource_group="my-rg",
        )
        assert options.subscription == "my-sub"
        assert options.resource_group == "my-rg"

    def test_missing_subscription_raises(self):
        """Test that missing subscription raises error."""
        with pytest.raises(ValidationError):
            StorageAccountListOptions()


# =============================================================================
# StorageAccountListTool Tests
# =============================================================================


class TestStorageAccountListTool:
    """Tests for StorageAccountListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = StorageAccountListTool()
        assert tool.name == "storage_account_list"
        assert "storage accounts" in tool.description.lower()
        assert tool.metadata.read_only is True
        assert tool.metadata.destructive is False
        assert tool.metadata.idempotent is True

    def test_options_schema(self):
        """Test that options schema is valid JSON schema."""
        tool = StorageAccountListTool()
        schema = tool.get_options_schema()

        assert "properties" in schema
        assert "subscription" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_calls_service(self):
        """Test that execute calls the service correctly."""
        tool = StorageAccountListTool()
        options = StorageAccountListOptions(subscription="my-sub")

        mock_result = [
            {"name": "storage1", "location": "eastus", "kind": "StorageV2"},
            {"name": "storage2", "location": "westus", "kind": "BlobStorage"},
        ]

        with patch(
            "azure_mcp.tools.storage.service.StorageService.list_accounts",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert len(result) == 2
        assert result[0]["name"] == "storage1"


# =============================================================================
# StorageAccountGetOptions Tests
# =============================================================================


class TestStorageAccountGetOptions:
    """Tests for StorageAccountGetOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = StorageAccountGetOptions(
            subscription="my-sub",
            account_name="myaccount",
        )
        assert options.subscription == "my-sub"
        assert options.account_name == "myaccount"
        assert options.resource_group == ""

    def test_missing_account_name_raises(self):
        """Test that missing account_name raises error."""
        with pytest.raises(ValidationError):
            StorageAccountGetOptions(subscription="my-sub")


# =============================================================================
# StorageAccountGetTool Tests
# =============================================================================


class TestStorageAccountGetTool:
    """Tests for StorageAccountGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = StorageAccountGetTool()
        assert tool.name == "storage_account_get"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self):
        """Test that execute calls the service correctly."""
        tool = StorageAccountGetTool()
        options = StorageAccountGetOptions(
            subscription="my-sub",
            account_name="myaccount",
        )

        mock_result = {
            "name": "myaccount",
            "location": "eastus",
            "kind": "StorageV2",
            "sku": "Standard_LRS",
        }

        with patch(
            "azure_mcp.tools.storage.service.StorageService.get_account",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert result["name"] == "myaccount"
        assert result["sku"] == "Standard_LRS"


# =============================================================================
# StorageContainerListOptions Tests
# =============================================================================


class TestStorageContainerListOptions:
    """Tests for StorageContainerListOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = StorageContainerListOptions(account_name="myaccount")
        assert options.account_name == "myaccount"
        assert options.prefix == ""
        assert options.max_results == 100

    def test_max_results_validation(self):
        """Test max_results bounds."""
        with pytest.raises(ValidationError):
            StorageContainerListOptions(account_name="myaccount", max_results=0)

        with pytest.raises(ValidationError):
            StorageContainerListOptions(account_name="myaccount", max_results=1000)


# =============================================================================
# StorageContainerListTool Tests
# =============================================================================


class TestStorageContainerListTool:
    """Tests for StorageContainerListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = StorageContainerListTool()
        assert tool.name == "storage_container_list"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self):
        """Test that execute calls the service correctly."""
        tool = StorageContainerListTool()
        options = StorageContainerListOptions(account_name="myaccount")

        mock_result = [
            {"name": "container1", "public_access": None},
            {"name": "container2", "public_access": "blob"},
        ]

        with patch(
            "azure_mcp.tools.storage.service.StorageService.list_containers",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert len(result) == 2
        assert result[0]["name"] == "container1"


# =============================================================================
# StorageBlobListOptions Tests
# =============================================================================


class TestStorageBlobListOptions:
    """Tests for StorageBlobListOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = StorageBlobListOptions(
            account_name="myaccount",
            container_name="mycontainer",
        )
        assert options.account_name == "myaccount"
        assert options.container_name == "mycontainer"
        assert options.prefix == ""
        assert options.max_results == 100
        assert options.include_metadata is False

    def test_max_results_bounds(self):
        """Test max_results validation."""
        options = StorageBlobListOptions(
            account_name="a",
            container_name="c",
            max_results=1000,
        )
        assert options.max_results == 1000

        with pytest.raises(ValidationError):
            StorageBlobListOptions(
                account_name="a",
                container_name="c",
                max_results=1001,
            )


# =============================================================================
# StorageBlobListTool Tests
# =============================================================================


class TestStorageBlobListTool:
    """Tests for StorageBlobListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = StorageBlobListTool()
        assert tool.name == "storage_blob_list"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self):
        """Test that execute calls the service correctly."""
        tool = StorageBlobListTool()
        options = StorageBlobListOptions(
            account_name="myaccount",
            container_name="mycontainer",
        )

        mock_result = [
            {"name": "file1.txt", "size": 1024, "content_type": "text/plain"},
            {"name": "file2.json", "size": 512, "content_type": "application/json"},
        ]

        with patch(
            "azure_mcp.tools.storage.service.StorageService.list_blobs",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert len(result) == 2
        assert result[0]["name"] == "file1.txt"


# =============================================================================
# StorageBlobReadOptions Tests
# =============================================================================


class TestStorageBlobReadOptions:
    """Tests for StorageBlobReadOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = StorageBlobReadOptions(
            account_name="myaccount",
            container_name="mycontainer",
            blob_name="myblob.txt",
        )
        assert options.encoding == "auto"
        assert options.max_size_bytes == 10 * 1024 * 1024

    def test_encoding_validation(self):
        """Test encoding options."""
        options = StorageBlobReadOptions(
            account_name="a",
            container_name="c",
            blob_name="b",
            encoding="base64",
        )
        assert options.encoding == "base64"

        with pytest.raises(ValidationError):
            StorageBlobReadOptions(
                account_name="a",
                container_name="c",
                blob_name="b",
                encoding="invalid",
            )


# =============================================================================
# StorageBlobReadTool Tests
# =============================================================================


class TestStorageBlobReadTool:
    """Tests for StorageBlobReadTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = StorageBlobReadTool()
        assert tool.name == "storage_blob_read"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_text_content(self):
        """Test reading text content."""
        tool = StorageBlobReadTool()
        options = StorageBlobReadOptions(
            account_name="myaccount",
            container_name="mycontainer",
            blob_name="test.txt",
        )

        mock_result = {
            "content": "Hello, World!",
            "encoding": "utf-8",
            "content_type": "text/plain",
            "size": 13,
        }

        with patch(
            "azure_mcp.tools.storage.service.StorageService.read_blob",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert result["content"] == "Hello, World!"
        assert result["encoding"] == "utf-8"


# =============================================================================
# StorageBlobWriteOptions Tests
# =============================================================================


class TestStorageBlobWriteOptions:
    """Tests for StorageBlobWriteOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = StorageBlobWriteOptions(
            account_name="myaccount",
            container_name="mycontainer",
            blob_name="myblob.txt",
            content="Hello, World!",
        )
        assert options.content_type == ""
        assert options.encoding == "utf-8"
        assert options.overwrite is True

    def test_encoding_options(self):
        """Test encoding validation."""
        options = StorageBlobWriteOptions(
            account_name="a",
            container_name="c",
            blob_name="b",
            content="SGVsbG8=",
            encoding="base64",
        )
        assert options.encoding == "base64"


# =============================================================================
# StorageBlobWriteTool Tests
# =============================================================================


class TestStorageBlobWriteTool:
    """Tests for StorageBlobWriteTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = StorageBlobWriteTool()
        assert tool.name == "storage_blob_write"
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is True

    @pytest.mark.asyncio
    async def test_execute_writes_content(self):
        """Test writing content."""
        tool = StorageBlobWriteTool()
        options = StorageBlobWriteOptions(
            account_name="myaccount",
            container_name="mycontainer",
            blob_name="test.txt",
            content="Hello, World!",
        )

        mock_result = {
            "blob_name": "test.txt",
            "container": "mycontainer",
            "account": "myaccount",
            "size": 13,
        }

        with patch(
            "azure_mcp.tools.storage.service.StorageService.write_blob",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert result["blob_name"] == "test.txt"
        assert result["size"] == 13


# =============================================================================
# StorageTableQueryOptions Tests
# =============================================================================


class TestStorageTableQueryOptions:
    """Tests for StorageTableQueryOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = StorageTableQueryOptions(
            account_name="myaccount",
            table_name="mytable",
        )
        assert options.filter_query == ""
        assert options.select == ""
        assert options.max_results == 100

    def test_filter_query(self):
        """Test with OData filter."""
        options = StorageTableQueryOptions(
            account_name="a",
            table_name="t",
            filter_query="PartitionKey eq 'pk1'",
        )
        assert options.filter_query == "PartitionKey eq 'pk1'"


# =============================================================================
# StorageTableQueryTool Tests
# =============================================================================


class TestStorageTableQueryTool:
    """Tests for StorageTableQueryTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = StorageTableQueryTool()
        assert tool.name == "storage_table_query"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_queries_table(self):
        """Test querying table entities."""
        tool = StorageTableQueryTool()
        options = StorageTableQueryOptions(
            account_name="myaccount",
            table_name="mytable",
        )

        mock_result = [
            {"PartitionKey": "pk1", "RowKey": "rk1", "Name": "Entity1"},
            {"PartitionKey": "pk1", "RowKey": "rk2", "Name": "Entity2"},
        ]

        with patch(
            "azure_mcp.tools.storage.service.StorageService.query_table_entities",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert len(result) == 2
        assert result[0]["Name"] == "Entity1"


# =============================================================================
# StorageQueueListOptions Tests
# =============================================================================


class TestStorageQueueListOptions:
    """Tests for StorageQueueListOptions validation."""

    def test_minimal_options(self):
        """Test with only required fields."""
        options = StorageQueueListOptions(account_name="myaccount")
        assert options.account_name == "myaccount"
        assert options.prefix == ""
        assert options.max_results == 100


# =============================================================================
# StorageQueueListTool Tests
# =============================================================================


class TestStorageQueueListTool:
    """Tests for StorageQueueListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = StorageQueueListTool()
        assert tool.name == "storage_queue_list"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_lists_queues(self):
        """Test listing queues."""
        tool = StorageQueueListTool()
        options = StorageQueueListOptions(account_name="myaccount")

        mock_result = [
            {"name": "queue1", "metadata": {}},
            {"name": "queue2", "metadata": {"env": "prod"}},
        ]

        with patch(
            "azure_mcp.tools.storage.service.StorageService.list_queues",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await tool.execute(options)

        assert len(result) == 2
        assert result[0]["name"] == "queue1"


# =============================================================================
# StorageService Binary Detection Tests
# =============================================================================


class TestStorageServiceBinaryDetection:
    """Tests for binary content detection in StorageService."""

    def test_binary_content_types(self):
        """Test that known binary content types are detected."""
        from azure_mcp.tools.storage.service import StorageService

        service = StorageService()

        # Test binary content types
        assert service._is_binary_content("image/png", b"test") is True
        assert service._is_binary_content("application/pdf", b"test") is True
        assert service._is_binary_content("application/zip", b"test") is True

        # Test text content types
        assert service._is_binary_content("text/plain", b"hello") is False
        assert service._is_binary_content("text/html", b"<html>") is False

    def test_magic_bytes_detection(self):
        """Test detection via magic bytes."""
        from azure_mcp.tools.storage.service import StorageService

        service = StorageService()

        # PNG magic bytes
        assert service._is_binary_content(None, b"\x89PNG\r\n\x1a\n") is True

        # JPEG magic bytes
        assert service._is_binary_content(None, b"\xff\xd8\xff") is True

        # PDF magic bytes
        assert service._is_binary_content(None, b"%PDF-1.4") is True

        # Text content
        assert service._is_binary_content(None, b"Hello, World!") is False

    def test_utf8_fallback(self):
        """Test UTF-8 decode fallback for unknown content."""
        from azure_mcp.tools.storage.service import StorageService

        service = StorageService()

        # Valid UTF-8
        assert service._is_binary_content(None, "Hello, World!".encode("utf-8")) is False

        # Invalid UTF-8 (binary)
        assert service._is_binary_content(None, b"\x80\x81\x82\x83") is True
