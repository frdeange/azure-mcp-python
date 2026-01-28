"""FastMCP Server for PSA Competencies."""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .cosmos_client import CosmosDBClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global cosmos client
cosmos_client: CosmosDBClient | None = None


@asynccontextmanager
async def lifespan(mcp: FastMCP):
    """Manage server lifecycle."""
    global cosmos_client

    # Startup
    logger.info("Starting MCP Server...")
    cosmos_client = CosmosDBClient(
        endpoint=os.getenv("COSMOS_ENDPOINT", ""),
        database_name=os.getenv("COSMOS_DATABASE", "psa-competencies-db"),
    )
    await cosmos_client.initialize()
    logger.info("MCP Server started successfully")

    yield

    # Shutdown
    if cosmos_client:
        await cosmos_client.close()
    logger.info("MCP Server stopped")


# =============================================================================
# Middleware para compatibilidad con AI Foundry
# =============================================================================


class MCPCompatibilityMiddleware:
    """Middleware que arregla headers para compatibilidad con Azure AI Agent Service.
    
    1. Añade Accept headers requeridos por MCP (AI Foundry no los envía)
    2. Añade mcp-session-id header en respuestas (AI Foundry lo espera)
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            # Fix Accept header en request
            headers = dict(scope.get("headers", []))
            accept = headers.get(b"accept", b"").decode()

            has_json = "application/json" in accept
            has_sse = "text/event-stream" in accept

            if not has_json or not has_sse:
                new_accept = "application/json, text/event-stream"
                new_headers = [(k, v) for k, v in scope["headers"] if k != b"accept"]
                new_headers.append((b"accept", new_accept.encode()))
                scope = {**scope, "headers": new_headers}

            # Generar session ID para añadir en respuesta
            session_id = uuid.uuid4().hex

            async def send_with_session_id(message: Message) -> None:
                if message["type"] == "http.response.start":
                    # Añadir mcp-session-id header a la respuesta
                    headers = list(message.get("headers", []))
                    headers.append((b"mcp-session-id", session_id.encode()))
                    message = {**message, "headers": headers}
                await send(message)

            await self.app(scope, receive, send_with_session_id)
        else:
            await self.app(scope, receive, send)

        await self.app(scope, receive, send)


# Create FastMCP server
mcp = FastMCP(
    "PSA Competencies",
    lifespan=lifespan,
)


def _score_to_level_name(score: int) -> str:
    """Convert score to level name."""
    if score <= 0:
        return "None"
    elif score <= 100:
        return "Basic"
    elif score <= 200:
        return "Intermediate"
    elif score <= 300:
        return "Advanced"
    elif score <= 400:
        return "Expert"
    else:
        return "Master"


# =============================================================================
# MCP Tools
# =============================================================================


@mcp.tool
async def list_psas(
    specialty: Annotated[str, "Filter PSAs by specialty: 'Data' or 'AI'. Leave empty for all."] = "",
) -> dict:
    """List all PSAs (Partner Solution Architects) with optional filtering by specialty.

    Returns a list of PSAs with their id, name, specialty, and partner count.
    """
    # Treat empty string as None for filtering
    filter_specialty = specialty if specialty else None
    psas = await cosmos_client.query_psas(specialty=filter_specialty)

    return {
        "psas": [
            {
                "id": psa["id"],
                "name": psa["name"],
                "specialty": psa["specialty"],
                "partnerCount": psa.get("partnerCount", 0),
            }
            for psa in psas
        ],
        "count": len(psas),
    }


@mcp.tool
async def get_psa_details(
    psa_id: Annotated[str, "The ID of the PSA to retrieve details for"],
) -> dict:
    """Get detailed information about a specific PSA including their full skills matrix.

    Returns PSA info grouped by skill platform with proficiency levels.
    """
    psa = await cosmos_client.get_psa_by_id(psa_id)
    if not psa:
        return {"error": f"PSA not found: {psa_id}"}

    # Format skills by platform
    skills_by_platform = {}
    for skill in psa.get("skills", []):
        platform = skill.get("platform", "Other")
        if platform not in skills_by_platform:
            skills_by_platform[platform] = []
        skills_by_platform[platform].append(
            {
                "category": skill.get("category"),
                "subcategory": skill.get("subcategory"),
                "score": skill.get("score"),
                "level": _score_to_level_name(skill.get("score", 0)),
            }
        )

    return {
        "psa": {
            "id": psa["id"],
            "name": psa["name"],
            "specialty": psa["specialty"],
            "partnerCount": psa.get("partnerCount", 0),
        },
        "skillsByPlatform": skills_by_platform,
    }


@mcp.tool
async def list_partners_by_psa(
    psa_id: Annotated[str, "The ID of the PSA"],
) -> dict:
    """Get the list of partners a specific PSA has worked with, including last assignment dates.

    Returns partners with name, country, and last assignment date.
    """
    partners = await cosmos_client.get_partners_by_psa(psa_id)

    return {
        "partners": [
            {
                "name": p.get("partnerName"),
                "country": p.get("country"),
                "lastAssignmentDate": p.get("lastAssignmentDate"),
            }
            for p in partners
        ],
        "count": len(partners),
    }


@mcp.tool
async def list_psas_by_partner(
    partner_name: Annotated[str, "The name of the partner (can be partial match)"],
) -> dict:
    """Find PSAs who have experience working with a specific partner.

    Returns PSAs with their id, name, and last assignment date for that partner.
    """
    assignments = await cosmos_client.get_psas_by_partner(partner_name)

    # Deduplicate and format
    psa_map = {}
    for assignment in assignments:
        psa_id = assignment.get("psaId")
        if psa_id and psa_id not in psa_map:
            psa_map[psa_id] = {
                "id": psa_id,
                "name": assignment.get("psaName"),
                "isTeamMember": assignment.get("isTeamMember", False),
                "lastAssignmentDate": assignment.get("lastAssignmentDate"),
            }

    return {
        "partnerName": partner_name,
        "psas": list(psa_map.values()),
        "count": len(psa_map),
    }


@mcp.tool
async def search_psas_by_skill(
    category: Annotated[
        str,
        "The skill category (e.g., 'Azure AI Services', 'Microsoft Fabric', 'Azure SQL Database')",
    ],
    subcategory: Annotated[str, "Optional specific subcategory within the category. Leave empty for all."] = "",
    min_level: Annotated[
        int, "Minimum proficiency level: 1=Basic, 2=Intermediate, 3=Advanced, 4=Expert, 5=Master"
    ] = 1,
) -> dict:
    """Search for PSAs with specific technical skills at a minimum proficiency level.

    Returns PSAs matching the skill criteria with their matching skill scores.
    """
    # Treat empty string as None for filtering
    filter_subcategory = subcategory if subcategory else None
    psas = await cosmos_client.search_psas_by_skill(
        category=category,
        subcategory=filter_subcategory,
        min_level=min_level,
    )

    return {
        "searchCriteria": {
            "category": category,
            "subcategory": subcategory,
            "minLevel": min_level,
        },
        "psas": [
            {
                "id": psa["id"],
                "name": psa["name"],
                "specialty": psa["specialty"],
                "matchingSkills": [
                    {
                        "subcategory": s.get("subcategory"),
                        "score": s.get("score"),
                        "level": _score_to_level_name(s.get("score", 0)),
                    }
                    for s in psa.get("matchingSkills", [])
                ],
            }
            for psa in psas
        ],
        "count": len(psas),
    }


@mcp.tool
async def get_last_psa_for_partner(
    partner_name: Annotated[str, "The name of the partner"],
) -> dict:
    """Find the PSA who most recently worked with a specific partner.

    Returns the most recent PSA assignment for the partner.
    """
    assignment = await cosmos_client.get_last_psa_for_partner(partner_name)

    if not assignment:
        return {
            "partnerName": partner_name,
            "lastPSA": None,
            "message": f"No PSA assignments found for partner: {partner_name}",
        }

    return {
        "partnerName": partner_name,
        "lastPSA": {
            "id": assignment.get("psaId"),
            "name": assignment.get("psaName"),
            "lastAssignmentDate": assignment.get("lastAssignmentDate"),
            "isTeamMember": assignment.get("isTeamMember", False),
        },
    }


# =============================================================================
# ASGI App with Middleware (Stateless mode for AI Foundry compatibility)
# =============================================================================

# Create the ASGI app with middleware for uvicorn
# stateless_http=True: No requiere session ID - cada request es independiente
# json_response=False (default): Respuestas en formato SSE (event: message\ndata: {...})
mcp_app = mcp.http_app(
    path="/",
    middleware=[Middleware(MCPCompatibilityMiddleware)],
    stateless_http=True,
)


# Create a wrapper ASGI app that handles /health separately
from starlette.responses import JSONResponse


class HealthCheckWrapper:
    """ASGI wrapper that adds /health endpoint to MCP app."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"] == "/health":
            response = JSONResponse({"status": "healthy", "service": "mcp-server"})
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


app = HealthCheckWrapper(mcp_app)


# =============================================================================
# Entry point (for local development)
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
