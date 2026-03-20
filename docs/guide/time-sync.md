# Time Synchronization

Some APIs require request timestamps that are within a few seconds of the server clock. `TimeSynchronizer` keeps the local client time aligned with server time by maintaining a rolling window of offset samples and computing a stable estimate using median and weighted-average statistics.

## How It Works

The synchronizer records the difference between the local clock and the server clock as offset samples. When `time()` is called, it combines the median and weighted average of stored samples (more-recent samples have higher weight) to produce a smooth, drift-resistant estimate.

If no samples exist, the synchronizer falls back to the raw difference between `time.time()` and `time.perf_counter()`.

## Basic Usage

```python
import asyncio
from networkpype.time_synchronizer import TimeSynchronizer


async def fetch_server_time_ms() -> float:
    # Replace with a real API call that returns server time in milliseconds
    return 1_700_000_000_000.0


async def main():
    sync = TimeSynchronizer(max_samples=5)

    # Update the offset with a single server time reading
    await sync.update_server_time_offset_with_time_provider(fetch_server_time_ms())

    # Get the synchronized current time in seconds
    current_time = sync.time()
    print(f"Synchronized time: {current_time}")

    # Inspect the raw offset in milliseconds
    print(f"Offset: {sync.time_offset_ms:.1f} ms")


asyncio.run(main())
```

## Periodic Updates

For long-running processes, refresh the offset periodically to account for clock drift:

```python
import asyncio
from networkpype.time_synchronizer import TimeSynchronizer


async def get_server_time_ms() -> float:
    # Real implementation: query your exchange's server time endpoint
    ...


async def sync_loop(sync: TimeSynchronizer) -> None:
    while True:
        await sync.update_server_time_offset_with_time_provider(get_server_time_ms())
        await asyncio.sleep(30)  # resync every 30 seconds
```

## Lazy Initialization with `update_server_time_if_not_initialized`

The `TimeSynchronizerRESTPreProcessor` uses this method to ensure at least one sample exists before any request is sent, without redundant server queries on subsequent requests:

```python
await sync.update_server_time_if_not_initialized(get_server_time_ms())
```

If samples already exist, the call cancels the pending coroutine (if it is an `asyncio.Task`) to avoid resource leaks.

## Manual Sample Management

```python
sync = TimeSynchronizer(max_samples=10)

# Add a known offset directly (in milliseconds)
sync.add_time_offset_ms_sample(offset=150.0)

# Clear all samples to force re-synchronization
sync.clear_time_offset_ms_samples()
```

## Integration via REST Pre-Processor

The recommended way to integrate time synchronization is through `TimeSynchronizerRESTPreProcessor`. This runs before every REST request and ensures the synchronizer is initialized:

```python
from networkpype.factory import ConnectionManagersFactory
from networkpype.rest.processor.time_synchronizer import TimeSynchronizerRESTPreProcessor
from networkpype.time_synchronizer import TimeSynchronizer
from networkpype.throttler.throttler import AsyncThrottler
from networkpype.throttler.rate_limit import RateLimit


async def get_server_time_ms() -> float:
    ...  # call your server time endpoint


synchronizer = TimeSynchronizer(max_samples=5)

factory = ConnectionManagersFactory(
    throttler=AsyncThrottler(
        rate_limits=[RateLimit(limit_id="default", limit=10, time_interval=1.0)]
    ),
    rest_pre_processors=[
        TimeSynchronizerRESTPreProcessor(
            synchronizer=synchronizer,
            time_provider=get_server_time_ms,
        )
    ],
    time_synchronizer=synchronizer,
)
```

The `time_provider` argument is a callable that returns an awaitable resolving to the server time in milliseconds.

## Using Synchronized Time in Auth

Pass the `TimeSynchronizer` to your `Auth` subclass so it can use the synchronized clock when constructing signatures:

```python
from networkpype.auth import Auth
from networkpype.rest.request import RESTRequest
from networkpype.time_synchronizer import TimeSynchronizer
from networkpype.websocket.request import WebSocketRequest


class HmacAuth(Auth):
    def __init__(self, api_key: str, api_secret: str, time_provider: TimeSynchronizer):
        super().__init__(time_provider=time_provider)
        self._api_key = api_key
        self._api_secret = api_secret

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        timestamp = int(self.time_provider.time() * 1000)
        # build signature using timestamp ...
        return request

    async def ws_authenticate(self, request: WebSocketRequest) -> WebSocketRequest:
        return request
```

## Next Steps

- [Authentication Guide](authentication.md) --- Using synchronized time in signatures
- [REST Guide](rest.md) --- TimeSynchronizerRESTPreProcessor integration
- [API Reference: TimeSynchronizer](../api/time-synchronizer.md)
