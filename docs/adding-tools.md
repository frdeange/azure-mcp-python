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
    resource_group: str = Field(
        default="",
        description="Resource group to filter by. Leave empty for all."
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
        resource_group: str = "",
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
            raise handle_azure_error(e, resource="Storage Account") from e
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

## File Organization

### When to Group Tools in One File

**Group tools by resource**, not by action. Multiple tools that operate on the same resource should be in the same file:

```
src/azure_mcp/tools/cosmos/
├── __init__.py
├── service.py           # Shared service logic
├── account.py           # cosmos_account_list (single tool for account resource)
├── database.py          # cosmos_database_list (single tool for database resource)
├── container.py         # cosmos_container_list (single tool for container resource)
└── item.py              # cosmos_item_query, cosmos_item_get, cosmos_item_upsert, cosmos_item_delete
                         # ↑ Multiple tools grouped because they all operate on "item" resource
```

### Grouping Rules

| Scenario | Approach | Example |
|----------|----------|---------|
| Multiple actions on same resource | **One file** | `item.py` → query, get, upsert, delete |
| Single action on a resource | **One file** | `account.py` → list only |
| Different resources | **Separate files** | `database.py`, `container.py` |
| Different Azure SDKs | **Separate files** | `query.py` (CostManagement), `budgets.py` (Consumption) |

### Service Class Location

- **One `service.py` per family**: Contains all Azure SDK operations
- Tools import from the shared service
- Keeps Azure SDK logic separate from tool definitions

```python
# src/azure_mcp/tools/{family}/service.py
class FamilyService(AzureService):
    async def list_resources(self, ...): ...
    async def get_resource(self, ...): ...
    async def create_resource(self, ...): ...
```

### File Naming

| File | Contains |
|------|----------|
| `service.py` | `FamilyService` class with Azure SDK operations |
| `{resource}.py` | All tools for that resource (list, get, create, delete, etc.) |
| `__init__.py` | Exports all tool classes |

### Example: Well-Organized Family

```
src/azure_mcp/tools/keyvault/
├── __init__.py              # Exports: SecretListTool, SecretGetTool, KeyListTool...
├── service.py               # KeyVaultService with all SDK operations
├── secret.py                # keyvault_secret_list, keyvault_secret_get, keyvault_secret_set
├── key.py                   # keyvault_key_list, keyvault_key_get
└── certificate.py           # keyvault_certificate_list, keyvault_certificate_get
```

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
    raise handle_azure_error(e, resource="Resource Name") from e
```

**Important**: Use `from e` to preserve the exception chain for debugging.

### Available Error Types

The `azure_mcp.core.errors` module provides these error classes:

| Error Class | Use Case | Key Attributes |
|-------------|----------|----------------|
| `ToolError` | Base class for all errors | `message`, `code`, `details` |
| `ValidationError` | Invalid input parameters | `field` |
| `NotFoundError` | Resource not found (404) | `resource` |
| `AuthenticationError` | Auth failures (401) | - |
| `AuthorizationError` | Permission denied (403) | `permission` |
| `AzureResourceError` | Azure resource operations | `resource_type`, `resource_name` |
| `NetworkError` | Connection issues | `endpoint` |
| `RateLimitError` | Throttling (429) | `retry_after` |
| `ConfigurationError` | Config problems | `setting` |

### Creating Errors Manually

When you need to raise specific errors:

```python
from azure_mcp.core.errors import (
    ValidationError,
    NotFoundError,
    AuthorizationError,
    AzureResourceError,
)

# Validation error with field context
raise ValidationError("Invalid format", field="container_name")

# Resource not found
raise NotFoundError("Database not found", resource="mydb")

# Permission denied with context
raise AuthorizationError("Access denied", permission="read")

# Azure resource operation failed
raise AzureResourceError(
    "Operation failed",
    resource_type="Microsoft.DocumentDB/databaseAccounts",
    resource_name="myaccount",
)
```

### Automatic Azure SDK Error Mapping

`handle_azure_error()` automatically converts Azure SDK exceptions:

| Azure SDK Exception | Mapped To |
|---------------------|-----------|
| `ResourceNotFoundError` | `NotFoundError` |
| `ClientAuthenticationError` | `AuthenticationError` |
| `HttpResponseError` (403) | `AuthorizationError` |
| `HttpResponseError` (429) | `RateLimitError` |
| `ServiceRequestError` | `NetworkError` |
| Other exceptions | `ToolError` |

### Error Serialization

All errors support `to_dict()` for JSON serialization:

```python
error = ValidationError("Invalid input", field="query")
print(error.to_dict())
# {
#     "error": "ValidationError",
#     "message": "Invalid input",
#     "field": "query"
# }
```

## AI Foundry Schema Compatibility

**⚠️ CRITICAL**: Azure AI Foundry does NOT support `anyOf`, `allOf`, or `oneOf` in JSON schemas.

Pydantic 2 generates `anyOf` for optional types (`str | None`). This causes `"Invalid tool schema"` errors.

### ❌ WRONG - Generates incompatible schema

```python
class MyOptions(BaseModel):
    resource_group: str | None = Field(default=None, description="...")
    parameters: list[dict] | None = Field(default=None, description="...")
```

### ✅ CORRECT - AI Foundry compatible

```python
class MyOptions(BaseModel):
    resource_group: str = Field(
        default="",
        description="Resource group to filter. Leave empty for all."
    )
    parameters: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Query parameters. Pass empty list if none needed."
    )
```

Empty values (`""` and `[]`) are falsy in Python, so existing `if value:` checks work unchanged.

**See [AI Foundry Deployment Guide](ai-foundry-deployment.md) for full details.**

## How Tools Are Registered (Behind the Scenes)

When you create a tool following the patterns above, the server automatically:

1. **Imports your tool** via `tools/__init__.py`
2. **Registers it** using the `@register_tool` decorator
3. **Generates a flat JSON schema** for AI Foundry compatibility

### Schema Flattening

The server uses `fastmcp` with dynamic handler generation to produce flat schemas without `$ref` or `$defs`. This is handled automatically in `server.py`:

```python
# Your Pydantic model (with proper patterns)
class MyOptions(BaseModel):
    subscription: str = Field(..., description="Subscription ID")
    resource_group: str = Field(default="", description="RG filter")

# Server automatically generates a flat handler like:
async def handler(
    subscription: Annotated[str, "Subscription ID"],
    resource_group: Annotated[str, "RG filter"] = ""
) -> Any:
    ...
```

**You don't need to understand this** - just follow the patterns in this guide and the server handles the rest.

## AzureService Base Class Methods

**⚠️ CRITICAL**: Always check what methods `AzureService` provides before implementing Azure SDK calls directly. Using base class methods ensures consistency, caching, testability, and prevents architectural violations.

### Available Methods

| Method | Purpose | When to Use |
|--------|---------|-------------|
| `get_credential()` | Get Azure credential | Any Azure SDK client initialization |
| `resolve_subscription()` | Name/GUID → subscription ID | Before any subscription-scoped query |
| `list_subscriptions()` | Get all accessible subscriptions | Discovery, multi-subscription queries |
| `execute_resource_graph_query()` | Run custom KQL queries | Complex queries, projections, aggregations |
| `list_resources()` | List resources by type | Simple resource listings |
| `get_resource()` | Get single resource | Fetch one resource by name |

### Simple vs. Custom Resource Graph Queries

For **simple listings** by resource type, use `list_resources()`:

```python
# Simple: List all storage accounts
results = await self.list_resources(
    resource_type="Microsoft.Storage/storageAccounts",
    subscription=subscription,
)
```

For **custom KQL queries** with projections, joins, or aggregations, use `execute_resource_graph_query()`:

```python
# Custom: Complex query with projections
query = """
resources
| where type =~ 'microsoft.compute/virtualmachines'
| project name, location, vmSize = properties.hardwareProfile.vmSize
| order by name
"""
result = await self.execute_resource_graph_query(
    query=query,
    subscriptions=[sub_id],
)
return result.get("data", [])
```

## Async-First SDK Usage

**ARCHITECTURE DECISION**: All Azure SDK clients MUST be used in async mode to prevent blocking the MCP server's event loop. See [Issue #78](https://github.com/frdeange/azure-mcp-python/issues/78) for the full analysis.

### Why Async?

| Factor | Sync Pattern | Async Pattern |
|--------|--------------|---------------|
| **Event Loop Blocking** | ❌ Blocks entire server | ✅ Non-blocking |
| **Concurrent Requests** | ❌ Sequential processing | ✅ Parallel processing |
| **Scalability** | ❌ Limited by blocking I/O | ✅ Handles many concurrent requests |
| **MCP Server Fit** | ❌ Poor for multi-tool calls | ✅ Ideal for tool orchestration |

**Real-world example**: Email sending takes 2-5 seconds. With sync, the MCP server cannot handle ANY other requests during that time. With async, it continues serving other tools.

### Priority Order

1. **Priority 1**: Use native async SDK (`.aio` module) when available
2. **Priority 2**: Wrap sync SDK with `asyncio.to_thread()` when no async version exists

### SDK Async Availability

| SDK Package | Async Module | Use Pattern |
|-------------|--------------|-------------|
| `azure-storage-blob` | ✅ `azure.storage.blob.aio` | Native async |
| `azure-monitor-query` | ✅ `azure.monitor.query.aio` | Native async |
| `azure-communication-email` | ✅ `azure.communication.email.aio` | Native async |
| `azure-communication-sms` | ✅ `azure.communication.sms.aio` | Native async |
| `azure-cosmos` | ✅ `azure.cosmos.aio` | Native async |
| `msgraph-sdk` | ✅ Default async | Native async |
| `azure-mgmt-costmanagement` | ❌ None | Use `asyncio.to_thread()` |
| `azure-mgmt-authorization` | ❌ None | Use `asyncio.to_thread()` |
| `azure-mgmt-resourcegraph` | ❌ None | Use `asyncio.to_thread()` |

### Pattern 1: Native Async SDK (Preferred)

When an `.aio` module exists, use it with `async with` context manager:

```python
# ✅ CORRECT - Use .aio module with async context manager
from azure.communication.email.aio import EmailClient

async def send_email(self, endpoint: str, ...) -> dict:
    credential = self.get_credential()
    
    async with EmailClient(endpoint, credential) as client:
        poller = await client.begin_send(message)
        result = await poller.result()
        return {"status": result.get("status")}
```

### Pattern 2: Async Iteration

For list operations that return iterators, use `async for`:

```python
# ✅ CORRECT - Async iteration for list operations
from azure.communication.phonenumbers.aio import PhoneNumbersClient

async def list_phone_numbers(self, endpoint: str) -> list[dict]:
    credential = self.get_credential()
    phone_numbers = []
    
    async with PhoneNumbersClient(endpoint, credential) as client:
        async for phone in client.list_purchased_phone_numbers():
            phone_numbers.append({"number": phone.phone_number})
    
    return phone_numbers
```

### Pattern 3: Wrapped Sync SDK (Fallback)

When no async SDK exists, wrap sync calls with `asyncio.to_thread()`:

```python
# ⚠️ ACCEPTABLE - When no async SDK exists
import asyncio
from azure.mgmt.costmanagement import CostManagementClient

async def query_costs(self, subscription: str, ...) -> dict:
    credential = self.get_credential()
    client = CostManagementClient(credential, subscription)
    
    # Wrap sync call to prevent blocking the event loop
    result = await asyncio.to_thread(
        client.query.usage,
        scope=f"/subscriptions/{subscription}",
        parameters=query_definition,
    )
    return result.as_dict()
```

### ❌ Anti-Pattern: Sync SDK in Async Method

```python
# ❌ WRONG - Sync SDK blocks the event loop
from azure.communication.email import EmailClient  # No .aio!

async def send_email(self, endpoint: str, ...) -> dict:
    client = EmailClient(endpoint, credential)
    poller = client.begin_send(message)  # BLOCKS!
    result = poller.result()  # BLOCKS!
    return {"status": result.get("status")}
```

## ❌ Anti-Patterns (Don't Do This)

These patterns cause architectural violations and will fail the `test_architecture_patterns.py` tests.

### Direct ResourceGraphClient Instantiation

```python
# ❌ WRONG - Don't create ResourceGraphClient directly
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest

credential = self.get_credential()
client = ResourceGraphClient(credential)
request = QueryRequest(subscriptions=[sub_id], query=query)
result = client.resources(request)

# ✅ CORRECT - Use base class method
result = await self.execute_resource_graph_query(
    query=query,
    subscriptions=[sub_id],
)
```

### Direct SubscriptionClient Usage

```python
# ❌ WRONG - Don't create SubscriptionClient directly
from azure.mgmt.resource import SubscriptionClient

client = SubscriptionClient(credential)
for sub in client.subscriptions.list():
    ...

# ✅ CORRECT - Use base class methods
sub_id = await self.resolve_subscription(subscription_name_or_id)
all_subs = await self.list_subscriptions()
```

### Direct Credential Creation

```python
# ❌ WRONG - Don't instantiate DefaultAzureCredential in services
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()

# ✅ CORRECT - Use base class method
credential = self.get_credential()
```

## Best Practices

1. **Check base class first** - Always use `AzureService` methods before implementing SDK calls directly
2. **Use async SDKs** - Prefer `.aio` modules when available; wrap sync with `asyncio.to_thread()` otherwise
3. **Keep tools focused** - One tool = one action
4. **Use Resource Graph** - For listing/querying, prefer ARG over individual API calls
5. **Document thoroughly** - Descriptions help the LLM understand when to use each tool
6. **Validate inputs** - Use Pydantic constraints (`ge`, `le`, `min_length`, etc.)
7. **Add tests** - Every tool needs unit tests
8. **Avoid Optional types** - Use empty defaults for AI Foundry compatibility
9. **Use specific types** - Use `str` instead of `Any` where possible
10. **Run architecture tests** - `pytest tests/unit/test_architecture_patterns.py` catches pattern violations

## ⚠️ Deployment Checklist

**CRITICAL**: When adding a new tool family, complete ALL these steps before considering the work done:

### Step 1: Update Dockerfile ⚡ FREQUENTLY FORGOTTEN!

The `Dockerfile` contains a hardcoded list of extras to install. **You MUST add your new extra**:

```dockerfile
# Line ~18 in Dockerfile - ADD YOUR EXTRA HERE!
RUN pip install --no-cache-dir ".[cosmos,cost,storage,entra,monitor,rbac,communication,search,YOUR_NEW_EXTRA]" uvicorn starlette
```

**Without this, the deployed MCP will fail with `ModuleNotFoundError: No module named 'azure.your_sdk'`**

### Step 2: Update pyproject.toml

Add your dependencies as an optional extra AND include it in `all`:

```toml
[project.optional-dependencies]
your_family = ["azure-your-sdk>=1.0.0"]
all = [
    # ... existing ...
    "azure-your-sdk>=1.0.0",  # ADD HERE TOO
]
```

### Step 3: Update RBAC Allowed Roles (if needed)

If your tools need data plane access, add the required roles to `src/azure_mcp/tools/rbac/service.py`:

```python
ALLOWED_RBAC_ROLES: set[str] = {
    # ... existing roles ...
    # Your Service - Data Plane
    "Your Service Data Reader",
    "Your Service Data Contributor",
}
```

### Step 4: Document Required Permissions

Update the README or create a doc noting what Azure RBAC roles the MCP's Managed Identity needs:

| Service | Required Role | Scope |
|---------|---------------|-------|
| Your Service | Data Reader | Resource level |

### Step 5: Verification Checklist

Before pushing:

- [ ] Tool files created in `src/azure_mcp/tools/{family}/`
- [ ] Tools exported in `src/azure_mcp/tools/{family}/__init__.py`
- [ ] Family imported in `src/azure_mcp/tools/__init__.py`
- [ ] Dependencies added to `pyproject.toml` (both extra AND `all`)
- [ ] **Dockerfile updated with new extra** ⚠️
- [ ] RBAC roles added if needed
- [ ] Unit tests created and passing
- [ ] Architecture tests passing: `pytest tests/unit/test_architecture_patterns.py`
- [ ] Schema tests passing: `pytest tests/unit/test_schema_compatibility.py`

