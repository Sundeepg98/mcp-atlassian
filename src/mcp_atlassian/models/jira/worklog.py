"""
Jira worklog models.

This module provides Pydantic models for Jira worklogs (time tracking entries).
"""

__all__ = ["JiraWorklog"]

import logging
from typing import Any

from mcp_atlassian.utils import safe_int

from ..base import ApiModel, TimestampMixin
from ..constants import (
    EMPTY_STRING,
    JIRA_DEFAULT_ID,
)
from .adf import adf_to_text
from .common import JiraUser

logger = logging.getLogger(__name__)


class JiraWorklog(ApiModel, TimestampMixin):
    """
    Model representing a Jira worklog entry.

    This model contains information about time spent on an issue,
    including the author, time spent, and related metadata.
    """

    id: str = JIRA_DEFAULT_ID
    author: JiraUser | None = None
    comment: str | None = None
    created: str = EMPTY_STRING
    updated: str = EMPTY_STRING
    started: str = EMPTY_STRING
    time_spent: str = EMPTY_STRING
    time_spent_seconds: int = 0

    @classmethod
    def from_api_response(cls, data: dict[str, Any], **kwargs: Any) -> "JiraWorklog":
        """
        Create a JiraWorklog from a Jira API response.

        Args:
            data: The worklog data from the Jira API

        Returns:
            A JiraWorklog instance
        """
        if (default := cls._validate_data_or_default(data)) is not None:
            return default

        # Extract author data
        author = None
        author_data = data.get("author")
        if author_data:
            author = JiraUser.from_api_response(author_data)

        # Ensure ID is a string
        worklog_id = data.get("id", JIRA_DEFAULT_ID)
        if worklog_id is not None:
            worklog_id = str(worklog_id)

        # Handle comment - convert from ADF if needed
        raw_comment = data.get("comment")
        comment: str | None = None
        if isinstance(raw_comment, dict):
            # Comment is in ADF format, convert to text
            comment = adf_to_text(raw_comment)
        elif isinstance(raw_comment, str):
            comment = raw_comment
        # else: comment remains None

        return cls(
            id=worklog_id,
            author=author,
            comment=comment,
            created=str(data.get("created", EMPTY_STRING)),
            updated=str(data.get("updated", EMPTY_STRING)),
            started=str(data.get("started", EMPTY_STRING)),
            time_spent=str(data.get("timeSpent", EMPTY_STRING)),
            time_spent_seconds=safe_int(data.get("timeSpentSeconds"), 0),
        )

    def to_simplified_dict(self) -> dict[str, Any]:
        """Convert to simplified dictionary for API response."""
        result = {
            "time_spent": self.time_spent,
            "time_spent_seconds": self.time_spent_seconds,
        }

        if self.author:
            result["author"] = self.author.to_simplified_dict()

        if self.comment:
            result["comment"] = self.comment

        if self.started:
            result["started"] = self.started

        if self.created:
            result["created"] = self.created

        if self.updated:
            result["updated"] = self.updated

        return result
