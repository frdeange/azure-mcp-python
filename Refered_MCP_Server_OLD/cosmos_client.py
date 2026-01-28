"""Cosmos DB client for the MCP server."""

import logging
from typing import Any

from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential

logger = logging.getLogger(__name__)


class CosmosDBClient:
    """Async Cosmos DB client for PSA data access."""

    def __init__(self, endpoint: str, database_name: str, connection_string: str | None = None):
        self.endpoint = endpoint
        self.database_name = database_name
        self.connection_string = connection_string
        self.client: CosmosClient | None = None
        self.database = None
        self.psas_container = None
        self.partners_container = None
        self.assignments_container = None

    async def initialize(self):
        """Initialize the Cosmos DB connection."""
        try:
            if self.connection_string:
                self.client = CosmosClient.from_connection_string(self.connection_string)
            else:
                credential = DefaultAzureCredential()
                self.client = CosmosClient(self.endpoint, credential=credential)

            self.database = self.client.get_database_client(self.database_name)
            self.psas_container = self.database.get_container_client("psas")
            self.partners_container = self.database.get_container_client("partners")
            self.assignments_container = self.database.get_container_client("assignments")

            logger.info("Cosmos DB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB client: {e}")
            # Don't raise - allow server to start without DB for development
            logger.warning("Running without database connection")

    async def close(self):
        """Close the Cosmos DB connection."""
        if self.client:
            await self.client.close()

    async def query_psas(
        self,
        specialty: str | None = None,
        name_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query PSAs with optional filters."""
        if not self.psas_container:
            return self._get_mock_psas(specialty, name_filter)

        query = "SELECT * FROM c WHERE 1=1"
        parameters: list[dict[str, Any]] = []

        if specialty:
            query += " AND c.specialty = @specialty"
            parameters.append({"name": "@specialty", "value": specialty})

        if name_filter:
            query += " AND CONTAINS(LOWER(c.name), LOWER(@name))"
            parameters.append({"name": "@name", "value": name_filter})

        results = []
        async for item in self.psas_container.query_items(
            query=query,
            parameters=parameters,
        ):
            results.append(item)

        return results

    async def get_psa_by_id(self, psa_id: str) -> dict[str, Any] | None:
        """Get a PSA by ID."""
        if not self.psas_container:
            return self._get_mock_psa(psa_id)

        query = "SELECT * FROM c WHERE c.id = @id"
        parameters = [{"name": "@id", "value": psa_id}]

        async for item in self.psas_container.query_items(
            query=query,
            parameters=parameters,
        ):
            return item

        return None

    async def get_partners_by_psa(self, psa_id: str) -> list[dict[str, Any]]:
        """Get partners associated with a PSA."""
        if not self.assignments_container:
            return self._get_mock_partners_for_psa(psa_id)

        query = "SELECT * FROM c WHERE c.psaId = @psaId"
        parameters = [{"name": "@psaId", "value": psa_id}]

        results = []
        async for item in self.assignments_container.query_items(
            query=query,
            parameters=parameters,
        ):
            results.append(item)

        return results

    async def get_psas_by_partner(self, partner_name: str) -> list[dict[str, Any]]:
        """Get PSAs with experience for a partner."""
        if not self.assignments_container:
            return self._get_mock_psas_for_partner(partner_name)

        # Normalize partner name for search
        partner_normalized = partner_name.lower().replace(" ", "-")

        query = """
            SELECT * FROM c 
            WHERE CONTAINS(LOWER(c.partnerName), LOWER(@partnerName))
               OR CONTAINS(LOWER(c.partnerNormalized), LOWER(@partnerNormalized))
        """
        parameters = [
            {"name": "@partnerName", "value": partner_name},
            {"name": "@partnerNormalized", "value": partner_normalized},
        ]

        results = []
        async for item in self.assignments_container.query_items(
            query=query,
            parameters=parameters,
        ):
            results.append(item)

        return results

    async def search_psas_by_skill(
        self,
        category: str,
        subcategory: str | None = None,
        min_level: int = 1,
    ) -> list[dict[str, Any]]:
        """Search PSAs by skill category and minimum level."""
        if not self.psas_container:
            return self._get_mock_psas_by_skill(category, subcategory, min_level)

        min_score = min_level * 100

        # Query all PSAs and filter by skill
        query = "SELECT * FROM c"
        results = []

        async for item in self.psas_container.query_items(query=query):
            skills = item.get("skills", [])
            matching_skills = [
                s
                for s in skills
                if s.get("category", "").lower() == category.lower()
                and s.get("score", 0) >= min_score
                and (subcategory is None or s.get("subcategory", "").lower() == subcategory.lower())
            ]
            if matching_skills:
                # Add matching skill info to result
                item["matchingSkills"] = matching_skills
                results.append(item)

        # Sort by highest matching skill score
        results.sort(
            key=lambda x: max(s.get("score", 0) for s in x.get("matchingSkills", [{"score": 0}])),
            reverse=True,
        )

        return results

    async def get_last_psa_for_partner(self, partner_name: str) -> dict[str, Any] | None:
        """Get the most recent PSA assignment for a partner."""
        assignments = await self.get_psas_by_partner(partner_name)
        if not assignments:
            return None

        # Sort by last assignment date and return the most recent
        assignments.sort(
            key=lambda x: x.get("lastAssignmentDate", ""),
            reverse=True,
        )

        return assignments[0] if assignments else None

    # =========================================================================
    # Mock data for development without database
    # =========================================================================

    def _get_mock_psas(
        self, specialty: str | None = None, name_filter: str | None = None
    ) -> list[dict]:
        """Return mock PSA data for development."""
        mock_data = [
            {"id": "alexandre-danoffre", "name": "Alexandre Danoffre", "specialty": "Data", "partnerCount": 4},
            {"id": "edwin-huber", "name": "Edwin Huber", "specialty": "AI", "partnerCount": 14},
            {"id": "frederic-gisbert", "name": "Frederic Gisbert", "specialty": "Data", "partnerCount": 19},
            {"id": "haroon-rashid", "name": "Haroon Rashid", "specialty": "Data", "partnerCount": 22},
            {"id": "johan-wallquist", "name": "Johan Wallquist", "specialty": "AI", "partnerCount": 8},
            {"id": "kiko-de-angel-gimeno", "name": "Kiko de Angel Gimeno", "specialty": "AI", "partnerCount": 18},
            {"id": "martin-abrle", "name": "Martin Abrle", "specialty": "AI", "partnerCount": 13},
            {"id": "raik-herrmann", "name": "Raik Herrmann", "specialty": "AI", "partnerCount": 4},
            {"id": "taras-kloba", "name": "Taras Kloba", "specialty": "Data", "partnerCount": 6},
            {"id": "zidan-m", "name": "Zidan M", "specialty": "Data", "partnerCount": 9},
        ]

        if specialty:
            mock_data = [p for p in mock_data if p["specialty"] == specialty]
        if name_filter:
            mock_data = [p for p in mock_data if name_filter.lower() in p["name"].lower()]

        return mock_data

    def _get_mock_psa(self, psa_id: str) -> dict | None:
        """Return mock PSA data for a specific ID."""
        psas = self._get_mock_psas()
        for psa in psas:
            if psa["id"] == psa_id:
                return psa
        return None

    def _get_mock_partners_for_psa(self, psa_id: str) -> list[dict]:
        """Return mock partners for a PSA."""
        mock_partners = {
            "kiko-de-angel-gimeno": [
                {"partnerId": "yooz-france", "partnerName": "Yooz", "country": "France", "lastAssignmentDate": "2026-01-20"},
                {"partnerId": "visiativ-france", "partnerName": "VISIATIV", "country": "France", "lastAssignmentDate": "2026-01-20"},
            ],
            "frederic-gisbert": [
                {"partnerId": "devoteam-france", "partnerName": "Devoteam", "country": "France", "lastAssignmentDate": "2026-01-16"},
            ],
        }
        return mock_partners.get(psa_id, [])

    def _get_mock_psas_for_partner(self, partner_name: str) -> list[dict]:
        """Return mock PSAs for a partner."""
        return [
            {"psaId": "kiko-de-angel-gimeno", "psaName": "Kiko de Angel Gimeno", "specialty": "AI"},
            {"psaId": "frederic-gisbert", "psaName": "Frederic Gisbert", "specialty": "Data"},
        ]

    def _get_mock_psas_by_skill(
        self, category: str, subcategory: str | None, min_level: int
    ) -> list[dict]:
        """Return mock PSAs filtered by skill."""
        return self._get_mock_psas()[:5]
