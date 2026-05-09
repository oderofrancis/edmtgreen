"""
tests/conftest.py

Shared pytest fixtures for the GreenPulse SDK test suite.

Every fixture that sets up a mocked HTTP environment lives here so
individual test modules stay focused on behaviour.
"""

import json
import pytest
import responses as rsps_lib

from edmtgreen import GreenPulse

# ---------------------------------------------------------------------------
# Constants reused across all test modules
# ---------------------------------------------------------------------------

SITE     = "http://testserver"
USERNAME = "test_user"
PASSWORD = "test_pass"
TOKEN    = "test.jwt.token"

LOGIN_URL       = f"{SITE}/api/auth/login/"
AUTH_STATUS_URL = f"{SITE}/api/auth/status/"
UPLOADS_URL     = f"{SITE}/api/uploads/"
WORKFLOWS_URL   = f"{SITE}/api/workflows/"
TIMESERIES_URL  = f"{SITE}/api/timeseries/"
COMPOSITES_URL  = f"{SITE}/api/composites/"
COLLECTIONS_URL = f"{SITE}/api/collections/"
REPORTS_URL     = f"{SITE}/api/reports/"


# ---------------------------------------------------------------------------
# Minimal JSON payloads
# ---------------------------------------------------------------------------

LOGIN_RESPONSE = {"access": TOKEN}

AUTH_STATUS_RESPONSE = {
    "valid": True,
    "user": {"username": USERNAME, "email": "test@greenpulse.io"},
}

UPLOADS_RESPONSE = {
    "type": "FeatureCollection",
    "features": [
        {
            "id": "upload-1",
            "type": "Feature",
            "geometry": {
                "type": "GeometryCollection",
                "geometries": [
                    {"type": "Point", "coordinates": [36.8219, -1.2921]},
                ],
            },
            "properties": {
                "name": "Nairobi ROI",
                "upload_session": "session-upload-1",
            },
        },
        {
            "id": "upload-2",
            "type": "Feature",
            "geometry": {
                "type": "GeometryCollection",
                "geometries": [
                    {"type": "Point", "coordinates": [37.0, -1.5]},
                ],
            },
            "properties": {
                "name": "Tsavo ROI",
                "upload_session": "session-upload-2",
            },
        },
    ],
}

WORKFLOWS_RESPONSE = [
    {
        "pk": "wf-1",
        "fields": {
            "workflow_session_id": "ws-1",
            "session_id": "sess-1",
            "workflow_splitter": "ndvi",
        },
    },
    {
        "pk": "wf-2",
        "fields": {
            "workflow_session_id": "ws-2",
            "session_id": "sess-2",
            "workflow_splitter": "evi",
        },
    },
]

TIMESERIES_RESPONSE = [
    {
        "pk": "ts-1",
        "fields": {
            "workflow_id": "wf-1",
            "workflow_session_id": "ws-1",
            "session_id": "sess-1",
            "timeseries_session": "tss-1",
            "workflow_splitter": "ndvi",
        },
    },
    {
        "pk": "ts-2",
        "fields": {
            "workflow_id": "wf-2",
            "workflow_session_id": "ws-2",
            "session_id": "sess-2",
            "timeseries_session": "tss-2",
            "workflow_splitter": "evi",
        },
    },
]

COMPOSITES_RESPONSE = [
    {
        "pk": "comp-1",
        "fields": {
            "workflow_id": "wf-1",
            "workflow_session_id": "ws-1",
            "session_id": "sess-1",
            "composite_sessions": "css-1",
            "workflow_splitter": "ndvi",
        },
    },
]

COLLECTIONS_RESPONSE = [
    {
        "pk": "col-1",
        "fields": {
            "workflow_id": "wf-1",
            "workflow_session_id": "ws-1",
            "session_id": "sess-1",
            "collection_session": "cls-1",
            "workflow_splitter": "ndvi",
        },
    },
]

REPORTS_RESPONSE = [
    {
        "pk": "rep-1",
        "fields": {
            "workflow_id": "wf-1",
            "workflow_session_id": "ws-1",
            "session_id": "sess-1",
            "report_session": "rss-1",
            "workflow_splitter": "ndvi",
        },
    },
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mocked_responses():
    """
    Activate the ``responses`` mock library for one test.

    Registers the login endpoint automatically so that constructing a
    ``GreenPulse`` instance always succeeds without real HTTP.
    """
    with rsps_lib.RequestsMock(assert_all_requests_are_fired=False) as mock:
        mock.add(rsps_lib.POST, LOGIN_URL, json=LOGIN_RESPONSE, status=200)
        yield mock


@pytest.fixture
def client(mocked_responses):
    """
    A fully authenticated ``GreenPulse`` instance backed by mocked HTTP.

    Depends on ``mocked_responses`` so the fixture chain is:
    mocked_responses → client → individual test.
    """
    return GreenPulse(site=SITE, username=USERNAME, password=PASSWORD)
