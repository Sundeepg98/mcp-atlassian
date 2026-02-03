"""
Constants and default values for model conversions.

This module centralizes all default values and fallbacks used when
converting API responses to models, eliminating "magic strings" in
the codebase and providing a single source of truth for defaults.
"""

__all__ = [
    # Common defaults
    "EMPTY_STRING",
    "UNKNOWN",
    "UNASSIGNED",
    "NONE_VALUE",
    # Jira defaults
    "JIRA_DEFAULT_ID",
    "JIRA_DEFAULT_KEY",
    "JIRA_DEFAULT_STATUS",
    "JIRA_DEFAULT_PRIORITY",
    "JIRA_DEFAULT_ISSUE_TYPE",
    "JIRA_DEFAULT_PROJECT",
    # Confluence defaults
    "CONFLUENCE_DEFAULT_ID",
    "CONFLUENCE_DEFAULT_SPACE",
    "CONFLUENCE_DEFAULT_VERSION",
    "DEFAULT_TIMESTAMP",
    # HTTP status codes
    "HTTP_AUTH_ERROR_CODES",
    "HTTP_NOT_FOUND",
    "HTTP_RATE_LIMITED",
    "HTTP_BAD_REQUEST",
    "HTTP_SERVER_ERROR_MIN",
    "HTTP_SERVER_ERROR_MAX",
]

#
# Common defaults
#
EMPTY_STRING = ""
UNKNOWN = "Unknown"
UNASSIGNED = "Unassigned"
NONE_VALUE = "None"

#
# Jira defaults
#
JIRA_DEFAULT_ID = "0"
JIRA_DEFAULT_KEY = "UNKNOWN-0"

# Status defaults
JIRA_DEFAULT_STATUS = {
    "name": UNKNOWN,
    "id": JIRA_DEFAULT_ID,
}

# Priority defaults
JIRA_DEFAULT_PRIORITY = {
    "name": NONE_VALUE,
    "id": JIRA_DEFAULT_ID,
}

# Issue type defaults
JIRA_DEFAULT_ISSUE_TYPE = {
    "name": UNKNOWN,
    "id": JIRA_DEFAULT_ID,
}

# Project defaults
JIRA_DEFAULT_PROJECT = JIRA_DEFAULT_ID

#
# Confluence defaults
#
CONFLUENCE_DEFAULT_ID = "0"

# Space defaults
CONFLUENCE_DEFAULT_SPACE = {
    "key": EMPTY_STRING,
    "name": UNKNOWN,
    "id": CONFLUENCE_DEFAULT_ID,
}

# Version defaults
CONFLUENCE_DEFAULT_VERSION = {
    "number": 0,
    "when": EMPTY_STRING,
}

# Date/Time defaults
DEFAULT_TIMESTAMP = "1970-01-01T00:00:00.000+0000"

#
# HTTP Status Codes for Error Handling
#
# Authentication error status codes (401 Unauthorized, 403 Forbidden)
# Used to detect when credentials are invalid/expired or permissions are insufficient
HTTP_AUTH_ERROR_CODES: frozenset[int] = frozenset({401, 403})

# Common HTTP status codes
HTTP_NOT_FOUND: int = 404
HTTP_RATE_LIMITED: int = 429
HTTP_BAD_REQUEST: int = 400

# Server error range
HTTP_SERVER_ERROR_MIN: int = 500
HTTP_SERVER_ERROR_MAX: int = 599
