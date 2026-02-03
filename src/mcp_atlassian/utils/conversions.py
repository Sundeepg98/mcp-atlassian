"""Safe type conversion utilities for API response parsing.

This module provides helper functions for safely converting values
from API responses to Python types with sensible defaults.
"""

from typing import Any

__all__ = ["safe_int", "safe_int_or_none", "safe_str"]


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to an integer with a fallback default.

    Args:
        value: The value to convert (can be str, int, float, or None)
        default: The default value to return if conversion fails

    Returns:
        The converted integer, or the default if conversion fails

    Examples:
        >>> safe_int("42")
        42
        >>> safe_int(None)
        0
        >>> safe_int("invalid", default=-1)
        -1
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_int_or_none(value: Any) -> int | None:
    """
    Safely convert a value to an integer, returning None on failure.

    Args:
        value: The value to convert (can be str, int, float, or None)

    Returns:
        The converted integer, or None if conversion fails

    Examples:
        >>> safe_int_or_none("42")
        42
        >>> safe_int_or_none(None)
        None
        >>> safe_int_or_none("invalid")
        None
    """
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_str(value: Any, default: str = "") -> str:
    """
    Safely convert a value to a string with a fallback default.

    Args:
        value: The value to convert
        default: The default value to return if value is None

    Returns:
        The string representation, or the default if value is None

    Examples:
        >>> safe_str(42)
        "42"
        >>> safe_str(None)
        ""
        >>> safe_str(None, default="N/A")
        "N/A"
    """
    if value is None:
        return default
    return str(value)
