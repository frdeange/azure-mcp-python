"""Core data models.

Provides base models for tool metadata and responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from http import HTTPStatus
from typing import Any


@dataclass
class ToolMetadata:
    """
    Metadata describing tool behavior for MCP clients.

    Attributes:
        read_only: Tool only reads data, no modifications.
        destructive: Tool may delete or overwrite data.
        idempotent: Multiple calls with same input produce same result.
    """

    read_only: bool = False
    destructive: bool = True
    idempotent: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to MCP-compatible metadata format."""
        return {
            "readOnly": {"value": self.read_only},
            "destructive": {"value": self.destructive},
            "idempotent": {"value": self.idempotent},
        }


@dataclass
class ToolResponse:
    """
    Response from a tool execution.

    Attributes:
        status: HTTP status code.
        message: Human-readable message.
        results: The actual data returned by the tool.
        duration_ms: Execution time in milliseconds.
    """

    status: HTTPStatus = HTTPStatus.OK
    message: str = "Success"
    results: Any = None
    duration_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "message": self.message,
            "results": self.results,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def success(cls, results: Any, message: str = "Success") -> ToolResponse:
        """Create a success response."""
        return cls(
            status=HTTPStatus.OK,
            message=message,
            results=results,
        )

    @classmethod
    def error(
        cls,
        message: str,
        status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
    ) -> ToolResponse:
        """Create an error response."""
        return cls(
            status=status,
            message=message,
            results=None,
        )
