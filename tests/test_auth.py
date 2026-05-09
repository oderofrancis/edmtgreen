"""
tests/test_auth.py

Tests for GreenPulseAuth login/logout behaviour and GreenPulse
authentication error-handling.
"""

import pytest
import responses as rsps_lib

from greenpulse_sdk import AuthenticationError, GreenPulse

from conftest import (
    AUTH_STATUS_RESPONSE,
    AUTH_STATUS_URL,
    LOGIN_URL,
    LOGIN_RESPONSE,
    PASSWORD,
    SITE,
    TOKEN,
    USERNAME,
)


class TestLogin:
    def test_successful_login_stores_token(self, client):
        """Token is stored and injected into the session after login."""
        assert client.token == TOKEN
        assert client.session.headers["Authorization"] == f"Bearer {TOKEN}"

    def test_failed_login_raises_authentication_error(self, mocked_responses):
        """A 401 from /api/auth/login/ raises AuthenticationError."""
        mocked_responses.replace(rsps_lib.POST, LOGIN_URL, json={"detail": "bad creds"}, status=401)

        with pytest.raises(AuthenticationError):
            GreenPulse(site=SITE, username=USERNAME, password="wrong")

    def test_login_strips_trailing_slash_from_site(self, mocked_responses):
        """Trailing slashes on site are stripped so URLs are always clean."""
        gp = GreenPulse(site=f"{SITE}/", username=USERNAME, password=PASSWORD)
        assert gp.site == SITE


class TestLogout:
    def test_logout_clears_token(self, client):
        client.logout()
        assert client.token is None

    def test_logout_removes_authorization_header(self, client):
        client.logout()
        assert "Authorization" not in client.session.headers

    def test_context_manager_calls_logout(self, mocked_responses):
        """__exit__ triggers logout automatically."""
        with GreenPulse(site=SITE, username=USERNAME, password=PASSWORD) as gp:
            assert gp.token == TOKEN
        assert gp.token is None


class TestGetAuthStatus:
    def test_returns_status_dict(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, AUTH_STATUS_URL, json=AUTH_STATUS_RESPONSE)
        status = client.get_auth_status()
        assert status["valid"] is True
        assert status["user"]["username"] == USERNAME
