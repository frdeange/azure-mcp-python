"""Tests for Azure AI Search tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from azure_mcp.tools.search.discovery import (
    SearchServiceGetOptions,
    SearchServiceGetTool,
    SearchServiceListOptions,
    SearchServiceListTool,
)
from azure_mcp.tools.search.document import (
    SearchDocumentDeleteOptions,
    SearchDocumentDeleteTool,
    SearchDocumentMergeOptions,
    SearchDocumentMergeTool,
    SearchDocumentUploadOptions,
    SearchDocumentUploadTool,
)
from azure_mcp.tools.search.index import (
    SearchIndexGetOptions,
    SearchIndexGetTool,
    SearchIndexListOptions,
    SearchIndexListTool,
    SearchIndexStatsOptions,
    SearchIndexStatsTool,
)
from azure_mcp.tools.search.query import (
    SearchDocumentGetOptions,
    SearchDocumentGetTool,
    SearchQueryOptions,
    SearchQueryTool,
)
from azure_mcp.tools.search.service import SearchService
from azure_mcp.tools.search.suggest import (
    SearchAutocompleteOptions,
    SearchAutocompleteTool,
    SearchSuggestOptions,
    SearchSuggestTool,
)


# =============================================================================
# search_service_list Tests
# =============================================================================


class TestSearchServiceListOptions:
    """Tests for SearchServiceListOptions model."""

    def test_minimal_options(self):
        """Test creation with minimal required fields."""
        options = SearchServiceListOptions(subscription="my-sub")
        assert options.subscription == "my-sub"
        assert options.resource_group == ""
        assert options.top == 100

    def test_full_options(self):
        """Test creation with all fields."""
        options = SearchServiceListOptions(
            subscription="my-sub",
            resource_group="my-rg",
            top=50,
        )
        assert options.subscription == "my-sub"
        assert options.resource_group == "my-rg"
        assert options.top == 50

    def test_top_validation(self):
        """Test that top must be between 1 and 1000."""
        with pytest.raises(ValueError):
            SearchServiceListOptions(subscription="sub", top=0)
        with pytest.raises(ValueError):
            SearchServiceListOptions(subscription="sub", top=1001)


class TestSearchServiceListTool:
    """Tests for SearchServiceListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = SearchServiceListTool()
        assert tool.name == "search_service_list"
        assert "Azure AI Search" in tool.description
        assert tool.metadata.read_only is True
        assert tool.metadata.destructive is False
        assert tool.metadata.idempotent is True

    def test_options_schema(self):
        """Test that options schema is valid."""
        tool = SearchServiceListTool()
        schema = tool.get_options_schema()
        assert "properties" in schema
        assert "subscription" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = SearchServiceListTool()
        options = SearchServiceListOptions(subscription="my-sub")

        with patch.object(SearchService, "list_search_services") as mock_list:
            mock_list.return_value = [
                {
                    "name": "mysearch",
                    "endpoint": "https://mysearch.search.windows.net",
                    "sku": "standard",
                }
            ]

            result = await tool.execute(options)

            mock_list.assert_called_once_with(
                subscription="my-sub",
                resource_group="",
                top=100,
            )
            assert len(result) == 1
            assert result[0]["name"] == "mysearch"


# =============================================================================
# search_service_get Tests
# =============================================================================


class TestSearchServiceGetOptions:
    """Tests for SearchServiceGetOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = SearchServiceGetOptions(
            subscription="my-sub",
            service_name="mysearch",
        )
        assert options.subscription == "my-sub"
        assert options.service_name == "mysearch"
        assert options.resource_group == ""


class TestSearchServiceGetTool:
    """Tests for SearchServiceGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = SearchServiceGetTool()
        assert tool.name == "search_service_get"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_returns_service(self, patch_credential):
        """Test successful service retrieval."""
        tool = SearchServiceGetTool()
        options = SearchServiceGetOptions(
            subscription="my-sub",
            service_name="mysearch",
        )

        with patch.object(SearchService, "get_search_service") as mock_get:
            mock_get.return_value = {
                "name": "mysearch",
                "endpoint": "https://mysearch.search.windows.net",
            }

            result = await tool.execute(options)

            assert result["name"] == "mysearch"

    @pytest.mark.asyncio
    async def test_execute_returns_error_when_not_found(self, patch_credential):
        """Test error response when service not found."""
        tool = SearchServiceGetTool()
        options = SearchServiceGetOptions(
            subscription="my-sub",
            service_name="nonexistent",
        )

        with patch.object(SearchService, "get_search_service") as mock_get:
            mock_get.return_value = None

            result = await tool.execute(options)

            assert "error" in result


# =============================================================================
# search_index_list Tests
# =============================================================================


class TestSearchIndexListOptions:
    """Tests for SearchIndexListOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = SearchIndexListOptions(endpoint="https://mysearch.search.windows.net")
        assert options.endpoint == "https://mysearch.search.windows.net"


class TestSearchIndexListTool:
    """Tests for SearchIndexListTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = SearchIndexListTool()
        assert tool.name == "search_index_list"
        assert "index" in tool.description.lower()
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = SearchIndexListTool()
        options = SearchIndexListOptions(endpoint="https://mysearch.search.windows.net")

        with patch.object(SearchService, "list_indexes") as mock_list:
            mock_list.return_value = [
                {"name": "index1", "fields_count": 10},
                {"name": "index2", "fields_count": 5},
            ]

            result = await tool.execute(options)

            mock_list.assert_called_once_with(endpoint="https://mysearch.search.windows.net")
            assert len(result) == 2


# =============================================================================
# search_index_get Tests
# =============================================================================


class TestSearchIndexGetOptions:
    """Tests for SearchIndexGetOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = SearchIndexGetOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
        )
        assert options.endpoint == "https://mysearch.search.windows.net"
        assert options.index_name == "myindex"


class TestSearchIndexGetTool:
    """Tests for SearchIndexGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = SearchIndexGetTool()
        assert tool.name == "search_index_get"
        assert "schema" in tool.description.lower()
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_returns_index_schema(self, patch_credential):
        """Test successful index retrieval."""
        tool = SearchIndexGetTool()
        options = SearchIndexGetOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
        )

        with patch.object(SearchService, "get_index") as mock_get:
            mock_get.return_value = {
                "name": "myindex",
                "fields": [
                    {"name": "id", "type": "Edm.String", "key": True},
                    {"name": "title", "type": "Edm.String", "searchable": True},
                ],
            }

            result = await tool.execute(options)

            assert result["name"] == "myindex"
            assert len(result["fields"]) == 2


# =============================================================================
# search_index_stats Tests
# =============================================================================


class TestSearchIndexStatsOptions:
    """Tests for SearchIndexStatsOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = SearchIndexStatsOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
        )
        assert options.endpoint == "https://mysearch.search.windows.net"
        assert options.index_name == "myindex"


class TestSearchIndexStatsTool:
    """Tests for SearchIndexStatsTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = SearchIndexStatsTool()
        assert tool.name == "search_index_stats"
        assert "statistics" in tool.description.lower()
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_returns_stats(self, patch_credential):
        """Test successful stats retrieval."""
        tool = SearchIndexStatsTool()
        options = SearchIndexStatsOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
        )

        with patch.object(SearchService, "get_index_statistics") as mock_stats:
            mock_stats.return_value = {
                "document_count": 1000,
                "storage_size_bytes": 1048576,
                "storage_size_mb": 1.0,
            }

            result = await tool.execute(options)

            assert result["document_count"] == 1000
            assert result["storage_size_mb"] == 1.0


# =============================================================================
# search_query Tests
# =============================================================================


class TestSearchQueryOptions:
    """Tests for SearchQueryOptions model."""

    def test_minimal_options(self):
        """Test creation with minimal required fields."""
        options = SearchQueryOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
        )
        assert options.endpoint == "https://mysearch.search.windows.net"
        assert options.index_name == "myindex"
        assert options.search_text == "*"
        assert options.top == 50
        assert options.skip == 0

    def test_full_options(self):
        """Test creation with all fields."""
        options = SearchQueryOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            search_text="machine learning",
            filter="category eq 'AI'",
            select="id,title,score",
            order_by="score desc",
            top=10,
            skip=20,
            include_total_count=True,
            search_fields="title,content",
            highlight_fields="title",
            facets=["category", "author"],
            query_type="full",
            search_mode="all",
        )
        assert options.search_text == "machine learning"
        assert options.filter == "category eq 'AI'"
        assert options.facets == ["category", "author"]

    def test_top_validation(self):
        """Test that top must be between 1 and 1000."""
        with pytest.raises(ValueError):
            SearchQueryOptions(
                endpoint="https://mysearch.search.windows.net",
                index_name="myindex",
                top=0,
            )
        with pytest.raises(ValueError):
            SearchQueryOptions(
                endpoint="https://mysearch.search.windows.net",
                index_name="myindex",
                top=1001,
            )


class TestSearchQueryTool:
    """Tests for SearchQueryTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = SearchQueryTool()
        assert tool.name == "search_query"
        assert "search" in tool.description.lower()
        assert tool.metadata.read_only is True
        assert tool.metadata.idempotent is True

    @pytest.mark.asyncio
    async def test_execute_calls_service(self, patch_credential):
        """Test that execute calls the service."""
        tool = SearchQueryTool()
        options = SearchQueryOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            search_text="test query",
        )

        with patch.object(SearchService, "search_documents") as mock_search:
            mock_search.return_value = {
                "documents": [
                    {"id": "1", "title": "Test Document"},
                ],
                "count": 1,
            }

            result = await tool.execute(options)

            mock_search.assert_called_once()
            assert result["count"] == 1
            assert len(result["documents"]) == 1


# =============================================================================
# search_document_get Tests
# =============================================================================


class TestSearchDocumentGetOptions:
    """Tests for SearchDocumentGetOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = SearchDocumentGetOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            key="doc123",
        )
        assert options.endpoint == "https://mysearch.search.windows.net"
        assert options.index_name == "myindex"
        assert options.key == "doc123"
        assert options.select == ""


class TestSearchDocumentGetTool:
    """Tests for SearchDocumentGetTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = SearchDocumentGetTool()
        assert tool.name == "search_document_get"
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_returns_document(self, patch_credential):
        """Test successful document retrieval."""
        tool = SearchDocumentGetTool()
        options = SearchDocumentGetOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            key="doc123",
        )

        with patch.object(SearchService, "get_document") as mock_get:
            mock_get.return_value = {
                "id": "doc123",
                "title": "Test Document",
            }

            result = await tool.execute(options)

            assert result["id"] == "doc123"


# =============================================================================
# search_suggest Tests
# =============================================================================


class TestSearchSuggestOptions:
    """Tests for SearchSuggestOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = SearchSuggestOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            search_text="micro",
            suggester_name="sg",
        )
        assert options.search_text == "micro"
        assert options.suggester_name == "sg"
        assert options.top == 5
        assert options.use_fuzzy_matching is False


class TestSearchSuggestTool:
    """Tests for SearchSuggestTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = SearchSuggestTool()
        assert tool.name == "search_suggest"
        assert "suggestion" in tool.description.lower()
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_returns_suggestions(self, patch_credential):
        """Test successful suggestions retrieval."""
        tool = SearchSuggestTool()
        options = SearchSuggestOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            search_text="micro",
            suggester_name="sg",
        )

        with patch.object(SearchService, "suggest") as mock_suggest:
            mock_suggest.return_value = [
                {"text": "microsoft", "document": {"id": "1"}},
                {"text": "microservices", "document": {"id": "2"}},
            ]

            result = await tool.execute(options)

            assert len(result) == 2
            assert result[0]["text"] == "microsoft"


# =============================================================================
# search_autocomplete Tests
# =============================================================================


class TestSearchAutocompleteOptions:
    """Tests for SearchAutocompleteOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = SearchAutocompleteOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            search_text="wash",
            suggester_name="sg",
        )
        assert options.search_text == "wash"
        assert options.mode == "oneTerm"
        assert options.top == 5


class TestSearchAutocompleteTool:
    """Tests for SearchAutocompleteTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = SearchAutocompleteTool()
        assert tool.name == "search_autocomplete"
        assert "autocomplete" in tool.description.lower()
        assert tool.metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_returns_completions(self, patch_credential):
        """Test successful autocomplete retrieval."""
        tool = SearchAutocompleteTool()
        options = SearchAutocompleteOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            search_text="wash",
            suggester_name="sg",
        )

        with patch.object(SearchService, "autocomplete") as mock_auto:
            mock_auto.return_value = [
                {"text": "washington", "query_plus_text": "washington"},
            ]

            result = await tool.execute(options)

            assert len(result) == 1
            assert result[0]["text"] == "washington"


# =============================================================================
# search_document_upload Tests
# =============================================================================


class TestSearchDocumentUploadOptions:
    """Tests for SearchDocumentUploadOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = SearchDocumentUploadOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            documents=[{"id": "1", "title": "Test"}],
        )
        assert options.endpoint == "https://mysearch.search.windows.net"
        assert len(options.documents) == 1

    def test_documents_validation(self):
        """Test that documents must not be empty."""
        with pytest.raises(ValueError):
            SearchDocumentUploadOptions(
                endpoint="https://mysearch.search.windows.net",
                index_name="myindex",
                documents=[],
            )


class TestSearchDocumentUploadTool:
    """Tests for SearchDocumentUploadTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = SearchDocumentUploadTool()
        assert tool.name == "search_document_upload"
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is False
        assert tool.metadata.idempotent is True

    @pytest.mark.asyncio
    async def test_execute_uploads_documents(self, patch_credential):
        """Test successful document upload."""
        tool = SearchDocumentUploadTool()
        options = SearchDocumentUploadOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            documents=[{"id": "1", "title": "Test"}],
        )

        with patch.object(SearchService, "upload_documents") as mock_upload:
            mock_upload.return_value = {
                "total": 1,
                "succeeded": 1,
                "failed": 0,
            }

            result = await tool.execute(options)

            assert result["succeeded"] == 1


# =============================================================================
# search_document_merge Tests
# =============================================================================


class TestSearchDocumentMergeOptions:
    """Tests for SearchDocumentMergeOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = SearchDocumentMergeOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            documents=[{"id": "1", "title": "Updated"}],
        )
        assert len(options.documents) == 1


class TestSearchDocumentMergeTool:
    """Tests for SearchDocumentMergeTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = SearchDocumentMergeTool()
        assert tool.name == "search_document_merge"
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is False

    @pytest.mark.asyncio
    async def test_execute_merges_documents(self, patch_credential):
        """Test successful document merge."""
        tool = SearchDocumentMergeTool()
        options = SearchDocumentMergeOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            documents=[{"id": "1", "title": "Updated"}],
        )

        with patch.object(SearchService, "merge_documents") as mock_merge:
            mock_merge.return_value = {
                "total": 1,
                "succeeded": 1,
                "failed": 0,
            }

            result = await tool.execute(options)

            assert result["succeeded"] == 1


# =============================================================================
# search_document_delete Tests
# =============================================================================


class TestSearchDocumentDeleteOptions:
    """Tests for SearchDocumentDeleteOptions model."""

    def test_options(self):
        """Test creation with required fields."""
        options = SearchDocumentDeleteOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            documents=[{"id": "1"}],
        )
        assert len(options.documents) == 1


class TestSearchDocumentDeleteTool:
    """Tests for SearchDocumentDeleteTool."""

    def test_tool_properties(self):
        """Test tool metadata properties."""
        tool = SearchDocumentDeleteTool()
        assert tool.name == "search_document_delete"
        assert tool.metadata.read_only is False
        assert tool.metadata.destructive is True

    @pytest.mark.asyncio
    async def test_execute_deletes_documents(self, patch_credential):
        """Test successful document deletion."""
        tool = SearchDocumentDeleteTool()
        options = SearchDocumentDeleteOptions(
            endpoint="https://mysearch.search.windows.net",
            index_name="myindex",
            documents=[{"id": "1"}],
        )

        with patch.object(SearchService, "delete_documents") as mock_delete:
            mock_delete.return_value = {
                "total": 1,
                "succeeded": 1,
                "failed": 0,
            }

            result = await tool.execute(options)

            assert result["succeeded"] == 1


# =============================================================================
# SearchService Tests
# =============================================================================


class TestSearchService:
    """Tests for SearchService class."""

    @pytest.mark.asyncio
    async def test_list_search_services_uses_resource_graph(self, patch_credential):
        """Test that list_search_services uses Resource Graph."""
        service = SearchService()

        with patch.object(service, "execute_resource_graph_query") as mock_query:
            with patch.object(service, "resolve_subscription") as mock_resolve:
                mock_resolve.return_value = "sub-id-123"
                mock_query.return_value = {
                    "data": [{"name": "search1", "endpoint": "https://search1.search.windows.net"}]
                }

                result = await service.list_search_services(subscription="my-sub")

                mock_resolve.assert_called_once_with("my-sub")
                mock_query.assert_called_once()
                # Verify Resource Graph query includes search services type
                call_args = mock_query.call_args
                assert "microsoft.search/searchservices" in call_args.kwargs["query"].lower()
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_search_service_not_found(self, patch_credential):
        """Test that get_search_service returns None when not found."""
        service = SearchService()

        with patch.object(service, "execute_resource_graph_query") as mock_query:
            with patch.object(service, "resolve_subscription") as mock_resolve:
                mock_resolve.return_value = "sub-id-123"
                mock_query.return_value = {"data": []}

                result = await service.get_search_service(
                    subscription="my-sub",
                    service_name="nonexistent",
                )

                assert result is None

    @pytest.mark.asyncio
    async def test_list_indexes_uses_async_client(self, patch_credential):
        """Test that list_indexes uses async SearchIndexClient."""
        service = SearchService()

        # Create mock index objects
        mock_index1 = MagicMock()
        mock_index1.name = "index1"
        mock_index1.fields = [MagicMock(), MagicMock()]
        mock_index1.suggesters = []
        mock_index1.scoring_profiles = []
        mock_index1.analyzers = []
        mock_index1.semantic_search = None
        mock_index1.vector_search = None

        # Create async iterator class that properly supports async for
        class AsyncIndexIterator:
            def __init__(self, indexes):
                self.indexes = indexes
                self.index = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.index >= len(self.indexes):
                    raise StopAsyncIteration
                result = self.indexes[self.index]
                self.index += 1
                return result

        # Create a mock that acts as async context manager
        class MockSearchIndexClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            def list_indexes(self):
                return AsyncIndexIterator([mock_index1])

        with patch("azure_mcp.tools.search.service.SearchService.get_credential") as mock_cred:
            mock_cred.return_value = MagicMock()
            with patch(
                "azure.search.documents.indexes.aio.SearchIndexClient",
                MockSearchIndexClient,
            ):
                result = await service.list_indexes(
                    endpoint="https://mysearch.search.windows.net"
                )

                assert len(result) == 1
                assert result[0]["name"] == "index1"
                assert result[0]["fields_count"] == 2

    @pytest.mark.asyncio
    async def test_search_documents_uses_async_client(self, patch_credential):
        """Test that search_documents uses async SearchClient."""
        service = SearchService()

        # Create mock search result
        mock_doc = {"id": "1", "title": "Test", "@search.score": 1.5}

        async def mock_search_results():
            yield mock_doc

        mock_results = AsyncMock()
        mock_results.__aiter__ = lambda self: mock_search_results()
        mock_results.get_count = AsyncMock(return_value=1)
        mock_results.get_facets = AsyncMock(return_value=None)

        mock_client = AsyncMock()
        mock_client.search.return_value = mock_results
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch("azure_mcp.tools.search.service.SearchService.get_credential") as mock_cred:
            mock_cred.return_value = MagicMock()
            with patch("azure.search.documents.aio.SearchClient") as MockClient:
                MockClient.return_value = mock_client

                result = await service.search_documents(
                    endpoint="https://mysearch.search.windows.net",
                    index_name="myindex",
                    search_text="test",
                    include_total_count=True,
                )

                assert result["count"] == 1
                assert result["total_count"] == 1
                # Verify score was renamed
                assert result["documents"][0].get("_search_score") == 1.5


# =============================================================================
# Schema Compatibility Tests (AI Foundry)
# =============================================================================


class TestSchemaCompatibility:
    """Tests to ensure schemas are AI Foundry compatible."""

    def test_no_optional_types_in_schemas(self):
        """Verify no str | None or list | None patterns (AI Foundry incompatible)."""
        # Check SearchQueryOptions - the most complex one
        schema = SearchQueryOptions.model_json_schema()

        # Verify no anyOf patterns (generated by Optional types)
        schema_str = str(schema)
        assert "anyOf" not in schema_str, (
            "Found anyOf in schema - use str = '' instead of str | None"
        )

        # All string fields should have default empty string, not None
        for tool_class in [
            SearchServiceListOptions,
            SearchServiceGetOptions,
            SearchIndexListOptions,
            SearchIndexGetOptions,
            SearchQueryOptions,
            SearchSuggestOptions,
            SearchAutocompleteOptions,
        ]:
            schema = tool_class.model_json_schema()
            assert "anyOf" not in str(schema), f"Found anyOf in {tool_class.__name__}"

    def test_list_fields_have_default_factory(self):
        """Verify list fields use default_factory, not None."""
        options = SearchQueryOptions(
            endpoint="https://test.search.windows.net",
            index_name="test",
        )
        # facets should be empty list, not None
        assert options.facets == []
