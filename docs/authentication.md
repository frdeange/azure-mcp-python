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

### Multi-tenant Issues

1. Ensure you're logged into the correct tenant: `az login --tenant <tenant-id>`
2. Pass the tenant ID explicitly in code: `CredentialProvider.get_credential(tenant_id="...")`
