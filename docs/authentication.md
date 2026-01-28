# Authentication

This document explains how authentication works in Azure MCP Server.

## Overview

Azure MCP Server uses the Azure Identity SDK with a **unified credential chain** that works seamlessly in both development and production environments. No configuration is needed - the same code works on your laptop and in Azure Container Apps.

## Credential Chain

The server uses `ChainedTokenCredential` which tries these methods in order:

| Priority | Credential | When Used |
|----------|------------|----------|
| 1 | **EnvironmentCredential** | CI/CD pipelines, explicit service principal configuration |
| 2 | **ManagedIdentityCredential** | Azure Container Apps, VMs, App Service, Functions |
| 3 | **VisualStudioCodeCredential** | VS Code with Azure extension |
| 4 | **AzureCliCredential** | Local development after `az login` |

The first credential that succeeds is used. This means:
- **In production** (Container Apps, VMs): Uses Managed Identity automatically
- **In development** (your laptop): Uses Azure CLI or VS Code credentials

### Local Development

```bash
# Login with Azure CLI
az login

# Optionally set a specific subscription
az account set --subscription "My Subscription"
```

## Usage in Code

### Getting a Credential

```python
from azure_mcp.core.auth import CredentialProvider

# Get default credential (unified chain)
credential = CredentialProvider.get_credential()

# Get credential for specific tenant
credential = CredentialProvider.get_credential(tenant_id="my-tenant-guid")
```

### In Services

Services automatically get credentials through the base class:

```python
class MyService(AzureService):
    async def do_something(self):
        credential = self.get_credential()
        client = SomeAzureClient(credential)
        # ...
```

## Tenant Support

For multi-tenant scenarios, pass the tenant ID:

```python
credential = CredentialProvider.get_credential(tenant_id="tenant-guid")
```

## Environment Variables

These environment variables affect authentication:

| Variable | Description |
|----------|-------------|
| `AZURE_CLIENT_ID` | Service principal client ID, or user-assigned managed identity client ID |
| `AZURE_CLIENT_SECRET` | Service principal secret |
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Default subscription ID |
| `AZURE_AUTHORITY_HOST` | Authority host URL (for sovereign clouds) |

## Managed Identity

For Azure-hosted workloads (Container Apps, VMs, App Service), managed identity is used automatically:

```python
# System-assigned managed identity (automatic)
# Just deploy to Azure and it works - no configuration needed

# User-assigned managed identity
# Set AZURE_CLIENT_ID environment variable to the managed identity's client ID
```

### Container Apps Example

When deploying to Azure Container Apps:

1. Enable system-assigned managed identity on the Container App
2. Assign appropriate RBAC roles to the identity
3. The server automatically uses the managed identity - no code changes needed

See [AI Foundry Deployment Guide](ai-foundry-deployment.md) for detailed RBAC setup.

## Microsoft Graph Permissions (Entra ID Tools)

The Entra ID tools require **Microsoft Graph API permissions**. These are configured on the App Registration, not via Azure RBAC.

### Required Permissions by Tool

| Tool | Permission (Application) | Notes |
|------|--------------------------|-------|
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
| `entraid_signin_logs` | `AuditLog.Read.All` | **Requires P1/P2 license** |
| `entraid_audit_logs` | `AuditLog.Read.All` | **Requires P1/P2 license** |

### Setting Up Graph Permissions

#### Option 1: Via Azure Portal (App Registration)

1. **In Azure Portal**: Go to App Registrations → Your App → API Permissions
2. **Add Permission**: Microsoft Graph → Application permissions
3. **Grant Admin Consent**: Required for application permissions

#### Option 2: Via Azure CLI (Managed Identity)

For **Managed Identities** (Container Apps, VMs, App Service), use the Azure CLI to assign Graph permissions:

```bash
# 1. Get your Managed Identity's Principal ID
PRINCIPAL_ID=$(az containerapp show \
  --name <your-container-app> \
  --resource-group <your-rg> \
  --query "identity.principalId" -o tsv)

# 2. Get Microsoft Graph's Service Principal ID
GRAPH_SP_ID=$(az ad sp list \
  --filter "appId eq '00000003-0000-0000-c000-000000000000'" \
  --query "[0].id" -o tsv)

# 3. Assign permissions using the App Role IDs below
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/${PRINCIPAL_ID}/appRoleAssignments" \
  --headers "Content-Type=application/json" \
  --body "{\"principalId\":\"${PRINCIPAL_ID}\",\"resourceId\":\"${GRAPH_SP_ID}\",\"appRoleId\":\"<APP_ROLE_ID>\"}"
```

### Microsoft Graph App Role IDs

Use these GUIDs when assigning permissions via Azure CLI:

| Permission | App Role ID |
|------------|-------------|
| `User.Read.All` | `df021288-bdef-4463-88db-98f22de89214` |
| `Group.Read.All` | `5b567255-7703-4780-807c-7be8301ae99b` |
| `GroupMember.Read.All` | `98830695-27a2-44f7-8c18-0c3ebc9698f6` |
| `Application.Read.All` | `9a5d68dd-52b0-4cc2-bd40-abcf44ac3a30` |
| `RoleManagement.Read.Directory` | `483bed4a-2ad3-4361-a73b-c83ccdbdc53c` |
| `AuditLog.Read.All` | `b0afded3-3588-46d8-8b3d-9842eff778da` |

#### Quick Setup Script

Assign all required permissions at once:

```bash
#!/bin/bash
PRINCIPAL_ID="<your-managed-identity-principal-id>"
GRAPH_SP_ID="<microsoft-graph-sp-id>"

# All required App Role IDs
declare -A PERMISSIONS=(
  ["User.Read.All"]="df021288-bdef-4463-88db-98f22de89214"
  ["Group.Read.All"]="5b567255-7703-4780-807c-7be8301ae99b"
  ["GroupMember.Read.All"]="98830695-27a2-44f7-8c18-0c3ebc9698f6"
  ["Application.Read.All"]="9a5d68dd-52b0-4cc2-bd40-abcf44ac3a30"
  ["RoleManagement.Read.Directory"]="483bed4a-2ad3-4361-a73b-c83ccdbdc53c"
  ["AuditLog.Read.All"]="b0afded3-3588-46d8-8b3d-9842eff778da"
)

for name in "${!PERMISSIONS[@]}"; do
  role_id="${PERMISSIONS[$name]}"
  echo "Assigning ${name}..."
  az rest --method POST \
    --uri "https://graph.microsoft.com/v1.0/servicePrincipals/${PRINCIPAL_ID}/appRoleAssignments" \
    --headers "Content-Type=application/json" \
    --body "{\"principalId\":\"${PRINCIPAL_ID}\",\"resourceId\":\"${GRAPH_SP_ID}\",\"appRoleId\":\"${role_id}\"}" \
    2>&1 | grep -q "already exists" && echo "  Already assigned" || echo "  Assigned"
done
```

#### Verify Assigned Permissions

```bash
az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/${PRINCIPAL_ID}/appRoleAssignments" \
  --query "value[].appRoleId" -o json
```

### License Requirements

⚠️ **Sign-in logs and audit logs require Entra ID P1 or P2 license.**

If you attempt to use these tools without the appropriate license, you'll receive an error message explaining the requirement:

```
This operation requires an Entra ID P1 or P2 license.
Sign-in logs and audit logs are premium features.
See: https://learn.microsoft.com/en-us/entra/identity/monitoring-health/concept-sign-ins
```

### Minimum Permission Sets

For read-only directory access (most common):
- `User.Read.All`
- `Group.Read.All`
- `GroupMember.Read.All`
- `Application.Read.All`

For security auditing (requires P1/P2):
- All of the above, plus:
- `RoleManagement.Read.Directory`
- `AuditLog.Read.All`

## Troubleshooting

### "No credential available"

1. Check if you're logged in: `az account show`
2. Try logging in again: `az login`
3. Verify environment variables if using service principal

### "Access denied" or "Forbidden"

1. Check RBAC permissions on the target resource
2. Verify you're using the correct subscription
3. Check if the operation requires specific roles
4. For Cosmos DB data operations, ensure Data Contributor role is assigned per account
5. For Entra ID tools, ensure Microsoft Graph permissions are granted and admin consent is given

### Microsoft Graph "Insufficient privileges"

1. Verify the app has the required Graph permissions
2. Check that admin consent was granted
3. For `signin_logs` and `audit_logs`, verify you have Entra ID P1/P2 license

### Multi-tenant Issues

1. Ensure you're logged into the correct tenant: `az login --tenant <tenant-id>`
2. Pass the tenant ID explicitly in code: `CredentialProvider.get_credential(tenant_id="...")`
