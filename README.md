# Azure MCP Server (Python)

A Python implementation of the Model Context Protocol (MCP) server for Azure services.
Enables AI assistants like GitHub Copilot, Claude, and others to interact with Azure resources.

## Features

- 🔐 **Secure Authentication** - Uses Azure Identity with credential chain
- 🛠️ **45+ Azure Tools** - Storage, Cosmos DB, Key Vault, SQL, Monitor, Cost, Entra ID, and more
- 🧩 **Extensible** - Easy to add new tools
- 📚 **Well Documented** - Comprehensive guides for users and contributors

## Quick Start

### Installation

```bash
pip install azure-mcp
```

With specific Azure services:

```bash
pip install azure-mcp[storage,cosmos,keyvault]
```

With all services:

```bash
pip install azure-mcp[all]
```

### Usage with VS Code

Add to your VS Code settings.json:

```json
{
  "mcp.servers": {
    "azure": {
      "command": "azure-mcp",
      "args": ["--stdio"]
    }
  }
}
```

### Authentication

```bash
# Login to Azure
az login

# Run the server
azure-mcp
```

## Available Tools

| Category | Tools | Description |
|----------|-------|-------------|
| Storage | `storage_account_get`, `storage_blob_get`, ... | Manage Azure Storage |
| Cosmos DB | `cosmos_database_list`, `cosmos_item_query`, ... | Query Cosmos DB |
| Key Vault | `keyvault_secret_get`, `keyvault_key_list`, ... | Manage secrets and keys |
| Cost | `cost_usage_query`, `cost_budget_list`, ... | Azure Cost Management |
| Entra ID | `entra_user_list`, `entra_group_get`, ... | Microsoft Entra ID |
| Monitor | `monitor_log_query`, `monitor_metrics_list`, ... | Azure Monitor |

[See all tools →](docs/tools/)

## Documentation

- [Getting Started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [Authentication](docs/authentication.md)
- [Developing Tools](docs/developing-tools.md)
- [API Reference](docs/api/)

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/azure-mcp-python.git
cd azure-mcp-python

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

### Using Dev Container

Open in VS Code and click "Reopen in Container" when prompted.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT - See [LICENSE](LICENSE)
