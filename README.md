# EDMTGreen

Python client for the **GreenPulse** geospatial monitoring and reporting platform.

## Installation

```bash
# editable / local development install
pip install -e ".[dev]"
```

## Quick start

```python
from edmtgreeen import GreenPulse

# context manager — auto-logout on exit
with GreenPulse(
    site     = "http://localhost:8000",
    username = "researcher_01",
    password = "s3cur3p@ss",
) as gp:

    uploads     = gp.get_uploads()                          # GeoDataFrame
    workflows   = gp.get_workflows(workflow_type="ndvi")    # DataFrame
    timeseries  = gp.get_timeseries(workflow_id="abc-123")
    composites  = gp.get_composites(workflow_type="evi")
    collections = gp.get_collections(session="session-xyz")
    reports     = gp.get_reports(report_session="rep-456")
```

## API reference

| Method | Endpoint | Returns |
|---|---|---|
| `get_auth_status()` | `GET /api/auth/status/` | `dict` |
| `get_uploads(...)` | `GET /api/uploads/` | `GeoDataFrame` |
| `get_workflows(...)` | `GET /api/workflows/` | `DataFrame` |
| `get_timeseries(...)` | `GET /api/timeseries/` | `DataFrame` |
| `get_composites(...)` | `GET /api/composites/` | `DataFrame` |
| `get_collections(...)` | `GET /api/collections/` | `DataFrame` |
| `get_reports(...)` | `GET /api/reports/` | `DataFrame` |

### Common filter parameters (all tabular methods)

| Parameter | Filters on |
|---|---|
| `workflow_id` | workflow primary key |
| `workflow_session` | `fields.workflow_session_id` |
| `session` | `fields.session_id` |
| `workflow_type` | `fields.workflow_splitter` — one of `evi`, `rain`, `ndvi`, `lst`, `all` |

Each method also accepts its own session filter:
`timeseries_session`, `composite_session`, `collection_session`, `report_session`.

## Exception handling

```python
from edmtgreeen import (
    GreenPulseError,      # base — catch all SDK errors
    AuthenticationError,  # 401 / bad credentials
    NotFoundError,        # 404
    ValidationError,      # 400  (.detail holds the server payload)
    APIError,             # any other non-2xx  (.status_code available)
)

try:
    workflows = gp.get_workflows(workflow_id="missing-id")
except NotFoundError:
    print("Workflow not found")
except AuthenticationError:
    print("Token expired — re-authenticate")
```

## Package layout

```
edmtgreeen/
├── __init__.py      ← public API — import everything from here
├── _auth.py         ← GreenPulseAuth  (JWT login / session management)
├── _client.py       ← GreenPulse      (all get_* methods)
├── _exceptions.py   ← typed exceptions
├── _types.py        ← STATUS / SPLITTER literals
└── py.typed         ← PEP 561 — package ships type information
pyproject.toml
README.md
```

## Development

```bash
pip install -e ".[dev]"
pytest                        # run tests with coverage
ruff check edmtgreeen     # lint
mypy edmtgreeen           # type-check
```
