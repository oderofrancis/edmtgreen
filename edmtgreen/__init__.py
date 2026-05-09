"""
GreenPulse SDK
==============

Python client for the GreenPulse geospatial monitoring and reporting platform.

Quick start
-----------
    from edmtgreen import GreenPulse

    with GreenPulse(
        site     = "http://localhost:8000",
        username = "researcher_01",
        password = "s3cur3p@ss",
    ) as gp:
        uploads    = gp.get_uploads()
        workflows  = gp.get_workflows(workflow_type="ndvi")
        timeseries = gp.get_timeseries(workflow_id="abc-123")
        composites = gp.get_composites()
        collections = gp.get_collections()
        reports    = gp.get_reports()
"""

from ._client import GreenPulse,SPLITTER, STATUS
from ._exceptions import (
    APIError,
    AuthenticationError,
    GreenPulseError,
    NotFoundError,
    ValidationError,
)

__all__ = [
    # Main client
    "GreenPulse",
    # Exceptions
    "GreenPulseError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "APIError",
    # Type aliases
    "STATUS",
    "SPLITTER",
]

__version__ = "0.1.0"
