"""Fields parameter handling utilities.

This module provides helper functions for converting and normalizing
fields parameters between different formats (list, tuple, set, string).
"""

from collections.abc import Iterable

__all__ = [
    "to_comma_separated",
    "from_comma_separated",
    "normalize_fields_param",
    "normalize_filter_string",
]


def to_comma_separated(
    value: str | list[str] | tuple[str, ...] | set[str] | None,
    default: str | None = None,
) -> str | None:
    """
    Convert a value to a comma-separated string.

    Args:
        value: The value to convert (str, list, tuple, set, or None)
        default: The default value if input is None

    Returns:
        A comma-separated string, or the default if value is None

    Examples:
        >>> to_comma_separated(["a", "b", "c"])
        'a,b,c'
        >>> to_comma_separated("a,b,c")
        'a,b,c'
        >>> to_comma_separated(None, default="id,key")
        'id,key'
        >>> to_comma_separated({"x", "y"})  # Sets are unordered
        'x,y' or 'y,x'
    """
    if value is None:
        return default
    if isinstance(value, str):
        return value
    if isinstance(value, list | tuple | set):
        return ",".join(str(item) for item in value)
    return default


def from_comma_separated(
    value: str | None,
    *,
    strip: bool = True,
) -> list[str]:
    """
    Convert a comma-separated string to a list of strings.

    Args:
        value: The comma-separated string (or None)
        strip: Whether to strip whitespace from each item

    Returns:
        A list of strings (empty list if value is None or empty)

    Examples:
        >>> from_comma_separated("a, b, c")
        ['a', 'b', 'c']
        >>> from_comma_separated("a,b,c", strip=False)
        ['a', 'b', 'c']
        >>> from_comma_separated(None)
        []
        >>> from_comma_separated("")
        []
    """
    if not value:
        return []
    if strip:
        return [item.strip() for item in value.split(",") if item.strip()]
    return [item for item in value.split(",") if item]


def normalize_fields_param(
    fields: str | Iterable[str] | None,
    default_fields: Iterable[str] | None = None,
) -> str:
    """
    Normalize a fields parameter to a comma-separated string.

    This is the primary function for handling the fields parameter
    in Jira/Confluence API calls. It handles:
    - None → uses default_fields
    - String → returns as-is
    - List/Tuple/Set → joins with commas

    Args:
        fields: The fields parameter (str, list, tuple, set, or None)
        default_fields: Default fields to use if fields is None

    Returns:
        A comma-separated string of fields

    Examples:
        >>> normalize_fields_param(["summary", "status"])
        'summary,status'
        >>> normalize_fields_param("summary,status,assignee")
        'summary,status,assignee'
        >>> normalize_fields_param(None, default_fields=["id", "key"])
        'id,key'
        >>> normalize_fields_param(None)
        ''
        >>> from mcp_atlassian.jira.constants import DEFAULT_READ_JIRA_FIELDS
        >>> normalize_fields_param(None, DEFAULT_READ_JIRA_FIELDS)  # doctest: +SKIP
        'summary,status,assignee,...'
    """
    if fields is None:
        if default_fields is None:
            return ""
        return ",".join(default_fields)

    if isinstance(fields, str):
        return fields

    # Handle any iterable (list, tuple, set, generator, etc.)
    return ",".join(str(f) for f in fields)


def normalize_filter_string(filter_string: str | None) -> list[str]:
    """
    Parse a comma-separated filter string into a list of trimmed values.

    This is used for parsing project or space filter configurations.

    Args:
        filter_string: Comma-separated string of filter values

    Returns:
        List of stripped, non-empty values

    Examples:
        >>> normalize_filter_string("PROJ1, PROJ2, PROJ3")
        ['PROJ1', 'PROJ2', 'PROJ3']
        >>> normalize_filter_string("SINGLE")
        ['SINGLE']
        >>> normalize_filter_string(None)
        []
        >>> normalize_filter_string("")
        []
    """
    return from_comma_separated(filter_string, strip=True)
