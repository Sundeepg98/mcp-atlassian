"""Tests for the retry utilities module."""

from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import ConnectionError, HTTPError, Timeout

from mcp_atlassian.exceptions import MCPAtlassianRateLimitError
from mcp_atlassian.utils.retry import (
    RETRYABLE_STATUS_CODES,
    _calculate_delay,
    with_retry,
)


class FakeHTTPError(HTTPError):
    """A real HTTPError subclass for testing retry logic."""

    def __init__(self, status_code: int, headers: dict | None = None):
        """Create a fake HTTPError with configurable response properties."""
        super().__init__(f"HTTP Error {status_code}")
        self.response = MagicMock()
        self.response.status_code = status_code
        self.response.headers = headers or {}


class TestWithRetryBasicBehavior:
    """Tests for basic retry decorator behavior."""

    def test_success_on_first_attempt(self):
        """Test that successful call doesn't retry."""
        call_count = 0

        @with_retry(max_attempts=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        with patch("mcp_atlassian.utils.retry.time.sleep"):
            result = successful_func()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.parametrize("status_code", list(RETRYABLE_STATUS_CODES))
    def test_retries_on_retryable_http_errors(self, status_code):
        """Test that retryable HTTP errors trigger retry."""
        call_count = 0

        @with_retry(max_attempts=3)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise FakeHTTPError(status_code)
            return "success"

        with patch("mcp_atlassian.utils.retry.time.sleep"):
            result = failing_func()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404])
    def test_no_retry_on_non_retryable_http_errors(self, status_code):
        """Test that non-retryable HTTP errors are raised immediately."""
        call_count = 0

        @with_retry(max_attempts=3)
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise FakeHTTPError(status_code)

        with patch("mcp_atlassian.utils.retry.time.sleep"):
            with pytest.raises(HTTPError):
                failing_func()

        assert call_count == 1  # No retry

    def test_retries_on_connection_error(self):
        """Test that ConnectionError triggers retry."""
        call_count = 0

        @with_retry(max_attempts=3)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        with patch("mcp_atlassian.utils.retry.time.sleep"):
            result = failing_func()

        assert result == "success"
        assert call_count == 3

    def test_retries_on_timeout(self):
        """Test that Timeout triggers retry."""
        call_count = 0

        @with_retry(max_attempts=3)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Timeout("Request timed out")
            return "success"

        with patch("mcp_atlassian.utils.retry.time.sleep"):
            result = failing_func()

        assert result == "success"
        assert call_count == 3

    def test_retries_on_rate_limit_error(self):
        """Test that MCPAtlassianRateLimitError triggers retry."""
        call_count = 0

        @with_retry(max_attempts=3)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise MCPAtlassianRateLimitError("Rate limited")
            return "success"

        with patch("mcp_atlassian.utils.retry.time.sleep"):
            result = failing_func()

        assert result == "success"
        assert call_count == 3


class TestWithRetryExhaustion:
    """Tests for retry exhaustion behavior."""

    def test_raises_last_exception_after_max_attempts(self):
        """Test that last exception is raised when all attempts fail."""

        @with_retry(max_attempts=3)
        def always_failing():
            raise FakeHTTPError(500)

        with patch("mcp_atlassian.utils.retry.time.sleep"):
            with pytest.raises(HTTPError) as exc_info:
                always_failing()

        assert "500" in str(exc_info.value)

    def test_logs_error_on_exhaustion(self):
        """Test that error is logged when all attempts fail."""

        @with_retry(max_attempts=3)
        def always_failing():
            raise FakeHTTPError(500)

        with patch("mcp_atlassian.utils.retry.time.sleep"):
            with patch("mcp_atlassian.utils.retry.logger") as mock_logger:
                with pytest.raises(HTTPError):
                    always_failing()

                # Check error was logged
                mock_logger.error.assert_called()
                error_msg = mock_logger.error.call_args[0][0]
                assert "3 attempts failed" in error_msg
                assert "always_failing" in error_msg

    def test_max_attempts_one_means_no_retry(self):
        """Test that max_attempts=1 means no retry (just one attempt)."""
        call_count = 0

        @with_retry(max_attempts=1)
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise FakeHTTPError(500)

        with patch("mcp_atlassian.utils.retry.time.sleep"):
            with pytest.raises(HTTPError):
                failing_func()

        assert call_count == 1


class TestCalculateDelay:
    """Tests for the _calculate_delay function."""

    def test_first_attempt_returns_base_delay(self):
        """Test that attempt=0 returns approximately base_delay."""
        # Without jitter
        delay = _calculate_delay(
            attempt=0,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=False,
        )
        assert delay == 1.0

    def test_exponential_growth(self):
        """Test that delay grows exponentially with each attempt."""
        delays = []
        for attempt in range(5):
            delay = _calculate_delay(
                attempt=attempt,
                base_delay=1.0,
                max_delay=1000.0,  # High max to not cap
                exponential_base=2.0,
                jitter=False,
            )
            delays.append(delay)

        assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]

    def test_delay_capped_at_max_delay(self):
        """Test that delay is capped at max_delay."""
        delay = _calculate_delay(
            attempt=10,  # Would be 1024 without cap
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=False,
        )
        assert delay == 30.0

    def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness to delay."""
        # Set random seed for reproducible test
        with patch("mcp_atlassian.utils.retry.random.random", return_value=0.5):
            # 0.5 + 0.5 = 1.0 multiplier (no change)
            delay = _calculate_delay(
                attempt=0,
                base_delay=2.0,
                max_delay=60.0,
                exponential_base=2.0,
                jitter=True,
            )
            assert delay == 2.0  # 2.0 * 1.0

        with patch("mcp_atlassian.utils.retry.random.random", return_value=0.0):
            # 0.5 + 0.0 = 0.5 multiplier
            delay = _calculate_delay(
                attempt=0,
                base_delay=2.0,
                max_delay=60.0,
                exponential_base=2.0,
                jitter=True,
            )
            assert delay == 1.0  # 2.0 * 0.5

        with patch("mcp_atlassian.utils.retry.random.random", return_value=1.0):
            # 0.5 + 1.0 = 1.5 multiplier
            delay = _calculate_delay(
                attempt=0,
                base_delay=2.0,
                max_delay=60.0,
                exponential_base=2.0,
                jitter=True,
            )
            assert delay == 3.0  # 2.0 * 1.5

    def test_jitter_false_returns_exact_delay(self):
        """Test that jitter=False returns exact calculated delay."""
        delay = _calculate_delay(
            attempt=2,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=False,
        )
        assert delay == 4.0  # 1.0 * (2^2)


class TestRetryAfterHeader:
    """Tests for Retry-After header handling."""

    def test_honors_retry_after_header_for_429(self):
        """Test that Retry-After header is honored for 429 responses."""
        call_count = 0
        sleep_delays = []

        @with_retry(max_attempts=3, base_delay=1.0)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise FakeHTTPError(429, headers={"Retry-After": "5"})
            return "success"

        def mock_sleep(delay):
            sleep_delays.append(delay)

        with patch("mcp_atlassian.utils.retry.time.sleep", side_effect=mock_sleep):
            result = failing_func()

        assert result == "success"
        assert call_count == 3
        # Both retries should use Retry-After value (5 seconds)
        assert all(d == 5.0 for d in sleep_delays)

    def test_retry_after_capped_by_max_delay(self):
        """Test that Retry-After is capped by max_delay."""
        call_count = 0
        sleep_delays = []

        @with_retry(max_attempts=2, base_delay=1.0, max_delay=10.0)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                # Server says wait 100 seconds, but our max is 10
                raise FakeHTTPError(429, headers={"Retry-After": "100"})
            return "success"

        def mock_sleep(delay):
            sleep_delays.append(delay)

        with patch("mcp_atlassian.utils.retry.time.sleep", side_effect=mock_sleep):
            result = failing_func()

        assert result == "success"
        assert sleep_delays[0] == 10.0  # Capped at max_delay

    def test_ignores_invalid_retry_after_value(self):
        """Test that invalid Retry-After values are ignored."""
        call_count = 0
        sleep_delays = []

        @with_retry(max_attempts=2, base_delay=2.0, jitter=False)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                # Invalid Retry-After value
                raise FakeHTTPError(429, headers={"Retry-After": "invalid"})
            return "success"

        def mock_sleep(delay):
            sleep_delays.append(delay)

        with patch("mcp_atlassian.utils.retry.time.sleep", side_effect=mock_sleep):
            with patch("mcp_atlassian.utils.retry.random.random", return_value=0.5):
                result = failing_func()

        assert result == "success"
        # Should use calculated delay instead of Retry-After
        assert sleep_delays[0] == 2.0  # base_delay with jitter multiplier 1.0


class TestDecoratorConfiguration:
    """Tests for decorator configuration options."""

    def test_custom_max_attempts(self):
        """Test that custom max_attempts is honored."""
        call_count = 0

        @with_retry(max_attempts=5)
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise FakeHTTPError(500)

        with patch("mcp_atlassian.utils.retry.time.sleep"):
            with pytest.raises(HTTPError):
                failing_func()

        assert call_count == 5

    def test_custom_base_delay(self):
        """Test that custom base_delay is used."""
        sleep_delays = []

        @with_retry(max_attempts=2, base_delay=5.0, jitter=False)
        def failing_func():
            raise FakeHTTPError(500)

        def mock_sleep(delay):
            sleep_delays.append(delay)

        with patch("mcp_atlassian.utils.retry.time.sleep", side_effect=mock_sleep):
            with pytest.raises(HTTPError):
                failing_func()

        assert sleep_delays[0] == 5.0

    def test_custom_max_delay(self):
        """Test that custom max_delay caps the delay."""
        sleep_delays = []

        @with_retry(
            max_attempts=2, base_delay=100.0, max_delay=5.0, jitter=False
        )
        def failing_func():
            raise FakeHTTPError(500)

        def mock_sleep(delay):
            sleep_delays.append(delay)

        with patch("mcp_atlassian.utils.retry.time.sleep", side_effect=mock_sleep):
            with pytest.raises(HTTPError):
                failing_func()

        assert sleep_delays[0] == 5.0  # Capped at max_delay

    def test_custom_exponential_base(self):
        """Test that custom exponential_base affects delay growth."""
        sleep_delays = []

        @with_retry(max_attempts=4, base_delay=1.0, exponential_base=3.0, jitter=False)
        def failing_func():
            raise FakeHTTPError(500)

        def mock_sleep(delay):
            sleep_delays.append(delay)

        with patch("mcp_atlassian.utils.retry.time.sleep", side_effect=mock_sleep):
            with pytest.raises(HTTPError):
                failing_func()

        # Delays should be: 1, 3, 9 (1 * 3^0, 1 * 3^1, 1 * 3^2)
        assert sleep_delays == [1.0, 3.0, 9.0]


class TestEdgeCases:
    """Tests for edge cases."""

    def test_preserves_function_name(self):
        """Test that decorated function preserves __name__."""

        @with_retry()
        def my_function():
            pass

        assert my_function.__name__ == "my_function"

    def test_preserves_function_docstring(self):
        """Test that decorated function preserves __doc__."""

        @with_retry()
        def my_function():
            """This is my docstring."""
            pass

        assert my_function.__doc__ == "This is my docstring."

    def test_return_value_is_passed_through(self):
        """Test that return value from successful call is returned."""

        @with_retry()
        def func_with_return():
            return {"key": "value", "number": 42}

        result = func_with_return()
        assert result == {"key": "value", "number": 42}

    def test_handles_http_error_with_none_response(self):
        """Test handling of HTTPError where response is None."""
        call_count = 0

        @with_retry(max_attempts=3)
        def failing_func():
            nonlocal call_count
            call_count += 1
            error = HTTPError("No response")
            error.response = None
            raise error

        with patch("mcp_atlassian.utils.retry.time.sleep"):
            with pytest.raises(HTTPError):
                failing_func()

        # Should not retry because response is None (can't check status code)
        assert call_count == 1

    def test_logs_warning_on_retry(self):
        """Test that warning is logged on each retry."""

        @with_retry(max_attempts=3)
        def always_failing():
            raise FakeHTTPError(500)

        with patch("mcp_atlassian.utils.retry.time.sleep"):
            with patch("mcp_atlassian.utils.retry.logger") as mock_logger:
                with pytest.raises(HTTPError):
                    always_failing()

                # Should have 2 warnings (for attempts 1 and 2)
                assert mock_logger.warning.call_count == 2
                # Check warning message format
                warning_msg = mock_logger.warning.call_args_list[0][0][0]
                assert "Attempt 1/3" in warning_msg
                assert "HTTP 500" in warning_msg
