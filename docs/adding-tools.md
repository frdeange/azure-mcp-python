# Adding New Tools

This guide explains how to add new Azure tools to the MCP server.

## Quick Start

1. Create a new folder under `src/azure_mcp/tools/{family}/`
2. Create your tool file (e.g., `query.py`, `get.py`, `list.py`)
3. Define your options model using Pydantic
4. Implement your tool class extending `AzureTool`
5. Register it with `@register_tool`
6. Add tests

## Step-by-Step Example

Let's add a new tool for listing Storage Accounts.

### 1. Create the Tool File

```python
# src/azure_mcp/tools/storage/account_list.py

from __future__ import annotations
from typing import Any

from pydantic import BaseModel, Field

from azure_mcp.core.base import AzureService, AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool


class StorageAccountListOptions(BaseModel):
    """Options for listing storage accounts."""
    
    subscription: str = Field(
        ...,
        description="Azure subscription ID or name"
    )
    resource_group: str | None = Field(
        default=None,
        description="Optional resource group to filter by"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of accounts to return"
    )


class StorageAccountService(AzureService):
    """Service for Storage Account operations."""
    
    async def list_accounts(
        self,
        subscription: str,
        resource_group: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List storage accounts using Resource Graph."""
        return await self.list_resources(
            resource_type="Microsoft.Storage/storageAccounts",
            subscription=subscription,
            resource_group=resource_group,
            limit=limit,
        )


@register_tool("storage", "account")
class StorageAccountListTool(AzureTool):
    """Tool for listing Azure Storage Accounts."""
    
    @property
    def name(self) -> str:
        return "storage_account_list"
    
    @property
    def description(self) -> str:
        return (
            "List Azure Storage Accounts in a subscription. "
            "Returns account names, locations, SKUs, and other properties."
        )
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,
            requires_confirmation=False,
            idempotent=True,
        )
    
    @property
    def options_model(self) -> type[BaseModel]:
        return StorageAccountListOptions
    
    async def execute(self, options: StorageAccountListOptions) -> Any:
        """Execute the list operation."""
        service = StorageAccountService()
        
        try:
            return await service.list_accounts(
                subscription=options.subscription,
                resource_group=options.resource_group,
                limit=options.limit,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="Storage Account")
```

### 2. Register in Package Init

```python
# src/azure_mcp/tools/storage/__init__.py

from azure_mcp.tools.storage.account_list import StorageAccountListTool

__all__ = ["StorageAccountListTool"]
```

### 3. Import in Tools Init

```python
# src/azure_mcp/tools/__init__.py

from azure_mcp.tools import resourcegraph, storage  # Add storage

__all__ = ["resourcegraph", "storage"]
```

### 4. Add Tests

```python
# tests/unit/tools/test_storage.py

import pytest
from azure_mcp.tools.storage.account_list import (
    StorageAccountListOptions,
    StorageAccountListTool,
)


class TestStorageAccountListTool:
    
    def test_tool_properties(self):
        tool = StorageAccountListTool()
        assert tool.name == "storage_account_list"
        assert tool.metadata.read_only is True
    
    def test_options_validation(self):
        # Valid options
        opts = StorageAccountListOptions(subscription="my-sub")
        assert opts.subscription == "my-sub"
        
        # Missing required field
        with pytest.raises(ValueError):
            StorageAccountListOptions()
```

## Naming Conventions

| Pattern | Example | Use Case |
|---------|---------|----------|
| `{family}_{resource}_list` | `storage_account_list` | List multiple resources |
| `{family}_{resource}_get` | `storage_account_get` | Get single resource |
| `{family}_{resource}_create` | `storage_account_create` | Create resource |
| `{family}_{resource}_delete` | `storage_account_delete` | Delete resource |
| `{family}_{resource}_query` | `cosmos_item_query` | Query/search |
| `{family}_{resource}_{action}` | `keyvault_secret_rotate` | Custom action |

## Metadata Guidelines

Set `ToolMetadata` appropriately:

```python
# Read-only operations
ToolMetadata(read_only=True, requires_confirmation=False, idempotent=True)

# Create/modify operations
ToolMetadata(read_only=False, requires_confirmation=True, idempotent=False)

# Delete operations
ToolMetadata(read_only=False, requires_confirmation=True, idempotent=True)
```

## Error Handling

Always wrap service calls with `handle_azure_error`:

```python
try:
    result = await service.do_operation()
except Exception as e:
    raise handle_azure_error(e, resource="Resource Name")
```

This ensures consistent error formatting and proper error type detection.

## Best Practices

1. **Keep tools focused** - One tool = one action
2. **Use Resource Graph** - For listing/querying, prefer ARG over individual API calls
3. **Document thoroughly** - Descriptions help the LLM understand when to use each tool
4. **Validate inputs** - Use Pydantic constraints (`ge`, `le`, `min_length`, etc.)
5. **Add tests** - Every tool needs unit tests
