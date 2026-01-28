# Testing Guide

This document covers testing practices for Azure MCP Server.

## Running Tests

```bash
# Run all unit tests
pytest tests/unit

# Run with coverage
pytest tests/unit --cov=azure_mcp --cov-report=html

# Run specific test file
pytest tests/unit/core/test_auth.py

# Run specific test
pytest tests/unit/core/test_auth.py::TestCredentialProvider::test_get_credential_returns_credential

# Run with verbose output
pytest tests/unit -v
```

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests (fast, isolated)
│   ├── core/            # Core module tests
│   └── tools/           # Tool-specific tests
└── integration/         # Integration tests (require Azure)
```

## Writing Unit Tests

### Testing Tools

```python
import pytest
from azure_mcp.tools.storage.account_list import (
    StorageAccountListOptions,
    StorageAccountListTool,
)


class TestStorageAccountListTool:
    """Tests for StorageAccountListTool."""
    
    def test_tool_properties(self):
        """Test tool metadata."""
        tool = StorageAccountListTool()
        assert tool.name == "storage_account_list"
        assert "Storage" in tool.description
        assert tool.metadata.read_only is True
    
    def test_options_schema(self):
        """Test that schema is valid."""
        tool = StorageAccountListTool()
        schema = tool.get_options_schema()
        assert "subscription" in schema["properties"]
    
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_azure_service):
        """Test successful execution."""
        tool = StorageAccountListTool()
        options = StorageAccountListOptions(subscription="test-sub")
        
        result = await tool.execute(options)
        
        assert isinstance(result, list)
```

### Testing Services

```python
import pytest
from unittest.mock import patch, MagicMock

from azure_mcp.core.base import AzureService


class TestAzureService:
    
    @pytest.mark.asyncio
    async def test_list_resources(self, mock_resourcegraph_client, patch_credential):
        """Test list_resources uses Resource Graph."""
        with patch("azure_mcp.core.base.ResourceGraphClient") as mock_cls:
            mock_cls.return_value = mock_resourcegraph_client
            mock_resourcegraph_client.resources.return_value.data = [
                {"id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/acc"}
            ]
            
            service = AzureService()
            result = await service.list_resources(
                resource_type="Microsoft.Storage/storageAccounts",
                subscription="test-sub",
            )
            
            assert len(result) == 1
```

### Using Fixtures

The `conftest.py` provides common fixtures:

```python
@pytest.fixture
def mock_credential():
    """Mock Azure credential."""
    ...

@pytest.fixture
def mock_subscription_client(mock_credential):
    """Mock subscription client."""
    ...

@pytest.fixture
def mock_resourcegraph_client(mock_credential):
    """Mock Resource Graph client."""
    ...

@pytest.fixture
def patch_credential(mock_credential):
    """Patch CredentialProvider."""
    ...
```

## Integration Tests

Integration tests require actual Azure credentials and resources.

```python
# tests/integration/test_resourcegraph_live.py

import pytest
from azure_mcp.tools.resourcegraph.query import ResourceGraphQueryTool


@pytest.mark.integration
class TestResourceGraphIntegration:
    
    @pytest.mark.asyncio
    async def test_query_resources(self):
        """Test real Resource Graph query."""
        tool = ResourceGraphQueryTool()
        result = await tool.run({
            "query": "resources | limit 5"
        })
        assert "data" in result
```

Run integration tests:

```bash
# Set credentials first
az login

# Run integration tests
pytest tests/integration -v --run-integration
```

## Mocking Best Practices

### Mock at the SDK Boundary

```python
# Good: Mock the Azure SDK client
with patch("azure_mcp.tools.storage.StorageManagementClient") as mock:
    mock.return_value.storage_accounts.list.return_value = [...]

# Avoid: Mocking internal functions
```

### Use Realistic Data

```python
# Good: Use realistic Azure resource structure
mock_resource = {
    "id": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/acc",
    "name": "mystorageaccount",
    "type": "Microsoft.Storage/storageAccounts",
    "location": "eastus",
    "properties": {
        "provisioningState": "Succeeded"
    }
}

# Avoid: Overly simplified mocks
mock_resource = {"name": "acc"}
```

## AI Foundry Schema Compatibility Testing

The project includes automated tests to ensure tool schemas are compatible with Azure AI Foundry.

### Schema Validation Test

The `tests/unit/test_schema_compatibility.py` file validates that all tool schemas:

- Do NOT contain `anyOf` patterns (breaks AI Foundry)
- Do NOT contain `allOf` patterns (breaks AI Foundry)
- Do NOT contain `oneOf` patterns (breaks AI Foundry)

This test runs automatically in CI and will fail if any tool uses incompatible patterns.

### Testing Tools with Optional Fields

When testing tools that have optional fields, remember they use empty values instead of `None`:

```python
# For optional string fields (default="")
options = MyToolOptions(
    subscription="test-sub",
    resource_group="",  # Empty string, NOT None
)

# For optional list fields (default_factory=list)
options = QueryOptions(
    query="SELECT * FROM c",
    parameters=[],  # Empty list, NOT None
)
```

### Verifying Schema Compatibility

To check if a tool's schema is AI Foundry compatible:

```python
def test_my_tool_schema_compatible():
    tool = MyTool()
    schema = tool.options_model.model_json_schema()
    
    # Recursively check for forbidden patterns
    def check_no_anyof(obj: dict) -> bool:
        if "anyOf" in obj or "allOf" in obj or "oneOf" in obj:
            return False
        for value in obj.values():
            if isinstance(value, dict) and not check_no_anyof(value):
                return False
        return True
    
    assert check_no_anyof(schema), "Schema contains anyOf/allOf/oneOf"
```

See [AI Foundry Deployment Guide](ai-foundry-deployment.md) for more details on schema requirements.

## Coverage Goals

- **Core modules**: 90%+ coverage
- **Tools**: 80%+ coverage
- **Overall**: 85%+ coverage

Check coverage:

```bash
pytest tests/unit --cov=azure_mcp --cov-report=term-missing
```

## Test Markers

Available pytest markers:

| Marker | Description |
|--------|-------------|
| `@pytest.mark.asyncio` | Async test |
| `@pytest.mark.integration` | Integration test |
| `@pytest.mark.slow` | Slow test |

Configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests",
    "slow: marks tests as slow",
]
```
