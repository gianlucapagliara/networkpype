# RESTConnection

`networkpype.rest.connection`

Low-level HTTP connection handler that wraps an `aiohttp.ClientSession`. You typically obtain instances through `ConnectionsFactory.get_rest_connection()` rather than constructing them directly.

```python
class RESTConnection
```

## Constructor

```python
RESTConnection(aiohttp_client_session: aiohttp.ClientSession)
```

**Parameters:**

- `aiohttp_client_session` — The aiohttp session to use for all HTTP requests.

## Methods

---

### `call`

```python
async def call(
    request: RESTRequest,
    encoded: bool = False,
    **kwargs: Any,
) -> RESTResponse
```

Execute an HTTP request.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `request` | `RESTRequest` | — | The request to execute |
| `encoded` | `bool` | `False` | If `True`, skip percent-encoding of the URL |
| `**kwargs` | `Any` | — | Extra arguments forwarded to `aiohttp.ClientSession.request()` |

**Returns:** `RESTResponse` — the wrapped server response.

**Raises:**

- `ValueError` — if `request.url` is `None`
- `aiohttp.ClientError` — on HTTP client errors
- `asyncio.TimeoutError` — if the request times out

## Example

```python
import aiohttp
from networkpype.rest.connection import RESTConnection
from networkpype.rest.request import RESTRequest
from networkpype.rest.method import RESTMethod

async with aiohttp.ClientSession() as session:
    connection = RESTConnection(aiohttp_client_session=session)
    request = RESTRequest(
        method=RESTMethod.GET,
        url="https://api.example.com/v1/ping",
    )
    response = await connection.call(request)
    print(response.status)
    data = await response.json()
```
