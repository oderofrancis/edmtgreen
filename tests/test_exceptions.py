"""
tests/test_exceptions.py

Verifies that every non-2xx HTTP status code is mapped to the correct
typed exception by ``GreenPulse._handle_response``.
"""

import pytest
import responses as rsps_lib

from edmtgreen import (
    APIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
)

from conftest import SITE, WORKFLOWS_URL


class TestHttpErrorMapping:
    """Each error status code raises the right SDK exception."""

    def test_400_raises_validation_error(self, client, mocked_responses):
        mocked_responses.add(
            rsps_lib.GET, WORKFLOWS_URL,
            json={"detail": "bad field value"}, status=400,
        )
        with pytest.raises(ValidationError) as exc_info:
            client.get_workflows()
        assert "bad field value" in str(exc_info.value.detail)

    def test_401_raises_authentication_error(self, client, mocked_responses):
        mocked_responses.add(
            rsps_lib.GET, WORKFLOWS_URL,
            json={"detail": "token expired"}, status=401,
        )
        with pytest.raises(AuthenticationError):
            client.get_workflows()

    def test_404_raises_not_found_error(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, status=404)
        with pytest.raises(NotFoundError):
            client.get_workflows()

    def test_500_raises_api_error_with_status_code(self, client, mocked_responses):
        mocked_responses.add(
            rsps_lib.GET, WORKFLOWS_URL,
            json={"detail": "internal server error"}, status=500,
        )
        with pytest.raises(APIError) as exc_info:
            client.get_workflows()
        assert exc_info.value.status_code == 500

    def test_204_returns_none(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, status=204)
        result = client._get("/workflows/")
        assert result is None

    def test_non_json_200_returns_raw_text(self, client, mocked_responses):
        mocked_responses.add(
            rsps_lib.GET, WORKFLOWS_URL,
            body="plain text response", status=200,
            content_type="text/plain",
        )
        result = client._get("/workflows/")
        assert result == "plain text response"
