"""
tests/test_uploads.py

Tests for ``GreenPulse.get_uploads`` — GeoJSON / ROI upload retrieval
and client-side filtering.
"""

import pytest
import responses as rsps_lib
import geopandas as gpd

from conftest import UPLOADS_URL, UPLOADS_RESPONSE


class TestGetUploads:
    def test_returns_geodataframe(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, UPLOADS_URL, json=UPLOADS_RESPONSE)
        result = client.get_uploads()
        assert isinstance(result, gpd.GeoDataFrame)

    def test_returns_all_rows_when_no_filter(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, UPLOADS_URL, json=UPLOADS_RESPONSE)
        result = client.get_uploads()
        assert len(result) == 2

    def test_geometry_column_is_populated(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, UPLOADS_URL, json=UPLOADS_RESPONSE)
        result = client.get_uploads()
        assert "geometry" in result.columns
        assert result["geometry"].notna().all()

    def test_crs_is_epsg_4326(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, UPLOADS_URL, json=UPLOADS_RESPONSE)
        result = client.get_uploads()
        assert result.crs.to_epsg() == 4326

    # ------------------------------------------------------------------
    # Filtering by id
    # ------------------------------------------------------------------

    def test_filter_by_single_id(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, UPLOADS_URL, json=UPLOADS_RESPONSE)
        result = client.get_uploads(id="upload-1")
        assert len(result) == 1
        assert result.iloc[0]["id"] == "upload-1"

    def test_filter_by_list_of_ids(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, UPLOADS_URL, json=UPLOADS_RESPONSE)
        result = client.get_uploads(id=["upload-1", "upload-2"])
        assert len(result) == 2

    def test_filter_by_unknown_id_returns_empty(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, UPLOADS_URL, json=UPLOADS_RESPONSE)
        result = client.get_uploads(id="does-not-exist")
        assert len(result) == 0

    # ------------------------------------------------------------------
    # Filtering by upload_session
    # ------------------------------------------------------------------

    def test_filter_by_upload_session(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, UPLOADS_URL, json=UPLOADS_RESPONSE)
        result = client.get_uploads(upload_session="session-upload-2")
        assert len(result) == 1
        assert result.iloc[0]["properties.upload_session"] == "session-upload-2"

    # ------------------------------------------------------------------
    # Filtering by name — with warning
    # ------------------------------------------------------------------

    def test_filter_by_name_emits_user_warning(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, UPLOADS_URL, json=UPLOADS_RESPONSE)
        with pytest.warns(UserWarning, match="unstable"):
            client.get_uploads(name="Nairobi ROI")

    def test_filter_by_name_returns_correct_row(self, client, mocked_responses):
        mocked_responses.add(rsps_lib.GET, UPLOADS_URL, json=UPLOADS_RESPONSE)
        with pytest.warns(UserWarning):
            result = client.get_uploads(name="Tsavo ROI")
        assert len(result) == 1
        assert result.iloc[0]["properties.name"] == "Tsavo ROI"
