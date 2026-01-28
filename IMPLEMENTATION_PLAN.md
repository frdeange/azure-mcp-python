# Plan Completo: MCP Python - Soporte HTTP para Azure AI Foundry

## Contexto del Proyecto

**Ubicación**: `/workspaces/Azure.Mcp.Server/_azure-mcp-python/`

**Estado Actual**:
- ✅ Core framework completo (`src/azure_mcp/core/`)
- ✅ 8 tools implementados (1 resourcegraph + 7 cosmos)
- ✅ Tests unitarios
- ✅ Documentación
- ❌ Server solo soporta stdio (no HTTP)
- ❌ Faltan dependencias HTTP (uvicorn, starlette)
- ❌ No hay Dockerfile
- ❌ No hay entry point CLI (`__main__.py`)

**Objetivo**: Desplegar a Azure Container App y probar con Azure AI Foundry Agent Service.

---

## Tools Implementados (8 total)

| Tool | Grupo | Archivo |
|------|-------|---------|
| `resourcegraph_query` | resourcegraph | `tools/resourcegraph/query.py` |
| `cosmos_account_list` | cosmos/account | `tools/cosmos/account.py` |
| `cosmos_database_list` | cosmos/database | `tools/cosmos/database.py` |
| `cosmos_container_list` | cosmos/container | `tools/cosmos/container.py` |
| `cosmos_item_query` | cosmos/item | `tools/cosmos/item.py` |
| `cosmos_item_get` | cosmos/item | `tools/cosmos/item.py` |
| `cosmos_item_upsert` | cosmos/item | `tools/cosmos/item.py` |
| `cosmos_item_delete` | cosmos/item | `tools/cosmos/item.py` |

---

## Archivos a Modificar/Crear

### 1. `src/azure_mcp/server.py` - REEMPLAZAR COMPLETO

**Motivo**: Actualmente solo soporta stdio. Necesita soporte HTTP para Foundry.

**Cambios**:
- Añadir variable `MCP_TRANSPORT` (stdio|http, default: stdio)
- Añadir variable `MCP_PORT` (default: 5000)
- Añadir variable `LOG_LEVEL` (default: INFO)
- Crear función `run_http_server()` con `mcp.http_app()`
- Añadir health endpoint `/health`
- Mantener `run_stdio_server()` para compatibilidad local

**Código completo nuevo**:

```python
"""Azure MCP Server - Main entry point."""

from __future__ import annotations

import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from azure_mcp.core.registry import registry

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP(
        name="Azure MCP Server",
    )
    return mcp


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""
    # Import tools to trigger registration
    from azure_mcp import tools  # noqa: F401

    logger.info(f"Registering {len(registry)} tools...")

    for tool in registry.list_tools():
        def make_handler(t: Any):
            async def handler(**kwargs: Any) -> Any:
                return await t.run(kwargs)
            return handler

        mcp.tool(
            name=tool.name,
            description=tool.description,
        )(make_handler(tool))
        logger.debug(f"Registered tool: {tool.name}")

    logger.info(f"Registered {len(registry)} tools")


def run_stdio_server() -> None:
    """Run the server in stdio mode (for local development)."""
    logger.info("Starting Azure MCP Server in stdio mode...")
    mcp = create_server()
    register_tools(mcp)
    mcp.run()


def run_http_server() -> None:
    """Run the server in HTTP mode (for Azure Container Apps / Foundry)."""
    import uvicorn
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    port = int(os.getenv("MCP_PORT", "5000"))
    host = os.getenv("MCP_HOST", "0.0.0.0")

    logger.info(f"Starting Azure MCP Server in HTTP mode on {host}:{port}...")

    mcp = create_server()
    register_tools(mcp)

    # Create MCP HTTP app
    mcp_app = mcp.http_app(
        path="/mcp",
        stateless_http=True,  # Required for Foundry - no session management
    )

    # Health endpoint
    async def health(request):
        return JSONResponse({
            "status": "healthy",
            "service": "azure-mcp-server",
            "tools_count": len(registry),
        })

    # Combine routes
    app = Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
        ],
    )

    # Mount MCP app
    app.mount("/", mcp_app)

    logger.info(f"Health endpoint: http://{host}:{port}/health")
    logger.info(f"MCP endpoint: http://{host}:{port}/mcp")

    uvicorn.run(app, host=host, port=port, log_level=log_level.lower())


def main() -> None:
    """Run the Azure MCP server."""
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport == "http":
        run_http_server()
    else:
        run_stdio_server()


if __name__ == "__main__":
    main()
```

---

### 2. `src/azure_mcp/__main__.py` - CREAR (nuevo archivo)

**Motivo**: Permite ejecutar `python -m azure_mcp`

**Código completo**:

```python
"""Entry point for running Azure MCP Server as a module."""

from azure_mcp.server import main

if __name__ == "__main__":
    main()
```

---

### 3. `pyproject.toml` - MODIFICAR (5 cambios puntuales)

**Motivo**: Añadir dependencias HTTP y actualizar a Python 3.12

**Cambio 1** - Línea `requires-python`:
```toml
# ANTES
requires-python = ">=3.11"

# DESPUÉS
requires-python = ">=3.12"
```

**Cambio 2** - En `dependencies`, añadir después de `"cachetools>=5.3.0",`:
```toml
    # HTTP Server
    "uvicorn>=0.30.0",
    "starlette>=0.27.0",
```

**Cambio 3** - En `classifiers`, reemplazar:
```toml
# ANTES
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",

# DESPUÉS
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
```

**Cambio 4** - En `[tool.ruff]`:
```toml
# ANTES
target-version = "py311"

# DESPUÉS
target-version = "py312"
```

**Cambio 5** - En `[tool.mypy]`:
```toml
# ANTES
python_version = "3.11"

# DESPUÉS
python_version = "3.12"
```

---

### 4. `.python-version` - MODIFICAR

**Motivo**: Actualizar versión de Python

**Contenido actual**: `3.11`

**Contenido nuevo**: `3.12`

---

### 5. `Dockerfile` - CREAR (nuevo archivo en raíz del proyecto)

**Motivo**: Necesario para desplegar a Azure Container App

**Código completo**:

```dockerfile
# Azure MCP Server - Python
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Environment variables
ENV MCP_TRANSPORT=http
ENV MCP_PORT=5000
ENV MCP_HOST=0.0.0.0
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run server
CMD ["python", "-m", "azure_mcp"]
```

---

### 6. `docs/deployment.md` - CREAR (nuevo archivo)

**Motivo**: Documentar comandos Azure CLI para despliegue manual

**Código completo**:

```markdown
# Deployment Guide

This guide covers deploying Azure MCP Server to Azure Container Apps.

## Prerequisites

- Azure CLI installed and logged in (`az login`)
- Docker (for local testing)
- Access to an Azure Container Registry (ACR)
- Access to a Container Apps Environment

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_TRANSPORT` | Transport mode: `stdio` or `http` | `stdio` |
| `MCP_PORT` | HTTP port (when transport=http) | `5000` |
| `MCP_HOST` | HTTP host (when transport=http) | `0.0.0.0` |
| `LOG_LEVEL` | Logging level: DEBUG, INFO, WARNING, ERROR | `INFO` |

## Local Testing

### Run in stdio mode (default)

\`\`\`bash
# Install dependencies
pip install -e .

# Run server
azure-mcp
# or
python -m azure_mcp
\`\`\`

### Run in HTTP mode

\`\`\`bash
MCP_TRANSPORT=http python -m azure_mcp
\`\`\`

### Test health endpoint

\`\`\`bash
curl http://localhost:5000/health
\`\`\`

## Docker Build & Test

\`\`\`bash
# Build image
docker build -t azure-mcp-python:local .

# Run container
docker run -p 5000:5000 azure-mcp-python:local

# Test
curl http://localhost:5000/health
\`\`\`

## Deploy to Azure Container Apps

### 1. Set variables

\`\`\`bash
# Change these to match your environment
RESOURCE_GROUP="RG-DistriAgentPlatform"
ACR_NAME="distriplatformacr"
ACA_ENV="distriplatform-aca-env"
ACA_NAME="azure-mcp-python"
IMAGE_NAME="azure-mcp-python"
IMAGE_TAG="v1"
\`\`\`

### 2. Build and push image to ACR

\`\`\`bash
# Login to ACR
az acr login --name $ACR_NAME

# Build image in ACR (recommended - no local Docker needed)
az acr build \
  --registry $ACR_NAME \
  --image $IMAGE_NAME:$IMAGE_TAG \
  --file Dockerfile \
  .

# Verify image
az acr repository show-tags --name $ACR_NAME --repository $IMAGE_NAME
\`\`\`

### 3. Create Container App with Managed Identity

\`\`\`bash
az containerapp create \
  --name $ACA_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ACA_ENV \
  --image $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG \
  --target-port 5000 \
  --ingress external \
  --registry-server $ACR_NAME.azurecr.io \
  --system-assigned \
  --env-vars \
    MCP_TRANSPORT=http \
    LOG_LEVEL=INFO \
  --cpu 0.5 \
  --memory 1Gi \
  --min-replicas 1 \
  --max-replicas 3
\`\`\`

### 4. Get the Container App URL

\`\`\`bash
ACA_FQDN=$(az containerapp show \
  --name $ACA_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.configuration.ingress.fqdn" \
  --output tsv)

echo "Container App URL: https://$ACA_FQDN"
echo "Health endpoint: https://$ACA_FQDN/health"
echo "MCP endpoint: https://$ACA_FQDN/mcp"
\`\`\`

### 5. Assign RBAC roles to Managed Identity

\`\`\`bash
# Get the Managed Identity principal ID
PRINCIPAL_ID=$(az containerapp show \
  --name $ACA_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "identity.principalId" \
  --output tsv)

# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id --output tsv)

# Assign Reader role (required for Resource Graph queries)
az role assignment create \
  --role "Reader" \
  --assignee $PRINCIPAL_ID \
  --scope /subscriptions/$SUBSCRIPTION_ID

# For Cosmos DB tools, also assign Cosmos DB roles:
# az role assignment create \
#   --role "Cosmos DB Account Reader Role" \
#   --assignee $PRINCIPAL_ID \
#   --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/<rg>/providers/Microsoft.DocumentDB/databaseAccounts/<account>
\`\`\`

### 6. Test the deployment

\`\`\`bash
# Health check
curl https://$ACA_FQDN/health

# Expected response:
# {"status":"healthy","service":"azure-mcp-server","tools_count":8}
\`\`\`

## Update Deployment

\`\`\`bash
# Build new image
az acr build \
  --registry $ACR_NAME \
  --image $IMAGE_NAME:$IMAGE_TAG \
  --file Dockerfile \
  .

# Update Container App
az containerapp update \
  --name $ACA_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG
\`\`\`

## Connect to Azure AI Foundry

1. Go to Azure AI Foundry portal
2. Create a new MCP connection:
   - URL: `https://<your-aca-fqdn>/mcp`
   - Authentication: None (uses Managed Identity internally)
3. Test with a simple query:
   - Tool: `resourcegraph_query`
   - Query: `resources | take 5`

## Troubleshooting

### View logs

\`\`\`bash
az containerapp logs show \
  --name $ACA_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow
\`\`\`

### Check container status

\`\`\`bash
az containerapp show \
  --name $ACA_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.runningStatus"
\`\`\`

### Common issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 401/403 errors | Missing RBAC | Assign Reader role to MI |
| Connection refused | Wrong port | Check MCP_PORT=5000 |
| Tools not found | Import error | Check logs for import errors |
```

---

## Resumen de Cambios

| Archivo | Acción | Líneas aprox |
|---------|--------|--------------|
| `src/azure_mcp/server.py` | REEMPLAZAR completo | ~100 |
| `src/azure_mcp/__main__.py` | CREAR | ~6 |
| `pyproject.toml` | MODIFICAR (5 cambios puntuales) | N/A |
| `.python-version` | MODIFICAR | 1 |
| `Dockerfile` | CREAR | ~35 |
| `docs/deployment.md` | CREAR | ~200 |

---

## Orden de Ejecución

1. **Primero**: Modificar `pyproject.toml` y `.python-version`
2. **Segundo**: Crear `src/azure_mcp/__main__.py`
3. **Tercero**: Reemplazar `src/azure_mcp/server.py`
4. **Cuarto**: Crear `Dockerfile`
5. **Quinto**: Crear `docs/deployment.md`
6. **Sexto**: Probar localmente con `MCP_TRANSPORT=http python -m azure_mcp`
7. **Séptimo**: Seguir guía de deployment para ACA

---

## Consideraciones Importantes para Foundry

**Si falla la conexión con Foundry**, hay 4 posibles fixes (aplicar uno a uno):

### Fix 1: `stateless_http=True` 
**Ya incluido en el código de arriba**

### Fix 2: Middleware Accept header
Si Foundry da error 406 Not Acceptable, añadir este middleware en server.py:

```python
class MCPCompatibilityMiddleware:
    """Middleware que arregla headers para compatibilidad con Azure AI Agent Service."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            accept = headers.get(b"accept", b"").decode()

            if "text/event-stream" not in accept:
                new_accept = "application/json, text/event-stream"
                new_headers = [(k, v) for k, v in scope["headers"] if k != b"accept"]
                new_headers.append((b"accept", new_accept.encode()))
                scope = {**scope, "headers": new_headers}

        await self.app(scope, receive, send)
```

### Fix 3: Middleware mcp-session-id
Si Foundry pide session ID, añadir header en respuesta:

```python
import uuid

async def send_with_session_id(message):
    if message["type"] == "http.response.start":
        headers = list(message.get("headers", []))
        headers.append((b"mcp-session-id", uuid.uuid4().hex.encode()))
        message = {**message, "headers": headers}
    await send(message)
```

### Fix 4: Schema sin anyOf
Si Foundry rechaza schemas de Pydantic con `anyOf` para tipos opcionales, crear transformador:

```python
def transform_schema_for_foundry(schema: dict) -> dict:
    """Remove anyOf patterns from Pydantic schemas."""
    if isinstance(schema, dict):
        if "anyOf" in schema:
            non_null = [s for s in schema["anyOf"] if s.get("type") != "null"]
            if len(non_null) == 1:
                schema.update(non_null[0])
                del schema["anyOf"]
        for key in ["properties", "items"]:
            if key in schema:
                if isinstance(schema[key], dict):
                    for prop in schema[key]:
                        schema[key][prop] = transform_schema_for_foundry(schema[key][prop])
    return schema
```

---

## Test Local Rápido

Después de implementar, probar con:

```bash
cd /workspaces/Azure.Mcp.Server/_azure-mcp-python

# Instalar dependencias
pip install -e .

# Probar stdio (default)
python -m azure_mcp

# Probar HTTP
MCP_TRANSPORT=http python -m azure_mcp

# En otra terminal
curl http://localhost:5000/health
```

---

## Infraestructura Azure (valores actuales)

| Recurso | Valor |
|---------|-------|
| Resource Group | `RG-DistriAgentPlatform` |
| ACR | `distriplatformacr` |
| Container Apps Environment | `distriplatform-aca-env` |
| Nuevo Container App | `azure-mcp-python` |
| Imagen | `azure-mcp-python:v1` |

---

## Después del Despliegue

Una vez desplegado y funcionando con Foundry, **eliminar este archivo** (`IMPLEMENTATION_PLAN.md`) ya que su contenido estará implementado.
