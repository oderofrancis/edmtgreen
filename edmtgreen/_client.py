"""

Class-based Python client for the GreenPulse API.

Usage
-----
    from edmtgreen import GreenPulse

    gp = GreenPulse(
        site     = "http://localhost:8000",
        username = "your_username",
        password = "your_password",
    )

    gp.get_workflows()
    gp.get_uploads()
    gp.get_timeseries()

Registered server endpoints
-----------------------------
    POST  /api/auth/login/
    POST  /api/auth/logout/
    POST  /api/auth/token/refresh/
    GET   /api/auth/status/
    GET   /api/uploads/
    GET   /api/workflows/
    GET   /api/timeseries/
    GET   /api/composites/
    GET   /api/collections/
    GET   /api/reports/
"""

from __future__ import annotations

import logging
import warnings
from typing import Any, List, Optional, Union

import geopandas as gpd
import pandas as pd
import shapely.geometry
from requests import Response

from ._auth import GreenPulseAuth
from ._exceptions import APIError, AuthenticationError, NotFoundError, ValidationError
from typing import Literal

STATUS   = Literal["all", "pending", "completed"]
SPLITTER = Literal["all", "evi", "rain", "ndvi", "lst"]


__all__ = ["GreenPulse"]

logger = logging.getLogger(__name__)


class GreenPulse(GreenPulseAuth):
    """
    GreenPulse read-only API client.

    Parameters
    ----------
    site : str
        Root URL of the GreenPulse server, e.g. ``"http://localhost:8000"``.
    username : str
        Account username.
    password : str
        Account password.
    timeout : int, optional
        Request timeout in seconds (default: 30).
    verify_ssl : bool, optional
        Verify TLS certificates (default: ``True``). Set ``False`` for local dev.

    Example
    -------
        gp = GreenPulse(
            site     = "http://localhost:8000",
            username = "researcher_01",
            password = "s3cur3p@ss",
        )

        # or as a context manager — auto-logout on exit
        with GreenPulse(...) as gp:
            df = gp.get_workflows(workflow_type="ndvi")
    """

    _API_PREFIX = "/api"

    def __init__(
        self,
        site:       str,
        username:   str,
        password:   str,
        timeout:    int  = 30,
        verify_ssl: bool = True,
    ) -> None:
        self._timeout    = timeout
        self._verify_ssl = verify_ssl

        try:
            super().__init__(username=username, password=password, site=site)
        except ValueError as exc:
            raise AuthenticationError(str(exc)) from exc

    # ------------------------------------------------------------------
    # Private helpers — HTTP layer
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        """Build a full URL from a relative API path."""
        path = path if path.startswith("/") else f"/{path}"
        return f"{self.site}{self._API_PREFIX}{path}"

    def _handle_response(self, response: Response) -> Any:
        """
        Map every HTTP status code to a return value or typed exception.

        Code  → outcome
        ----    -------
        204   → ``None``
        2xx   → parsed JSON (or raw text if body is not JSON)
        400   → :exc:`~edmtgreen.ValidationError`
        401   → :exc:`~edmtgreen.AuthenticationError`
        404   → :exc:`~edmtgreen.NotFoundError`
        other → :exc:`~edmtgreen.APIError`
        """
        if response.status_code == 204:
            return None

        if response.ok:
            try:
                return response.json()
            except ValueError:
                return response.text

        try:
            body   = response.json()
            detail = body.get("detail") or body.get("errors") or body
        except ValueError:
            detail = response.text or response.reason

        code = response.status_code
        if code == 400:
            raise ValidationError(detail)
        if code == 401:
            raise AuthenticationError(
                f"Token expired or invalid — re-authenticate. ({detail})"
            )
        if code == 404:
            raise NotFoundError(f"Resource not found: {response.url}")
        raise APIError(code, str(detail))

    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        """Execute a GET request and return the parsed response."""
        response = self.session.get(
            self._url(path),
            params  = params,
            timeout = self._timeout,
            verify  = self._verify_ssl,
        )
        return self._handle_response(response)

    # ------------------------------------------------------------------
    # Private helpers — data normalisation
    # ------------------------------------------------------------------

    @staticmethod
    def _to_list(
        value: Optional[Union[str, List[str]]],
    ) -> Optional[List[str]]:
        """Normalise a single string or list of strings into a list."""
        if value is None:
            return None
        return [value] if isinstance(value, str) else list(value)

    @staticmethod
    def _build_geodataframe(data: pd.DataFrame) -> gpd.GeoDataFrame:
        """Convert a normalised uploads DataFrame into a GeoDataFrame."""
        if "geometry.geometries" in data.columns:
            data["geometry"] = data["geometry.geometries"].apply(
                lambda geoms: shapely.geometry.shape(
                    {"type": "GeometryCollection", "geometries": geoms}
                )
                if isinstance(geoms, list)
                else None
            )
        return gpd.GeoDataFrame(data, geometry="geometry", crs="EPSG:4326")

    def _filter_records(
        self,
        path: str,
        *,
        workflow_id:       Optional[Union[str, List[str]]] = None,
        workflow_session:  Optional[Union[str, List[str]]] = None,
        session:           Optional[Union[str, List[str]]] = None,
        extra_session:     Optional[Union[str, List[str]]] = None,
        extra_session_col: Optional[str] = None,
        workflow_type:     SPLITTER = "all",
        workflow_id_col:   str = "fields.workflow_id",
    ) -> pd.DataFrame:
        """
        Fetch a tabular endpoint and apply the standard filter set.

        Shared by :meth:`get_workflows`, :meth:`get_timeseries`,
        :meth:`get_composites`, :meth:`get_collections`, and
        :meth:`get_reports`.

        Parameters
        ----------
        path : str
            Relative API path, e.g. ``"/timeseries/"``.
        workflow_id : str or list of str, optional
            Filter on the column named by *workflow_id_col*.
        workflow_session : str or list of str, optional
            Filter on ``fields.workflow_session_id``.
        session : str or list of str, optional
            Filter on ``fields.session_id``.
        extra_session : str or list of str, optional
            Filter on the endpoint-specific session column named by
            *extra_session_col*.
        extra_session_col : str, optional
            Column holding the endpoint-specific session value,
            e.g. ``"fields.timeseries_session"``.
        workflow_type : SPLITTER, default ``'all'``
            Filter on ``fields.workflow_splitter``.
        workflow_id_col : str, default ``'fields.workflow_id'``
            Override the column used for *workflow_id*.
            Pass ``'pk'`` for the ``/workflows/`` endpoint.
        """
        raw  = self._get(path)
        data = pd.json_normalize(raw)

        filter_map: dict[str, Optional[List[str]]] = {
            workflow_id_col:              self._to_list(workflow_id),
            "fields.workflow_session_id": self._to_list(workflow_session),
            "fields.session_id":          self._to_list(session),
        }

        if extra_session_col and extra_session is not None:
            filter_map[extra_session_col] = self._to_list(extra_session)

        for col, values in filter_map.items():
            if values and col in data.columns:
                data = data[data[col].isin(values)]

        if workflow_type != "all":
            data = data[data["fields.workflow_splitter"] == workflow_type]

        return data.reset_index(drop=True)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def get_auth_status(self) -> dict:
        """
        GET /api/auth/status/

        Returns token validity and the authenticated user's profile.
        """
        return self._get("/auth/status/")

    # ------------------------------------------------------------------
    # Uploads  (ROI / GeoJSON)
    # ------------------------------------------------------------------

    def get_uploads(
        self,
        id:             Optional[Union[str, List[str]]] = None,
        upload_session: Optional[Union[str, List[str]]] = None,
        name:           Optional[Union[str, List[str]]] = None,
    ) -> gpd.GeoDataFrame:
        """
        GET /api/uploads/

        All ROI / GeoJSON uploads owned by the authenticated user,
        ordered newest first.

        Parameters
        ----------
        id : str or list of str, optional
            Filter by one or more upload IDs.
        upload_session : str or list of str, optional
            Filter by one or more upload session identifiers.
        name : str or list of str, optional
            Filter by upload name(s).

            .. warning::
                Filtering by ``name`` is unstable — names are free-text and
                not guaranteed to be unique. Prefer ``id`` or
                ``upload_session`` for reproducible results.

        Returns
        -------
        geopandas.GeoDataFrame
        """
        if name is not None:
            warnings.warn(
                "Filtering by 'name' is unstable: names are user-supplied free-text "
                "values that are not guaranteed to be unique and may change at any "
                "time. Use 'id' or 'upload_session' for reliable filtering.",
                UserWarning,
                stacklevel=2,
            )

        raw  = self._get("/uploads/")
        data = pd.json_normalize(raw["features"])

        ids      = self._to_list(id)
        sessions = self._to_list(upload_session)
        names    = self._to_list(name)

        if ids:
            data = data[data["id"].isin(ids)]
        if sessions:
            data = data[data["properties.upload_session"].isin(sessions)]
        if names:
            data = data[data["properties.name"].isin(names)]

        return self._build_geodataframe(data.reset_index(drop=True))

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------

    def get_workflows(
        self,
        workflow_id:      Optional[Union[str, List[str]]] = None,
        workflow_session: Optional[Union[str, List[str]]] = None,
        session:          Optional[Union[str, List[str]]] = None,
        workflow_type:    SPLITTER = "all",
    ) -> pd.DataFrame:
        """
        GET /api/workflows/

        All workflows owned by the authenticated user, ordered newest first.

        Parameters
        ----------
        workflow_id : str or list of str, optional
        workflow_session : str or list of str, optional
        session : str or list of str, optional
        workflow_type : SPLITTER, default ``'all'``

        Returns
        -------
        pandas.DataFrame
        """
        return self._filter_records(
            "/workflows/",
            workflow_id      = workflow_id,
            workflow_session = workflow_session,
            session          = session,
            workflow_type    = workflow_type,
            workflow_id_col  = "pk",  # workflows are keyed on pk, not fields.workflow_id
        )

    # ------------------------------------------------------------------
    # Timeseries
    # ------------------------------------------------------------------

    def get_timeseries(
        self,
        workflow_id:        Optional[Union[str, List[str]]] = None,
        workflow_session:   Optional[Union[str, List[str]]] = None,
        session:            Optional[Union[str, List[str]]] = None,
        timeseries_session: Optional[Union[str, List[str]]] = None,
        workflow_type:      SPLITTER = "all",
    ) -> pd.DataFrame:
        """
        GET /api/timeseries/

        All timeseries records owned by the authenticated user.

        Parameters
        ----------
        workflow_id : str or list of str, optional
        workflow_session : str or list of str, optional
        session : str or list of str, optional
        timeseries_session : str or list of str, optional
        workflow_type : SPLITTER, default ``'all'``

        Returns
        -------
        pandas.DataFrame
        """
        return self._filter_records(
            "/timeseries/",
            workflow_id       = workflow_id,
            workflow_session  = workflow_session,
            session           = session,
            extra_session     = timeseries_session,
            extra_session_col = "fields.timeseries_session",
            workflow_type     = workflow_type,
        )

    # ------------------------------------------------------------------
    # Composites
    # ------------------------------------------------------------------

    def get_composites(
        self,
        workflow_id:       Optional[Union[str, List[str]]] = None,
        workflow_session:  Optional[Union[str, List[str]]] = None,
        session:           Optional[Union[str, List[str]]] = None,
        composite_session: Optional[Union[str, List[str]]] = None,
        workflow_type:     SPLITTER = "all",
    ) -> pd.DataFrame:
        """
        GET /api/composites/

        All composite records owned by the authenticated user.

        Parameters
        ----------
        workflow_id : str or list of str, optional
        workflow_session : str or list of str, optional
        session : str or list of str, optional
        composite_session : str or list of str, optional
        workflow_type : SPLITTER, default ``'all'``

        Returns
        -------
        pandas.DataFrame
        """
        return self._filter_records(
            "/composites/",
            workflow_id       = workflow_id,
            workflow_session  = workflow_session,
            session           = session,
            extra_session     = composite_session,
            extra_session_col = "fields.composite_sessions",
            workflow_type     = workflow_type,
        )

    # ------------------------------------------------------------------
    # Collections
    # ------------------------------------------------------------------

    def get_collections(
        self,
        workflow_id:        Optional[Union[str, List[str]]] = None,
        workflow_session:   Optional[Union[str, List[str]]] = None,
        session:            Optional[Union[str, List[str]]] = None,
        collection_session: Optional[Union[str, List[str]]] = None,
        workflow_type:      SPLITTER = "all",
    ) -> pd.DataFrame:
        """
        GET /api/collections/

        All collection records owned by the authenticated user.

        Parameters
        ----------
        workflow_id : str or list of str, optional
        workflow_session : str or list of str, optional
        session : str or list of str, optional
        collection_session : str or list of str, optional
        workflow_type : SPLITTER, default ``'all'``

        Returns
        -------
        pandas.DataFrame
        """
        return self._filter_records(
            "/collections/",
            workflow_id       = workflow_id,
            workflow_session  = workflow_session,
            session           = session,
            extra_session     = collection_session,
            extra_session_col = "fields.collection_session",
            workflow_type     = workflow_type,
        )

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def get_reports(
        self,
        workflow_id:      Optional[Union[str, List[str]]] = None,
        workflow_session: Optional[Union[str, List[str]]] = None,
        session:          Optional[Union[str, List[str]]] = None,
        report_session:   Optional[Union[str, List[str]]] = None,
        workflow_type:    SPLITTER = "all",
    ) -> pd.DataFrame:
        """
        GET /api/reports/

        All reports owned by the authenticated user.

        Parameters
        ----------
        workflow_id : str or list of str, optional
        workflow_session : str or list of str, optional
        session : str or list of str, optional
        report_session : str or list of str, optional
        workflow_type : SPLITTER, default ``'all'``

        Returns
        -------
        pandas.DataFrame
        """
        return self._filter_records(
            "/reports/",
            workflow_id       = workflow_id,
            workflow_session  = workflow_session,
            session           = session,
            extra_session     = report_session,
            extra_session_col = "fields.report_session",
            workflow_type     = workflow_type,
        )

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        state = "authenticated" if self.token else "unauthenticated"
        return f"<GreenPulse site='{self.site}' user='{self.username}' [{state}]>"

    def __enter__(self) -> "GreenPulse":
        return self

    def __exit__(self, *_: Any) -> None:
        self.logout()





























