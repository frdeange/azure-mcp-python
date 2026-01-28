# Research Notes: .NET to Python Migration

This document captures all research conducted during the migration planning phase.

## Original .NET Project Analysis

### Project Structure

```
AzureMCPServer/
├── core/
│   ├── Azure.Mcp.Core/           # Core abstractions
│   ├── Microsoft.Mcp.Core/       # MCP protocol implementation
│   └── Template.Mcp.Core/        # Tool templates
├── servers/
│   └── Azure.Mcp.Server/         # Main server entry point
├── tools/
│   ├── Azure.Mcp.Tools.Acr/      # Container Registry
│   ├── Azure.Mcp.Tools.Aks/      # Kubernetes Service
│   ├── Azure.Mcp.Tools.AppConfig/# App Configuration
│   ├── Azure.Mcp.Tools.AppLens/  # App Lens diagnostics
│   ├── Azure.Mcp.Tools.AppService/# App Service
│   ├── Azure.Mcp.Tools.Authorization/ # RBAC
│   ├── Azure.Mcp.Tools.Cosmos/   # Cosmos DB
│   ├── Azure.Mcp.Tools.EventGrid/# Event Grid
│   ├── Azure.Mcp.Tools.EventHubs/# Event Hubs
│   ├── Azure.Mcp.Tools.FunctionApp/ # Functions
│   ├── Azure.Mcp.Tools.KeyVault/ # Key Vault
│   ├── Azure.Mcp.Tools.Kusto/    # Data Explorer
│   ├── Azure.Mcp.Tools.Monitor/  # Azure Monitor
│   ├── Azure.Mcp.Tools.MySql/    # MySQL
│   ├── Azure.Mcp.Tools.Postgres/ # PostgreSQL
│   ├── Azure.Mcp.Tools.Redis/    # Redis Cache
│   ├── Azure.Mcp.Tools.ResourceGraph/ # Resource Graph
│   ├── Azure.Mcp.Tools.ServiceBus/# Service Bus
│   ├── Azure.Mcp.Tools.Storage/  # Storage (Blob, Table, Queue)
│   └── ... (45+ tool projects)
└── docs/
    └── design/                   # Architecture documents
```

### Core Patterns Identified

#### 1. IAzureService Interface
```csharp
public interface IAzureService
{
    TokenCredential GetCredential(string? tenantId = null);
    Task<string> ResolveSubscriptionAsync(string subscription, string? tenant = null);
    Task<IReadOnlyList<SubscriptionInfo>> ListSubscriptionsAsync(string? tenant = null);
}
```

#### 2. Resource Graph Integration
All tools that list resources use Azure Resource Graph instead of individual API calls:

```csharp
// From Azure.Mcp.Tools.Storage
public async Task<IEnumerable<StorageAccountInfo>> ListStorageAccountsAsync(
    string subscription,
    string? resourceGroup = null)
{
    var query = "resources | where type =~ 'Microsoft.Storage/storageAccounts'";
    if (resourceGroup != null)
        query += $" | where resourceGroup =~ '{resourceGroup}'";
    
    return await _resourceGraph.QueryAsync<StorageAccountInfo>(subscription, query);
}
```

#### 3. Tool Registration Pattern
```csharp
[McpTool("storage_account_list")]
[ToolDescription("List storage accounts in a subscription")]
public class StorageAccountListTool : AzureTool<StorageAccountListOptions>
{
    public override async Task<object> ExecuteAsync(StorageAccountListOptions options)
    {
        // Implementation
    }
}
```

#### 4. Error Handling
```csharp
public static class AzureExceptionHandler
{
    public static ToolException HandleException(Exception ex, string? resourceContext = null)
    {
        return ex switch
        {
            AuthenticationFailedException => new AuthenticationToolException(...),
            RequestFailedException { Status: 403 } => new AuthorizationToolException(...),
            RequestFailedException { Status: 404 } => new ResourceNotFoundToolException(...),
            RequestFailedException { Status: 429 } => new RateLimitToolException(...),
            _ => new ToolException(...)
        };
    }
}
```

### Tool Categories

| Category | Count | Examples |
|----------|-------|----------|
| Storage | 8 | blob_list, blob_read, table_query |
| Cosmos DB | 6 | item_query, item_get, container_list |
| Key Vault | 5 | secret_get, key_list, certificate_list |
| App Service | 4 | webapp_list, webapp_get, config_get |
| Functions | 3 | function_list, function_get, invoke |
| Monitoring | 4 | metrics_query, logs_query, alerts_list |
| Databases | 6 | mysql_*, postgres_* |
| Messaging | 4 | servicebus_*, eventhub_* |
| Identity | 3 | authorization_*, rbac_* |
| Container | 4 | aks_*, acr_* |
| Other | 8+ | Various utilities |

### What's Missing (Our Priority)

1. **Cost Management** - No cost query, forecast, or budget tools
2. **Entra ID** - No user, group, or app registration tools
3. **Advanced Cosmos** - Limited to basic operations
4. **Graph API** - No Microsoft Graph integration

## Python MCP SDK Research

### Official SDK: `fastmcp`

```python
# Installation
pip install fastmcp

# Basic usage
from fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description."""
    return f"Result: {param}"

mcp.run()
```

### Key Features

1. **FastMCP** - High-level API for rapid development
2. **Pydantic Integration** - Automatic schema generation
3. **Async Support** - Native async/await
4. **Type Hints** - Full typing support
5. **HTTP Transport** - `http_app(stateless_http=True)` for AI Foundry
6. **Protocol Compliance** - MCP 2024-11-05

### Schema Generation

```python
from pydantic import BaseModel, Field

class MyOptions(BaseModel):
    name: str = Field(..., description="Resource name")
    limit: int = Field(default=50, ge=1, le=100)

# Generates JSON Schema automatically
schema = MyOptions.model_json_schema()
```

## Azure SDK for Python Research

### Authentication

```python
from azure_mcp.core.auth import CredentialProvider

# Unified chain - works in dev and production
credential = CredentialProvider.get_credential()

# With tenant
credential = CredentialProvider.get_credential(tenant_id="my-tenant")
```

### Resource Graph

```python
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest

client = ResourceGraphClient(credential)
result = client.resources(QueryRequest(
    subscriptions=["sub-id"],
    query="resources | where type =~ 'Microsoft.Storage/storageAccounts'"
))
```

### Cost Management

```python
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import (
    QueryDefinition,
    QueryTimePeriod,
    QueryDataset,
    QueryAggregation,
)

client = CostManagementClient(credential)
result = client.query.usage(
    scope=f"/subscriptions/{subscription_id}",
    parameters=QueryDefinition(
        type="Usage",
        timeframe="MonthToDate",
        dataset=QueryDataset(
            aggregation={"totalCost": QueryAggregation(name="Cost", function="Sum")},
            granularity="Daily",
        )
    )
)
```

### Microsoft Graph (Entra ID)

```python
from msgraph import GraphServiceClient
from azure_mcp.core.auth import CredentialProvider

credential = CredentialProvider.get_credential()
scopes = ["https://graph.microsoft.com/.default"]

client = GraphServiceClient(credentials=credential, scopes=scopes)

# List users
users = await client.users.get()

# Get groups
groups = await client.groups.get()
```

## Performance Considerations

### Caching Strategy

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Subscription list | 12 hours | Rarely changes |
| Subscription resolution | 12 hours | Name → ID mapping stable |
| Resource Graph results | 5 minutes | Resources can change |
| Cosmos metadata | 1 hour | Databases/containers stable |

### Async Patterns

```python
# Good: Parallel operations
async def list_all_resources(subscriptions: list[str]):
    tasks = [list_resources(sub) for sub in subscriptions]
    return await asyncio.gather(*tasks)

# Bad: Sequential operations
async def list_all_resources_slow(subscriptions: list[str]):
    results = []
    for sub in subscriptions:
        results.append(await list_resources(sub))
    return results
```

## Comparison: .NET vs Python Implementation

| Aspect | .NET | Python |
|--------|------|--------|
| Type System | Strong, compile-time | Strong, runtime (Pydantic) |
| Async | async/await, Task | async/await, asyncio |
| Dependency Injection | Built-in | Manual (or frameworks) |
| Package Size | Larger (runtime) | Smaller |
| Startup Time | Slower (JIT) | Faster |
| Memory | Higher | Lower |
| Azure SDK Parity | ✅ Full | ✅ Full |
| MCP SDK Maturity | Official | Official |

## Recommendations Applied

1. ✅ Use `src/` layout for package structure
2. ✅ Use Pydantic for all models and validation
3. ✅ Include Resource Graph helpers in base class
4. ✅ Use optional dependencies per service
5. ✅ Implement singleton registry with decorator
6. ✅ Comprehensive error handling with Azure-specific types
7. ✅ Cache subscription resolution aggressively
8. ✅ Prioritize Cost Management and Entra ID tools
