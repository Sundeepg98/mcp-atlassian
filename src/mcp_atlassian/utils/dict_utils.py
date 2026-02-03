"""Safe nested dictionary extraction utilities for API response parsing.

This module provides helper functions for extracting values from
nested dictionaries, which is common when parsing Atlassian API responses.
"""

from typing import Any, TypeVar

T = TypeVar("T")

__all__ = ["get_nested", "get_nested_str", "get_nested_int"]


def get_nested(data: dict[str, Any], *keys: str, default: T = None) -> Any | T:
    """
    Safely extract a nested value from a dictionary.

    Traverses the dictionary using the provided keys and returns
    the value at the deepest level, or the default if any key is missing.

    Args:
        data: The dictionary to extract from
        *keys: The sequence of keys to traverse
        default: The default value if any key is missing

    Returns:
        The nested value or the default

    Examples:
        >>> get_nested({"a": {"b": {"c": 1}}}, "a", "b", "c")
        1
        >>> get_nested({"a": {}}, "a", "b", "c", default="N/A")
        'N/A'
        >>> get_nested({"author": {"displayName": "John"}}, "author", "displayName")
        'John'
    """
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def get_nested_str(data: dict[str, Any], *keys: str, default: str = "") -> str:
    """
    Extract a nested string value with string type guarantee.

    Like get_nested(), but always returns a string. Non-string values
    are converted to strings, and None returns the default.

    Args:
        data: The dictionary to extract from
        *keys: The sequence of keys to traverse
        default: The default string value

    Returns:
        The nested string value or the default

    Examples:
        >>> get_nested_str({"author": {"displayName": "John"}}, "author", "displayName")
        'John'
        >>> get_nested_str({"author": {}}, "author", "displayName", default="Unknown")
        'Unknown'
        >>> get_nested_str({"status": {"name": None}}, "status", "name")
        ''
    """
    result = get_nested(data, *keys, default=default)
    if result is None:
        return default
    return str(result)


def get_nested_int(data: dict[str, Any], *keys: str, default: int = 0) -> int:
    """
    Extract a nested integer value with int type guarantee.

    Like get_nested(), but always returns an int. Numeric strings
    are converted to integers, and invalid values return the default.

    Args:
        data: The dictionary to extract from
        *keys: The sequence of keys to traverse
        default: The default integer value

    Returns:
        The nested integer value or the default

    Examples:
        >>> get_nested_int({"issue": {"id": 123}}, "issue", "id")
        123
        >>> get_nested_int({"issue": {"id": "456"}}, "issue", "id")
        456
        >>> get_nested_int({}, "issue", "id", default=-1)
        -1
    """
    result = get_nested(data, *keys, default=default)
    if result is None:
        return default
    try:
        return int(result)
    except (ValueError, TypeError):
        return default
