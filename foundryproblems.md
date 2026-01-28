Problema
El servidor MCP basado en FastMCP no funcionaba con Azure AI Foundry Agent Service. El agente fallaba inmediatamente al intentar conectar con tools: [] vacío y error Connection not found.

Síntomas observados
Error 406 Not Acceptable en requests GET/POST
tools: [] vacío en la respuesta de AI Foundry
Fallo instantáneo (duration: 0, prompt_tokens: 0)
Error: Connection 'PSACosmosConnectionMCP' not found
Investigación
Después de múltiples pruebas comparando con el MCP de Microsoft Learn (https://learn.microsoft.com/api/mcp), se identificaron 4 problemas de compatibilidad:

1. Header Accept faltante
AI Foundry no envía el header Accept: text/event-stream que FastMCP requiere.

Solución: Middleware ASGI que inyecta el header automáticamente.

2. Modo stateful vs stateless
FastMCP por defecto usa sesiones (requiere mcp-session-id), pero AI Foundry espera un endpoint stateless donde cada request es independiente.

Solución: Configurar stateless_http=True en mcp.http_app().

3. Formato de respuesta JSON vs SSE
Con json_response=True, FastMCP devuelve JSON puro, pero AI Foundry espera formato SSE:

event: message
data: {"jsonrpc":"2.0",...}
Solución: Usar json_response=False (default) para mantener formato SSE.

4. Schema anyOf con null no soportado ⚠️ PROBLEMA PRINCIPAL
FastMCP genera schemas con anyOf para tipos opcionales:

"specialty": {
  "anyOf": [{"type": "string"}, {"type": "null"}],
  "default": null
}
Azure AI Agent Service NO soporta este patrón. Espera schemas simples:

"specialty": {
  "type": "string",
  "default": ""
}
Solución: Cambiar parámetros de str | None = None a str = "" y manejar string vacío como None en el código.

Solución implementada
1. Middleware de compatibilidad
class MCPCompatibilityMiddleware:
    """Middleware que arregla headers para compatibilidad con Azure AI Agent Service."""
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Fix Accept header en request
            headers = dict(scope.get("headers", []))
            accept = headers.get(b"accept", b"").decode()
            if "text/event-stream" not in accept:
                new_accept = "application/json, text/event-stream"
                # ... reconstruir headers
            
            # Añadir mcp-session-id en respuesta
            session_id = uuid.uuid4().hex
            # ... inyectar header en respuesta
2. Configuración stateless con SSE
app = mcp.http_app(
    path="/",
    middleware=[Middleware(MCPCompatibilityMiddleware)],
    stateless_http=True,  # Sin sesiones
    # json_response=False (default) - mantiene formato SSE
)
3. Schemas simplificados
# ANTES (no funciona con AI Foundry)
async def list_psas(
    specialty: Annotated[str | None, "Filter by specialty"] = None,
):

# DESPUÉS (funciona con AI Foundry)
async def list_psas(
    specialty: Annotated[str, "Filter by specialty. Leave empty for all."] = "",
):
    filter_specialty = specialty if specialty else None  # Manejar "" como None
Archivos modificados
mcp-server/mcp_server/main.py - Middleware, configuración stateless, schemas simplificados
mcp-server/pyproject.toml - Añadidas dependencias uvicorn, starlette
mcp-server/Dockerfile - Cambiado a usar uvicorn directamente
Lecciones aprendidas
Azure AI Agent Service es muy estricto con el formato de schemas JSON
El patrón anyOf para nullable types no es soportado - usar valores por defecto simples
Formato SSE es requerido aunque sea stateless
Header mcp-session-id debe estar presente en respuestas
Header Accept debe ser inyectado si el cliente no lo envía
Referencias
FastMCP: https://github.com/jlowin/fastmcp
MCP Protocol: https://modelcontextprotocol.io/
Azure AI Agent Service MCP: https://learn.microsoft.com/en-us/azure/ai-services/agents/