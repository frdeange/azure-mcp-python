# Authentication

This document explains how authentication works in Azure MCP Server.

## Overview

Azure MCP Server uses the Azure Identity SDK for authentication. It supports the standard Azure credential chain, which automatically tries multiple authentication methods.

## Credential Chain

### Production (DefaultAzureCredential)

In production, we use `DefaultAzureCredential` which tries these methods in order:

1. **Environment Variables** - `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
2. **Workload Identity** - For Kubernetes workloads
3. **Managed Identity** - For Azure VMs, App Service, Functions
4. **Azure CLI** - Uses `az login` credentials
5. **Azure PowerShell** - Uses `Connect-AzAccount` credentials
6. **Visual Studio Code** - Uses VS Code Azure Account extension
7. **Azure Developer CLI** - Uses `azd auth login` credentials
8. **Interactive Browser** - Opens browser for interactive login

### Development (AzureCliCredential)

For local development, we default to `AzureCliCredential`:

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

# Get default credential
credential = CredentialProvider.get_credential()

# Get credential for specific tenant
credential = CredentialProvider.get_credential(tenant="my-tenant-id")

# Get development credential (CLI-based)
credential = CredentialProvider.get_credential_for_dev()
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
credential = CredentialProvider.get_credential(tenant="tenant-guid")
```

## Environment Variables

These environment variables affect authentication:

| Variable | Description |
|----------|-------------|
| `AZURE_CLIENT_ID` | Service principal client ID |
| `AZURE_CLIENT_SECRET` | Service principal secret |
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Default subscription ID |
| `AZURE_AUTHORITY_HOST` | Authority host URL (for sovereign clouds) |

## Managed Identity

For Azure-hosted workloads, managed identity is preferred:

```python
# System-assigned managed identity (automatic)
# Just deploy to Azure and it works

# User-assigned managed identity
# Set AZURE_CLIENT_ID to the managed identity's client ID
```

## Troubleshooting

### "No credential available"

1. Check if you're logged in: `az account show`
2. Try logging in again: `az login`
3. Verify environment variables if using service principal

### "Access denied" or "Forbidden"

1. Check RBAC permissions on the target resource
2. Verify you're using the correct subscription
3. Check if the operation requires specific roles

### Multi-tenant Issues

1. Ensure you're logged into the correct tenant: `az login --tenant <tenant-id>`
2. Pass the tenant ID explicitly in code
