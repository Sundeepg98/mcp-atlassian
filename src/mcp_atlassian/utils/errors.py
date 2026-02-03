"""Error handling utilities for MCP Atlassian.

This module provides helper functions for consistent HTTP error handling
across the codebase, reducing duplication and ensuring uniform error messages.
"""

import logging

from requests.exceptions import HTTPError

from mcp_atlassian.exceptions import (
    MCPAtlassianAPIError,
    MCPAtlassianAuthenticationError,
    MCPAtlassianNotFoundError,
    MCPAtlassianPermissionError,
    MCPAtlassianRateLimitError,
    MCPAtlassianValidationError,
)
from mcp_atlassian.models.constants import (
    HTTP_AUTH_ERROR_CODES,
    HTTP_BAD_REQUEST,
    HTTP_NOT_FOUND,
    HTTP_RATE_LIMITED,
    HTTP_SERVER_ERROR_MAX,
    HTTP_SERVER_ERROR_MIN,
)

logger = logging.getLogger(__name__)


def get_http_status_code(http_err: HTTPError) -> int | None:
    """Extract status code from HTTPError safely.

    Args:
        http_err: The HTTPError exception

    Returns:
        The status code if available, None otherwise
    """
    return http_err.response.status_code if http_err.response is not None else None


def is_auth_error(http_err: HTTPError) -> bool:
    """Check if HTTPError is an authentication/permission error (401/403).

    Args:
        http_err: The HTTPError exception

    Returns:
        True if status code is 401 or 403
    """
    status_code = get_http_status_code(http_err)
    return status_code is not None and status_code in HTTP_AUTH_ERROR_CODES


def raise_for_auth_error(http_err: HTTPError, operation: str = "") -> None:
    """Raise MCPAtlassianAuthenticationError if http_err is 401/403.

    Call this before generic error handling to ensure auth errors propagate
    correctly. This is the recommended pattern for exception handlers:

        except HTTPError as http_err:
            raise_for_auth_error(http_err, "retrieving issue")
            # Handle non-auth errors...

    Args:
        http_err: The HTTPError exception
        operation: Optional description of the operation for error messages

    Raises:
        MCPAtlassianAuthenticationError: For 401 errors (invalid/expired token)
        MCPAtlassianPermissionError: For 403 errors (insufficient permissions)
    """
    if http_err.response is None:
        return

    status_code = http_err.response.status_code
    op_suffix = f" while {operation}" if operation else ""

    if status_code == 401:
        error_msg = (
            f"Authentication failed (401){op_suffix}. "
            "Token may be expired or invalid. Please verify credentials."
        )
        logger.error(error_msg)
        raise MCPAtlassianAuthenticationError(error_msg) from http_err

    elif status_code == 403:
        error_msg = (
            f"Permission denied (403){op_suffix}. "
            "User lacks required permissions for this operation."
        )
        logger.error(error_msg)
        raise MCPAtlassianPermissionError(error_msg) from http_err


def wrap_http_error(
    http_err: HTTPError,
    operation: str,
    log_exc_info: bool = False,
) -> MCPAtlassianAPIError:
    """Wrap an HTTPError in MCPAtlassianAPIError with proper context.

    This function creates the appropriate exception but does NOT raise it,
    allowing the caller to do additional processing before raising.

    Args:
        http_err: The HTTPError exception
        operation: Description of the operation for error messages
        log_exc_info: Whether to include traceback in error log

    Returns:
        MCPAtlassianAPIError with proper status_code and message
    """
    status_code = get_http_status_code(http_err)
    error_msg = f"HTTP error ({status_code}) {operation}: {http_err}"
    logger.error(error_msg, exc_info=log_exc_info)
    return MCPAtlassianAPIError(error_msg, status_code=status_code)


def get_response_text(http_err: HTTPError, max_length: int = 500) -> str:
    """Extract response text from HTTPError safely.

    Args:
        http_err: The HTTPError exception
        max_length: Maximum characters to return

    Returns:
        Response text (truncated if necessary), or empty string
    """
    if http_err.response is None:
        return ""
    try:
        return http_err.response.text[:max_length]
    except Exception:
        try:
            return str(http_err.response.content)[:max_length]
        except Exception:
            return ""


def raise_for_not_found(
    http_err: HTTPError,
    resource_type: str,
    identifier: str,
    operation: str = "",
) -> None:
    """Raise MCPAtlassianNotFoundError if http_err is 404.

    Args:
        http_err: The HTTPError exception
        resource_type: Type of resource (e.g., "Page", "Issue")
        identifier: Resource identifier
        operation: Optional description of the operation

    Raises:
        MCPAtlassianNotFoundError: If status code is 404
    """
    status_code = get_http_status_code(http_err)
    if status_code == HTTP_NOT_FOUND:
        op_suffix = f" during {operation}" if operation else ""
        error_msg = f"Resource not found (404): {resource_type} '{identifier}'{op_suffix}"
        logger.warning(error_msg)
        raise MCPAtlassianNotFoundError(
            resource_type=resource_type,
            identifier=identifier,
            message=error_msg,
        ) from http_err


def raise_for_rate_limit(http_err: HTTPError, service_name: str = "") -> None:
    """Raise MCPAtlassianRateLimitError if http_err is 429.

    Args:
        http_err: The HTTPError exception
        service_name: Optional service name for error message

    Raises:
        MCPAtlassianRateLimitError: If status code is 429
    """
    status_code = get_http_status_code(http_err)
    if status_code == HTTP_RATE_LIMITED:
        retry_seconds = None
        if http_err.response is not None:
            retry_header = http_err.response.headers.get("Retry-After")
            if retry_header:
                try:
                    retry_seconds = int(retry_header)
                except ValueError:
                    pass  # Header might be a date string, ignore

        service_suffix = f" for {service_name}" if service_name else ""
        error_msg = f"Rate limit exceeded (429){service_suffix}"
        logger.warning(error_msg)
        raise MCPAtlassianRateLimitError(
            error_msg, retry_after=retry_seconds
        ) from http_err


def raise_for_bad_request(
    http_err: HTTPError,
    operation: str,
    include_response: bool = True,
) -> None:
    """Raise MCPAtlassianValidationError if http_err is 400.

    Args:
        http_err: The HTTPError exception
        operation: Description of the operation
        include_response: Whether to include response text in error message

    Raises:
        MCPAtlassianValidationError: If status code is 400
    """
    status_code = get_http_status_code(http_err)
    if status_code == HTTP_BAD_REQUEST:
        response_text = get_response_text(http_err) if include_response else ""
        error_msg = f"Bad request (400) during {operation}"
        if response_text:
            error_msg = f"{error_msg}: {response_text}"
        logger.error(error_msg)
        raise MCPAtlassianValidationError(error_msg) from http_err


def raise_for_server_error(
    http_err: HTTPError,
    operation: str,
    service_name: str = "",
) -> None:
    """Raise MCPAtlassianAPIError with is_retryable=True if http_err is 5xx.

    Args:
        http_err: The HTTPError exception
        operation: Description of the operation
        service_name: Optional service name for error message

    Raises:
        MCPAtlassianAPIError: If status code is 5xx (with is_retryable=True)
    """
    status_code = get_http_status_code(http_err)
    if status_code is not None and HTTP_SERVER_ERROR_MIN <= status_code <= HTTP_SERVER_ERROR_MAX:
        response_text = get_response_text(http_err)
        service_suffix = f" from {service_name}" if service_name else ""
        error_msg = f"Server error ({status_code}){service_suffix} during {operation}"
        if response_text:
            error_msg = f"{error_msg}: {response_text}"
        logger.error(error_msg)
        raise MCPAtlassianAPIError(
            error_msg, status_code=status_code, is_retryable=True
        ) from http_err
