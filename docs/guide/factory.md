# Connection Factory

NetworkPype provides two factory classes that separate session management from manager orchestration:

- **`ConnectionsFactory`** — manages a single shared `aiohttp.ClientSession` and creates low-level connection objects.
- **`ConnectionManagersFactory`** — holds shared configuration (throttler, auth, processors, time synchronizer) and vends fully configured `RESTManager` and `WebSocketManager` instances.

In most applications you interact only with `ConnectionManagersFactory`.

## ConnectionsFactory

`ConnectionsFactory` is a thin aiohttp wrapper. It creates one `ClientSession` shared across all connections, enabling connection pooling and cookie sharing.

```python
from networkpype.factory import ConnectionsFactory

factory = ConnectionsFactory()

rest_conn = await factory.get_rest_connection()
ws_conn = await factory.get_ws_connection()

# Update cookies across the shared session
await factory.update_cookies({"session_id": "abc123"})

# Always close when done
await factory.close()
```

Passing keyword arguments to `get_ws_connection` forwards them to the `ClientSession` constructor (e.g., custom connectors or timeouts).

## ConnectionManagersFactory

`ConnectionManagersFactory` wraps a `ConnectionsFactory` and provides high-level managers with all features wired up:

```python
from networkpype.factory import ConnectionManagersFactory
from networkpype.throttler.rate_limit import RateLimit
from networkpype.throttler.throttler import AsyncThrottler

throttler = AsyncThrottler(
    rate_limits=[RateLimit(limit_id="default", limit=10, time_interval=1.0)]
)

factory = ConnectionManagersFactory(throttler=throttler)
```

### Full Configuration

```python
from networkpype.factory import ConnectionManagersFactory
from networkpype.throttler.throttler import AsyncThrottler
from networkpype.throttler.rate_limit import RateLimit
from networkpype.time_synchronizer import TimeSynchronizer
from networkpype.rest.processor.time_synchronizer import TimeSynchronizerRESTPreProcessor

synchronizer = TimeSynchronizer(max_samples=5)
throttler = AsyncThrottler(
    rate_limits=[RateLimit(limit_id="default", limit=10, time_interval=1.0)]
)

factory = ConnectionManagersFactory(
    throttler=throttler,
    auth=MyAuth(api_key="key", api_secret="secret"),
    rest_pre_processors=[
        TimeSynchronizerRESTPreProcessor(
            synchronizer=synchronizer,
            time_provider=fetch_server_time,
        )
    ],
    rest_post_processors=[],
    ws_pre_processors=[],
    ws_post_processors=[],
    time_synchronizer=synchronizer,
)
```

### Getting Managers

Each call to `get_rest_manager` creates a new `RESTManager` bound to the shared session. The same shared `aiohttp.ClientSession` is reused across calls:

```python
rest_manager = await factory.get_rest_manager()
ws_manager = await factory.get_ws_manager()
```

Pass keyword arguments to `get_ws_manager` to forward them to `get_ws_connection` (and thus to the `ClientSession`).

### Accessing Shared State

The factory exposes its shared components as read-only properties:

```python
factory.throttler          # AsyncThrottler
factory.time_synchronizer  # TimeSynchronizer | None
factory.auth               # Auth | None
```

### Lifecycle

Always close the factory when finished to release the aiohttp session:

```python
try:
    manager = await factory.get_rest_manager()
    data = await manager.execute_request(...)
finally:
    await factory.close()
```

Calling `close` is idempotent if the session was never opened.

## Sharing a Factory Across Tasks

Because all managers share a single `ClientSession`, it is safe — and efficient — to pass one factory to multiple concurrent tasks:

```python
import asyncio
from networkpype.factory import ConnectionManagersFactory
from networkpype.throttler.rate_limit import RateLimit
from networkpype.throttler.throttler import AsyncThrottler
from networkpype.rest.method import RESTMethod


async def fetch_ticker(factory: ConnectionManagersFactory, symbol: str) -> dict:
    manager = await factory.get_rest_manager()
    return await manager.execute_request(
        url=f"https://api.example.com/ticker/{symbol}",
        throttler_limit_id="ticker",
        method=RESTMethod.GET,
    )


async def main():
    throttler = AsyncThrottler(
        rate_limits=[RateLimit(limit_id="ticker", limit=5, time_interval=1.0)]
    )
    factory = ConnectionManagersFactory(throttler=throttler)

    try:
        results = await asyncio.gather(
            fetch_ticker(factory, "BTCUSDT"),
            fetch_ticker(factory, "ETHUSDT"),
        )
        print(results)
    finally:
        await factory.close()


asyncio.run(main())
```

The shared throttler serializes requests automatically, so both tasks respect the rate limit together.

## Next Steps

- [REST Guide](rest.md) --- Processors and advanced request patterns
- [WebSocket Guide](websocket.md) --- WebSocket connection lifecycle
- [Authentication Guide](authentication.md) --- Implementing custom auth
- [API Reference: ConnectionManagersFactory](../api/factory.md)
