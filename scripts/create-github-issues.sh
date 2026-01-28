#!/usr/bin/env bash
# Script to create GitHub issues from the planned issue list
# Usage: ./scripts/create-github-issues.sh

set -e

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) is required. Install from: https://cli.github.com/"
    exit 1
fi

# Check if logged in
if ! gh auth status &> /dev/null; then
    echo "Please login with: gh auth login"
    exit 1
fi

echo "Creating GitHub issues for Azure MCP Server (Python)..."
echo ""

# Create labels first
echo "Creating labels..."
gh label create "core" --color "0366d6" --description "Core framework" --force 2>/dev/null || true
gh label create "tool" --color "1d76db" --description "Tool implementation" --force 2>/dev/null || true
gh label create "priority" --color "d93f0b" --description "High priority" --force 2>/dev/null || true
gh label create "storage" --color "c5def5" --description "Azure Storage" --force 2>/dev/null || true
gh label create "cosmos" --color "c5def5" --description "Cosmos DB" --force 2>/dev/null || true
gh label create "cost" --color "fbca04" --description "Cost Management" --force 2>/dev/null || true
gh label create "entraid" --color "d4c5f9" --description "Entra ID (Azure AD)" --force 2>/dev/null || true
gh label create "keyvault" --color "c5def5" --description "Key Vault" --force 2>/dev/null || true
gh label create "resourcegraph" --color "c5def5" --description "Resource Graph" --force 2>/dev/null || true
gh label create "docs" --color "0075ca" --description "Documentation" --force 2>/dev/null || true
gh label create "setup" --color "bfdadc" --description "Project setup" --force 2>/dev/null || true
gh label create "auth" --color "e99695" --description "Authentication" --force 2>/dev/null || true
gh label create "performance" --color "5319e7" --description "Performance" --force 2>/dev/null || true

# Create milestones
echo "Creating milestones..."
gh api repos/:owner/:repo/milestones -f title="1. Core Framework" -f description="Foundation for all tools" -f state="open" 2>/dev/null || true
gh api repos/:owner/:repo/milestones -f title="2. Storage Tools" -f description="Azure Storage Blob, Table, Queue, File" -f state="open" 2>/dev/null || true
gh api repos/:owner/:repo/milestones -f title="3. Cosmos DB Tools" -f description="Cosmos DB operations" -f state="open" 2>/dev/null || true
gh api repos/:owner/:repo/milestones -f title="4. Cost Management" -f description="Cost Management tools (PRIORITY)" -f state="open" 2>/dev/null || true
gh api repos/:owner/:repo/milestones -f title="5. Entra ID" -f description="Entra ID / Azure AD tools (PRIORITY)" -f state="open" 2>/dev/null || true
gh api repos/:owner/:repo/milestones -f title="6. Key Vault" -f description="Key Vault tools" -f state="open" 2>/dev/null || true
gh api repos/:owner/:repo/milestones -f title="7. Additional Services" -f description="Event Grid, Service Bus, Functions, etc." -f state="open" 2>/dev/null || true

echo ""
echo "Creating issues..."

# Milestone 4: Cost Management (PRIORITY - create first)
gh issue create --title "[Tool] cost_query - Query cost data" --label "tool,cost,priority" --milestone "4. Cost Management" --body "## Description
Query cost data using the Cost Management API.

**Note**: This is NEW functionality not in the .NET version.

## Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription ID or name |
| scope | string | No | Scope (subscription, resource group, etc.) |
| timeframe | string | Yes | MonthToDate, BillingMonthToDate, Custom |
| granularity | string | No | None, Daily, Monthly |
| group_by | string[] | No | Dimensions to group by |
| filter | object | No | Filter expression |

## Returns
- Cost breakdown by grouping dimensions
- Total cost
- Currency

## Acceptance Criteria
- [ ] CostManagementService implementation
- [ ] CostQueryTool with Pydantic options
- [ ] Unit tests
- [ ] Integration test"

gh issue create --title "[Tool] cost_forecast - Get cost forecasts" --label "tool,cost,priority" --milestone "4. Cost Management" --body "## Description
Get cost forecasts for a subscription or scope.

## Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription |
| timeframe | string | Yes | Forecast period |
| granularity | string | No | Daily, Monthly |

## Acceptance Criteria
- [ ] Tool implementation
- [ ] Unit tests"

gh issue create --title "[Tool] cost_budgets_list - List budgets" --label "tool,cost,priority" --milestone "4. Cost Management" --body "## Description
List budgets for a scope.

## Acceptance Criteria
- [ ] Tool implementation
- [ ] Unit tests"

gh issue create --title "[Tool] cost_budgets_get - Get budget details" --label "tool,cost,priority" --milestone "4. Cost Management" --body "## Description
Get budget details and current spend vs. limit.

## Acceptance Criteria
- [ ] Tool implementation
- [ ] Unit tests"

gh issue create --title "[Tool] cost_recommendations - Get Advisor recommendations" --label "tool,cost,priority" --milestone "4. Cost Management" --body "## Description
Get Azure Advisor cost recommendations.

## Acceptance Criteria
- [ ] Tool implementation
- [ ] Unit tests"

# Milestone 5: Entra ID (PRIORITY)
gh issue create --title "[Tool] entraid_user_list - List users" --label "tool,entraid,priority" --milestone "5. Entra ID" --body "## Description
List users in Entra ID (Azure AD).

**Note**: This is NEW functionality not in the .NET version.

Uses Microsoft Graph SDK.

## Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| filter | string | No | OData filter |
| search | string | No | Search by displayName or email |
| select | string[] | No | Properties to return |
| top | int | No | Max results |

## Acceptance Criteria
- [ ] EntraIdService with Graph SDK
- [ ] EntraIdUserListTool implementation
- [ ] Unit tests"

gh issue create --title "[Tool] entraid_user_get - Get user details" --label "tool,entraid,priority" --milestone "5. Entra ID" --body "## Description
Get a specific user by ID or UPN.

## Acceptance Criteria
- [ ] Tool implementation
- [ ] Unit tests"

gh issue create --title "[Tool] entraid_group_list - List groups" --label "tool,entraid,priority" --milestone "5. Entra ID" --body "## Description
List groups in Entra ID.

## Acceptance Criteria
- [ ] Tool implementation
- [ ] Unit tests"

gh issue create --title "[Tool] entraid_group_members - List group members" --label "tool,entraid,priority" --milestone "5. Entra ID" --body "## Description
List members of a group.

## Acceptance Criteria
- [ ] Tool implementation
- [ ] Unit tests"

gh issue create --title "[Tool] entraid_app_list - List app registrations" --label "tool,entraid,priority" --milestone "5. Entra ID" --body "## Description
List app registrations in Entra ID.

## Acceptance Criteria
- [ ] Tool implementation
- [ ] Unit tests"

# Milestone 2: Storage Tools
gh issue create --title "[Tool] storage_account_list - List storage accounts" --label "tool,storage" --milestone "2. Storage Tools" --body "## Description
List Azure Storage Accounts using Resource Graph.

## Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| subscription | string | Yes | Subscription ID or name |
| resource_group | string | No | Filter by resource group |
| limit | int | No | Max results (default 50) |

## Acceptance Criteria
- [ ] Tool implementation
- [ ] Unit tests"

gh issue create --title "[Tool] storage_blob_list - List blobs" --label "tool,storage" --milestone "2. Storage Tools" --body "## Description
List blobs in a container.

## Acceptance Criteria
- [ ] Tool implementation
- [ ] Unit tests"

gh issue create --title "[Tool] storage_blob_read - Read blob content" --label "tool,storage" --milestone "2. Storage Tools" --body "## Description
Read blob content (text or base64 for binary).

## Acceptance Criteria
- [ ] Tool implementation
- [ ] Unit tests"

# Milestone 3: Cosmos DB Tools
gh issue create --title "[Tool] cosmos_item_query - Query items" --label "tool,cosmos" --milestone "3. Cosmos DB Tools" --body "## Description
Query items using SQL-like syntax.

## Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| account_name | string | Yes | Cosmos account name |
| database_name | string | Yes | Database name |
| container_name | string | Yes | Container name |
| query | string | Yes | SQL query |
| parameters | object | No | Query parameters |
| max_items | int | No | Max results |

## Acceptance Criteria
- [ ] CosmosService implementation
- [ ] Tool implementation
- [ ] Unit tests"

echo ""
echo "✅ Issues created successfully!"
echo ""
echo "View your issues at: gh issue list"
