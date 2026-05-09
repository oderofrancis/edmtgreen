"""
tests/test_workflows.py

Tests for ``GreenPulse.get_workflows`` — tabular workflow retrieval
and client-side filtering.
"""

import pandas as pd
import responses as rsps_lib

from conftest import WORKFLOWS_URL, WORKFLOWS_RESPONSE


class TestGetWorkflows:
    def test_returns_dataframe(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, json=WORKFLOWS_RESPONSE)
        result = client.get_workflows()
        assert isinstance(result, pd.DataFrame)

    def test_returns_all_rows_when_no_filter(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, json=WORKFLOWS_RESPONSE)
        result = client.get_workflows()
        assert len(result) == 2

    def test_index_is_reset(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, json=WORKFLOWS_RESPONSE)
        result = client.get_workflows()
        assert list(result.index) == list(range(len(result)))

    # ------------------------------------------------------------------
    # Filter by workflow_id  (keyed on "pk")
    # ------------------------------------------------------------------

    def test_filter_by_single_workflow_id(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, json=WORKFLOWS_RESPONSE)
        result = client.get_workflows(workflow_id="wf-1")
        assert len(result) == 1
        assert result.iloc[0]["pk"] == "wf-1"

    def test_filter_by_list_of_workflow_ids(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, json=WORKFLOWS_RESPONSE)
        result = client.get_workflows(workflow_id=["wf-1", "wf-2"])
        assert len(result) == 2

    def test_filter_by_unknown_workflow_id_returns_empty(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, json=WORKFLOWS_RESPONSE)
        result = client.get_workflows(workflow_id="wf-999")
        assert len(result) == 0

    # ------------------------------------------------------------------
    # Filter by workflow_session
    # ------------------------------------------------------------------

    def test_filter_by_workflow_session(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, json=WORKFLOWS_RESPONSE)
        result = client.get_workflows(workflow_session="ws-1")
        assert len(result) == 1
        assert result.iloc[0]["fields.workflow_session_id"] == "ws-1"

    # ------------------------------------------------------------------
    # Filter by session
    # ------------------------------------------------------------------

    def test_filter_by_session(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, json=WORKFLOWS_RESPONSE)
        result = client.get_workflows(session="sess-2")
        assert len(result) == 1
        assert result.iloc[0]["fields.session_id"] == "sess-2"

    # ------------------------------------------------------------------
    # Filter by workflow_type
    # ------------------------------------------------------------------

    def test_filter_by_workflow_type(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, json=WORKFLOWS_RESPONSE)
        result = client.get_workflows(workflow_type="ndvi")
        assert len(result) == 1
        assert result.iloc[0]["fields.workflow_splitter"] == "ndvi"

    def test_workflow_type_all_returns_everything(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, json=WORKFLOWS_RESPONSE)
        result = client.get_workflows(workflow_type="all")
        assert len(result) == 2

    def test_unknown_workflow_type_returns_empty(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, WORKFLOWS_URL, json=WORKFLOWS_RESPONSE)
        result = client.get_workflows(workflow_type="lst")
        assert len(result) == 0
