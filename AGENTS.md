# Agent Guidelines for Azure MCP Server (Python)

This document provides essential context for AI coding assistants working on this project.

## Quick Context

- **What**: Python MCP server providing Azure tools for AI assistants
- **Why**: Team prefers Python, need features Microsoft doesn't provide (Cost, Entra ID)
- **Based on**: Microsoft's .NET Azure MCP Server (reimplemented, not ported)

## Core Principles

1. **Use Resource Graph** for listing resources (not management API)
2. **Pydantic everywhere** for options validation and schema generation
3. **Async/await** for all Azure operations
4. **Handle errors** with `handle_azure_error()` wrapper
5. **Register tools** with `@register_tool("family", "subgroup")` decorator

## Adding a Tool (Quick Reference)

```python
# src/azure_mcp/tools/{family}/{action}.py

from pydantic import BaseModel, Field
from azure_mcp.core.base import AzureService, AzureTool
from azure_mcp.core.errors import handle_azure_error
from azure_mcp.core.models import ToolMetadata
from azure_mcp.core.registry import register_tool

class MyOptions(BaseModel):
    subscription: str = Field(..., description="Subscription ID or name")

class MyService(AzureService):
    async def do_work(self, subscription: str):
        sub_id = await self.resolve_subscription(subscription)
        return await self.list_resources("Microsoft.Type/resources", sub_id)

@register_tool("family", "subgroup")
class MyTool(AzureTool):
    @property
    def name(self) -> str: return "family_resource_action"
    
    @property
    def description(self) -> str: return "What this tool does"
    
    @property
    def options_model(self): return MyOptions
    
    async def execute(self, options):
        try:
            return await MyService().do_work(options.subscription)
        except Exception as e:
            raise handle_azure_error(e)
```

## Naming: `{family}_{resource}_{action}`

- `cost_query`, `cost_forecast`, `cost_budgets_list`
- `entraid_user_list`, `entraid_group_members`
- `storage_blob_read`, `cosmos_item_query`

## Priority Order

1. **Cost Management** (Issues #22-28) - NEW FEATURES ⭐
2. **Entra ID** (Issues #29-38) - NEW FEATURES ⭐
3. Storage, Cosmos, Key Vault, etc.

## Key Files

- `src/azure_mcp/core/base.py` - Base classes
- `src/azure_mcp/core/registry.py` - Tool registration
- `docs/adding-tools.md` - Detailed guide
- `.github/copilot-instructions.md` - Full agent instructions
- `.github/ISSUES.md` - All 59 planned issues

## Don't Forget

- Import new tool modules in `tools/__init__.py`
- Add tests in `tests/unit/tools/`
- Use `ToolMetadata(read_only=False, requires_confirmation=True)` for write ops
