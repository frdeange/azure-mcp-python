"""Tests for Bing Search tools.

Tests for all 7 Bing tools and the BingService layer, covering:
- Options model validation (required fields, defaults, boundary constraints)
- Tool properties (name, description, metadata flags)
- Schema compatibility with Azure AI Foundry (no anyOf/allOf/oneOf)
- Execute method delegation to BingService
- BingService._get_api_key: ARM key retrieval, caching, error handling
- BingService search methods: correct endpoint and parameter mapping
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from azure_mcp.core.errors import ToolError
from azure_mcp.tools.bing.discovery import (
    BingResourceGetOptions,
    BingResourceGetTool,
    BingResourceListOptions,
    BingResourceListTool,
)
from azure_mcp.tools.bing.entities import BingEntitySearchOptions, BingEntitySearchTool
from azure_mcp.tools.bing.images import BingImageSearchOptions, BingImageSearchTool
from azure_mcp.tools.bing.news import BingNewsSearchOptions, BingNewsSearchTool
from azure_mcp.tools.bing.service import BingService
from azure_mcp.tools.bing.videos import BingVideoSearchOptions, BingVideoSearchTool
from azure_mcp.tools.bing.web import BingWebSearchOptions, BingWebSearchTool


# =============================================================================
# BingResourceListOptions / BingResourceListTool
# =============================================================================


class TestBingResourceListOptions:
    """Tests for BingResourceListOptions model."""

    def test_minimal_options(self):
        """Test creation with required fields only."""
        options = BingResourceListOptions(subscription="my-sub")
        assert options.subscription == "my-sub"
        assert options.resource_group == ""
        assert options.limit == 50

    def test_full_options(self):
        """Test creation with all optional fields."""
        options = BingResourceListOptions(
            subscription="my-sub",
            resource_group="my-rg",
            limit=25,
        )
        assert options.subscription == "my-sub"
        assert options.resource_group == "my-rg"
        assert options.limit == 25

    def test_limit_validation_lower(self):
        """Limit must be at least 1."""
        with pytest.raises(ValueError):
            BingResourceListOptions(subscription="sub", limit=0)

    def test_limit_validation_upper(self):
        """Limit must not exceed 200."""
        with pytest.raises(ValueError):
            BingResourceListOptions(subscription="sub", limit=201)

    def test_no_optional_none_types(self):
        """Verify schema has no anyOf (AI Foundry compatibility)."""
        schema = BingResourceListOptions.model_json_schema()
        schema_str = str(schema)
        assert "anyOf" not in schema_str
        assert "allOf" not in schema_str
        assert "oneOf" not in schema_str


class TestBingResourceListTool:
    """Tests for BingResourceListTool."""

    def test_tool_name(self):
        assert BingResourceListTool().name == "bing_resource_list"

    def test_tool_description_contains_key_context(self):
        desc = BingResourceListTool().description
        assert "Microsoft.Bing/accounts" in desc
        assert "bing_resource_list" in desc or "bing_web_search" in desc

    def test_tool_metadata_read_only(self):
        meta = BingResourceListTool().metadata
        assert meta.read_only is True
        assert meta.destructive is False
        assert meta.idempotent is True

    def test_options_schema_has_subscription(self):
        schema = BingResourceListTool().get_options_schema()
        assert "properties" in schema
        assert "subscription" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_delegates_to_service(self, patch_credential):
        """Execute should call BingService.list_bing_resources."""
        tool = BingResourceListTool()
        options = BingResourceListOptions(subscription="my-sub", resource_group="my-rg")

        with patch.object(BingService, "list_bing_resources", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [{"name": "my-bing", "resourceGroup": "my-rg"}]
            result = await tool.execute(options)

        mock_list.assert_called_once_with(
            subscription="my-sub",
            resource_group="my-rg",
            limit=50,
        )
        assert len(result) == 1
        assert result[0]["name"] == "my-bing"

    @pytest.mark.asyncio
    async def test_execute_propagates_errors(self, patch_credential):
        """Errors from service should be wrapped by handle_azure_error."""
        tool = BingResourceListTool()
        options = BingResourceListOptions(subscription="bad-sub")

        with patch.object(BingService, "list_bing_resources", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = ValueError("Subscription not found")
            with pytest.raises(ToolError):
                await tool.execute(options)


# =============================================================================
# BingResourceGetOptions / BingResourceGetTool
# =============================================================================


class TestBingResourceGetOptions:
    """Tests for BingResourceGetOptions model."""

    def test_required_fields(self):
        options = BingResourceGetOptions(subscription="sub", resource_name="bing1")
        assert options.subscription == "sub"
        assert options.resource_name == "bing1"
        assert options.resource_group == ""

    def test_with_resource_group(self):
        options = BingResourceGetOptions(
            subscription="sub", resource_name="bing1", resource_group="rg1"
        )
        assert options.resource_group == "rg1"

    def test_missing_resource_name_raises(self):
        with pytest.raises(ValueError):
            BingResourceGetOptions(subscription="sub")

    def test_schema_no_any_of(self):
        schema = BingResourceGetOptions.model_json_schema()
        assert "anyOf" not in str(schema)


class TestBingResourceGetTool:
    """Tests for BingResourceGetTool."""

    def test_tool_name(self):
        assert BingResourceGetTool().name == "bing_resource_get"

    def test_tool_metadata_read_only(self):
        assert BingResourceGetTool().metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_found(self, patch_credential):
        """Returns resource dict when found."""
        tool = BingResourceGetTool()
        options = BingResourceGetOptions(
            subscription="sub", resource_name="bing1", resource_group="rg1"
        )
        resource = {"name": "bing1", "resourceGroup": "rg1"}

        with patch.object(BingService, "get_bing_resource", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = resource
            result = await tool.execute(options)

        assert result["name"] == "bing1"
        mock_get.assert_called_once_with(subscription="sub", name="bing1", resource_group="rg1")

    @pytest.mark.asyncio
    async def test_execute_not_found_returns_error_dict(self, patch_credential):
        """Returns error dict when resource is not found."""
        tool = BingResourceGetTool()
        options = BingResourceGetOptions(subscription="sub", resource_name="missing")

        with patch.object(BingService, "get_bing_resource", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            result = await tool.execute(options)

        assert "error" in result
        assert "missing" in result["error"]


# =============================================================================
# BingWebSearchOptions / BingWebSearchTool
# =============================================================================


class TestBingWebSearchOptions:
    """Tests for BingWebSearchOptions model."""

    def test_minimal_required_fields(self):
        options = BingWebSearchOptions(
            subscription="sub",
            resource_name="bing1",
            resource_group="rg1",
            query="azure AI",
        )
        assert options.query == "azure AI"
        assert options.market == ""
        assert options.safe_search == ""
        assert options.count == 10
        assert options.offset == 0

    def test_full_options(self):
        options = BingWebSearchOptions(
            subscription="sub",
            resource_name="bing1",
            resource_group="rg1",
            query="azure AI",
            market="en-US",
            safe_search="Moderate",
            count=20,
            offset=10,
        )
        assert options.market == "en-US"
        assert options.safe_search == "Moderate"
        assert options.count == 20
        assert options.offset == 10

    def test_count_lower_bound(self):
        with pytest.raises(ValueError):
            BingWebSearchOptions(
                subscription="sub", resource_name="b", resource_group="rg", query="q", count=0
            )

    def test_count_upper_bound(self):
        with pytest.raises(ValueError):
            BingWebSearchOptions(
                subscription="sub", resource_name="b", resource_group="rg", query="q", count=51
            )

    def test_schema_no_any_of(self):
        assert "anyOf" not in str(BingWebSearchOptions.model_json_schema())


class TestBingWebSearchTool:
    """Tests for BingWebSearchTool."""

    def test_tool_name(self):
        assert BingWebSearchTool().name == "bing_web_search"

    def test_tool_metadata_read_only(self):
        assert BingWebSearchTool().metadata.read_only is True

    def test_description_mentions_managed_identity(self):
        assert "managed identity" in BingWebSearchTool().description.lower()

    @pytest.mark.asyncio
    async def test_execute_delegates_to_service(self, patch_credential):
        tool = BingWebSearchTool()
        options = BingWebSearchOptions(
            subscription="sub",
            resource_name="bing1",
            resource_group="rg1",
            query="azure openai",
            market="en-US",
            count=5,
        )
        expected = {"webPages": {"value": []}}

        with patch.object(BingService, "web_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = expected
            result = await tool.execute(options)

        mock_search.assert_called_once_with(
            subscription="sub",
            resource_name="bing1",
            resource_group="rg1",
            query="azure openai",
            market="en-US",
            safe_search="",
            count=5,
            offset=0,
        )
        assert result == expected


# =============================================================================
# BingNewsSearchOptions / BingNewsSearchTool
# =============================================================================


class TestBingNewsSearchOptions:
    """Tests for BingNewsSearchOptions model."""

    def test_defaults(self):
        options = BingNewsSearchOptions(
            subscription="sub", resource_name="b", resource_group="rg", query="q"
        )
        assert options.count == 10
        assert options.freshness == ""
        assert options.market == ""

    def test_count_bounds(self):
        with pytest.raises(ValueError):
            BingNewsSearchOptions(
                subscription="sub", resource_name="b", resource_group="rg", query="q", count=0
            )
        with pytest.raises(ValueError):
            BingNewsSearchOptions(
                subscription="sub", resource_name="b", resource_group="rg", query="q", count=101
            )

    def test_schema_no_any_of(self):
        assert "anyOf" not in str(BingNewsSearchOptions.model_json_schema())


class TestBingNewsSearchTool:
    """Tests for BingNewsSearchTool."""

    def test_tool_name(self):
        assert BingNewsSearchTool().name == "bing_news_search"

    def test_tool_metadata_read_only(self):
        assert BingNewsSearchTool().metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_delegates_to_service(self, patch_credential):
        tool = BingNewsSearchTool()
        options = BingNewsSearchOptions(
            subscription="sub",
            resource_name="bing1",
            resource_group="rg1",
            query="AI news",
            freshness="Day",
        )

        with patch.object(BingService, "news_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {"value": []}
            await tool.execute(options)

        mock_search.assert_called_once_with(
            subscription="sub",
            resource_name="bing1",
            resource_group="rg1",
            query="AI news",
            market="",
            count=10,
            freshness="Day",
        )


# =============================================================================
# BingImageSearchOptions / BingImageSearchTool
# =============================================================================


class TestBingImageSearchOptions:
    """Tests for BingImageSearchOptions model."""

    def test_defaults(self):
        options = BingImageSearchOptions(
            subscription="sub", resource_name="b", resource_group="rg", query="q"
        )
        assert options.count == 10
        assert options.size == ""
        assert options.color == ""
        assert options.safe_search == ""

    def test_count_bounds(self):
        with pytest.raises(ValueError):
            BingImageSearchOptions(
                subscription="sub", resource_name="b", resource_group="rg", query="q", count=0
            )
        with pytest.raises(ValueError):
            BingImageSearchOptions(
                subscription="sub", resource_name="b", resource_group="rg", query="q", count=151
            )

    def test_schema_no_any_of(self):
        assert "anyOf" not in str(BingImageSearchOptions.model_json_schema())


class TestBingImageSearchTool:
    """Tests for BingImageSearchTool."""

    def test_tool_name(self):
        assert BingImageSearchTool().name == "bing_image_search"

    def test_tool_metadata_read_only(self):
        assert BingImageSearchTool().metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_delegates_to_service(self, patch_credential):
        tool = BingImageSearchTool()
        options = BingImageSearchOptions(
            subscription="sub",
            resource_name="bing1",
            resource_group="rg1",
            query="azure logo",
            size="Large",
        )

        with patch.object(BingService, "image_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {"value": []}
            await tool.execute(options)

        mock_search.assert_called_once_with(
            subscription="sub",
            resource_name="bing1",
            resource_group="rg1",
            query="azure logo",
            market="",
            safe_search="",
            count=10,
            size="Large",
            color="",
        )


# =============================================================================
# BingEntitySearchOptions / BingEntitySearchTool
# =============================================================================


class TestBingEntitySearchOptions:
    """Tests for BingEntitySearchOptions model."""

    def test_required_fields(self):
        options = BingEntitySearchOptions(
            subscription="sub", resource_name="b", resource_group="rg", query="Microsoft"
        )
        assert options.query == "Microsoft"
        assert options.market == ""

    def test_missing_query_raises(self):
        with pytest.raises(ValueError):
            BingEntitySearchOptions(subscription="sub", resource_name="b", resource_group="rg")

    def test_schema_no_any_of(self):
        assert "anyOf" not in str(BingEntitySearchOptions.model_json_schema())


class TestBingEntitySearchTool:
    """Tests for BingEntitySearchTool."""

    def test_tool_name(self):
        assert BingEntitySearchTool().name == "bing_entity_search"

    def test_tool_metadata_read_only(self):
        assert BingEntitySearchTool().metadata.read_only is True

    def test_description_mentions_entities(self):
        desc = BingEntitySearchTool().description.lower()
        assert "entit" in desc

    @pytest.mark.asyncio
    async def test_execute_delegates_to_service(self, patch_credential):
        tool = BingEntitySearchTool()
        options = BingEntitySearchOptions(
            subscription="sub",
            resource_name="bing1",
            resource_group="rg1",
            query="Satya Nadella",
            market="en-US",
        )

        with patch.object(BingService, "entity_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {"entities": {"value": []}}
            await tool.execute(options)

        mock_search.assert_called_once_with(
            subscription="sub",
            resource_name="bing1",
            resource_group="rg1",
            query="Satya Nadella",
            market="en-US",
        )


# =============================================================================
# BingVideoSearchOptions / BingVideoSearchTool
# =============================================================================


class TestBingVideoSearchOptions:
    """Tests for BingVideoSearchOptions model."""

    def test_defaults(self):
        options = BingVideoSearchOptions(
            subscription="sub", resource_name="b", resource_group="rg", query="q"
        )
        assert options.count == 10
        assert options.pricing == ""
        assert options.resolution == ""

    def test_count_bounds(self):
        with pytest.raises(ValueError):
            BingVideoSearchOptions(
                subscription="sub", resource_name="b", resource_group="rg", query="q", count=0
            )
        with pytest.raises(ValueError):
            BingVideoSearchOptions(
                subscription="sub", resource_name="b", resource_group="rg", query="q", count=106
            )

    def test_schema_no_any_of(self):
        assert "anyOf" not in str(BingVideoSearchOptions.model_json_schema())


class TestBingVideoSearchTool:
    """Tests for BingVideoSearchTool."""

    def test_tool_name(self):
        assert BingVideoSearchTool().name == "bing_video_search"

    def test_tool_metadata_read_only(self):
        assert BingVideoSearchTool().metadata.read_only is True

    @pytest.mark.asyncio
    async def test_execute_delegates_to_service(self, patch_credential):
        tool = BingVideoSearchTool()
        options = BingVideoSearchOptions(
            subscription="sub",
            resource_name="bing1",
            resource_group="rg1",
            query="azure tutorial",
            pricing="Free",
            resolution="HD720p",
        )

        with patch.object(BingService, "video_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {"value": []}
            await tool.execute(options)

        mock_search.assert_called_once_with(
            subscription="sub",
            resource_name="bing1",
            resource_group="rg1",
            query="azure tutorial",
            market="",
            count=10,
            pricing="Free",
            resolution="HD720p",
        )


# =============================================================================
# BingService unit tests
# =============================================================================


class TestBingServiceListResources:
    """Tests for BingService.list_bing_resources."""

    @pytest.mark.asyncio
    async def test_delegates_to_list_resources(self, patch_credential):
        """list_bing_resources must call the base class list_resources."""
        service = BingService()

        with patch.object(BingService, "list_resources", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [{"name": "bing1"}]
            result = await service.list_bing_resources("sub", "rg", limit=10)

        mock_list.assert_called_once_with(
            resource_type="Microsoft.Bing/accounts",
            subscription="sub",
            resource_group="rg",
            limit=10,
        )
        assert result[0]["name"] == "bing1"

    @pytest.mark.asyncio
    async def test_empty_resource_group_passes_none(self, patch_credential):
        """Empty string resource_group should translate to None for the base class."""
        service = BingService()

        with patch.object(BingService, "list_resources", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = []
            await service.list_bing_resources("sub", resource_group="", limit=5)

        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs["resource_group"] is None


class TestBingServiceGetApiKey:
    """Tests for BingService._get_api_key (ARM key retrieval pattern)."""

    @pytest.mark.asyncio
    async def test_returns_cached_key_on_second_call(self, patch_credential):
        """Second call should return cached value without a new HTTP request."""
        service = BingService(credential=patch_credential)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"key1": "test-api-key"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("azure_mcp.tools.bing.service.aiohttp") as mock_aiohttp:
            mock_aiohttp.ClientSession = MagicMock(return_value=mock_session)

            key1 = await service._get_api_key("sub-id", "rg", "bing1")
            key2 = await service._get_api_key("sub-id", "rg", "bing1")

        assert key1 == "test-api-key"
        assert key2 == "test-api-key"
        # Cache hit — POST called only once
        assert mock_session.post.call_count == 1

    @pytest.mark.asyncio
    async def test_404_raises_value_error(self, patch_credential):
        """A 404 from ARM should raise ValueError."""
        service = BingService(credential=patch_credential)

        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("azure_mcp.tools.bing.service.aiohttp") as mock_aiohttp:
            mock_aiohttp.ClientSession = MagicMock(return_value=mock_session)
            with pytest.raises(ValueError, match="not found"):
                await service._get_api_key("sub-id", "rg", "missing-resource")

    @pytest.mark.asyncio
    async def test_403_raises_permission_error(self, patch_credential):
        """A 403 from ARM should raise PermissionError."""
        service = BingService(credential=patch_credential)

        mock_response = MagicMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("azure_mcp.tools.bing.service.aiohttp") as mock_aiohttp:
            mock_aiohttp.ClientSession = MagicMock(return_value=mock_session)
            with pytest.raises(PermissionError):
                await service._get_api_key("sub-id", "rg", "bing1")

    @pytest.mark.asyncio
    async def test_arm_url_contains_correct_path(self, patch_credential):
        """The ARM POST URL must include the correct provider path and API version."""
        service = BingService(credential=patch_credential)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"key1": "k"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("azure_mcp.tools.bing.service.aiohttp") as mock_aiohttp:
            mock_aiohttp.ClientSession = MagicMock(return_value=mock_session)
            await service._get_api_key("my-sub-id", "my-rg", "my-bing")

        call_args = mock_session.post.call_args
        url = call_args[0][0]
        assert "my-sub-id" in url
        assert "my-rg" in url
        assert "my-bing" in url
        assert "Microsoft.Bing/accounts" in url
        assert "listKeys" in url
        assert "2020-06-10" in url


class TestBingServiceSearchMethods:
    """Tests for BingService search method endpoint and parameter routing."""

    @pytest.mark.asyncio
    async def test_web_search_uses_correct_endpoint(self, patch_credential):
        """web_search must call /search endpoint."""
        service = BingService(credential=patch_credential)

        with (
            patch.object(BingService, "resolve_subscription", new_callable=AsyncMock) as mock_sub,
            patch.object(BingService, "_get_api_key", new_callable=AsyncMock) as mock_key,
            patch.object(BingService, "_search", new_callable=AsyncMock) as mock_search,
        ):
            mock_sub.return_value = "sub-id"
            mock_key.return_value = "api-key"
            mock_search.return_value = {"webPages": {"value": []}}

            await service.web_search("sub", "bing1", "rg", "query")

        mock_search.assert_called_once()
        endpoint = mock_search.call_args[0][0]
        assert endpoint == "/search"

    @pytest.mark.asyncio
    async def test_news_search_uses_correct_endpoint(self, patch_credential):
        """news_search must call /news/search endpoint."""
        service = BingService(credential=patch_credential)

        with (
            patch.object(BingService, "resolve_subscription", new_callable=AsyncMock) as mock_sub,
            patch.object(BingService, "_get_api_key", new_callable=AsyncMock) as mock_key,
            patch.object(BingService, "_search", new_callable=AsyncMock) as mock_search,
        ):
            mock_sub.return_value = "sub-id"
            mock_key.return_value = "api-key"
            mock_search.return_value = {}

            await service.news_search("sub", "bing1", "rg", "query")

        endpoint = mock_search.call_args[0][0]
        assert endpoint == "/news/search"

    @pytest.mark.asyncio
    async def test_image_search_uses_correct_endpoint(self, patch_credential):
        """image_search must call /images/search endpoint."""
        service = BingService(credential=patch_credential)

        with (
            patch.object(BingService, "resolve_subscription", new_callable=AsyncMock) as mock_sub,
            patch.object(BingService, "_get_api_key", new_callable=AsyncMock) as mock_key,
            patch.object(BingService, "_search", new_callable=AsyncMock) as mock_search,
        ):
            mock_sub.return_value = "sub-id"
            mock_key.return_value = "api-key"
            mock_search.return_value = {}

            await service.image_search("sub", "bing1", "rg", "query")

        endpoint = mock_search.call_args[0][0]
        assert endpoint == "/images/search"

    @pytest.mark.asyncio
    async def test_entity_search_uses_correct_endpoint(self, patch_credential):
        """entity_search must call /entities endpoint."""
        service = BingService(credential=patch_credential)

        with (
            patch.object(BingService, "resolve_subscription", new_callable=AsyncMock) as mock_sub,
            patch.object(BingService, "_get_api_key", new_callable=AsyncMock) as mock_key,
            patch.object(BingService, "_search", new_callable=AsyncMock) as mock_search,
        ):
            mock_sub.return_value = "sub-id"
            mock_key.return_value = "api-key"
            mock_search.return_value = {}

            await service.entity_search("sub", "bing1", "rg", "Microsoft")

        endpoint = mock_search.call_args[0][0]
        assert endpoint == "/entities"

    @pytest.mark.asyncio
    async def test_video_search_uses_correct_endpoint(self, patch_credential):
        """video_search must call /videos/search endpoint."""
        service = BingService(credential=patch_credential)

        with (
            patch.object(BingService, "resolve_subscription", new_callable=AsyncMock) as mock_sub,
            patch.object(BingService, "_get_api_key", new_callable=AsyncMock) as mock_key,
            patch.object(BingService, "_search", new_callable=AsyncMock) as mock_search,
        ):
            mock_sub.return_value = "sub-id"
            mock_key.return_value = "api-key"
            mock_search.return_value = {}

            await service.video_search("sub", "bing1", "rg", "azure tutorial")

        endpoint = mock_search.call_args[0][0]
        assert endpoint == "/videos/search"

    @pytest.mark.asyncio
    async def test_search_strips_empty_params(self, patch_credential):
        """_search must not send empty string params to the Bing API."""
        service = BingService(credential=patch_credential)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"webPages": {}})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("azure_mcp.tools.bing.service.aiohttp") as mock_aiohttp:
            mock_aiohttp.ClientSession = MagicMock(return_value=mock_session)
            await service._search(
                "/search",
                "my-key",
                {"q": "test", "mkt": "", "safeSearch": ""},
            )

        call_kwargs = mock_session.get.call_args.kwargs
        sent_params = call_kwargs.get("params", {})
        # Empty strings must be stripped
        assert "mkt" not in sent_params
        assert "safeSearch" not in sent_params
        # Non-empty params must remain
        assert sent_params["q"] == "test"

    @pytest.mark.asyncio
    async def test_search_sends_subscription_key_header(self, patch_credential):
        """_search must pass the API key in Ocp-Apim-Subscription-Key header."""
        service = BingService(credential=patch_credential)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("azure_mcp.tools.bing.service.aiohttp") as mock_aiohttp:
            mock_aiohttp.ClientSession = MagicMock(return_value=mock_session)
            await service._search("/search", "secret-key", {"q": "test"})

        call_kwargs = mock_session.get.call_args.kwargs
        headers = call_kwargs.get("headers", {})
        assert headers.get("Ocp-Apim-Subscription-Key") == "secret-key"
