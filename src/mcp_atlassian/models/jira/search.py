"""
Jira search result models.

This module provides Pydantic models for Jira search (JQL) results.
"""

__all__ = ["JiraSearchResult"]

import logging
from typing import Any

from pydantic import Field, model_validator

from mcp_atlassian.utils import safe_int

from ..base import ApiModel
from .issue import JiraIssue

logger = logging.getLogger(__name__)


class JiraSearchResult(ApiModel):
    """
    Model representing a Jira search (JQL) result.
    """

    total: int = 0
    start_at: int = 0
    max_results: int = 0
    issues: list[JiraIssue] = Field(default_factory=list)

    @classmethod
    def from_api_response(
        cls, data: dict[str, Any], **kwargs: Any
    ) -> "JiraSearchResult":
        """
        Create a JiraSearchResult from a Jira API response.

        Args:
            data: The search result data from the Jira API
            **kwargs: Additional arguments to pass to the constructor

        Returns:
            A JiraSearchResult instance
        """
        if (default := cls._validate_data_or_default(data)) is not None:
            return default

        issues = []
        issues_data = data.get("issues", [])
        if isinstance(issues_data, list):
            for issue_data in issues_data:
                if issue_data:
                    requested_fields = kwargs.get("requested_fields")
                    issues.append(
                        JiraIssue.from_api_response(
                            issue_data, requested_fields=requested_fields
                        )
                    )

        return cls(
            total=safe_int(data.get("total"), -1),
            start_at=safe_int(data.get("startAt"), -1),
            max_results=safe_int(data.get("maxResults"), -1),
            issues=issues,
        )

    @model_validator(mode="after")
    def validate_search_result(self) -> "JiraSearchResult":
        """
        Validate the search result.

        This validator ensures that pagination values are sensible and
        consistent with the number of issues returned.

        Returns:
            The validated JiraSearchResult instance
        """
        # Ensure non-negative pagination values
        if self.start_at < 0:
            self.start_at = 0
        if self.max_results < 0:
            self.max_results = 0
        # Note: total can be -1 for v3 cloud API which doesn't provide counts
        if self.total < -1:
            self.total = -1
        return self

    def to_simplified_dict(self) -> dict[str, Any]:
        """Convert to simplified dictionary for API response."""
        return {
            "total": self.total,
            "start_at": self.start_at,
            "max_results": self.max_results,
            "issues": [issue.to_simplified_dict() for issue in self.issues],
        }
