# Authentication

NetworkPype's authentication system is built around the abstract `Auth` base class. Subclass it to implement any authentication scheme — API key, OAuth, HMAC signatures, JWT, or custom protocols. The `Auth` instance is passed to `ConnectionManagersFactory` and automatically applied to requests that set `is_auth_required=True`.

## The Auth Interface

```python
from networkpype.auth import Auth
from networkpype.rest.request import RESTRequest
from networkpype.websocket.request import WebSocketRequest


class MyAuth(Auth):
    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        # Modify and return the request
        ...

    async def ws_authenticate(self, request: WebSocketRequest) -> WebSocketRequest:
        # Modify and return the request
        ...
```

Both methods receive a copy of the request (deep-copied by the manager) and must return a modified version. They are `async`, so you can make network calls inside them if needed.

## API Key Authentication

```python
from networkpype.auth import Auth
from networkpype.rest.request import RESTRequest
from networkpype.websocket.request import WebSocketRequest, WebSocketJSONRequest


class ApiKeyAuth(Auth):
    def __init__(self, api_key: str) -> None:
        super().__init__()
        self._api_key = api_key

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        headers = dict(request.headers or {})
        headers["X-API-KEY"] = self._api_key
        return RESTRequest(
            method=request.method,
            url=request.url,
            endpoint_url=request.endpoint_url,
            params=request.params,
            data=request.data,
            headers=headers,
            is_auth_required=request.is_auth_required,
            throttler_limit_id=request.throttler_limit_id,
        )

    async def ws_authenticate(self, request: WebSocketRequest) -> WebSocketRequest:
        # WebSocket authentication often happens at the subscription level
        return request
```

## HMAC Signature Authentication

A common pattern for exchange APIs — signs the query string or body with a secret key and includes a timestamp:

```python
import hashlib
import hmac
from networkpype.auth import Auth
from networkpype.rest.request import RESTRequest
from networkpype.time_synchronizer import TimeSynchronizer
from networkpype.websocket.request import WebSocketRequest


class HmacAuth(Auth):
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        time_provider: TimeSynchronizer | None = None,
    ) -> None:
        super().__init__(time_provider=time_provider)
        self._api_key = api_key
        self._api_secret = api_secret

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        timestamp = int(self.time_provider.time() * 1000)
        params = dict(request.params or {})
        params["timestamp"] = str(timestamp)

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        signature = hmac.new(
            self._api_secret.encode(),
            query_string.encode(),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature

        headers = dict(request.headers or {})
        headers["X-API-KEY"] = self._api_key

        return RESTRequest(
            method=request.method,
            url=request.url,
            endpoint_url=request.endpoint_url,
            params=params,
            data=request.data,
            headers=headers,
            is_auth_required=request.is_auth_required,
            throttler_limit_id=request.throttler_limit_id,
        )

    async def ws_authenticate(self, request: WebSocketRequest) -> WebSocketRequest:
        return request
```

## Registering Auth with the Factory

Pass your `Auth` instance when constructing `ConnectionManagersFactory`:

```python
from networkpype.factory import ConnectionManagersFactory
from networkpype.throttler.throttler import AsyncThrottler
from networkpype.throttler.rate_limit import RateLimit
from networkpype.time_synchronizer import TimeSynchronizer

synchronizer = TimeSynchronizer()
auth = HmacAuth(
    api_key="your-api-key",
    api_secret="your-api-secret",
    time_provider=synchronizer,
)

factory = ConnectionManagersFactory(
    throttler=AsyncThrottler(
        rate_limits=[RateLimit(limit_id="default", limit=10, time_interval=1.0)]
    ),
    auth=auth,
    time_synchronizer=synchronizer,
)
```

## Triggering Authentication on Requests

Authentication only runs for requests that set `is_auth_required=True`:

```python
# Public endpoint — no auth
data = await manager.execute_request(
    url="https://api.example.com/v1/ticker",
    throttler_limit_id="default",
    method=RESTMethod.GET,
)

# Private endpoint — auth applied automatically
account = await manager.execute_request(
    url="https://api.example.com/v1/account",
    throttler_limit_id="default",
    method=RESTMethod.GET,
    is_auth_required=True,
)
```

For WebSocket messages:

```python
from networkpype.websocket.request import WebSocketJSONRequest

# Public subscription — no auth
await ws_manager.subscribe(
    WebSocketJSONRequest(
        payload={"method": "SUBSCRIBE", "params": ["btcusdt@trade"]}
    )
)

# Private subscription — auth applied
await ws_manager.subscribe(
    WebSocketJSONRequest(
        payload={"method": "SUBSCRIBE", "params": ["account.update"]},
        is_auth_required=True,
    )
)
```

## Time-Synchronized Auth

If your API requires timestamps in signatures, pass a `TimeSynchronizer` to `Auth.__init__`. The synchronizer is then accessible as `self.time_provider`:

```python
class MyAuth(Auth):
    def __init__(self, api_key: str, time_provider: TimeSynchronizer) -> None:
        super().__init__(time_provider=time_provider)

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        ts_ms = int(self.time_provider.time() * 1000)
        # use ts_ms in your signature
        ...
```

If no `TimeSynchronizer` is passed, `Auth.__init__` creates a default one with five sample slots.

## Next Steps

- [Time Synchronization](time-sync.md) --- Keeping clocks aligned
- [API Reference: Auth](../api/factory.md) --- Full class reference
