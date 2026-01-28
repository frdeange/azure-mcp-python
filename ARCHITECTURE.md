# Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Clients                                  │
│         (VS Code, Claude Desktop, AI Assistants)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                   MCP Protocol (stdio/HTTP)
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    azure_mcp.server                              │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Tool Registry                            │  │
│  │   Discovers and exposes tools to MCP clients               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┴───────────────────────────────┐  │
│  │                    azure_mcp.tools                         │  │
│  │                                                            │  │
│  │   storage/     cosmos/     keyvault/    cost/    ...      │  │
│  │   ├── service.py    (Azure SDK wrapper)                   │  │
│  │   ├── models.py     (Pydantic models)                     │  │
│  │   └── *.py          (Tool implementations)                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┴───────────────────────────────┐  │
│  │                    azure_mcp.core                          │  │
│  │                                                            │  │
│  │   AzureService    (base class with auth, ARG helpers)     │  │
│  │   AzureTool       (base class for tool implementations)   │  │
│  │   Registry        (tool discovery and registration)       │  │
│  │   Errors          (unified error handling)                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Azure Resource Manager
                    Azure Service SDKs
```

## Core Components

### AzureService (`core/base.py`)

Base class for all service implementations. Provides:

- **Credential management** via `CredentialProvider`
- **Subscription resolution** (name → ID with caching)
- **Resource Graph queries** via `list_resources()` and `get_resource()`

```python
class AzureService:
    async def get_credential(self, tenant: str | None = None) -> TokenCredential
    async def resolve_subscription(self, subscription: str) -> str
    async def list_resources(self, resource_type: str, subscription: str, ...) -> list[dict]
    async def get_resource(self, resource_type: str, subscription: str, name: str) -> dict | None
```

### AzureTool (`core/base.py`)

Abstract base class for tool implementations. Requires:

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Tool identifier (e.g., `storage_account_get`) |
| `description` | `str` | Human-readable description for LLM context |
| `metadata` | `ToolMetadata` | Behavioral hints (read_only, destructive, idempotent) |
| `options_model` | `type[BaseModel]` | Pydantic model for input validation |
| `execute()` | `async method` | Implementation logic |

### Tool Registry (`core/registry.py`)

Singleton that manages tool discovery and registration:

- Tools self-register via `@register_tool("group", "subgroup")` decorator
- Registry provides tool schemas for MCP protocol
- Enables filtering by group for selective loading

### CredentialProvider (`core/auth.py`)

Manages Azure credentials with automatic fallback chain:

1. Environment variables (Service Principal)
2. VS Code credential
3. Azure CLI credential
4. Managed Identity (in production)

## Data Flow

```
1. MCP Client sends tool invocation request
         │
         ▼
2. Server routes to registered tool by name
         │
         ▼
3. Tool validates options via Pydantic model
         │
         ▼
4. Tool calls Service methods
         │
         ▼
5. Service uses Azure SDK with credentials from CredentialProvider
         │
         ▼
6. Response flows back through the chain
```

## File Organization

Each tool family follows this structure:

```
tools/{family}/
├── __init__.py      # Exports, triggers registration
├── service.py       # Azure SDK wrapper (extends AzureService)
├── models.py        # Pydantic models for data and options
├── {resource}.py    # Tools grouped by resource type
└── ...
```

### Example: Cosmos DB

```
tools/cosmos/
├── __init__.py      # Exports CosmosItemQueryTool, etc.
├── service.py       # CosmosService with query_items(), create_item()
├── models.py        # ItemQueryOptions, ItemInfo, DatabaseInfo
├── database.py      # cosmos_database_list, cosmos_database_get
├── container.py     # cosmos_container_list, cosmos_container_get
└── item.py          # cosmos_item_query, cosmos_item_create, cosmos_item_delete
```

## Authentication

See [authentication.md](authentication.md) for details.

## Adding New Tools

See [developing-tools.md](developing-tools.md) for the complete guide.
