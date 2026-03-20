# RESTManager

`networkpype.rest.manager`

High-level manager for REST API communication. Orchestrates throttling, authentication, and pre/post processing. Obtain instances via `ConnectionManagersFactory.get_rest_manager()`.

```python
class RESTManager
```

## Constructor

```python
RESTManager(
    connection: RESTConnection,
    throttler: AsyncThrottler,
    rest_pre_processors: list[RESTPreProcessor] | None = None,
    rest_post_processors: list[RESTPostProcessor] | None = None,
    auth: Auth | None = None,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connection` | `RESTConnection` | — | Underlying HTTP connection |
| `throttler` | `AsyncThrottler` | — | Rate limiting component |
| `rest_pre_processors` | `list[RESTPreProcessor] \| None` | `None` | Request processors |
| `rest_post_processors` | `list[RESTPostProcessor] \| None` | `None` | Response processors |
| `auth` | `Auth \| None` | `None` | Authentication handler |

## Methods

---

### `execute_request`

```python
async def execute_request(
    url: str,
    throttler_limit_id: str,
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    method: RESTMethod = RESTMethod.GET,
    is_auth_required: bool = False,
    return_err: bool = False,
    timeout: float | None = None,
    headers: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]
```

The primary method for making REST API calls. Handles header setup, JSON serialization, rate limiting, authentication, error detection, and response parsing.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | — | Full URL for the request |
| `throttler_limit_id` | `str` | — | Rate limit ID (must exist in throttler) |
| `params` | `dict \| None` | `None` | Query parameters; `None` values are filtered out |
| `data` | `dict \| None` | `None` | Request body; serialized to JSON for POST/PUT |
| `method` | `RESTMethod` | `GET` | HTTP method |
| `is_auth_required` | `bool` | `False` | Trigger `Auth.rest_authenticate` |
| `return_err` | `bool` | `False` | Return error body as dict instead of raising |
| `timeout` | `float \| None` | `None` | Request timeout in seconds |
| `headers` | `dict \| None` | `None` | Additional headers (merged with auto-set headers) |
| `**kwargs` | `Any` | — | Forwarded to `RESTConnection.call` |

**Returns:** `dict[str, Any]` — parsed JSON response.

**Raises:**

- `OSError` — on HTTP 4xx/5xx when `return_err=False`
- `asyncio.TimeoutError` — when `timeout` is exceeded
- `json.JSONDecodeError` — if the response is not valid JSON

**Content-Type behaviour:**

- `POST` and `PUT` → `application/json`
- All other methods → `application/x-www-form-urlencoded`

---

### `call`

```python
async def call(
    request: RESTRequest,
    timeout: float | None = None,
    **kwargs: Any,
) -> RESTResponse
```

Lower-level entry point. Runs the full pipeline (pre-process → authenticate → send → post-process) and returns the raw `RESTResponse` without JSON parsing.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `request` | `RESTRequest` | — | The request to execute |
| `timeout` | `float \| None` | `None` | Timeout in seconds |
| `**kwargs` | `Any` | — | Forwarded to `RESTConnection.call` |

**Returns:** `RESTResponse`

**Raises:** `asyncio.TimeoutError`

## Example

```python
from networkpype.factory import ConnectionManagersFactory
from networkpype.rest.method import RESTMethod
from networkpype.throttler.rate_limit import RateLimit
from networkpype.throttler.throttler import AsyncThrottler

throttler = AsyncThrottler(
    rate_limits=[RateLimit(limit_id="ticker", limit=10, time_interval=1.0)]
)
factory = ConnectionManagersFactory(throttler=throttler)
manager = await factory.get_rest_manager()

data = await manager.execute_request(
    url="https://api.example.com/v1/ticker",
    throttler_limit_id="ticker",
    method=RESTMethod.GET,
    params={"symbol": "BTCUSDT"},
    timeout=10.0,
)
```
