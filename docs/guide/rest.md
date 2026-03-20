# REST

NetworkPype's REST stack is a layered pipeline. At the bottom is `RESTConnection`, which wraps an aiohttp session. Above it is `RESTManager`, which orchestrates throttling, authentication, and pre/post processing. `ConnectionManagersFactory` ties everything together with shared configuration.

## Connections

`RESTConnection` is a thin aiohttp wrapper. You rarely instantiate it directly — use `ConnectionsFactory` or `ConnectionManagersFactory` instead.

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
    data = await response.json()
```

The `call` method accepts an `encoded` flag — set it to `True` if the URL is already percent-encoded and you want to skip aiohttp's own encoding pass.

## Requests

`RESTRequest` is a dataclass. All fields except `method` are optional:

```python
from networkpype.rest.request import RESTRequest
from networkpype.rest.method import RESTMethod

request = RESTRequest(
    method=RESTMethod.POST,
    url="https://api.example.com/v1/order",
    params={"recvWindow": "5000"},
    data='{"symbol":"BTCUSDT","side":"BUY","quantity":"0.001"}',
    headers={"X-API-KEY": "my-key"},
    is_auth_required=True,
    throttler_limit_id="/api/order",
)
```

Set `is_auth_required=True` to instruct the manager to run the `Auth.rest_authenticate` method before sending.

## Responses

`RESTResponse` wraps the aiohttp response and exposes:

| Property / Method | Returns | Notes |
|---|---|---|
| `status` | `int` | HTTP status code |
| `url` | `str` | Request URL |
| `method` | `RESTMethod` | HTTP method used |
| `headers` | `Mapping[str, str] \| None` | Response headers |
| `await response.json(content_type=...)` | `Any` | Parsed JSON body |
| `await response.text()` | `str` | Raw text body |

## Making Requests with RESTManager

`RESTManager.execute_request` is the main API for making REST calls. It handles:

- Setting `Content-Type` headers automatically (JSON for POST/PUT, form-encoded otherwise)
- Filtering `None` values from `params` and `data`
- Rate limiting through the throttler
- Error detection (raises `OSError` on 4xx/5xx by default)
- Response parsing

```python
from networkpype.factory import ConnectionManagersFactory
from networkpype.rest.method import RESTMethod
from networkpype.throttler.rate_limit import RateLimit
from networkpype.throttler.throttler import AsyncThrottler

throttler = AsyncThrottler(
    rate_limits=[RateLimit(limit_id="/v1/data", limit=5, time_interval=1.0)]
)
factory = ConnectionManagersFactory(throttler=throttler)

manager = await factory.get_rest_manager()

data = await manager.execute_request(
    url="https://api.example.com/v1/data",
    throttler_limit_id="/v1/data",
    method=RESTMethod.GET,
    params={"limit": "100"},
    timeout=10.0,
)
```

To receive error responses as data rather than raising:

```python
result = await manager.execute_request(
    url="https://api.example.com/v1/order",
    throttler_limit_id="/v1/order",
    method=RESTMethod.POST,
    data={"symbol": "BTCUSDT"},
    return_err=True,
)
if "code" in result:
    print(f"API error: {result}")
```

## Pre-Processors

Implement `RESTPreProcessor` to modify a request before it is sent:

```python
from networkpype.rest.processor.base import RESTPreProcessor
from networkpype.rest.request import RESTRequest


class RequestLogger(RESTPreProcessor):
    async def pre_process(self, request: RESTRequest) -> RESTRequest:
        print(f"Sending {request.method} {request.url}")
        return request
```

Register processors when constructing the factory:

```python
factory = ConnectionManagersFactory(
    throttler=throttler,
    rest_pre_processors=[RequestLogger()],
)
```

Multiple pre-processors execute in the order they are listed.

## Post-Processors

Implement `RESTPostProcessor` to transform or inspect a response before it reaches the caller:

```python
from networkpype.rest.processor.base import RESTPostProcessor
from networkpype.rest.response import RESTResponse


class StatusLogger(RESTPostProcessor):
    async def post_process(self, response: RESTResponse) -> RESTResponse:
        print(f"Response status: {response.status}")
        return response
```

```python
factory = ConnectionManagersFactory(
    throttler=throttler,
    rest_post_processors=[StatusLogger()],
)
```

## Time Synchronizer Pre-Processor

The built-in `TimeSynchronizerRESTPreProcessor` ensures the `TimeSynchronizer` has at least one server time sample before any request is sent — useful for APIs that reject requests with stale timestamps:

```python
from networkpype.rest.processor.time_synchronizer import TimeSynchronizerRESTPreProcessor
from networkpype.time_synchronizer import TimeSynchronizer

synchronizer = TimeSynchronizer()

async def get_server_time() -> float:
    # Fetch server time in milliseconds from your API
    ...

pre_processor = TimeSynchronizerRESTPreProcessor(
    synchronizer=synchronizer,
    time_provider=get_server_time,
)

factory = ConnectionManagersFactory(
    throttler=throttler,
    rest_pre_processors=[pre_processor],
    time_synchronizer=synchronizer,
)
```

## Next Steps

- [Rate Limiting](throttling.md) --- Configure the throttler
- [Authentication](authentication.md) --- Implement `Auth`
- [API Reference: RESTManager](../api/rest-manager.md) --- Full method signatures
