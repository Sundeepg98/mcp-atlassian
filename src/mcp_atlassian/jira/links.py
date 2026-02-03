"""Module for Jira issue link operations."""

import logging
from typing import Any

from requests.exceptions import HTTPError

from ..exceptions import MCPAtlassianAPIError
from ..models.jira import JiraIssueLinkType
from ..utils.errors import raise_for_auth_error, wrap_http_error
from .client import JiraClient

logger = logging.getLogger("mcp-jira")


class LinksMixin(JiraClient):
    """Mixin for Jira issue link operations."""

    def get_issue_link_types(self) -> list[JiraIssueLinkType]:
        """
        Get all available issue link types.

        Returns:
            List of JiraIssueLinkType objects

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails with the Jira API
                (401/403)
            Exception: If there is an error retrieving issue link types
        """
        try:
            link_types_response = self.jira.get("rest/api/2/issueLinkType")
            if not isinstance(link_types_response, dict):
                msg = f"Unexpected return value type from `jira.get`: {type(link_types_response)}"
                logger.error(msg)
                raise TypeError(msg)

            link_types_data = link_types_response.get("issueLinkTypes", [])

            link_types = [
                JiraIssueLinkType.from_api_response(link_type)
                for link_type in link_types_data
            ]

            return link_types

        except HTTPError as http_err:
            raise_for_auth_error(http_err, "getting issue link types")
            raise wrap_http_error(http_err, "getting issue link types") from http_err
        except Exception as e:
            msg = f"Error getting issue link types: {e}"
            logger.error(msg, exc_info=True)
            raise MCPAtlassianAPIError(msg) from e

    def create_issue_link(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a link between two issues.

        Args:
            data: A dictionary containing the link data with the following structure:
                {
                    "type": {"name": "Duplicate" },  # Link type name (e.g., "Duplicate", "Blocks", "Relates to")
                    "inwardIssue": { "key": "ISSUE-1"},  # The issue that is the source of the link
                    "outwardIssue": {"key": "ISSUE-2"},  # The issue that is the target of the link
                    "comment": {  # Optional comment to add to the link
                        "body": "Linked related issue!",
                        "visibility": {  # Optional visibility settings
                            "type": "group",
                            "value": "jira-software-users"
                        }
                    }
                }

        Returns:
            Dictionary with the created link information

        Raises:
            ValueError: If required fields are missing
            MCPAtlassianAuthenticationError: If authentication fails with the Jira API (401/403)
            Exception: If there is an error creating the issue link
        """
        # Validate required fields
        if not data.get("type"):
            raise ValueError("Link type is required")
        if not data.get("inwardIssue") or not data["inwardIssue"].get("key"):
            raise ValueError("Inward issue key is required")
        if not data.get("outwardIssue") or not data["outwardIssue"].get("key"):
            raise ValueError("Outward issue key is required")

        try:
            # Create the issue link
            self.jira.create_issue_link(data)

            # Return a response with the link information
            response = {
                "success": True,
                "message": f"Link created between {data['inwardIssue']['key']} and {data['outwardIssue']['key']}",
                "link_type": data["type"]["name"],
                "inward_issue": data["inwardIssue"]["key"],
                "outward_issue": data["outwardIssue"]["key"],
            }

            return response

        except HTTPError as http_err:
            raise_for_auth_error(http_err, "creating issue link")
            raise wrap_http_error(http_err, "creating issue link") from http_err
        except Exception as e:
            msg = f"Error creating issue link: {e}"
            logger.error(msg, exc_info=True)
            raise MCPAtlassianAPIError(msg) from e

    def create_remote_issue_link(
        self, issue_key: str, link_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a remote issue link (web link or Confluence link) for an issue.

        Args:
            issue_key: The key of the issue to add the link to (e.g., 'PROJ-123')
            link_data: A dictionary containing the remote link data with the following structure:
                {
                    "object": {
                        "url": "https://example.com/page",  # The URL to link to
                        "title": "Example Page",  # The title/name of the link
                        "summary": "Optional description of the link",  # Optional description
                        "icon": {  # Optional icon configuration
                            "url16x16": "https://example.com/icon16.png",
                            "title": "Icon Title"
                        }
                    },
                    "relationship": "causes"  # Optional relationship description
                }

        Returns:
            Dictionary with the created remote link information

        Raises:
            ValueError: If required fields are missing
            MCPAtlassianAuthenticationError: If authentication fails with the Jira API (401/403)
            Exception: If there is an error creating the remote issue link
        """
        # Validate required fields
        if not issue_key:
            raise ValueError("Issue key is required")
        if not link_data.get("object"):
            raise ValueError("Link object is required")
        if not link_data["object"].get("url"):
            raise ValueError("URL is required in link object")
        if not link_data["object"].get("title"):
            raise ValueError("Title is required in link object")

        try:
            # Create the remote issue link using the Jira API
            endpoint = f"rest/api/3/issue/{issue_key}/remotelink"
            response = self.jira.post(endpoint, json=link_data)

            # Return a response with the link information
            result = {
                "success": True,
                "message": f"Remote link created for issue {issue_key}",
                "issue_key": issue_key,
                "link_title": link_data["object"]["title"],
                "link_url": link_data["object"]["url"],
                "relationship": link_data.get("relationship", ""),
            }

            return result

        except HTTPError as http_err:
            raise_for_auth_error(http_err, f"creating remote issue link for {issue_key}")
            raise wrap_http_error(
                http_err, f"creating remote issue link for {issue_key}"
                ) from http_err
        except Exception as e:
            msg = f"Error creating remote issue link: {e}"
            logger.error(msg, exc_info=True)
            raise MCPAtlassianAPIError(msg) from e

    def remove_issue_link(self, link_id: str) -> dict[str, Any]:
        """
        Remove a link between two issues.

        Args:
            link_id: The ID of the link to remove

        Returns:
            Dictionary with the result of the operation

        Raises:
            ValueError: If link_id is empty
            MCPAtlassianAuthenticationError: If authentication fails with the Jira API (401/403)
            Exception: If there is an error removing the issue link
        """
        # Validate input
        if not link_id:
            raise ValueError("Link ID is required")

        try:
            # Remove the issue link
            self.jira.remove_issue_link(link_id)

            # Return a response indicating success
            response = {
                "success": True,
                "message": f"Link with ID {link_id} has been removed",
                "link_id": link_id,
            }

            return response

        except HTTPError as http_err:
            raise_for_auth_error(http_err, f"removing issue link {link_id}")
            raise wrap_http_error(http_err, f"removing issue link {link_id}") from http_err
        except Exception as e:
            msg = f"Error removing issue link: {e}"
            logger.error(msg, exc_info=True)
            raise MCPAtlassianAPIError(msg) from e
