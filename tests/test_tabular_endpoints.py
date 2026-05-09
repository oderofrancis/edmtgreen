"""
tests/test_tabular_endpoints.py

Tests for the four endpoints that share ``_filter_records``:
  - get_timeseries
  - get_composites
  - get_collections
  - get_reports

Each section follows the same pattern: verify the response type, row
counts, and that every filter parameter routes to the right column.
"""

import pandas as pd
import pytest
import responses as rsps_lib

from conftest import (
    TIMESERIES_URL,  TIMESERIES_RESPONSE,
    COMPOSITES_URL,  COMPOSITES_RESPONSE,
    COLLECTIONS_URL, COLLECTIONS_RESPONSE,
    REPORTS_URL,     REPORTS_RESPONSE,
)


# ===========================================================================
# Helpers
# ===========================================================================

def _register(mock, url, payload):
    mock.add(rsps_lib.GET, url, json=payload)


# ===========================================================================
# get_timeseries
# ===========================================================================

class TestGetTimeseries:
    def test_returns_dataframe(self, client, mocked_responses):
        _register(mocked_responses, TIMESERIES_URL, TIMESERIES_RESPONSE)
        assert isinstance(client.get_timeseries(), pd.DataFrame)

    def test_returns_all_rows_unfiltered(self, client, mocked_responses):
        _register(mocked_responses, TIMESERIES_URL, TIMESERIES_RESPONSE)
        assert len(client.get_timeseries()) == 2

    def test_filter_by_workflow_id(self, client, mocked_responses):
        _register(mocked_responses, TIMESERIES_URL, TIMESERIES_RESPONSE)
        result = client.get_timeseries(workflow_id="wf-1")
        assert len(result) == 1
        assert result.iloc[0]["fields.workflow_id"] == "wf-1"

    def test_filter_by_workflow_session(self, client, mocked_responses):
        _register(mocked_responses, TIMESERIES_URL, TIMESERIES_RESPONSE)
        result = client.get_timeseries(workflow_session="ws-2")
        assert len(result) == 1
        assert result.iloc[0]["fields.workflow_session_id"] == "ws-2"

    def test_filter_by_session(self, client, mocked_responses):
        _register(mocked_responses, TIMESERIES_URL, TIMESERIES_RESPONSE)
        result = client.get_timeseries(session="sess-1")
        assert len(result) == 1

    def test_filter_by_timeseries_session(self, client, mocked_responses):
        _register(mocked_responses, TIMESERIES_URL, TIMESERIES_RESPONSE)
        result = client.get_timeseries(timeseries_session="tss-2")
        assert len(result) == 1
        assert result.iloc[0]["fields.timeseries_session"] == "tss-2"

    def test_filter_by_workflow_type(self, client, mocked_responses):
        _register(mocked_responses, TIMESERIES_URL, TIMESERIES_RESPONSE)
        result = client.get_timeseries(workflow_type="evi")
        assert len(result) == 1
        assert result.iloc[0]["fields.workflow_splitter"] == "evi"

    def test_combined_filters_are_additive(self, client, mocked_responses):
        """Two filters applied together narrow the result further."""
        _register(mocked_responses, TIMESERIES_URL, TIMESERIES_RESPONSE)
        result = client.get_timeseries(workflow_id="wf-1", workflow_type="evi")
        # wf-1 is ndvi, so combining with evi type should return nothing
        assert len(result) == 0

    def test_unknown_filter_returns_empty(self, client, mocked_responses):
        _register(mocked_responses, TIMESERIES_URL, TIMESERIES_RESPONSE)
        result = client.get_timeseries(workflow_id="does-not-exist")
        assert len(result) == 0


# ===========================================================================
# get_composites
# ===========================================================================

class TestGetComposites:
    def test_returns_dataframe(self, client, mocked_responses):
        _register(mocked_responses, COMPOSITES_URL, COMPOSITES_RESPONSE)
        assert isinstance(client.get_composites(), pd.DataFrame)

    def test_returns_all_rows_unfiltered(self, client, mocked_responses):
        _register(mocked_responses, COMPOSITES_URL, COMPOSITES_RESPONSE)
        assert len(client.get_composites()) == 1

    def test_filter_by_workflow_id(self, client, mocked_responses):
        _register(mocked_responses, COMPOSITES_URL, COMPOSITES_RESPONSE)
        result = client.get_composites(workflow_id="wf-1")
        assert len(result) == 1

    def test_filter_by_composite_session(self, client, mocked_responses):
        _register(mocked_responses, COMPOSITES_URL, COMPOSITES_RESPONSE)
        result = client.get_composites(composite_session="css-1")
        assert len(result) == 1
        assert result.iloc[0]["fields.composite_sessions"] == "css-1"

    def test_filter_by_workflow_type(self, client, mocked_responses):
        _register(mocked_responses, COMPOSITES_URL, COMPOSITES_RESPONSE)
        result = client.get_composites(workflow_type="ndvi")
        assert len(result) == 1

    def test_unknown_composite_session_returns_empty(self, client, mocked_responses):
        _register(mocked_responses, COMPOSITES_URL, COMPOSITES_RESPONSE)
        result = client.get_composites(composite_session="no-such-session")
        assert len(result) == 0


# ===========================================================================
# get_collections
# ===========================================================================

class TestGetCollections:
    def test_returns_dataframe(self, client, mocked_responses):
        _register(mocked_responses, COLLECTIONS_URL, COLLECTIONS_RESPONSE)
        assert isinstance(client.get_collections(), pd.DataFrame)

    def test_returns_all_rows_unfiltered(self, client, mocked_responses):
        _register(mocked_responses, COLLECTIONS_URL, COLLECTIONS_RESPONSE)
        assert len(client.get_collections()) == 1

    def test_filter_by_workflow_id(self, client, mocked_responses):
        _register(mocked_responses, COLLECTIONS_URL, COLLECTIONS_RESPONSE)
        result = client.get_collections(workflow_id="wf-1")
        assert len(result) == 1

    def test_filter_by_collection_session(self, client, mocked_responses):
        _register(mocked_responses, COLLECTIONS_URL, COLLECTIONS_RESPONSE)
        result = client.get_collections(collection_session="cls-1")
        assert len(result) == 1
        assert result.iloc[0]["fields.collection_session"] == "cls-1"

    def test_filter_by_workflow_type(self, client, mocked_responses):
        _register(mocked_responses, COLLECTIONS_URL, COLLECTIONS_RESPONSE)
        result = client.get_collections(workflow_type="ndvi")
        assert len(result) == 1

    def test_unknown_collection_session_returns_empty(self, client, mocked_responses):
        _register(mocked_responses, COLLECTIONS_URL, COLLECTIONS_RESPONSE)
        result = client.get_collections(collection_session="no-such")
        assert len(result) == 0


# ===========================================================================
# get_reports
# ===========================================================================

class TestGetReports:
    def test_returns_dataframe(self, client, mocked_responses):
        _register(mocked_responses, REPORTS_URL, REPORTS_RESPONSE)
        assert isinstance(client.get_reports(), pd.DataFrame)

    def test_returns_all_rows_unfiltered(self, client, mocked_responses):
        _register(mocked_responses, REPORTS_URL, REPORTS_RESPONSE)
        assert len(client.get_reports()) == 1

    def test_filter_by_workflow_id(self, client, mocked_responses):
        _register(mocked_responses, REPORTS_URL, REPORTS_RESPONSE)
        result = client.get_reports(workflow_id="wf-1")
        assert len(result) == 1

    def test_filter_by_report_session(self, client, mocked_responses):
        _register(mocked_responses, REPORTS_URL, REPORTS_RESPONSE)
        result = client.get_reports(report_session="rss-1")
        assert len(result) == 1
        assert result.iloc[0]["fields.report_session"] == "rss-1"

    def test_filter_by_workflow_type(self, client, mocked_responses):
        _register(mocked_responses, REPORTS_URL, REPORTS_RESPONSE)
        result = client.get_reports(workflow_type="ndvi")
        assert len(result) == 1

    def test_unknown_report_session_returns_empty(self, client, mocked_responses):
        _register(mocked_responses, REPORTS_URL, REPORTS_RESPONSE)
        result = client.get_reports(report_session="no-such")
        assert len(result) == 0
