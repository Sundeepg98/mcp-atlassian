"""Retry utilities with exponential backoff for MCP Atlassian.

This module provides a decorator for adding retry logic with exponential
backoff to functions that make HTTP requests. It handles transient failures
like rate limiting (429), server errors (5xx), and network issues.
"""

import logging
import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from requests.exceptions import ConnectionError, HTTPError, Timeout

from mcp_atlassian.exceptions import MCPAtlassianRateLimitError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# HTTP status codes that should trigger a retry
RETRYABLE_STATUS_CODES: set[int] = {429, 500, 502, 503, 504}

# Exception types that should trigger a retry
RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    ConnectionError,
    Timeout,
    MCPAtlassianRateLimitError,
)


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> Callable[[F], F]:
    """Decorator for adding retry logic with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts before giving up (default: 3)
        base_delay: Initial delay in seconds between retries (default: 1.0)
        max_delay: Maximum delay in seconds between retries (default: 60.0)
        exponential_base: Base for exponential backoff calculation (default: 2.0)
        jitter: Whether to add random jitter to delay (default: True)

    Returns:
        Decorated function with retry logic

    Example:
        @with_retry(max_attempts=5, base_delay=2.0)
        def fetch_data():
            return requests.get("https://api.example.com/data")
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except HTTPError as e:
                    if (
                        e.response is not None
                        and e.response.status_code in RETRYABLE_STATUS_CODES
                    ):
                        last_exception = e
                        delay = _calculate_delay(
                            attempt, base_delay, max_delay, exponential_base, jitter
                        )

                        # Honor Retry-After header for 429 responses
                        if e.response.status_code == 429:
                            retry_after = e.response.headers.get("Retry-After")
                            if retry_after:
                                try:
                                    delay = min(float(retry_after), max_delay)
                                except ValueError:
                                    pass  # Might be a date string, use calculated delay

                        if attempt < max_attempts - 1:
                            logger.warning(
                                f"Attempt {attempt + 1}/{max_attempts} failed with "
                                f"HTTP {e.response.status_code}, retrying in {delay:.2f}s"
                            )
                            time.sleep(delay)
                    else:
                        # Non-retryable HTTP error, re-raise immediately
                        raise
                except RETRYABLE_EXCEPTIONS as e:
                    last_exception = e
                    delay = _calculate_delay(
                        attempt, base_delay, max_delay, exponential_base, jitter
                    )

                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed with "
                            f"{type(e).__name__}, retrying in {delay:.2f}s"
                        )
                        time.sleep(delay)

            # All attempts exhausted, raise the last exception
            if last_exception is not None:
                logger.error(
                    f"All {max_attempts} attempts failed for {func.__name__}"
                )
                raise last_exception

            # Should never reach here, but satisfy type checker
            raise RuntimeError("Unexpected state in retry logic")

        return wrapper  # type: ignore[return-value]

    return decorator


def _calculate_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    exponential_base: float,
    jitter: bool,
) -> float:
    """Calculate the delay before the next retry attempt.

    Uses exponential backoff with optional jitter to prevent thundering herd.

    Args:
        attempt: Zero-based attempt number
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Whether to add random jitter

    Returns:
        Delay in seconds
    """
    # Calculate exponential delay: base_delay * (exponential_base ^ attempt)
    delay = min(base_delay * (exponential_base**attempt), max_delay)

    if jitter:
        # Add jitter: multiply by random value between 0.5 and 1.5
        delay = delay * (0.5 + random.random())

    return delay
