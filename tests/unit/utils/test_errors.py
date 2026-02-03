"""Tests for the error handling utilities module."""

from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import HTTPError

from mcp_atlassian.exceptions import (
    MCPAtlassianAPIError,
    MCPAtlassianAuthenticationError,
    MCPAtlassianNotFoundError,
    MCPAtlassianPermissionError,
    MCPAtlassianRateLimitError,
    MCPAtlassianValidationError,
)
from mcp_atlassian.utils.errors import (
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


class FakeHTTPError(HTTPError):
    """A real HTTPError subclass for testing that supports 'from' chaining."""

    def __init__(self, status_code: int, text: str, headers: dict, content: bytes):
        """Create a fake HTTPError with configurable response properties."""
        super().__init__(f"HTTP Error {status_code}")
        self._status_code = status_code
        self._text = text
        self._headers = headers
        self._content = content

        # Create a mock response object
        self.response = MagicMock()
        self.response.status_code = status_code
        self.response.text = text
        self.response.headers = headers
        self.response.content = content


class MockHTTPError:
    """Factory for creating mock HTTPError objects."""

    @staticmethod
    def create(
        status_code: int,
        text: str = "Error response",
        headers: dict | None = None,
        content: bytes | None = None,
    ) -> FakeHTTPError:
        """Create a FakeHTTPError with configurable properties."""
        return FakeHTTPError(
            status_code=status_code,
            text=text,
            headers=headers or {},
            content=content or text.encode(),
        )

    @staticmethod
    def create_without_response() -> FakeHTTPError:
        """Create FakeHTTPError with response=None."""
        error = FakeHTTPError(
            status_code=0, text="", headers={}, content=b""
        )
        error.response = None
        return error


class TestGetHttpStatusCode:
    """Tests for get_http_status_code function."""

    def test_returns_status_code_when_response_exists(self):
        """Test that status code is extracted correctly."""
        http_err = MockHTTPError.create(status_code=404)
        assert get_http_status_code(http_err) == 404

    def test_returns_none_when_response_is_none(self):
        """Test that None is returned when response is None."""
        http_err = MockHTTPError.create_without_response()
        assert get_http_status_code(http_err) is None

    @pytest.mark.parametrize(
        "status_code", [200, 201, 400, 401, 403, 404, 429, 500, 502, 503, 504]
    )
    def test_returns_various_status_codes(self, status_code):
        """Test extraction of various HTTP status codes."""
        http_err = MockHTTPError.create(status_code=status_code)
        assert get_http_status_code(http_err) == status_code


class TestIsAuthError:
    """Tests for is_auth_error function."""

    def test_returns_true_for_401(self):
        """Test that 401 is recognized as auth error."""
        http_err = MockHTTPError.create(status_code=401)
        assert is_auth_error(http_err) is True

    def test_returns_true_for_403(self):
        """Test that 403 is recognized as auth error."""
        http_err = MockHTTPError.create(status_code=403)
        assert is_auth_error(http_err) is True

    @pytest.mark.parametrize("status_code", [200, 400, 404, 429, 500])
    def test_returns_false_for_non_auth_codes(self, status_code):
        """Test that non-auth status codes return False."""
        http_err = MockHTTPError.create(status_code=status_code)
        assert is_auth_error(http_err) is False

    def test_returns_false_when_response_is_none(self):
        """Test that False is returned when response is None."""
        http_err = MockHTTPError.create_without_response()
        assert is_auth_error(http_err) is False


class TestRaiseForAuthError:
    """Tests for raise_for_auth_error function."""

    def test_raises_authentication_error_for_401(self):
        """Test that 401 raises MCPAtlassianAuthenticationError."""
        http_err = MockHTTPError.create(status_code=401)
        with pytest.raises(MCPAtlassianAuthenticationError) as exc_info:
            raise_for_auth_error(http_err, "retrieving issue")
        assert "401" in str(exc_info.value)
        assert "retrieving issue" in str(exc_info.value)
        assert exc_info.value.__cause__ is http_err

    def test_raises_permission_error_for_403(self):
        """Test that 403 raises MCPAtlassianPermissionError."""
        http_err = MockHTTPError.create(status_code=403)
        with pytest.raises(MCPAtlassianPermissionError) as exc_info:
            raise_for_auth_error(http_err, "updating page")
        assert "403" in str(exc_info.value)
        assert "updating page" in str(exc_info.value)
        assert exc_info.value.__cause__ is http_err

    @pytest.mark.parametrize("status_code", [200, 400, 404, 429, 500])
    def test_does_not_raise_for_non_auth_codes(self, status_code):
        """Test that non-auth status codes don't raise."""
        http_err = MockHTTPError.create(status_code=status_code)
        # Should not raise
        raise_for_auth_error(http_err, "some operation")

    def test_does_not_raise_when_response_is_none(self):
        """Test that no exception is raised when response is None."""
        http_err = MockHTTPError.create_without_response()
        # Should not raise
        raise_for_auth_error(http_err, "some operation")

    def test_error_message_format_without_operation(self):
        """Test error message format when operation is not provided."""
        http_err = MockHTTPError.create(status_code=401)
        with pytest.raises(MCPAtlassianAuthenticationError) as exc_info:
            raise_for_auth_error(http_err)
        assert "while" not in str(exc_info.value)


class TestWrapHttpError:
    """Tests for wrap_http_error function."""

    def test_returns_api_error_with_status_code(self):
        """Test that API error is created with correct status code."""
        http_err = MockHTTPError.create(status_code=500)
        result = wrap_http_error(http_err, "fetching data")
        assert isinstance(result, MCPAtlassianAPIError)
        assert result.status_code == 500

    def test_error_message_includes_operation(self):
        """Test that error message includes the operation description."""
        http_err = MockHTTPError.create(status_code=500)
        result = wrap_http_error(http_err, "creating issue")
        assert "creating issue" in str(result)
        assert "500" in str(result)

    def test_handles_none_response(self):
        """Test handling when response is None."""
        http_err = MockHTTPError.create_without_response()
        result = wrap_http_error(http_err, "operation")
        assert isinstance(result, MCPAtlassianAPIError)
        assert result.status_code is None

    def test_logs_error_without_traceback_by_default(self):
        """Test that error is logged without traceback by default."""
        http_err = MockHTTPError.create(status_code=500)
        with patch("mcp_atlassian.utils.errors.logger") as mock_logger:
            wrap_http_error(http_err, "test operation")
            mock_logger.error.assert_called_once()
            args, kwargs = mock_logger.error.call_args
            assert kwargs.get("exc_info") is False

    def test_logs_error_with_traceback_when_requested(self):
        """Test that traceback is logged when log_exc_info=True."""
        http_err = MockHTTPError.create(status_code=500)
        with patch("mcp_atlassian.utils.errors.logger") as mock_logger:
            wrap_http_error(http_err, "test operation", log_exc_info=True)
            args, kwargs = mock_logger.error.call_args
            assert kwargs.get("exc_info") is True


class TestGetResponseText:
    """Tests for get_response_text function."""

    def test_returns_response_text(self):
        """Test that response text is extracted correctly."""
        http_err = MockHTTPError.create(status_code=400, text="Bad request details")
        assert get_response_text(http_err) == "Bad request details"

    def test_truncates_at_max_length(self):
        """Test that response text is truncated at max_length."""
        long_text = "x" * 1000
        http_err = MockHTTPError.create(status_code=400, text=long_text)
        result = get_response_text(http_err, max_length=100)
        assert len(result) == 100
        assert result == "x" * 100

    def test_returns_empty_string_when_response_is_none(self):
        """Test that empty string is returned when response is None."""
        http_err = MockHTTPError.create_without_response()
        assert get_response_text(http_err) == ""

    def test_handles_empty_text(self):
        """Test handling of empty response text."""
        http_err = MockHTTPError.create(status_code=400, text="")
        result = get_response_text(http_err)
        assert result == ""

    def test_default_max_length(self):
        """Test that default max_length is 500."""
        long_text = "x" * 600
        http_err = MockHTTPError.create(status_code=400, text=long_text)
        result = get_response_text(http_err)
        assert len(result) == 500


class TestRaiseForNotFound:
    """Tests for raise_for_not_found function."""

    def test_raises_not_found_error_for_404(self):
        """Test that 404 raises MCPAtlassianNotFoundError."""
        http_err = MockHTTPError.create(status_code=404)
        with pytest.raises(MCPAtlassianNotFoundError) as exc_info:
            raise_for_not_found(http_err, "Issue", "TEST-123", "fetching")
        assert exc_info.value.resource_type == "Issue"
        assert exc_info.value.identifier == "TEST-123"
        assert exc_info.value.__cause__ is http_err

    @pytest.mark.parametrize("status_code", [200, 400, 401, 403, 429, 500])
    def test_does_not_raise_for_non_404_codes(self, status_code):
        """Test that non-404 status codes don't raise."""
        http_err = MockHTTPError.create(status_code=status_code)
        # Should not raise
        raise_for_not_found(http_err, "Issue", "TEST-123")

    def test_error_message_format(self):
        """Test error message includes all context."""
        http_err = MockHTTPError.create(status_code=404)
        with pytest.raises(MCPAtlassianNotFoundError) as exc_info:
            raise_for_not_found(http_err, "Page", "12345", "retrieving content")
        error_msg = str(exc_info.value)
        assert "404" in error_msg
        assert "Page" in error_msg
        assert "12345" in error_msg


class TestRaiseForRateLimit:
    """Tests for raise_for_rate_limit function."""

    def test_raises_rate_limit_error_for_429(self):
        """Test that 429 raises MCPAtlassianRateLimitError."""
        http_err = MockHTTPError.create(status_code=429)
        with pytest.raises(MCPAtlassianRateLimitError) as exc_info:
            raise_for_rate_limit(http_err, "Jira API")
        assert "429" in str(exc_info.value)
        assert exc_info.value.__cause__ is http_err

    def test_extracts_retry_after_header(self):
        """Test that Retry-After header is extracted."""
        http_err = MockHTTPError.create(
            status_code=429, headers={"Retry-After": "60"}
        )
        with pytest.raises(MCPAtlassianRateLimitError) as exc_info:
            raise_for_rate_limit(http_err)
        assert exc_info.value.retry_after == 60

    def test_handles_invalid_retry_after_header(self):
        """Test handling of invalid Retry-After header value."""
        http_err = MockHTTPError.create(
            status_code=429, headers={"Retry-After": "invalid"}
        )
        with pytest.raises(MCPAtlassianRateLimitError) as exc_info:
            raise_for_rate_limit(http_err)
        # Should not fail, retry_after should be None
        assert exc_info.value.retry_after is None

    def test_handles_missing_retry_after_header(self):
        """Test handling when Retry-After header is missing."""
        http_err = MockHTTPError.create(status_code=429)
        with pytest.raises(MCPAtlassianRateLimitError) as exc_info:
            raise_for_rate_limit(http_err)
        assert exc_info.value.retry_after is None

    @pytest.mark.parametrize("status_code", [200, 400, 401, 403, 404, 500])
    def test_does_not_raise_for_non_429_codes(self, status_code):
        """Test that non-429 status codes don't raise."""
        http_err = MockHTTPError.create(status_code=status_code)
        # Should not raise
        raise_for_rate_limit(http_err)


class TestRaiseForBadRequest:
    """Tests for raise_for_bad_request function."""

    def test_raises_validation_error_for_400(self):
        """Test that 400 raises MCPAtlassianValidationError."""
        http_err = MockHTTPError.create(status_code=400, text="Field is required")
        with pytest.raises(MCPAtlassianValidationError) as exc_info:
            raise_for_bad_request(http_err, "creating issue")
        assert "400" in str(exc_info.value)
        assert exc_info.value.__cause__ is http_err

    def test_includes_response_text_by_default(self):
        """Test that response text is included in error message."""
        http_err = MockHTTPError.create(status_code=400, text="Missing summary field")
        with pytest.raises(MCPAtlassianValidationError) as exc_info:
            raise_for_bad_request(http_err, "creating issue")
        assert "Missing summary field" in str(exc_info.value)

    def test_excludes_response_text_when_requested(self):
        """Test that response text can be excluded from error message."""
        http_err = MockHTTPError.create(status_code=400, text="Secret details")
        with pytest.raises(MCPAtlassianValidationError) as exc_info:
            raise_for_bad_request(http_err, "creating issue", include_response=False)
        assert "Secret details" not in str(exc_info.value)

    @pytest.mark.parametrize("status_code", [200, 401, 403, 404, 429, 500])
    def test_does_not_raise_for_non_400_codes(self, status_code):
        """Test that non-400 status codes don't raise."""
        http_err = MockHTTPError.create(status_code=status_code)
        # Should not raise
        raise_for_bad_request(http_err, "creating issue")


class TestRaiseForServerError:
    """Tests for raise_for_server_error function."""

    @pytest.mark.parametrize("status_code", [500, 502, 503, 504])
    def test_raises_api_error_for_5xx_codes(self, status_code):
        """Test that 5xx status codes raise MCPAtlassianAPIError."""
        http_err = MockHTTPError.create(status_code=status_code)
        with pytest.raises(MCPAtlassianAPIError) as exc_info:
            raise_for_server_error(http_err, "fetching data", "Jira")
        assert exc_info.value.status_code == status_code
        assert exc_info.value.is_retryable is True
        assert exc_info.value.__cause__ is http_err

    def test_error_message_includes_service_name(self):
        """Test that error message includes service name."""
        http_err = MockHTTPError.create(status_code=500)
        with pytest.raises(MCPAtlassianAPIError) as exc_info:
            raise_for_server_error(http_err, "fetching data", "Confluence")
        assert "Confluence" in str(exc_info.value)

    def test_error_message_includes_response_text(self):
        """Test that error message includes response text."""
        http_err = MockHTTPError.create(status_code=500, text="Internal server error")
        with pytest.raises(MCPAtlassianAPIError) as exc_info:
            raise_for_server_error(http_err, "fetching data")
        assert "Internal server error" in str(exc_info.value)

    @pytest.mark.parametrize("status_code", [200, 400, 401, 403, 404, 429, 499])
    def test_does_not_raise_for_non_5xx_codes(self, status_code):
        """Test that non-5xx status codes don't raise."""
        http_err = MockHTTPError.create(status_code=status_code)
        # Should not raise
        raise_for_server_error(http_err, "operation")

    def test_handles_none_response(self):
        """Test handling when response is None."""
        http_err = MockHTTPError.create_without_response()
        # Should not raise (status_code is None, which is not in 5xx range)
        raise_for_server_error(http_err, "operation")
