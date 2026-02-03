"""
Jira version models.

This module provides Pydantic models for Jira project versions.
"""

__all__ = ["JiraVersion"]

import logging
from typing import Any

from ..base import ApiModel

logger = logging.getLogger(__name__)


class JiraVersion(ApiModel):
    """
    Model representing a Jira project version (fix version).
    """

    id: str
    name: str
    description: str | None = None
    startDate: str | None = None  # noqa: N815
    releaseDate: str | None = None  # noqa: N815
    released: bool = False
    archived: bool = False

    @classmethod
    def _validate_data_or_default(cls, data: Any) -> "JiraVersion | None":
        """Override base validation to provide required field defaults.

        JiraVersion has required fields (id, name) without defaults,
        so we must provide them explicitly when returning a default instance.
        """
        if not data or not isinstance(data, dict):
            return cls(id="", name="")
        return None

    @classmethod
    def from_api_response(cls, data: dict[str, Any], **kwargs: Any) -> "JiraVersion":
        """Create JiraVersion from API response.

        Args:
            data: API response dictionary containing version data
            **kwargs: Additional keyword arguments (ignored)

        Returns:
            JiraVersion instance
        """
        if (default := cls._validate_data_or_default(data)) is not None:
            return default

        # Safe extraction with type coercion
        version_id = data.get("id")
        version_id = str(version_id) if version_id is not None else ""

        version_name = data.get("name")
        version_name = str(version_name) if version_name is not None else ""

        return cls(
            id=version_id,
            name=version_name,
            description=data.get("description"),
            startDate=data.get("startDate"),
            releaseDate=data.get("releaseDate"),
            released=bool(data.get("released", False)),
            archived=bool(data.get("archived", False)),
        )

    def to_simplified_dict(self) -> dict[str, Any]:
        """Convert to simple dict for API output."""
        result = {
            "id": self.id,
            "name": self.name,
            "released": self.released,
            "archived": self.archived,
        }
        if self.description is not None:
            result["description"] = self.description
        if self.startDate is not None:
            result["startDate"] = self.startDate
        if self.releaseDate is not None:
            result["releaseDate"] = self.releaseDate
        return result
