"""
Utility functions for the MCP Atlassian integration.
This package provides various utility functions used throughout the codebase.
"""

from .conversions import safe_int, safe_int_or_none, safe_str
from .date import parse_date
from .errors import (
    get_http_status_code,
    get_response_text,
    is_auth_error,
    raise_for_auth_error,
    raise_for_bad_request,
    raise_for_not_found,
    raise_for_rate_limit,
    raise_for_server_error,
    wrap_http_error,
)
from .io import is_read_only_mode

# Export lifecycle utilities
from .lifecycle import (
    ensure_clean_exit,
    setup_signal_handlers,
)
from .logging import setup_logging

# Export retry utilities
from .retry import with_retry

# Export OAuth utilities
from .oauth import OAuthConfig, configure_oauth_session
from .ssl import SSLIgnoreAdapter, configure_ssl_verification
from .urls import is_atlassian_cloud_url

# Export all utility functions for backward compatibility
__all__ = [
    "SSLIgnoreAdapter",
    "configure_ssl_verification",
    "is_atlassian_cloud_url",
    "is_read_only_mode",
    "setup_logging",
    "parse_date",
    "OAuthConfig",
    "configure_oauth_session",
    "setup_signal_handlers",
    "ensure_clean_exit",
    "with_retry",
    # Error handling utilities
    "get_http_status_code",
    "get_response_text",
    "is_auth_error",
    "raise_for_auth_error",
    "raise_for_bad_request",
    "raise_for_not_found",
    "raise_for_rate_limit",
    "raise_for_server_error",
    "wrap_http_error",
    # Type conversion utilities
    "safe_int",
    "safe_int_or_none",
    "safe_str",
]
