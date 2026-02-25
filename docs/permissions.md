# Permissions & RBAC Reference

Complete reference of Azure RBAC roles, Cosmos DB data plane roles, and Microsoft Graph permissions required by each tool family.

## Quick Reference

| Family | Azure RBAC Roles | Graph Permissions | Special Notes |
|--------|-----------------|-------------------|---------------|
| Resource Graph | `Reader` | — | Subscription-level |
| Cosmos DB | `Cosmos DB Account Reader Role` | — | Data plane uses separate Cosmos RBAC (per-account) |
| Cost Management | `Cost Management Reader` | — | Subscription or resource group scope |
| Storage | `Storage Blob/Table/Queue Data Reader/Contributor` | — | Per storage account or subscription |
| Entra ID | — | `User.Read.All`, `Group.Read.All`, etc. | Microsoft Graph API, not Azure RBAC |
| Monitor | `Monitoring Reader`, `Log Analytics Reader` | — | Log Analytics workspaces need separate role |
| App Insights | `Monitoring Reader`, `Log Analytics Reader` | — | KQL queries need Log Analytics Reader |
| RBAC | `Reader` | `Application.Read.All` (for app roles) | Read-only; write ops need RBAC Administrator |
| Communication | — | — | Connection string based (data plane) |
| Azure AI Search | `Search Index Data Reader/Contributor` | — | Per search service scope |

---

## Detailed Permissions by Family

### 🔍 Resource Graph (1 tool)

| Tool | Required Role | Scope |
|------|--------------|-------|
| `resourcegraph_query` | `Reader` | Subscription |

> **Note**: Resource Graph queries operate across subscriptions. The identity needs `Reader` on each subscription it should be able to query.

---

### 🗄️ Cosmos DB (12 tools)

Cosmos DB has **two separate RBAC systems**:

1. **Azure RBAC** (control plane) — for listing accounts via Resource Graph
2. **Cosmos DB Data Plane RBAC** — for database, container, and item operations

#### Control Plane (Azure RBAC)

| Tool | Required Role | Scope |
|------|--------------|-------|
| `cosmos_account_list` | `Reader` | Subscription |
| `cosmos_account_get` | `Reader` | Subscription |

#### Data Plane (Cosmos DB RBAC)

These roles are assigned **per Cosmos DB account**, not at subscription level.

| Tool | Required Cosmos Role | Notes |
|------|---------------------|-------|
| `cosmos_database_list` | `Cosmos DB Built-in Data Reader` | Role ID: `00000000-0000-0000-0000-000000000001` |
| `cosmos_database_create` | **Custom: Database Manager** | See custom role below |
| `cosmos_database_delete` | **Custom: Database Manager** | See custom role below |
| `cosmos_container_list` | `Cosmos DB Built-in Data Reader` | |
| `cosmos_container_create` | `Cosmos DB Built-in Data Contributor` | Role ID: `00000000-0000-0000-0000-000000000002` |
| `cosmos_container_delete` | `Cosmos DB Built-in Data Contributor` | |
| `cosmos_item_query` | `Cosmos DB Built-in Data Reader` | |
| `cosmos_item_get` | `Cosmos DB Built-in Data Reader` | |
| `cosmos_item_upsert` | `Cosmos DB Built-in Data Contributor` | |
| `cosmos_item_delete` | `Cosmos DB Built-in Data Contributor` | |

#### ⚠️ Custom Role: Cosmos DB Database Manager

The built-in `Cosmos DB Built-in Data Contributor` role does **NOT** include permissions to create or delete databases. It only covers:
- `Microsoft.DocumentDB/databaseAccounts/readMetadata`
- `Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*`
- `Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*`

To enable `cosmos_database_create` and `cosmos_database_delete`, you must create a **custom Cosmos DB data plane role**:

```bash
# Create custom role definition
az cosmosdb sql role definition create \
  --account-name <cosmos-account> \
  --resource-group <resource-group> \
  --body '{
    "RoleName": "Cosmos DB Database Manager",
    "Type": "CustomRole",
    "AssignableScopes": ["/"],
    "Permissions": [{
      "DataActions": [
        "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/write",
        "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/delete",
        "Microsoft.DocumentDB/databaseAccounts/readMetadata"
      ]
    }]
  }'

# Assign the custom role
az cosmosdb sql role assignment create \
  --account-name <cosmos-account> \
  --resource-group <resource-group> \
  --principal-id <identity-principal-id> \
  --role-definition-id <custom-role-definition-id> \
  --scope "/"
```

#### Recommended Cosmos DB Role Assignment

For **full CRUD** (all 12 tools), assign both:
1. `Cosmos DB Built-in Data Contributor` (role `00000000-0000-0000-0000-000000000002`)
2. Custom `Cosmos DB Database Manager` (for database create/delete)

For **read-only** (6 read tools), assign:
1. `Cosmos DB Built-in Data Reader` (role `00000000-0000-0000-0000-000000000001`)

Use `scripts/assign-cosmos-data-roles.sh` to automate this across all accounts.

---

### 💰 Cost Management (7 tools)

| Tool | Required Role | Scope |
|------|--------------|-------|
| `cost_query` | `Cost Management Reader` | Subscription |
| `cost_forecast` | `Cost Management Reader` | Subscription |
| `cost_usage_by_resource` | `Cost Management Reader` | Subscription |
| `cost_budgets_list` | `Cost Management Reader` | Subscription |
| `cost_budgets_get` | `Cost Management Reader` | Subscription |
| `cost_recommendations` | `Reader` | Subscription |
| `cost_exports_list` | `Cost Management Reader` | Subscription |

> **Note**: `cost_recommendations` uses Azure Advisor, which only needs `Reader`. The rest use the Cost Management API.

---

### 📦 Storage (9 tools)

| Tool | Read Role | Write Role | Scope |
|------|----------|-----------|-------|
| `storage_account_list` | `Reader` | — | Subscription |
| `storage_account_get` | `Reader` | — | Subscription |
| `storage_container_list` | `Storage Blob Data Reader` | — | Storage Account |
| `storage_blob_list` | `Storage Blob Data Reader` | — | Storage Account |
| `storage_blob_read` | `Storage Blob Data Reader` | — | Storage Account |
| `storage_blob_write` | — | `Storage Blob Data Contributor` | Storage Account |
| `storage_blob_delete` | — | `Storage Blob Data Contributor` | Storage Account |
| `storage_queue_list` | `Storage Queue Data Reader` | — | Storage Account |
| `storage_table_query` | `Storage Table Data Reader` | — | Storage Account |

#### Recommended Storage Roles

For **read-only**: `Storage Blob Data Reader` + `Storage Queue Data Reader` + `Storage Table Data Reader`

For **full access**: `Storage Blob Data Contributor` + `Storage Queue Data Contributor` + `Storage Table Data Contributor`

> **Note**: Storage roles can be scoped to individual storage accounts or containers for fine-grained access.

---

### 👥 Entra ID (18 tools)

Entra ID tools use **Microsoft Graph API**, not Azure RBAC. Permissions are configured as **Application permissions** on an App Registration or Managed Identity.

| Tool | Graph Permission | Notes |
|------|-----------------|-------|
| `entraid_user_list` | `User.Read.All` | |
| `entraid_user_get` | `User.Read.All` | |
| `entraid_user_manager` | `User.Read.All` | |
| `entraid_user_directreports` | `User.Read.All` | |
| `entraid_user_memberof` | `User.Read.All`, `GroupMember.Read.All` | |
| `entraid_user_licenses` | `User.Read.All` | |
| `entraid_group_list` | `Group.Read.All` | |
| `entraid_group_get` | `Group.Read.All` | |
| `entraid_group_members` | `GroupMember.Read.All` | |
| `entraid_group_owners` | `GroupMember.Read.All` | |
| `entraid_app_list` | `Application.Read.All` | |
| `entraid_app_get` | `Application.Read.All` | |
| `entraid_serviceprincipal_list` | `Application.Read.All` | |
| `entraid_serviceprincipal_get` | `Application.Read.All` | |
| `entraid_directory_roles` | `RoleManagement.Read.Directory` | |
| `entraid_role_assignments` | `RoleManagement.Read.Directory` | |
| `entraid_signin_logs` | `AuditLog.Read.All` | **Requires Entra ID P1/P2 license** |
| `entraid_audit_logs` | `AuditLog.Read.All` | **Requires Entra ID P1/P2 license** |

#### Minimum Permission Sets

**Basic directory access** (14 tools):
- `User.Read.All`
- `Group.Read.All`
- `GroupMember.Read.All`
- `Application.Read.All`

**Full access including security** (all 18 tools):
- All of the above, plus:
- `RoleManagement.Read.Directory`
- `AuditLog.Read.All` *(requires P1/P2 license)*

#### Setting Up Graph Permissions

See [Authentication Guide](authentication.md#microsoft-graph-permissions-entra-id-tools) for detailed setup instructions, including:
- Azure Portal (App Registration) method
- Azure CLI (Managed Identity) method
- App Role IDs for CLI assignment
- Quick setup script

---

### 📈 Monitor (17 tools)

| Tool | Required Role | Scope |
|------|--------------|-------|
| `monitor_metrics_query` | `Monitoring Reader` | Subscription |
| `monitor_metric_definitions_list` | `Monitoring Reader` | Subscription |
| `monitor_metric_baselines_get` | `Monitoring Reader` | Subscription |
| `monitor_alerts_list` | `Monitoring Reader` | Subscription |
| `monitor_alert_rule_get` | `Monitoring Reader` | Subscription |
| `monitor_action_groups_list` | `Monitoring Reader` | Subscription |
| `monitor_activity_log_query` | `Monitoring Reader` | Subscription |
| `monitor_diagnostic_settings_list` | `Monitoring Reader` | Subscription |
| `monitor_data_collection_rules_list` | `Monitoring Reader` | Subscription |
| `monitor_autoscale_settings_list` | `Monitoring Reader` | Subscription |
| `monitor_autoscale_settings_get` | `Monitoring Reader` | Subscription |
| `monitor_scheduled_query_rules_list` | `Monitoring Reader` | Subscription |
| `monitor_workspace_list` | `Monitoring Reader` | Subscription |
| `monitor_logs_query` | `Log Analytics Reader` | Log Analytics Workspace |
| `monitor_logs_query_resource` | `Log Analytics Reader` | Log Analytics Workspace |
| `monitor_logs_batch_query` | `Log Analytics Reader` | Log Analytics Workspace |
| `monitor_alerts_list` | `Monitoring Reader` | Subscription |

> **Important**: Log queries (`monitor_logs_query`, `monitor_logs_query_resource`, `monitor_logs_batch_query`) require `Log Analytics Reader` on the target workspace, not just `Monitoring Reader`.

---

### 🔬 Application Insights (8 tools)

| Tool | Required Role | Scope |
|------|--------------|-------|
| `appinsights_get` | `Monitoring Reader` | Subscription |
| `appinsights_list` | `Monitoring Reader` | Subscription |
| `appinsights_query` | `Log Analytics Reader` | App Insights Resource / Workspace |
| `appinsights_traces_query` | `Log Analytics Reader` | App Insights Resource / Workspace |
| `appinsights_exceptions_query` | `Log Analytics Reader` | App Insights Resource / Workspace |
| `appinsights_requests_query` | `Log Analytics Reader` | App Insights Resource / Workspace |
| `appinsights_dependencies_query` | `Log Analytics Reader` | App Insights Resource / Workspace |
| `appinsights_events_query` | `Log Analytics Reader` | App Insights Resource / Workspace |

> **Note**: For workspace-based App Insights resources, `Log Analytics Reader` must be assigned on the linked Log Analytics workspace.

---

### 🔑 RBAC (8 tools)

| Tool | Required Role | Scope | Notes |
|------|--------------|-------|-------|
| `rbac_role_list` | `Reader` | Subscription | List role definitions |
| `rbac_role_get` | `Reader` | Subscription | Get role definition |
| `rbac_assignment_list` | `Reader` | Subscription | List role assignments |
| `rbac_assignment_create` | `Role Based Access Control Administrator` | Target scope | **Write operation** |
| `rbac_assignment_delete` | `Role Based Access Control Administrator` | Target scope | **Write operation** |
| `rbac_allowed_list` | — | — | Returns RBAC whitelist (no Azure call) |
| `rbac_approle_list` | — | `Application.Read.All` | Microsoft Graph API |
| `rbac_approle_grant` | — | `AppRoleAssignment.ReadWrite.All` | Microsoft Graph API, **write operation** |

> **Security Note**: The RBAC tools have built-in security whitelists that prevent assigning dangerous roles like `Owner`, `Contributor`, and `User Access Administrator`. Only data-plane roles from the whitelist can be assigned. See [RBAC Security Whitelists](#rbac-security-whitelists) below.

---

### 📱 Communication Services (7 tools)

| Tool | Access Method | Notes |
|------|-------------|-------|
| `communication_resource_list` | `Reader` (Azure RBAC) | Lists resources via Resource Graph |
| `communication_resource_get` | `Reader` (Azure RBAC) | Gets resource details via Resource Graph |
| `communication_phonenumber_list` | Connection String | Data plane, extracted from resource |
| `communication_phonenumber_get` | Connection String | Data plane, extracted from resource |
| `communication_sms_send` | Connection String | Data plane, **write operation** |
| `communication_email_send` | Connection String | Data plane, **write operation** |
| `communication_email_status` | Connection String | Data plane |

> **Note**: Communication Services data plane operations use connection strings extracted from the resource, not Azure RBAC. The identity needs `Reader` to discover resources, plus `Contributor` on the Communication Services resource to retrieve connection keys, or alternatively use connection strings directly.

---

### 🔎 Azure AI Search (12 tools)

| Tool | Required Role | Scope |
|------|--------------|-------|
| `search_service_list` | `Reader` | Subscription |
| `search_service_get` | `Reader` | Subscription |
| `search_index_list` | `Search Index Data Reader` | Search Service |
| `search_index_get` | `Search Index Data Reader` | Search Service |
| `search_index_stats` | `Search Index Data Reader` | Search Service |
| `search_query` | `Search Index Data Reader` | Search Service |
| `search_suggest` | `Search Index Data Reader` | Search Service |
| `search_autocomplete` | `Search Index Data Reader` | Search Service |
| `search_document_get` | `Search Index Data Reader` | Search Service |
| `search_document_upload` | `Search Index Data Contributor` | Search Service |
| `search_document_merge` | `Search Index Data Contributor` | Search Service |
| `search_document_delete` | `Search Index Data Contributor` | Search Service |

> **Important**: Search data plane roles must be scoped to the **individual Search Service**, not at subscription level. Use the full resource ID as scope:
> ```
> /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Search/searchServices/<name>
> ```

---

## RBAC Security Whitelists

The RBAC tools enforce security whitelists to prevent privilege escalation.

### Allowed Azure RBAC Roles (for assignment)

Only these data-plane roles can be assigned via `rbac_assignment_create`:

| Category | Roles |
|----------|-------|
| **Storage** | Storage Blob Data Reader, Storage Blob Data Contributor, Storage Blob Data Owner, Storage Queue Data Reader, Storage Queue Data Contributor, Storage Queue Data Message Processor, Storage Queue Data Message Sender, Storage Table Data Reader, Storage Table Data Contributor, Storage File Data SMB Share Reader, Storage File Data SMB Share Contributor |
| **Cosmos DB** | Cosmos DB Account Reader Role, Cosmos DB Built-in Data Reader, Cosmos DB Built-in Data Contributor, DocumentDB Account Contributor |
| **Key Vault** | Key Vault Reader, Key Vault Secrets User, Key Vault Secrets Officer, Key Vault Crypto User, Key Vault Crypto Officer, Key Vault Certificates Officer |
| **Search** | Search Index Data Reader, Search Index Data Contributor, Search Service Contributor |
| **Cost** | Cost Management Reader, Cost Management Contributor |
| **Monitor** | Monitoring Reader, Monitoring Contributor, Log Analytics Reader, Log Analytics Contributor |
| **General** | Reader |

### Blocked Roles (cannot be assigned)

- `Owner`
- `Contributor`
- `User Access Administrator`
- `Role Based Access Control Administrator`

### Allowed Graph Permissions (for app role grant)

Only these Microsoft Graph permissions can be granted via `rbac_approle_grant`:

- `User.Read.All`, `User.ReadBasic.All`
- `Group.Read.All`, `GroupMember.Read.All`
- `Application.Read.All`
- `Directory.Read.All`
- `ServicePrincipalEndpoint.Read.All`
- `RoleManagement.Read.Directory`
- `AuditLog.Read.All`

---

## Quick Setup Scripts

### Assign All Azure RBAC Roles (Subscription Level)

```bash
#!/bin/bash
# Assign minimum RBAC roles for the MCP server
# Usage: ./assign-rbac-roles.sh <principal-id> <subscription-id>

IDENTITY="$1"
SUB="/subscriptions/$2"

echo "Assigning RBAC roles..."

# Core - Required for Resource Graph queries
az role assignment create --assignee "$IDENTITY" --role "Reader" --scope "$SUB"

# Cost Management
az role assignment create --assignee "$IDENTITY" --role "Cost Management Reader" --scope "$SUB"

# Storage (use Contributor for write access, Reader for read-only)
az role assignment create --assignee "$IDENTITY" --role "Storage Blob Data Contributor" --scope "$SUB"
az role assignment create --assignee "$IDENTITY" --role "Storage Table Data Contributor" --scope "$SUB"
az role assignment create --assignee "$IDENTITY" --role "Storage Queue Data Reader" --scope "$SUB"

# Monitor + App Insights
az role assignment create --assignee "$IDENTITY" --role "Monitoring Reader" --scope "$SUB"
az role assignment create --assignee "$IDENTITY" --role "Log Analytics Reader" --scope "$SUB"

# Cosmos DB (control plane only - data plane requires per-account setup)
az role assignment create --assignee "$IDENTITY" --role "Cosmos DB Account Reader Role" --scope "$SUB"

echo "Done! Remember to also set up:"
echo "  - Cosmos DB data plane roles (per account): ./scripts/assign-cosmos-data-roles.sh $IDENTITY"
echo "  - Search roles (per service): az role assignment create --assignee $IDENTITY --role 'Search Index Data Reader' --scope <search-service-id>"
echo "  - Graph permissions (for Entra ID): see docs/authentication.md"
```

### Assign Cosmos DB Data Plane Roles

Use the provided script to assign Cosmos DB data plane roles to all accounts:

```bash
./scripts/assign-cosmos-data-roles.sh <principal-id>
```

See [Cosmos DB section](#️-cosmos-db-12-tools) for custom role requirements.

### Assign Graph Permissions (Entra ID)

See [Authentication Guide — Graph Permissions](authentication.md#microsoft-graph-permissions-entra-id-tools) for the full setup script.

---

## Least Privilege Summary

### Read-Only Access (84 read tools)

| Role | Scope | Covers |
|------|-------|--------|
| `Reader` | Subscription | Resource Graph, account listings |
| `Cost Management Reader` | Subscription | Cost tools |
| `Storage Blob Data Reader` | Subscription/Account | Blob read tools |
| `Storage Table Data Reader` | Subscription/Account | Table query |
| `Storage Queue Data Reader` | Subscription/Account | Queue listing |
| `Monitoring Reader` | Subscription | Monitor metrics, alerts |
| `Log Analytics Reader` | Subscription/Workspace | Log queries, App Insights queries |
| `Cosmos DB Account Reader Role` | Subscription | Account listing |
| `Cosmos DB Built-in Data Reader` | Per Account | Cosmos read tools |
| `Search Index Data Reader` | Per Search Service | Search read tools |
| **Graph**: `User.Read.All` | Tenant | Entra ID user tools |
| **Graph**: `Group.Read.All` | Tenant | Entra ID group tools |
| **Graph**: `GroupMember.Read.All` | Tenant | Group members/owners |
| **Graph**: `Application.Read.All` | Tenant | App/SP tools |

### Full Access (all 99 tools)

All read-only roles above, plus:

| Role | Scope | Covers |
|------|-------|--------|
| `Storage Blob Data Contributor` | Subscription/Account | Blob write/delete |
| `Storage Table Data Contributor` | Subscription/Account | Table write |
| `Storage Queue Data Contributor` | Subscription/Account | Queue write |
| `Cosmos DB Built-in Data Contributor` | Per Account | Container/item CRUD |
| Custom `Cosmos DB Database Manager` | Per Account | Database create/delete |
| `Search Index Data Contributor` | Per Search Service | Document write |
| **Graph**: `RoleManagement.Read.Directory` | Tenant | Directory roles |
| **Graph**: `AuditLog.Read.All` | Tenant | Sign-in/audit logs (P1/P2) |

---

## Important Considerations

### 1. Cosmos DB Custom Role Requirement

The Cosmos DB Built-in Data Contributor does **not** support database-level operations (`sqlDatabases/write`, `sqlDatabases/delete`). If you need `cosmos_database_create` and `cosmos_database_delete`, you **must** create a custom Cosmos DB data plane role. See the [Cosmos DB section](#️-cosmos-db-12-tools) for instructions.

### 2. Entra ID P1/P2 License

The `entraid_signin_logs` and `entraid_audit_logs` tools require an **Entra ID P1 or P2 license**. Without it, these tools will return a license requirement error.

### 3. Search Per-Service Scoping

Azure AI Search data plane roles (`Search Index Data Reader/Contributor`) must be scoped to individual search services. Subscription-level assignment is not supported for data plane access.

### 4. Communication Services Access

Communication Services data plane operations use connection strings, not Azure RBAC tokens. The identity needs enough Azure RBAC access to list resources and retrieve keys.

### 5. Log Analytics Workspace Access

Monitor and App Insights log query tools require `Log Analytics Reader` on the target Log Analytics workspace. This is separate from `Monitoring Reader`, which only covers metrics and alerts.

### 6. RBAC Tool Paradox

The RBAC tools (`rbac_assignment_create`, `rbac_assignment_delete`) require `Role Based Access Control Administrator` to operate, but this role is in the blocked list. This is by design — the MCP identity cannot assign these roles to itself. An administrator must pre-assign them.
