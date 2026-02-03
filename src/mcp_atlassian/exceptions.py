"""Exception classes for MCP Atlassian."""

from typing import Any


class MCPAtlassianError(Exception):
    """Base exception for all MCP Atlassian errors."""

    pass


class MCPAtlassianAuthenticationError(MCPAtlassianError):
    """Raised when Atlassian API authentication fails (401).

    This indicates invalid or expired credentials.
    """

    pass


class MCPAtlassianPermissionError(MCPAtlassianError):
    """Raised when user lacks permission to perform an action (403).

    This indicates valid credentials but insufficient permissions.
    """

    pass


class MCPAtlassianNotFoundError(MCPAtlassianError):
    """Raised when a requested resource is not found (404).

    Examples: issue not found, user not found, space not found.
    """

    def __init__(
        self, resource_type: str, identifier: str, message: str | None = None
    ):
        self.resource_type = resource_type
        self.identifier = identifier
        if message is None:
            message = f"{resource_type} '{identifier}' not found"
        super().__init__(message)


class MCPAtlassianRateLimitError(MCPAtlassianError):
    """Raised when API rate limit is exceeded (429).

    Contains retry information when available.
    """

    def __init__(self, message: str, retry_after: int | None = None):
        self.retry_after = retry_after
        if retry_after:
            message = f"{message}. Retry after {retry_after} seconds."
        super().__init__(message)


class MCPAtlassianValidationError(MCPAtlassianError):
    """Raised when input validation fails.

    Examples: missing required fields, invalid field values, invalid transition ID.
    """

    def __init__(
        self, message: str, field: str | None = None, value: Any = None
    ):
        self.field = field
        self.value = value
        super().__init__(message)


class MCPAtlassianAPIError(MCPAtlassianError):
    """Raised for other API errors not covered by specific exceptions.

    Contains the HTTP status code when available.

    Attributes:
        status_code: HTTP status code (if applicable)
        is_retryable: Whether this error might succeed on retry (default: False)
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        is_retryable: bool = False,
    ):
        self.status_code = status_code
        self.is_retryable = is_retryable
        super().__init__(message)
