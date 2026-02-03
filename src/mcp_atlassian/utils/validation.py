"""API response validation utilities.

This module provides helper functions for validating API response types
and raising consistent, descriptive errors when validation fails.
"""

import logging
from typing import Any, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)

__all__ = [
    "ensure_dict_response",
    "ensure_list_response",
    "validate_api_response",
]


def ensure_dict_response(
    response: Any,
    operation: str,
    source: str = "",
) -> dict[str, Any]:
    """
    Ensure an API response is a dictionary, raising TypeError if not.

    Args:
        response: The API response to validate
        operation: Description of the operation (e.g., "jira.get_issue")
        source: Optional source identifier (e.g., "v3 API")

    Returns:
        The response as a dict if valid

    Raises:
        TypeError: If the response is not a dictionary

    Examples:
        >>> data = ensure_dict_response(api_result, "jira.jql")
        >>> data = ensure_dict_response(result, "search", source="v3 API")
    """
    if not isinstance(response, dict):
        source_suffix = f" from {source}" if source else ""
        msg = (
            f"Unexpected response type{source_suffix} from `{operation}`: "
            f"expected dict, got {type(response).__name__}"
        )
        logger.error(msg)
        raise TypeError(msg)
    return response


def ensure_list_response(
    response: Any,
    operation: str,
    source: str = "",
) -> list[Any]:
    """
    Ensure an API response is a list, raising TypeError if not.

    Args:
        response: The API response to validate
        operation: Description of the operation
        source: Optional source identifier

    Returns:
        The response as a list if valid

    Raises:
        TypeError: If the response is not a list

    Examples:
        >>> items = ensure_list_response(api_result, "jira.get_boards")
    """
    if not isinstance(response, list):
        source_suffix = f" from {source}" if source else ""
        msg = (
            f"Unexpected response type{source_suffix} from `{operation}`: "
            f"expected list, got {type(response).__name__}"
        )
        logger.error(msg)
        raise TypeError(msg)
    return response


def validate_api_response(
    response: Any,
    expected_type: type[T],
    operation: str,
    source: str = "",
) -> T:
    """
    Generic validation for API responses with flexible type checking.

    This is a more flexible version that can validate any expected type.
    For common cases, prefer ensure_dict_response() or ensure_list_response().

    Args:
        response: The API response to validate
        expected_type: The expected type (dict, list, str, etc.)
        operation: Description of the operation
        source: Optional source identifier

    Returns:
        The response cast to the expected type

    Raises:
        TypeError: If the response doesn't match the expected type

    Examples:
        >>> data = validate_api_response(result, dict, "jira.get_issue")
        >>> items = validate_api_response(result, list, "jira.search")
    """
    if not isinstance(response, expected_type):
        source_suffix = f" from {source}" if source else ""
        msg = (
            f"Unexpected response type{source_suffix} from `{operation}`: "
            f"expected {expected_type.__name__}, got {type(response).__name__}"
        )
        logger.error(msg)
        raise TypeError(msg)
    return response
