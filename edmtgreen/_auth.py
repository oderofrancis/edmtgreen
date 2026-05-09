"""
Authentication base class for the GreenPulse SDK.
Handles JWT login, session management, and logout.
"""

import logging

import requests

logger = logging.getLogger(__name__)


class GreenPulseAuth:
    """
    Simple authentication client for GreenPulse.

    Logs in on construction and attaches the JWT Bearer token to every
    subsequent request via a shared :class:`requests.Session`.

    Parameters
    ----------
    username : str
        GreenPulse account username.
    password : str
        GreenPulse account password.
    site : str
        Root server URL, e.g. ``"http://localhost:8000"``.
        Trailing slashes are stripped automatically.
    """

    def __init__(self, username: str, password: str, site: str) -> None:
        self.username = username
        self.password = password
        self.site     = site.rstrip("/")
        self.token:   str | None = None
        self.session  = requests.Session()

        self._login()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _login(self) -> None:
        """POST credentials to /api/auth/login/ and store the JWT token."""
        url = f"{self.site}/api/auth/login/"

        response = self.session.post(
            url,
            json    = {"username": self.username, "password": self.password},
            timeout = 10,
        )

        if response.status_code == 200:
            self.token = response.json().get("access")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            logger.info("Logged in as '%s'.", self.username)
        else:
            raise ValueError(
                f"Login failed for '{self.username}' at {url}. "
                f"Status: {response.status_code} — {response.text[:200]}"
            )

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def logout(self) -> None:
        """Clear the token and remove the Authorization header."""
        self.token = None
        self.session.headers.pop("Authorization", None)
        logger.info("'%s' logged out.", self.username)

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        state = "authenticated" if self.token else "unauthenticated"
        return f"<GreenPulseAuth user='{self.username}' site='{self.site}' [{state}]>"
