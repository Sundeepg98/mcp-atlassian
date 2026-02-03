"""Constants specific to Jira operations."""

# Set of default fields returned by Jira read operations when no specific fields are requested.
DEFAULT_READ_JIRA_FIELDS: set[str] = {
    "summary",
    "description",
    "status",
    "assignee",
    "reporter",
    "labels",
    "priority",
    "created",
    "updated",
    "issuetype",
}

# Field name mapping: Python model name → JIRA API name
# This allows users to use either naming convention when requesting fields
PYTHON_TO_API_FIELD_MAP: dict[str, str] = {
    "issue_type": "issuetype",
    "fix_versions": "fixVersions",
    "status_category": "statusCategory",
    "due_date": "duedate",
    "resolution_date": "resolutiondate",
    "time_tracking": "timetracking",
    "issue_links": "issuelinks",
}

# Reverse mapping: JIRA API name → Python model name
API_TO_PYTHON_FIELD_MAP: dict[str, str] = {
    v: k for k, v in PYTHON_TO_API_FIELD_MAP.items()
}


# Common Epic Link field IDs (fallback when dynamic discovery fails)
# These vary by Jira instance, but these are the most commonly used
COMMON_EPIC_LINK_FIELD_IDS: list[str] = [
    "customfield_10014",  # Common in Jira Cloud
    "customfield_10008",  # Common in Jira Server
    "customfield_10100",
    "customfield_10000",
    "customfield_10001",
    "customfield_10002",
    "customfield_10003",
    "customfield_10004",
    "customfield_10005",
    "customfield_10006",
    "customfield_10007",
    "customfield_11703",
]

# Common Epic Name field IDs
COMMON_EPIC_NAME_FIELD_IDS: list[str] = [
    "customfield_10011",
    "customfield_10005",
    "customfield_10004",
]

# Common Epic Color field IDs
COMMON_EPIC_COLOR_FIELD_IDS: list[str] = [
    "customfield_10012",
    "customfield_10013",
]


def normalize_field_names(fields_str: str) -> str:
    """Convert Python field names to JIRA API field names (string input).

    Args:
        fields_str: Comma-separated string of field names, or "*all"

    Returns:
        Normalized comma-separated string with JIRA API field names

    Example:
        >>> normalize_field_names("issue_type,fix_versions")
        "issuetype,fixVersions"
    """
    if fields_str == "*all":
        return fields_str
    field_list = [f.strip() for f in fields_str.split(",")]
    normalized = [PYTHON_TO_API_FIELD_MAP.get(f, f) for f in field_list]
    return ",".join(normalized)


def normalize_field_list(fields: list[str]) -> list[str]:
    """Convert Python field names to JIRA API field names (list input).

    Args:
        fields: List of field names

    Returns:
        List with normalized JIRA API field names

    Example:
        >>> normalize_field_list(["issue_type", "fix_versions"])
        ["issuetype", "fixVersions"]
    """
    return [PYTHON_TO_API_FIELD_MAP.get(f.strip(), f.strip()) for f in fields]
