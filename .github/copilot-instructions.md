# Agent Instructions for Azure MCP Server (Python)

You are an AI coding assistant working on the **Azure MCP Server** project - a Python implementation of Model Context Protocol (MCP) tools for Azure services.

## Project Overview

This project provides MCP tools that allow AI assistants (like Claude, GPT-4) to interact with Azure resources. It's a Python port/reimplementation inspired by Microsoft's .NET Azure MCP Server, with additional features not available in the original.

### Key Differentiators

- **Cost Management tools** - Query costs, forecasts, budgets (NOT in .NET version)
- **Entra ID tools** - Users, groups, apps via Microsoft Graph (NOT in .NET version)
- **Simplified architecture** - Easier to extend and maintain
- **Python ecosystem** - Better for teams familiar with Python

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| MCP SDK | `fastmcp` | >=2.14.0 |
| Validation | Pydantic | >=2.5.0 |
| Azure Auth | azure-identity | latest |
| Azure Resource Graph | azure-mgmt-resourcegraph | latest |
| Logging | structlog | latest |
| Caching | cachetools | latest |
| Testing | pytest, pytest-asyncio | latest |
| Linting | ruff | latest |
| Type Checking | mypy | latest |

## Project Structure

```
azure-mcp-python/
├── src/azure_mcp/
│   ├── __init__.py              # Package exports
│   ├── server.py                # MCP server entry point (FastMCP)
│   ├── core/                    # Core framework
│   │   ├── __init__.py
│   │   ├── auth.py              # CredentialProvider
│   │   ├── base.py              # AzureService, AzureTool base classes
│   │   ├── cache.py             # CacheService
│   │   ├── errors.py            # Error types + handle_azure_error()
│   │   ├── models.py            # ToolMetadata, ToolResponse
│   │   └── registry.py          # @register_tool decorator, ToolRegistry
│   └── tools/                   # Tool implementations
│       ├── __init__.py          # Import all tool modules
│       ├── resourcegraph/       # Resource Graph tools
│       │   ├── __init__.py
│       │   └── query.py         # resourcegraph_query tool
│       ├── storage/             # Storage tools (to implement)
│       ├── cosmos/              # Cosmos DB tools (to implement)
│       ├── cost/                # Cost Management tools (PRIORITY)
│       ├── entraid/             # Entra ID tools (PRIORITY)
│       ├── keyvault/            # Key Vault tools
│       └── monitor/             # Azure Monitor tools
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── unit/
│   │   ├── core/                # Core module tests
│   │   └── tools/               # Tool tests
│   └── integration/             # Integration tests (require Azure)
├── docs/
│   ├── adding-tools.md          # How to add new tools
│   ├── authentication.md        # Auth guide
│   └── testing.md               # Testing guide
└── .github/
    ├── PROJECT_PLAN.md          # Project plan and decisions
    ├── ISSUES.md                # All planned issues
    └── RESEARCH_NOTES.md        # .NET analysis, SDK research
```

## Architecture Patterns

### 1. Tool Structure

Every tool follows this pattern:

```python
from pydantic import BaseModel, Field
from azure_mcp.core.base import AzureService, AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool


class MyToolOptions(BaseModel):
    """Pydantic model for tool parameters."""
    param1: str = Field(..., description="Required parameter")
    param2: int = Field(default=50, ge=1, le=100, description="Optional with constraints")
    # For optional strings, use empty default (NOT str | None) for AI Foundry compatibility
    optional_filter: str = Field(default="", description="Filter value. Leave empty for all.")


class MyService(AzureService):
    """Service class for Azure operations."""
    
    async def do_operation(self, param1: str, param2: int, optional_filter: str = "") -> dict:
        # Use self.get_credential() for auth
        # Use self.resolve_subscription() for sub name→ID
        # Use self.list_resources() for simple Resource Graph queries
        # Use self.execute_resource_graph_query() for custom KQL queries
        pass


@register_tool("family", "subgroup")  # e.g., ("cost", "query")
class MyTool(AzureTool):
    """Tool exposed to MCP."""
    
    @property
    def name(self) -> str:
        return "family_resource_action"  # e.g., "cost_query"
    
    @property
    def description(self) -> str:
        return "Description for LLM to understand when to use this tool."
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            read_only=True,           # False for write operations
            requires_confirmation=False,  # True for destructive ops
            idempotent=True,          # True if safe to retry
        )
    
    @property
    def options_model(self) -> type[BaseModel]:
        return MyToolOptions
    
    async def execute(self, options: MyToolOptions) -> Any:
        service = MyService()
        try:
            return await service.do_operation(
                param1=options.param1,
                param2=options.param2,
                optional_filter=options.optional_filter,
            )
        except Exception as e:
            raise handle_azure_error(e, resource="MyResource")
```

**⚠️ AI Foundry Schema Compatibility**: Never use `str | None` or `list | None` - these generate `anyOf` schemas that AI Foundry rejects. Use `str = ""` and `list = Field(default_factory=list)` instead. See `docs/ai-foundry-deployment.md`.

### 2. Naming Conventions

| Pattern | Example | Use Case |
|---------|---------|----------|
| `{family}_{resource}_list` | `storage_account_list` | List multiple resources |
| `{family}_{resource}_get` | `cosmos_item_get` | Get single resource |
| `{family}_{resource}_create` | `keyvault_secret_set` | Create resource |
| `{family}_{resource}_delete` | `storage_blob_delete` | Delete resource |
| `{family}_{resource}_query` | `cost_query` | Query/search |
| `{family}_{action}` | `resourcegraph_query` | Service-level action |

### 3. Resource Graph First

**IMPORTANT**: For listing Azure resources, ALWAYS use Azure Resource Graph instead of individual management API calls.

#### Simple Listings - Use `list_resources()`

```python
# ✅ CORRECT - Use list_resources() for simple queries
async def list_storage_accounts(self, subscription: str) -> list[dict]:
    return await self.list_resources(
        resource_type="Microsoft.Storage/storageAccounts",
        subscription=subscription,
    )

# ❌ WRONG - Don't use management client for listing
async def list_storage_accounts_slow(self, subscription: str):
    client = StorageManagementClient(...)
    return list(client.storage_accounts.list())  # Slow, limited
```

#### Custom Queries - Use `execute_resource_graph_query()`

For complex KQL queries with projections, joins, or aggregations:

```python
# ✅ CORRECT - Use execute_resource_graph_query() for custom KQL
async def list_vms_with_details(self, subscription: str) -> list[dict]:
    sub_id = await self.resolve_subscription(subscription)
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

# ❌ WRONG - Don't create ResourceGraphClient directly
from azure.mgmt.resourcegraph import ResourceGraphClient
client = ResourceGraphClient(credential)  # NEVER do this in services
```

The `AzureService` base class provides:
- `execute_resource_graph_query(query, subscriptions, ...)` - Custom KQL queries
- `list_resources(resource_type, subscription, ...)` - Simple resource listings
- `get_resource(resource_type, subscription, name, ...)` - Get single resource
- `resolve_subscription(name_or_id)` - Convert subscription name to ID
- `list_subscriptions()` - Get all accessible subscriptions
- `get_credential()` - Get Azure credential

**Run `pytest tests/unit/test_architecture_patterns.py`** to validate pattern compliance.

### 4. Async-First SDK Usage

**ARCHITECTURE DECISION**: All Azure SDK clients MUST be used in async mode. See [Issue #78](https://github.com/frdeange/azure-mcp-python/issues/78).

#### Priority Order

1. **Priority 1**: Use native async SDK (`.aio` module) when available
2. **Priority 2**: Wrap sync SDK with `asyncio.to_thread()` when no async version exists

#### Pattern 1: Native Async SDK (Preferred)

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

#### Pattern 2: Wrapped Sync SDK (Fallback)

```python
# ⚠️ ACCEPTABLE - When no async SDK exists
import asyncio
from azure.mgmt.costmanagement import CostManagementClient

async def query_costs(self, subscription: str, ...) -> dict:
    credential = self.get_credential()
    client = CostManagementClient(credential, subscription)
    
    # Wrap sync call to prevent blocking
    result = await asyncio.to_thread(
        client.query.usage,
        scope=f"/subscriptions/{subscription}",
        parameters=query_definition,
    )
    return result.as_dict()
```

#### SDK Async Availability

| SDK Package | Async Module |
|-------------|--------------|
| `azure-storage-blob` | ✅ `azure.storage.blob.aio` |
| `azure-monitor-query` | ✅ `azure.monitor.query.aio` |
| `azure-communication-*` | ✅ `azure.communication.*.aio` |
| `azure-cosmos` | ✅ `azure.cosmos.aio` |
| `msgraph-sdk` | ✅ Default async |
| `azure-mgmt-*` | ❌ Use `asyncio.to_thread()` |

### 5. Error Handling

Always wrap Azure operations with `handle_azure_error()`:

```python
from azure_mcp.core.errors import handle_azure_error

try:
    result = await service.do_something()
except Exception as e:
    raise handle_azure_error(e, resource="Storage Account")
```

This converts Azure SDK exceptions to appropriate tool errors:
- `AuthenticationError` - Credential issues
- `AuthorizationError` - Permission denied (403)
- `AzureResourceError` - Resource not found (404)
- `RateLimitError` - Throttling (429)
- `NetworkError` - Connection issues

### 6. Caching

Use the cache for expensive operations:

```python
from azure_mcp.core.cache import cache
from datetime import timedelta

# Simple get/set
cache.set("key", value, ttl=timedelta(hours=1))
value = cache.get("key")

# Cache-aside pattern
result = await cache.get_or_set(
    "cache_key",
    fetch_function,  # async callable
    ttl=timedelta(minutes=5),
)
```

Default TTLs:
- Subscription resolution: 12 hours
- Resource listings: 5 minutes
- Metadata: 1 hour

## Development Workflow

### Adding a New Tool

1. **Create folder**: `src/azure_mcp/tools/{family}/`
2. **Create files**:
   - `__init__.py` - Export tool classes
   - `{action}.py` - Tool implementation
3. **Implement**:
   - Options model (Pydantic)
   - Service class (extends `AzureService`)
   - Tool class (extends `AzureTool`, decorated with `@register_tool`)
4. **Register**: Import in `src/azure_mcp/tools/__init__.py`
5. **Test**: Add tests in `tests/unit/tools/test_{family}.py`
6. **Document**: Update relevant docs if needed
7. **⚠️ UPDATE DOCKERFILE**: Add your new extra to the `pip install` line!

### ⚠️ CRITICAL: Dockerfile Update (FREQUENTLY FORGOTTEN!)

When adding a new tool family with new dependencies, you **MUST** update the `Dockerfile`:

```dockerfile
# Line ~18 - ADD YOUR NEW EXTRA HERE!
RUN pip install --no-cache-dir ".[cosmos,cost,storage,entra,monitor,rbac,communication,search,YOUR_NEW_EXTRA]" uvicorn starlette
```

**Without this, deployment will fail with `ModuleNotFoundError`!**

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run unit tests
pytest tests/unit -v

# Run with coverage
pytest tests/unit --cov=azure_mcp --cov-report=html

# Run linting
ruff check src tests
ruff format src tests

# Run type checking
mypy src
```

### Running the Server

```bash
# Development
python -m azure_mcp.server

# Or via entry point
azure-mcp-server
```

## Priority Tools (Implement First)

### 1. Cost Management (Milestone 4) ⭐

These are NEW features not in the .NET version:

| Tool | Description | Issue |
|------|-------------|-------|
| `cost_query` | Query cost data | #22 |
| `cost_forecast` | Get cost forecasts | #23 |
| `cost_budgets_list` | List budgets | #24 |
| `cost_budgets_get` | Get budget details | #25 |
| `cost_recommendations` | Advisor recommendations | #26 |

**Azure SDK**:
```python
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import QueryDefinition, QueryDataset
```

### 2. Entra ID (Milestone 5) ⭐

These are NEW features not in the .NET version:

| Tool | Description | Issue |
|------|-------------|-------|
| `entraid_user_list` | List users | #29 |
| `entraid_user_get` | Get user | #30 |
| `entraid_group_list` | List groups | #31 |
| `entraid_group_members` | List group members | #33 |
| `entraid_app_list` | List app registrations | #34 |

**Azure SDK**:
```python
from msgraph import GraphServiceClient
from azure_mcp.core.auth import CredentialProvider

credential = CredentialProvider.get_credential()
client = GraphServiceClient(credentials=credential)
users = await client.users.get()
```
```

## Code Style Guidelines

### Python Style

- Use `from __future__ import annotations` for forward references
- Use type hints everywhere
- Use `async/await` for all Azure operations
- Prefer `|` over `Union` for type unions (Python 3.10+)
- Use `snake_case` for functions/variables, `PascalCase` for classes

### Imports Order

```python
from __future__ import annotations

# Standard library
import asyncio
from typing import Any

# Third-party
from pydantic import BaseModel, Field

# Azure SDK
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient

# Local
from azure_mcp.core.base import AzureService, AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.registry import register_tool
```

### Documentation

- All public classes/methods need docstrings
- Tool descriptions should explain WHEN to use the tool
- Parameter descriptions should be clear for LLM understanding

## Testing Guidelines

### Unit Tests

- Mock Azure SDK clients at the boundary
- Use fixtures from `conftest.py`
- Test both success and error paths
- Test Pydantic validation

```python
@pytest.mark.asyncio
async def test_tool_execute_success(mock_client, patch_credential):
    tool = MyTool()
    options = MyToolOptions(param1="value")
    
    result = await tool.execute(options)
    
    assert "expected_key" in result
```

### Integration Tests

- Mark with `@pytest.mark.integration`
- Require real Azure credentials
- Skip in CI unless explicitly enabled

## Git Workflow

- Branch from `main`
- Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- Reference issue numbers: `feat: add cost_query tool (#22)`
- PR template is in `.github/pull_request_template.md`

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/azure_mcp/core/base.py` | AzureService and AzureTool base classes |
| `src/azure_mcp/core/registry.py` | @register_tool decorator |
| `src/azure_mcp/core/errors.py` | Error types and handle_azure_error() |
| `docs/adding-tools.md` | Detailed guide for adding tools |
| `.github/ISSUES.md` | All 59 planned issues with details |
| `.github/PROJECT_PLAN.md` | Architecture decisions and milestones |
| `.github/RESEARCH_NOTES.md` | .NET analysis and SDK research |

## Common Patterns

### Subscription Resolution

```python
# In AzureService methods
sub_id = await self.resolve_subscription(options.subscription)
# Handles both GUID and display name, with caching
```

### Pagination

```python
# For tools that list resources
class ListOptions(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    skip: int = Field(default=0, ge=0)
```

### Optional Dependencies

Each tool family has optional dependencies in `pyproject.toml`:

```toml
[project.optional-dependencies]
storage = ["azure-storage-blob", "azure-storage-queue", "azure-data-tables"]
cosmos = ["azure-cosmos"]
cost = ["azure-mgmt-costmanagement"]
entraid = ["msgraph-sdk"]
```

Install specific extras: `pip install -e ".[cost,entraid]"`

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure to import tool modules in `tools/__init__.py`
2. **Tool not registered**: Check `@register_tool` decorator is applied
3. **Auth failures**: Run `az login` for development
4. **Type errors**: Run `mypy src` to catch issues early

### Debug Mode

Set environment variable for verbose logging:
```bash
export AZURE_MCP_DEBUG=1
```

## Links

- [GitHub Repository](https://github.com/frdeange/azure-mcp-python)
- [MCP Protocol Spec](https://modelcontextprotocol.io/)
- [Azure SDK for Python](https://learn.microsoft.com/en-us/azure/developer/python/)
- [Microsoft Graph SDK](https://learn.microsoft.com/en-us/graph/sdks/sdk-installation#python)
