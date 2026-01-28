# Azure AI Foundry Deployment Guide

This guide covers deploying the Azure MCP Server for use with Azure AI Foundry Agent Service.

## Overview

Azure AI Foundry Agent Service can connect to remote MCP servers to extend agent capabilities. However, it has specific requirements that differ from local MCP usage.

## Prerequisites

- Azure Container Apps or Azure Functions for hosting
- Azure Container Registry (ACR) for images
- The MCP server must be publicly accessible (or use VNet integration)

## Key Compatibility Requirements

### 1. HTTP Transport (Not stdio)

AI Foundry requires HTTP endpoints, not stdio transport:

```python
# Use http_app() instead of run()
app = mcp.http_app(stateless_http=True)
```

### 2. Stateless Mode Required

AI Foundry expects stateless MCP servers:

```python
app = mcp.http_app(stateless_http=True)  # Critical!
```

### 3. Accept Header Middleware

AI Foundry may not send the required `Accept: text/event-stream` header. Add middleware:

```python
from starlette.types import ASGIApp, Message, Receive, Scope, Send

class MCPCompatibilityMiddleware:
    """Fix headers for Azure AI Agent Service compatibility."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            accept = headers.get(b"accept", b"").decode()

            if "application/json" not in accept or "text/event-stream" not in accept:
                new_accept = "application/json, text/event-stream"
                new_headers = [(k, v) for k, v in scope["headers"] if k != b"accept"]
                new_headers.append((b"accept", new_accept.encode()))
                scope = {**scope, "headers": new_headers}

        await self.app(scope, receive, send)
```

### 4. JSON Schema Restrictions ⚠️ CRITICAL

**Azure AI Foundry does NOT support these JSON Schema features:**

- `anyOf`
- `allOf`
- `oneOf`

Pydantic 2 generates `anyOf` for optional types like `str | None`. This causes the error:

```
Invalid tool schema for: AzureMCPPython.my_tool
```

## Schema-Compatible Pydantic Patterns

### ❌ WRONG - Generates `anyOf`

```python
class MyOptions(BaseModel):
    # This generates: {"anyOf": [{"type": "string"}, {"type": "null"}]}
    resource_group: str | None = Field(default=None, description="...")
    
    # This also generates anyOf
    parameters: list[dict] | None = Field(default=None, description="...")
```

### ✅ CORRECT - Simple types only

```python
class MyOptions(BaseModel):
    # Use empty string as default, describe that empty means "all"
    resource_group: str = Field(
        default="",
        description="Resource group to filter. Leave empty for all."
    )
    
    # Use default_factory for lists
    parameters: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Query parameters. Pass empty list [] if none needed."
    )
```

### Handling Empty Values in Code

The empty values work naturally with Python's truthiness:

```python
async def execute(self, options: MyOptions):
    # Both "" and None are falsy
    if options.resource_group:
        query += f" | where resourceGroup =~ '{options.resource_group}'"
    
    # Both [] and None are falsy
    if options.parameters:
        # use parameters
```

### Schema Comparison

```json
// ❌ Incompatible (anyOf)
{
  "resource_group": {
    "anyOf": [{"type": "string"}, {"type": "null"}],
    "default": null,
    "description": "..."
  }
}

// ✅ Compatible (simple type)
{
  "resource_group": {
    "type": "string",
    "default": "",
    "description": "... Leave empty for all."
  }
}
```

## Deployment to Azure Container Apps

### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir -e ".[cosmos]"

EXPOSE 8000

CMD ["python", "-m", "azure_mcp.server", "--http"]
```

### 2. Build and Push to ACR

```bash
# Build
docker build -t myacr.azurecr.io/azure-mcp-python:v1.0 .

# Login to ACR
az acr login --name myacr

# Push
docker push myacr.azurecr.io/azure-mcp-python:v1.0
```

### 3. Deploy Container App

```bash
az containerapp create \
  --name azure-mcp-python \
  --resource-group MyResourceGroup \
  --environment my-aca-env \
  --image myacr.azurecr.io/azure-mcp-python:v1.0 \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --registry-server myacr.azurecr.io \
  --registry-identity system
```

### 4. Assign Managed Identity Permissions

```bash
# Get Container App identity
IDENTITY=$(az containerapp show \
  --name azure-mcp-python \
  --resource-group MyResourceGroup \
  --query identity.principalId -o tsv)

# Assign Reader role on subscription
az role assignment create \
  --assignee $IDENTITY \
  --role "Reader" \
  --scope /subscriptions/<subscription-id>
```

## Using with AI Foundry

### Python SDK Example

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MCPTool

tool = MCPTool(
    server_label="azure-mcp",
    server_url="https://azure-mcp-python.myenv.region.azurecontainerapps.io/mcp",
    require_approval="always",
)

agent = project_client.agents.create_version(
    agent_name="AzureAgent",
    definition=PromptAgentDefinition(
        model="gpt-4",
        instructions="Use MCP tools to query Azure resources",
        tools=[tool],
    ),
)
```

## Troubleshooting

### "Invalid tool schema" Error

**Cause**: Schema contains `anyOf`, `allOf`, or `oneOf`

**Solution**: 
1. Check your Pydantic models for `| None` patterns
2. Replace with empty defaults (`""` for strings, `[]` for lists)
3. Rebuild and redeploy

### "421 Invalid Host header" Error

**Cause**: DNS rebinding protection in some MCP SDK versions

**Solution**: Use `fastmcp` package with `http_app(stateless_http=True)`

### Server Returns Empty Tools List

**Cause**: Tools not properly registered

**Solution**: 
1. Check imports in `tools/__init__.py`
2. Verify `@register_tool` decorator on tool classes
3. Check server logs for import errors

### Authentication Failures

**Cause**: Container App doesn't have Azure permissions

**Solution**: 
1. Enable system-assigned managed identity
2. Assign appropriate RBAC roles (Reader, Cosmos DB Account Reader, etc.)

## Security Considerations

For production deployments:

1. **Enable authentication** - Use Easy Auth with Entra ID
2. **Restrict network access** - Use VNet integration or IP restrictions
3. **Use managed identity** - Avoid storing credentials
4. **Enable audit logging** - Track tool invocations
5. **Review tool permissions** - Use least-privilege RBAC roles

## References

- [Azure AI Foundry MCP Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/model-context-protocol)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
