# RESTRequest

`networkpype.rest.request` · `networkpype.rest.method`

## RESTMethod

Enum of supported HTTP methods.

```python
class RESTMethod(Enum):
    GET    = "GET"
    POST   = "POST"
    PUT    = "PUT"
    DELETE = "DELETE"
```

`str(RESTMethod.GET)` returns `"GET"`.

## RESTRequest

Dataclass representing a REST API request. All fields except `method` are optional.

```python
@dataclass
class RESTRequest:
    method: RESTMethod
    url: str | None = None
    endpoint_url: str | None = None
    params: Mapping[str, str] | None = None
    data: Any = None
    headers: Mapping[str, str] | None = None
    is_auth_required: bool = False
    throttler_limit_id: str | None = None
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `method` | `RESTMethod` | — | HTTP method |
| `url` | `str \| None` | `None` | Full URL; takes precedence over `endpoint_url` |
| `endpoint_url` | `str \| None` | `None` | Endpoint path; used if `url` is `None` |
| `params` | `Mapping[str, str] \| None` | `None` | Query parameters |
| `data` | `Any` | `None` | Request body (string or serializable object) |
| `headers` | `Mapping[str, str] \| None` | `None` | HTTP headers |
| `is_auth_required` | `bool` | `False` | If `True`, `Auth.rest_authenticate` is called |
| `throttler_limit_id` | `str \| None` | `None` | Rate limit ID for throttling |

### Example

```python
from networkpype.rest.request import RESTRequest
from networkpype.rest.method import RESTMethod

request = RESTRequest(
    method=RESTMethod.POST,
    url="https://api.example.com/v1/order",
    params={"recvWindow": "5000"},
    data='{"symbol":"BTCUSDT","side":"BUY","quantity":"0.001"}',
    headers={"Content-Type": "application/json"},
    is_auth_required=True,
    throttler_limit_id="/v1/order",
)
```
