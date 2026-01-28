#!/bin/bash
# Script para asignar Cosmos DB Data Contributor a todas las cuentas de la suscripción
# Uso: ./scripts/assign-cosmos-data-roles.sh <principal-id>

set -e

PRINCIPAL_ID="${1:-1537d9d5-01b3-4b30-bdc9-03953dcc4bf6}"
ROLE_ID="00000000-0000-0000-0000-000000000002"  # Cosmos DB Built-in Data Contributor

echo "🔍 Buscando cuentas de Cosmos DB..."
ACCOUNTS=$(az cosmosdb list --query "[].{name:name, rg:resourceGroup}" -o tsv)

if [ -z "$ACCOUNTS" ]; then
    echo "No se encontraron cuentas de Cosmos DB"
    exit 0
fi

echo ""
echo "📝 Asignando Cosmos DB Data Contributor a:"
echo "$ACCOUNTS" | while read -r NAME RG; do
    echo "   - $NAME ($RG)"
done
echo ""

echo "$ACCOUNTS" | while read -r NAME RG; do
    echo -n "⏳ $NAME... "
    
    # Verificar si ya existe
    EXISTING=$(az cosmosdb sql role assignment list \
        --account-name "$NAME" \
        --resource-group "$RG" \
        --query "[?principalId=='$PRINCIPAL_ID'].name" \
        -o tsv 2>/dev/null | head -1)
    
    if [ -n "$EXISTING" ]; then
        echo "✅ Ya asignado"
    else
        az cosmosdb sql role assignment create \
            --account-name "$NAME" \
            --resource-group "$RG" \
            --principal-id "$PRINCIPAL_ID" \
            --role-definition-id "$ROLE_ID" \
            --scope "/" \
            --no-wait \
            -o none 2>/dev/null && echo "✅ Asignado" || echo "❌ Error"
    fi
done

echo ""
echo "✅ Completado"
