# GitHub Issues for Azure MCP Server (Python)

This document contains all planned issues organized by milestone.
You can import these into GitHub using the GitHub CLI or manually.

---

## Milestone 1: Core Framework

### Issue #1: Project scaffolding and configuration
**Labels**: `core`, `setup`
**Priority**: P0

#### Description
Set up the initial project structure with all configuration files.

#### Acceptance Criteria
- [x] `pyproject.toml` with dependencies and optional extras
- [x] `src/` layout structure
- [x] Dev Container configuration
- [x] GitHub workflows (CI, Release)
- [x] Issue and PR templates
- [x] README, CONTRIBUTING, ARCHITECTURE docs

**Status**: ✅ COMPLETE

---

### Issue #2: Implement CredentialProvider
**Labels**: `core`, `auth`
**Priority**: P0

#### Description
Implement credential management with support for:
- DefaultAzureCredential chain
- Development-friendly AzureCliCredential
- Multi-tenant support with explicit tenant ID
- Credential caching

#### Acceptance Criteria
- [x] `CredentialProvider.get_credential(tenant=None)` method
- [x] `CredentialProvider.get_credential_for_dev()` method
- [x] Unit tests for credential provider
- [x] Documentation in `docs/authentication.md`

**Status**: ✅ COMPLETE

---

### Issue #3: Implement CacheService
**Labels**: `core`, `performance`
**Priority**: P0

#### Description
Implement in-memory caching with TTL support for:
- Subscription resolution (name → ID)
- Resource metadata
- Frequently accessed data

#### Acceptance Criteria
- [x] `CacheService` class with get/set/delete/clear
- [x] TTL support with configurable defaults
- [x] `get_or_set()` async method for cache-aside pattern
- [x] Unit tests

**Status**: ✅ COMPLETE

---

### Issue #4: Implement error handling framework
**Labels**: `core`, `errors`
**Priority**: P0

#### Description
Create a comprehensive error handling system that:
- Provides consistent error types for tools
- Converts Azure SDK errors to tool errors
- Includes context for debugging

#### Error Types
- `ToolError` (base)
- `ValidationError` (invalid input)
- `AuthenticationError` (auth failures)
- `AuthorizationError` (permission denied)
- `AzureResourceError` (resource operations)
- `NetworkError` (connectivity)
- `RateLimitError` (throttling)
- `ConfigurationError` (setup issues)

#### Acceptance Criteria
- [x] Error class hierarchy
- [x] `handle_azure_error()` function
- [x] Error serialization to dict
- [x] Unit tests

**Status**: ✅ COMPLETE

---

### Issue #5: Implement AzureService base class
**Labels**: `core`, `services`
**Priority**: P0

#### Description
Create base class for all Azure service implementations with:
- Credential management
- Subscription resolution (name → GUID)
- Resource Graph query helpers

#### Methods
- `get_credential(tenant=None)`
- `resolve_subscription(subscription, tenant=None)`
- `list_subscriptions(tenant=None)`
- `list_resources(resource_type, subscription, ...)`
- `get_resource(resource_type, subscription, name, ...)`

#### Acceptance Criteria
- [x] AzureService class with all methods
- [x] Resource Graph integration
- [x] Subscription caching
- [x] Unit tests

**Status**: ✅ COMPLETE

---

### Issue #6: Implement AzureTool base class
**Labels**: `core`, `tools`
**Priority**: P0

#### Description
Create abstract base class for all MCP tools with:
- Tool naming convention enforcement
- Pydantic-based options validation
- JSON Schema generation for MCP
- Metadata for tool behavior hints

#### Properties
- `name` (abstract)
- `description` (abstract)
- `metadata` (ToolMetadata)
- `options_model` (Pydantic model class)

#### Methods
- `get_options_schema()` → JSON Schema dict
- `execute(options)` (abstract)
- `run(raw_options)` → validates and executes

#### Acceptance Criteria
- [x] AzureTool ABC
- [x] ToolMetadata dataclass
- [x] Schema generation from Pydantic
- [x] Unit tests

**Status**: ✅ COMPLETE

---

### Issue #7: Implement tool registry
**Labels**: `core`, `tools`
**Priority**: P0

#### Description
Create tool registration and discovery system:
- `@register_tool(group, subgroup)` decorator
- Global `ToolRegistry` singleton
- Tool listing and schema export

#### Acceptance Criteria
- [x] `@register_tool` decorator
- [x] `ToolRegistry` class
- [x] `list_tools()`, `get_tool()`, `list_groups()`
- [x] `get_tool_schemas()` for MCP export
- [x] Unit tests

**Status**: ✅ COMPLETE

---

### Issue #8: Implement MCP server entry point
**Labels**: `core`, `server`
**Priority**: P0

#### Description
Create the MCP server using FastMCP:
- Auto-register all tools from registry
- Server configuration
- Entry point for `python -m azure_mcp`

#### Acceptance Criteria
- [x] `server.py` with FastMCP setup
- [x] Dynamic tool registration
- [x] `main()` entry point
- [ ] Integration test with MCP client

**Status**: ✅ MOSTLY COMPLETE (needs integration test)

---

### Issue #9: Implement resourcegraph_query tool
**Labels**: `tool`, `resourcegraph`
**Priority**: P0

#### Description
First tool implementation to validate the entire stack.

Executes arbitrary KQL queries against Azure Resource Graph.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| query | string | Yes | KQL query |
| subscriptions | string[] | No | Subscription IDs to query |
| management_groups | string[] | No | Management groups (precedence over subs) |
| skip | int | No | Pagination offset |
| top | int | No | Max results (1-1000) |

#### Acceptance Criteria
- [x] `ResourceGraphQueryTool` implementation
- [x] `ResourceGraphService` with query method
- [x] Pydantic options model with validation
- [x] Unit tests
- [ ] Integration test with real Azure

**Status**: ✅ MOSTLY COMPLETE (needs integration test)

---

### Issue #10: Documentation and examples
**Labels**: `docs`
**Priority**: P1

#### Description
Complete documentation for the core framework.

#### Acceptance Criteria
- [x] `docs/adding-tools.md` - How to add new tools
- [x] `docs/authentication.md` - Auth guide
- [x] `docs/testing.md` - Testing guide
- [ ] Example tool implementation walkthrough
- [ ] Video or detailed tutorial

**Status**: 🔄 IN PROGRESS

---

## Milestone 2: Storage Tools

### Issue #11: storage_account_list
**Labels**: `tool`, `storage`
**Priority**: P1

#### Description
List Azure Storage Accounts using Resource Graph.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription ID or name |
| resource_group | string | No | Filter by resource group |
| limit | int | No | Max results (default 50) |

#### Acceptance Criteria
- [ ] Tool implementation
- [ ] Unit tests
- [ ] Integration test

---

### Issue #12: storage_account_get
**Labels**: `tool`, `storage`
**Priority**: P1

#### Description
Get details of a specific Storage Account.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription ID or name |
| account_name | string | Yes | Storage account name |
| resource_group | string | No | Resource group (optional, uses ARG) |

---

### Issue #13: storage_blob_list
**Labels**: `tool`, `storage`
**Priority**: P1

#### Description
List blobs in a container.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_name | string | Yes | Storage account name |
| container_name | string | Yes | Container name |
| prefix | string | No | Blob name prefix filter |
| limit | int | No | Max results |

---

### Issue #14: storage_blob_read
**Labels**: `tool`, `storage`
**Priority**: P1

#### Description
Read blob content (text or base64 for binary).

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_name | string | Yes | Storage account name |
| container_name | string | Yes | Container name |
| blob_name | string | Yes | Blob name |
| encoding | string | No | text/base64 (default: text) |

---

### Issue #15: storage_blob_write
**Labels**: `tool`, `storage`
**Priority**: P2

#### Description
Write content to a blob.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_name | string | Yes | Storage account name |
| container_name | string | Yes | Container name |
| blob_name | string | Yes | Blob name |
| content | string | Yes | Content to write |
| overwrite | bool | No | Overwrite if exists |

---

### Issue #16: storage_container_list
**Labels**: `tool`, `storage`
**Priority**: P1

#### Description
List containers in a storage account.

---

### Issue #17: storage_table_query
**Labels**: `tool`, `storage`
**Priority**: P2

#### Description
Query entities from Azure Table Storage.

---

### Issue #18: storage_queue_list
**Labels**: `tool`, `storage`
**Priority**: P2

#### Description
List queues in a storage account.

---

## Milestone 3: Cosmos DB Tools

### Issue #21: cosmos_account_list
**Labels**: `tool`, `cosmos`
**Priority**: P1

#### Description
List Cosmos DB accounts using Resource Graph.

---

### Issue #22: cosmos_database_list
**Labels**: `tool`, `cosmos`
**Priority**: P1

#### Description
List databases in a Cosmos DB account.

---

### Issue #23: cosmos_container_list
**Labels**: `tool`, `cosmos`
**Priority**: P1

#### Description
List containers in a Cosmos DB database.

---

### Issue #24: cosmos_item_query
**Labels**: `tool`, `cosmos`
**Priority**: P0

#### Description
Query items using SQL-like syntax.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_name | string | Yes | Cosmos account name |
| database_name | string | Yes | Database name |
| container_name | string | Yes | Container name |
| query | string | Yes | SQL query |
| parameters | object | No | Query parameters |
| max_items | int | No | Max results |

---

### Issue #25: cosmos_item_get
**Labels**: `tool`, `cosmos`
**Priority**: P1

#### Description
Get a single item by ID and partition key.

---

### Issue #26: cosmos_item_upsert
**Labels**: `tool`, `cosmos`
**Priority**: P2

#### Description
Create or update an item.

---

### Issue #27: cosmos_item_delete
**Labels**: `tool`, `cosmos`
**Priority**: P2

#### Description
Delete an item by ID and partition key.

---

## Milestone 4: Cost Management Tools ⭐ PRIORITY

### Issue #31: cost_query
**Labels**: `tool`, `cost`, `priority`
**Priority**: P0

#### Description
Query cost data using the Cost Management API.

**Note**: This is NEW functionality not in the .NET version.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription ID or name |
| scope | string | No | Scope (subscription, resource group, etc.) |
| timeframe | string | Yes | MonthToDate, BillingMonthToDate, Custom |
| granularity | string | No | None, Daily, Monthly |
| group_by | string[] | No | Dimensions to group by |
| filter | object | No | Filter expression |

#### Returns
- Cost breakdown by grouping dimensions
- Total cost
- Currency

---

### Issue #32: cost_forecast
**Labels**: `tool`, `cost`, `priority`
**Priority**: P0

#### Description
Get cost forecasts.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription |
| timeframe | string | Yes | Forecast period |
| granularity | string | No | Daily, Monthly |

---

### Issue #33: cost_budgets_list
**Labels**: `tool`, `cost`, `priority`
**Priority**: P1

#### Description
List budgets for a scope.

---

### Issue #34: cost_budgets_get
**Labels**: `tool`, `cost`, `priority`
**Priority**: P1

#### Description
Get budget details and current spend vs. limit.

---

### Issue #35: cost_recommendations
**Labels**: `tool`, `cost`, `priority`
**Priority**: P1

#### Description
Get Azure Advisor cost recommendations.

---

### Issue #36: cost_exports_list
**Labels**: `tool`, `cost`
**Priority**: P2

#### Description
List configured cost exports.

---

## Milestone 5: Entra ID Tools ⭐ PRIORITY

### Issue #41: entraid_user_list
**Labels**: `tool`, `entraid`, `priority`
**Priority**: P0

#### Description
List users in Entra ID (Azure AD).

**Note**: This is NEW functionality not in the .NET version.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| filter | string | No | OData filter |
| search | string | No | Search by displayName or email |
| select | string[] | No | Properties to return |
| top | int | No | Max results |

---

### Issue #42: entraid_user_get
**Labels**: `tool`, `entraid`, `priority`
**Priority**: P0

#### Description
Get a specific user by ID or UPN.

---

### Issue #43: entraid_group_list
**Labels**: `tool`, `entraid`, `priority`
**Priority**: P0

#### Description
List groups in Entra ID.

---

### Issue #44: entraid_group_get
**Labels**: `tool`, `entraid`, `priority`
**Priority**: P1

#### Description
Get group details.

---

### Issue #45: entraid_group_members
**Labels**: `tool`, `entraid`, `priority`
**Priority**: P1

#### Description
List members of a group.

---

### Issue #46: entraid_app_list
**Labels**: `tool`, `entraid`, `priority`
**Priority**: P1

#### Description
List app registrations.

---

### Issue #47: entraid_app_get
**Labels**: `tool`, `entraid`, `priority`
**Priority**: P1

#### Description
Get app registration details.

---

### Issue #48: entraid_serviceprincipal_list
**Labels**: `tool`, `entraid`
**Priority**: P2

#### Description
List service principals (enterprise apps).

---

### Issue #49: entraid_role_assignments
**Labels**: `tool`, `entraid`
**Priority**: P2

#### Description
List role assignments for a user or service principal.

---

### Issue #50: entraid_signin_logs
**Labels**: `tool`, `entraid`
**Priority**: P2

#### Description
Query sign-in logs (requires Premium license).

---

## Milestone 6: Key Vault Tools

### Issue #51: keyvault_list
**Labels**: `tool`, `keyvault`
**Priority**: P1

#### Description
List Key Vaults using Resource Graph.

---

### Issue #52: keyvault_secret_list
**Labels**: `tool`, `keyvault`
**Priority**: P1

#### Description
List secrets in a Key Vault (names only, not values).

---

### Issue #53: keyvault_secret_get
**Labels**: `tool`, `keyvault`
**Priority**: P1

#### Description
Get a secret value.

---

### Issue #54: keyvault_secret_set
**Labels**: `tool`, `keyvault`
**Priority**: P2

#### Description
Set a secret value.

---

### Issue #55: keyvault_key_list
**Labels**: `tool`, `keyvault`
**Priority**: P2

#### Description
List keys in a Key Vault.

---

### Issue #56: keyvault_certificate_list
**Labels**: `tool`, `keyvault`
**Priority**: P2

#### Description
List certificates in a Key Vault.

---

## Milestone 7: Additional Services

### Issue #61: eventgrid_topic_list
**Labels**: `tool`, `eventgrid`
**Priority**: P2

---

### Issue #62: servicebus_namespace_list
**Labels**: `tool`, `servicebus`
**Priority**: P2

---

### Issue #63: servicebus_queue_list
**Labels**: `tool`, `servicebus`
**Priority**: P2

---

### Issue #64: functionapp_list
**Labels**: `tool`, `functions`
**Priority**: P2

---

### Issue #65: functionapp_function_list
**Labels**: `tool`, `functions`
**Priority**: P2

---

### Issue #66: appservice_webapp_list
**Labels**: `tool`, `appservice`
**Priority**: P2

---

### Issue #67: monitor_metrics_query
**Labels**: `tool`, `monitor`
**Priority**: P1

#### Description
Query Azure Monitor metrics for a resource.

---

### Issue #68: monitor_logs_query
**Labels**: `tool`, `monitor`
**Priority**: P1

#### Description
Query Log Analytics workspace.

---

### Issue #69: aks_cluster_list
**Labels**: `tool`, `aks`
**Priority**: P2

---

### Issue #70: acr_repository_list
**Labels**: `tool`, `acr`
**Priority**: P2

---

## Milestone 9: Bing Search

Bing Search tools provide access to the Bing Search API v7 via `Microsoft.Bing/accounts`
resources in Azure. The Managed Identity retrieves the API key automatically from ARM
(no environment variables required) and caches it for 12 hours.

### Issue #71: BingService ARM key retrieval pattern
**Labels**: `tool`, `bing`, `architecture`
**Priority**: P1

#### Description
Implement `BingService(AzureService)` with the ARM key-retrieval pattern:
- `list_bing_resources()` and `get_bing_resource()` via Resource Graph
- `_get_api_key()`: POST to `Microsoft.Bing/accounts/{name}/listKeys?api-version=2020-06-10`
  authenticated with `DefaultAzureCredential`; result cached for 12 hours
- `_search()`: async `aiohttp.ClientSession` GET with `Ocp-Apim-Subscription-Key` header
- All five search methods delegating to `_search()`

#### Parameters / Service Methods
| Method | Description |
|--------|-------------|
| `list_bing_resources(subscription, resource_group, limit)` | Resource Graph KQL |
| `get_bing_resource(subscription, name, resource_group)` | Single resource lookup |
| `_get_api_key(subscription_id, rg, name)` | ARM listKeys + 12h cache |
| `_search(endpoint, api_key, params)` | aiohttp GET, strips empty params |
| `web_search(...)` | Delegates to `_search("/search", ...)` |
| `news_search(...)` | Delegates to `_search("/news/search", ...)` |
| `image_search(...)` | Delegates to `_search("/images/search", ...)` |
| `entity_search(...)` | Delegates to `_search("/entities", ...)` |
| `video_search(...)` | Delegates to `_search("/videos/search", ...)` |

#### Acceptance Criteria
- [x] `src/azure_mcp/tools/bing/service.py` implemented
- [x] `get_token()` wrapped in `asyncio.to_thread()` (async-first rule)
- [x] Key cached with `cache.get_or_set()` for 12 hours
- [x] Empty params stripped before Bing API call
- [x] Proper error messages for 401/403/404 ARM responses
- [x] Unit tests in `tests/unit/tools/test_bing.py`
- [x] `bing` extra added to `pyproject.toml` with `aiohttp>=3.8.0`
- [x] Dockerfile updated with `bing` extra

**Status**: ✅ COMPLETE

---

### Issue #72: bing_resource_list
**Labels**: `tool`, `bing`
**Priority**: P1

#### Description
List all `Microsoft.Bing/accounts` resources in an Azure subscription using Resource Graph.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription ID or display name |
| resource_group | string | No | Filter by resource group. Leave empty for all. |
| limit | integer | No | Max results (1-200, default 50) |

#### Acceptance Criteria
- [x] `BingResourceListOptions` Pydantic model (AI Foundry compatible, no `anyOf`)
- [x] `BingResourceListTool` class in `discovery.py`
- [x] `@register_tool("bing", "discovery")` decorator
- [x] `metadata.read_only = True`
- [x] Unit tests

**Status**: ✅ COMPLETE

---

### Issue #73: bing_resource_get
**Labels**: `tool`, `bing`
**Priority**: P1

#### Description
Get details of a specific `Microsoft.Bing/accounts` resource.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription ID or display name |
| resource_name | string | Yes | Name of the Bing resource |
| resource_group | string | No | Resource group. Leave empty to search all. |

#### Acceptance Criteria
- [x] `BingResourceGetOptions` Pydantic model
- [x] `BingResourceGetTool` class in `discovery.py`
- [x] Returns `{"error": "..."}` dict when resource not found
- [x] Unit tests

**Status**: ✅ COMPLETE

---

### Issue #74: bing_web_search
**Labels**: `tool`, `bing`
**Priority**: P1

#### Description
Search the web using Bing Web Search API v7.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription ID or display name |
| resource_name | string | Yes | Name of the Microsoft.Bing/accounts resource |
| resource_group | string | Yes | Resource group of the Bing resource |
| query | string | Yes | Web search query |
| market | string | No | BCP 47 market code (e.g. 'en-US'). Leave empty for default. |
| safe_search | string | No | 'Off', 'Moderate', or 'Strict'. Leave empty for default. |
| count | integer | No | Number of results (1-50, default 10) |
| offset | integer | No | Pagination offset (default 0) |

#### Acceptance Criteria
- [x] `BingWebSearchOptions` Pydantic model (count ge=1 le=50)
- [x] `BingWebSearchTool` in `web.py` with `@register_tool("bing", "search")`
- [x] Calls `BingService.web_search()`
- [x] Unit tests

**Status**: ✅ COMPLETE

---

### Issue #75: bing_news_search
**Labels**: `tool`, `bing`
**Priority**: P1

#### Description
Search for news articles using Bing News Search API v7.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription ID or display name |
| resource_name | string | Yes | Name of the Microsoft.Bing/accounts resource |
| resource_group | string | Yes | Resource group |
| query | string | Yes | News search query |
| market | string | No | BCP 47 market code. Leave empty for default. |
| count | integer | No | Number of articles (1-100, default 10) |
| freshness | string | No | 'Day', 'Week', or 'Month'. Leave empty for any date. |

#### Acceptance Criteria
- [x] `BingNewsSearchOptions` Pydantic model (count ge=1 le=100)
- [x] `BingNewsSearchTool` in `news.py`
- [x] Unit tests

**Status**: ✅ COMPLETE

---

### Issue #76: bing_image_search
**Labels**: `tool`, `bing`
**Priority**: P1

#### Description
Search for images using Bing Image Search API v7.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription ID or display name |
| resource_name | string | Yes | Name of the Microsoft.Bing/accounts resource |
| resource_group | string | Yes | Resource group |
| query | string | Yes | Image search query |
| market | string | No | BCP 47 market code. Leave empty for default. |
| safe_search | string | No | 'Off', 'Moderate', 'Strict'. Leave empty for default. |
| count | integer | No | Number of results (1-150, default 10) |
| size | string | No | 'Small', 'Medium', 'Large', 'Wallpaper'. Leave empty for any. |
| color | string | No | Color filter (e.g. 'Red', 'Monochrome'). Leave empty for any. |

#### Acceptance Criteria
- [x] `BingImageSearchOptions` Pydantic model (count ge=1 le=150)
- [x] `BingImageSearchTool` in `images.py`
- [x] Unit tests

**Status**: ✅ COMPLETE

---

### Issue #77: bing_entity_search
**Labels**: `tool`, `bing`
**Priority**: P1

#### Description
Search for named entities (people, places, organizations) using Bing Entity Search API v7.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription ID or display name |
| resource_name | string | Yes | Name of the Microsoft.Bing/accounts resource |
| resource_group | string | Yes | Resource group |
| query | string | Yes | Entity name or description |
| market | string | No | BCP 47 market code. Leave empty for default. |

#### Acceptance Criteria
- [x] `BingEntitySearchOptions` Pydantic model
- [x] `BingEntitySearchTool` in `entities.py`
- [x] Unit tests

**Status**: ✅ COMPLETE

---

### Issue #78: bing_video_search
**Labels**: `tool`, `bing`
**Priority**: P1

#### Description
Search for videos using Bing Video Search API v7.

#### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription ID or display name |
| resource_name | string | Yes | Name of the Microsoft.Bing/accounts resource |
| resource_group | string | Yes | Resource group |
| query | string | Yes | Video search query |
| market | string | No | BCP 47 market code. Leave empty for default. |
| count | integer | No | Number of results (1-105, default 10) |
| pricing | string | No | 'Free' or 'Paid'. Leave empty for any. |
| resolution | string | No | 'SD480p', 'HD720p', 'HD1080p'. Leave empty for any. |

#### Acceptance Criteria
- [x] `BingVideoSearchOptions` Pydantic model (count ge=1 le=105)
- [x] `BingVideoSearchTool` in `videos.py`
- [x] Unit tests

**Status**: ✅ COMPLETE

---

## GitHub CLI Import Commands

To create these issues in your repository, you can use the GitHub CLI:

```bash
# Example: Create a single issue
gh issue create \
  --title "[Core] Implement CredentialProvider" \
  --body "$(cat issue-2-body.md)" \
  --label "core,auth" \
  --milestone "Core Framework"

# Or use the gh api for bulk import
```

Alternatively, use the GitHub web interface or a tool like:
- https://github.com/gavinr/github-csv-tools
- https://github.com/mattduck/gh-issues-import
