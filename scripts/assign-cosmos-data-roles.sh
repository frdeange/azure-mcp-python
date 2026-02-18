#!/bin/bash
# Script to assign Cosmos DB data plane roles to all accounts in the subscription.
#
# Assigns two roles:
#   1. Built-in Data Contributor (containers + items CRUD)
#   2. Custom Database Manager (database create/delete) - created if not exists
#
# Usage: ./scripts/assign-cosmos-data-roles.sh <principal-id> [--skip-db-manager]
#
# The --skip-db-manager flag skips the custom role (only assigns Data Contributor).
# See docs/permissions.md for details on why the custom role is needed.

set -e

PRINCIPAL_ID="${1:-1537d9d5-01b3-4b30-bdc9-03953dcc4bf6}"
SKIP_DB_MANAGER=false
if [ "$2" = "--skip-db-manager" ]; then
    SKIP_DB_MANAGER=true
fi

DATA_CONTRIBUTOR_ROLE="00000000-0000-0000-0000-000000000002"  # Cosmos DB Built-in Data Contributor
DB_MANAGER_ROLE_NAME="Cosmos DB Database Manager"

echo "🔍 Searching for Cosmos DB accounts..."
ACCOUNTS=$(az cosmosdb list --query "[].{name:name, rg:resourceGroup}" -o tsv)

if [ -z "$ACCOUNTS" ]; then
    echo "No Cosmos DB accounts found"
    exit 0
fi

echo ""
echo "📝 Accounts found:"
echo "$ACCOUNTS" | while read -r NAME RG; do
    echo "   - $NAME ($RG)"
done
echo ""

# Function to create Database Manager custom role if it doesn't exist
create_db_manager_role() {
    local ACCOUNT_NAME="$1"
    local RG="$2"
    
    # Check if custom role already exists
    EXISTING_ROLE=$(az cosmosdb sql role definition list \
        --account-name "$ACCOUNT_NAME" \
        --resource-group "$RG" \
        --query "[?roleName=='$DB_MANAGER_ROLE_NAME'].name" \
        -o tsv 2>/dev/null | head -1)
    
    if [ -n "$EXISTING_ROLE" ]; then
        echo "$EXISTING_ROLE"
        return 0
    fi
    
    # Create the custom role
    ROLE_BODY='{
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
    
    RESULT=$(az cosmosdb sql role definition create \
        --account-name "$ACCOUNT_NAME" \
        --resource-group "$RG" \
        --body "$ROLE_BODY" \
        --query "name" -o tsv 2>/dev/null)
    
    echo "$RESULT"
}

# Assign roles for each account
assign_role() {
    local ACCOUNT_NAME="$1"
    local RG="$2"
    local ROLE_ID="$3"
    local ROLE_LABEL="$4"
    
    # Check if already assigned
    EXISTING=$(az cosmosdb sql role assignment list \
        --account-name "$ACCOUNT_NAME" \
        --resource-group "$RG" \
        --query "[?principalId=='$PRINCIPAL_ID' && roleDefinitionId contains '$ROLE_ID'].name" \
        -o tsv 2>/dev/null | head -1)
    
    if [ -n "$EXISTING" ]; then
        echo "  ✅ $ROLE_LABEL: Already assigned"
    else
        az cosmosdb sql role assignment create \
            --account-name "$ACCOUNT_NAME" \
            --resource-group "$RG" \
            --principal-id "$PRINCIPAL_ID" \
            --role-definition-id "$ROLE_ID" \
            --scope "/" \
            --no-wait \
            -o none 2>/dev/null && echo "  ✅ $ROLE_LABEL: Assigned" || echo "  ❌ $ROLE_LABEL: Error"
    fi
}

echo "$ACCOUNTS" | while read -r NAME RG; do
    echo "⏳ $NAME ($RG)"
    
    # 1. Assign Data Contributor (containers + items)
    assign_role "$NAME" "$RG" "$DATA_CONTRIBUTOR_ROLE" "Data Contributor"
    
    # 2. Create and assign Database Manager custom role (database create/delete)
    if [ "$SKIP_DB_MANAGER" = false ]; then
        DB_MANAGER_ROLE_ID=$(create_db_manager_role "$NAME" "$RG")
        if [ -n "$DB_MANAGER_ROLE_ID" ]; then
            assign_role "$NAME" "$RG" "$DB_MANAGER_ROLE_ID" "Database Manager"
        else
            echo "  ❌ Database Manager: Failed to create custom role"
        fi
    fi
    
    echo ""
done

echo "✅ Complete!"
if [ "$SKIP_DB_MANAGER" = true ]; then
    echo "⚠️  Skipped Database Manager role. cosmos_database_create/delete will not work."
    echo "   Run without --skip-db-manager to enable full Cosmos DB CRUD."
fi
