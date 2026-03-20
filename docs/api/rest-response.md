# RESTResponse

`networkpype.rest.response`

Wrapper around an `aiohttp.ClientResponse`. Instances are created internally by `RESTConnection` and returned by `RESTManager.call`. You typically access response data through `RESTManager.execute_request`, which parses the JSON for you.

```python
class RESTResponse
```

## Constructor

```python
RESTResponse(aiohttp_response: aiohttp.ClientResponse)
```

**Parameters:**

- `aiohttp_response` — The underlying aiohttp response object.

## Properties

---

### `status`

```python
@property
def status() -> int
```

HTTP status code (e.g. `200`, `404`, `500`).

---

### `url`

```python
@property
def url() -> str
```

The URL that was requested, as a string.

---

### `method`

```python
@property
def method() -> RESTMethod
```

The HTTP method used for the request.

---

### `headers`

```python
@property
def headers() -> Mapping[str, str] | None
```

Response headers, or `None` if none are present.

## Methods

---

### `json`

```python
async def json(content_type: str | None = "application/json") -> Any
```

Read and parse the response body as JSON.

**Parameters:**

- `content_type` — Expected MIME type. Pass `None` to skip content-type checking (useful for APIs that return JSON with non-standard types).

**Returns:** The parsed JSON value (`dict`, `list`, `str`, `int`, etc.).

**Raises:** `aiohttp.ContentTypeError` if the body cannot be parsed as JSON.

---

### `text`

```python
async def text() -> str
```

Read the response body as a plain string.

**Returns:** `str` — the response body text.

## Example

```python
from networkpype.factory import ConnectionManagersFactory
from networkpype.rest.method import RESTMethod
from networkpype.rest.request import RESTRequest

manager = await factory.get_rest_manager()

# Using the low-level call() to access RESTResponse directly
request = RESTRequest(method=RESTMethod.GET, url="https://api.example.com/v1/ping")
response = await manager.call(request)

print(response.status)         # e.g. 200
print(response.url)            # "https://api.example.com/v1/ping"
data = await response.json()   # {"pong": true}
```
