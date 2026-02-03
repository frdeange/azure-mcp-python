# 🔷 Azure MCP Server (Python)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP 1.0](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io/)
[![Azure](https://img.shields.io/badge/Azure-Ready-0078D4.svg)](https://azure.microsoft.com/)

A powerful **Python implementation** of the Model Context Protocol (MCP) server for Azure services. Enables AI assistants like **GitHub Copilot**, **Claude**, **GPT-4**, and others to interact with Azure resources seamlessly.

---

## ✨ Highlights

| Feature | Description |
|---------|-------------|
| 🔐 **Secure Authentication** | Azure Identity with DefaultAzureCredential chain |
| 🛠️ **94 Azure Tools** | Comprehensive coverage across 10 Azure service families |
| 💰 **Cost Management** | Query costs, forecasts, budgets *(NOT in Microsoft's .NET version)* |
| 👥 **Entra ID** | Users, groups, apps via Microsoft Graph *(NOT in Microsoft's .NET version)* |
| 📱 **Communication Services** | SMS, Email, Phone Numbers *(NOT in Microsoft's .NET version)* |
| 🔎 **Azure AI Search** | Full-text search, indexing, document management *(NOT in Microsoft's .NET version)* |
| ☁️ **AI Foundry Ready** | Compatible with Azure AI Foundry Agent Service |
| 🧩 **Modular Design** | Install only the Azure services you need |
| 📚 **Well Documented** | Comprehensive guides for users and contributors |

---

## 🚀 Quick Start

### Installation

\`\`\`bash
# Base installation
pip install azure-mcp

# With specific services
pip install azure-mcp[cosmos,cost,storage]

# With all services
pip install azure-mcp[all]
\`\`\`

### Usage with VS Code

Add to your VS Code \`settings.json\`:

\`\`\`json
{
  "mcp.servers": {
    "azure": {
      "command": "azure-mcp",
      "args": ["--stdio"]
    }
  }
}
\`\`\`

### Authentication

\`\`\`bash
# Login to Azure
az login

# Run the server
azure-mcp
\`\`\`

---

## 🛠️ Available Tools (94 Total)

### 📊 Summary

| Family | Tools | Read | Write | Description |
|--------|-------|------|-------|-------------|
| 🔍 Resource Graph | 1 | 1 | 0 | Query Azure resources with KQL |
| 🗄️ Cosmos DB | 7 | 6 | 1 | Database, container, and item operations |
| 💰 Cost Management | 7 | 7 | 0 | Costs, forecasts, budgets, recommendations |
| 📦 Storage | 9 | 6 | 3 | Blobs, queues, tables, accounts |
| 👥 Entra ID | 18 | 18 | 0 | Users, groups, apps, service principals |
| 📈 Monitor | 17 | 17 | 0 | Metrics, alerts, logs, autoscale |
| 🔬 App Insights | 8 | 8 | 0 | Logs, metrics, availability, exceptions |
| 🔑 RBAC | 8 | 8 | 0 | Roles, assignments, permissions |
| 📱 Communication | 7 | 4 | 3 | SMS, Email, Phone Numbers |
| 🔎 Azure AI Search | 12 | 9 | 3 | Full-text search, indexing, documents |
| **Total** | **94** | **84** | **10** | |

---

<details>
<summary><h3>🔍 Resource Graph (1 tool)</h3></summary>

| Tool | Type | Description |
|------|------|-------------|
| \`resourcegraph_query\` | 📖 Read | Execute Azure Resource Graph queries using KQL |

**Example:**
\`\`\`
Query all virtual machines in my subscription
\`\`\`

</details>

<details>
<summary><h3>🗄️ Cosmos DB (7 tools)</h3></summary>

| Tool | Type | Description |
|------|------|-------------|
| \`cosmos_account_list\` | 📖 Read | List Cosmos DB accounts in a subscription |
| \`cosmos_account_get\` | 📖 Read | Get details of a specific Cosmos DB account |
| \`cosmos_database_list\` | 📖 Read | List databases in a Cosmos DB account |
| \`cosmos_database_get\` | 📖 Read | Get database details and throughput info |
| \`cosmos_container_list\` | 📖 Read | List containers in a database |
| \`cosmos_container_get\` | 📖 Read | Get container details including partition key |
| \`cosmos_item_query\` | 📖 Read | Query items using SQL-like syntax |

**Example:**
\`\`\`
List all Cosmos DB accounts in my production subscription
Query items from the users container where status = 'active'
\`\`\`

</details>

<details>
<summary><h3>💰 Cost Management (7 tools) ⭐ Exclusive</h3></summary>

> 🌟 **Not available in Microsoft's .NET Azure MCP Server!**

| Tool | Type | Description |
|------|------|-------------|
| `cost_query` | 📖 Read | Query cost and usage data with flexible grouping |
| `cost_forecast` | 📖 Read | Get cost forecasts for future periods |
| `cost_usage_by_resource` | 📖 Read | Get detailed usage data by resource |
| `cost_budgets_list` | 📖 Read | List all budgets in a scope |
| `cost_budgets_get` | 📖 Read | Get budget details including alerts |
| `cost_recommendations` | 📖 Read | List Azure Advisor cost recommendations |
| \`cost_exports_list\` | 📖 Read | List scheduled cost exports |

**Example:**
\`\`\`
Show me the cost breakdown by service for the last month
What's the forecasted cost for my subscription this quarter?
List all budgets that are over 80% consumed
\`\`\`

</details>

<details>
<summary><h3>📦 Storage (9 tools)</h3></summary>

| Tool | Type | Description |
|------|------|-------------|
| \`storage_account_list\` | 📖 Read | List storage accounts in a subscription |
| \`storage_account_get\` | 📖 Read | Get storage account details |
| \`storage_container_list\` | 📖 Read | List blob containers |
| \`storage_blob_list\` | 📖 Read | List blobs in a container |
| \`storage_blob_read\` | 📖 Read | Read blob content |
| \`storage_blob_write\` | ✏️ Write | Write content to a blob |
| `storage_blob_delete` | ✏️ Write | Delete a blob from a container |
| `storage_queue_list` | 📖 Read | List queues in a storage account |
| \`storage_table_query\` | 📖 Read | Query table entities |

**Example:**
\`\`\`
List all blobs in the 'documents' container
Read the config.json file from my storage account
\`\`\`

</details>

<details>
<summary><h3>👥 Entra ID (18 tools) ⭐ Exclusive</h3></summary>

> 🌟 **Not available in Microsoft's .NET Azure MCP Server!**

| Tool | Type | Description |
|------|------|-------------|
| \`entraid_user_list\` | 📖 Read | List users in the directory |
| \`entraid_user_get\` | 📖 Read | Get user details by ID or UPN |
| \`entraid_user_groups\` | 📖 Read | List groups a user belongs to |
| \`entraid_user_manager\` | 📖 Read | Get user's manager |
| \`entraid_user_direct_reports\` | 📖 Read | List user's direct reports |
| \`entraid_group_list\` | 📖 Read | List groups in the directory |
| \`entraid_group_get\` | 📖 Read | Get group details |
| \`entraid_group_members\` | 📖 Read | List group members |
| \`entraid_group_owners\` | 📖 Read | List group owners |
| \`entraid_app_list\` | 📖 Read | List app registrations |
| \`entraid_app_get\` | 📖 Read | Get app registration details |
| \`entraid_sp_list\` | 📖 Read | List service principals |
| \`entraid_sp_get\` | 📖 Read | Get service principal details |
| \`entraid_role_list\` | 📖 Read | List directory roles |
| \`entraid_role_members\` | 📖 Read | List role members |
| \`entraid_domain_list\` | 📖 Read | List verified domains |
| \`entraid_device_list\` | 📖 Read | List registered devices |
| \`entraid_device_get\` | 📖 Read | Get device details |

**Example:**
\`\`\`
Find all users in the Sales department
List members of the 'IT Admins' group
Show me all app registrations created this year
\`\`\`

</details>

<details>
<summary><h3>📈 Monitor (17 tools)</h3></summary>

| Tool | Type | Description |
|------|------|-------------|
| \`monitor_metrics_list\` | 📖 Read | List available metrics for a resource |
| \`monitor_metrics_get\` | 📖 Read | Get metric values with aggregations |
| \`monitor_alerts_list\` | 📖 Read | List metric alert rules |
| \`monitor_alerts_get\` | 📖 Read | Get alert rule details |
| \`monitor_alerts_history\` | 📖 Read | Get alert history/incidents |
| \`monitor_action_groups_list\` | 📖 Read | List action groups |
| \`monitor_action_groups_get\` | 📖 Read | Get action group details |
| \`monitor_activity_log\` | 📖 Read | Query activity log events |
| \`monitor_diagnostic_settings_list\` | 📖 Read | List diagnostic settings |
| \`monitor_diagnostic_settings_get\` | 📖 Read | Get diagnostic setting details |
| \`monitor_log_profiles_list\` | 📖 Read | List log profiles |
| \`monitor_autoscale_list\` | 📖 Read | List autoscale settings |
| \`monitor_autoscale_get\` | 📖 Read | Get autoscale setting details |
| \`monitor_scheduled_query_rules_list\` | 📖 Read | List log alert rules |
| \`monitor_scheduled_query_rules_get\` | 📖 Read | Get log alert rule details |
| \`monitor_private_link_scopes_list\` | 📖 Read | List private link scopes |

**Example:**
\`\`\`
Show CPU metrics for my VM over the last hour
List all firing alerts in my subscription
Get the activity log for resource group changes
\`\`\`

</details>

<details>
<summary><h3>🔬 Application Insights (8 tools)</h3></summary>

| Tool | Type | Description |
|------|------|-------------|
| \`appinsights_query\` | 📖 Read | Execute KQL queries against App Insights |
| \`appinsights_metrics_list\` | 📖 Read | List available metrics |
| \`appinsights_metrics_get\` | 📖 Read | Get metric values |
| \`appinsights_events\` | 📖 Read | Query telemetry events |
| \`appinsights_exceptions\` | 📖 Read | Query exception telemetry |
| \`appinsights_availability\` | 📖 Read | Query availability test results |
| \`appinsights_components_list\` | 📖 Read | List App Insights resources |
| \`appinsights_components_get\` | 📖 Read | Get App Insights resource details |

**Example:**
\`\`\`
Query the top 10 slowest requests in the last 24 hours
Show me all exceptions from the payment service
Check availability test results for my API
\`\`\`

</details>

<details>
<summary><h3>🔑 RBAC (8 tools)</h3></summary>

| Tool | Type | Description |
|------|------|-------------|
| \`rbac_role_definitions_list\` | 📖 Read | List role definitions in a scope |
| \`rbac_role_definitions_get\` | 📖 Read | Get role definition details |
| \`rbac_role_assignments_list\` | 📖 Read | List role assignments |
| \`rbac_role_assignments_get\` | 📖 Read | Get role assignment details |
| \`rbac_permissions_list\` | 📖 Read | List permissions for a scope |
| \`rbac_classic_admins_list\` | 📖 Read | List classic subscription admins |
| \`rbac_deny_assignments_list\` | 📖 Read | List deny assignments |
| \`rbac_deny_assignments_get\` | 📖 Read | Get deny assignment details |

**Example:**
\`\`\`
List all Contributor role assignments in my subscription
Who has Owner access to this resource group?
Show me the permissions for the Storage Blob Data Reader role
\`\`\`

</details>

<details>
<summary><h3>📱 Communication Services (7 tools) ⭐ Exclusive</h3></summary>

> 🌟 **Not available in Microsoft's .NET Azure MCP Server!**

| Tool | Type | Description |
|------|------|-------------|
| \`communication_resource_list\` | 📖 Read | List Communication Services resources |
| \`communication_resource_get\` | 📖 Read | Get resource details including endpoints |
| \`communication_phonenumber_list\` | 📖 Read | List purchased phone numbers |
| \`communication_phonenumber_get\` | 📖 Read | Get phone number details and capabilities |
| \`communication_sms_send\` | ✏️ Write | Send SMS messages |
| \`communication_email_send\` | ✏️ Write | Send emails with HTML/text content |
| \`communication_email_status\` | 📖 Read | Check email delivery status |

**Example:**
\`\`\`
List all phone numbers in my Communication Services resource
Send an SMS notification to +1234567890
Send a welcome email to new users
Check the status of email message abc-123
\`\`\`

</details>

<details>
<summary><h3>🔎 Azure AI Search (12 tools) ⭐ Exclusive</h3></summary>

> 🌟 **Not available in Microsoft's .NET Azure MCP Server!**

| Tool | Type | Description |
|------|------|-------------|
| \`search_service_list\` | 📖 Read | List Azure AI Search services |
| \`search_service_get\` | 📖 Read | Get search service details |
| \`search_index_list\` | 📖 Read | List indexes in a search service |
| \`search_index_get\` | 📖 Read | Get index schema and settings |
| \`search_index_stats\` | 📖 Read | Get index statistics (document count, size) |
| \`search_query\` | 📖 Read | Execute full-text search queries |
| \`search_suggest\` | 📖 Read | Get search suggestions |
| \`search_autocomplete\` | 📖 Read | Get autocomplete suggestions |
| \`search_document_get\` | 📖 Read | Retrieve a document by key |
| \`search_document_upload\` | ✏️ Write | Upload documents to an index |
| \`search_document_merge\` | ✏️ Write | Merge/update documents in an index |
| \`search_document_delete\` | ✏️ Write | Delete documents from an index |

**Example:**
\`\`\`
Search for "machine learning" in my knowledge base
Get the schema of my products index
Upload new documents to the search index
Find all search services in my subscription
\`\`\`

</details>

---

## 🌐 Deployment Options

### Local Development

\`\`\`bash
# Clone and install
git clone https://github.com/frdeange/azure-mcp-python.git
cd azure-mcp-python
pip install -e ".[dev,all]"

# Run
azure-mcp
\`\`\`

### Docker

\`\`\`bash
docker build -t azure-mcp .
docker run -it azure-mcp
\`\`\`

### Azure Container Apps

See [AI Foundry Deployment Guide](docs/ai-foundry-deployment.md) for deploying to Azure AI Foundry Agent Service.

\`\`\`bash
# Deploy to Azure Container Apps
az containerapp up \\
  --name azure-mcp-server \\
  --source . \\
  --ingress external \\
  --target-port 8000
\`\`\`

---

## 📦 Modular Installation

Install only the Azure services you need:

\`\`\`bash
# Individual services
pip install azure-mcp[cosmos]          # Cosmos DB tools
pip install azure-mcp[cost]            # Cost Management tools
pip install azure-mcp[storage]         # Storage tools
pip install azure-mcp[entra]           # Entra ID tools
pip install azure-mcp[monitor]         # Monitor + App Insights tools
pip install azure-mcp[rbac]            # RBAC tools
pip install azure-mcp[communication]   # Communication Services tools
pip install azure-mcp[search]          # Azure AI Search tools

# Multiple services
pip install azure-mcp[cosmos,cost,storage]

# All services
pip install azure-mcp[all]
\`\`\`

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Adding Tools](docs/adding-tools.md) | Guide for implementing new tools |
| [Authentication](docs/authentication.md) | Azure authentication setup |
| [Testing](docs/testing.md) | Testing guide and best practices |
| [AI Foundry Deployment](docs/ai-foundry-deployment.md) | Deploy to Azure AI Foundry |
| [Architecture](ARCHITECTURE.md) | System architecture overview |
| [Contributing](CONTRIBUTING.md) | Contribution guidelines |

---

## 🔧 Development

### Setup

\`\`\`bash
# Clone the repository
git clone https://github.com/frdeange/azure-mcp-python.git
cd azure-mcp-python

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\\Scripts\\activate   # Windows

# Install in development mode with all extras
pip install -e ".[dev,all]"

# Run tests
pytest

# Run linting
ruff check src tests
ruff format src tests

# Type checking
mypy src
\`\`\`

### Using Dev Container

Open in VS Code and click "Reopen in Container" when prompted. Everything is pre-configured!

---

## 🗺️ Roadmap

### ✅ Completed
- [x] Core framework (auth, registry, caching, errors)
- [x] Resource Graph tools
- [x] Cosmos DB tools
- [x] Cost Management tools ⭐
- [x] Storage tools
- [x] Entra ID tools ⭐
- [x] Monitor tools
- [x] Application Insights tools
- [x] RBAC tools
- [x] Communication Services (Phase 1) ⭐
- [x] Azure AI Search tools ⭐

### 🔜 Planned
- [ ] Communication Services (Phase 2: WhatsApp, Chat, Rooms, Call Automation)
- [ ] Key Vault tools
- [ ] Event Grid tools
- [ ] Service Bus tools
- [ ] Cognitive Services tools

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (\`git checkout -b feat/amazing-feature\`)
3. Commit your changes (\`git commit -m 'feat: add amazing feature'\`)
4. Push to the branch (\`git push origin feat/amazing-feature\`)
5. Open a Pull Request

---

## 📄 License

MIT - See [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- [Microsoft Azure MCP Server (.NET)](https://github.com/microsoft/azure-mcp) - Inspiration
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [FastMCP](https://github.com/jlowin/fastmcp) - Python MCP SDK

---

<p align="center">
  Made with ❤️ for the Azure community
</p>
