# Quick Start

This guide walks through the core patterns in networkpype: creating a factory, making REST requests, opening WebSocket connections, and applying rate limiting.

## Creating a Connection Factory

`ConnectionManagersFactory` is the main entry point. It holds shared configuration — throttler, auth, and processors — and vends `RESTManager` and `WebSocketManager` instances on demand.

The only required argument is a `throttler`:

```python
from networkpype.factory import ConnectionManagersFactory
from networkpype.throttler.rate_limit import RateLimit
from networkpype.throttler.throttler import AsyncThrottler

throttler = AsyncThrottler(
    rate_limits=[
        RateLimit(limit_id="default", limit=10, time_interval=1.0),
    ]
)

factory = ConnectionManagersFactory(throttler=throttler)
```

Always call `await factory.close()` when done, or manage the session in a try/finally block.

## Making REST Requests

Get a `RESTManager` from the factory and call `execute_request`:

```python
import asyncio

from networkpype.factory import ConnectionManagersFactory
from networkpype.rest.method import RESTMethod
from networkpype.throttler.rate_limit import RateLimit
from networkpype.throttler.throttler import AsyncThrottler


async def main():
    throttler = AsyncThrottler(
        rate_limits=[RateLimit(limit_id="default", limit=10, time_interval=1.0)]
    )
    factory = ConnectionManagersFactory(throttler=throttler)

    try:
        manager = await factory.get_rest_manager()

        # GET request with query parameters
        data = await manager.execute_request(
            url="https://api.example.com/v1/ticker",
            throttler_limit_id="default",
            method=RESTMethod.GET,
            params={"symbol": "BTCUSDT"},
        )
        print(data)

        # POST request with a JSON body
        result = await manager.execute_request(
            url="https://api.example.com/v1/order",
            throttler_limit_id="default",
            method=RESTMethod.POST,
            data={"symbol": "BTCUSDT", "side": "BUY", "quantity": "0.001"},
            is_auth_required=True,
        )
        print(result)
    finally:
        await factory.close()


asyncio.run(main())
```

`execute_request` returns the parsed JSON response as a `dict`. It raises `OSError` on HTTP 4xx/5xx errors by default; pass `return_err=True` to receive the error body instead.

## Setting Up WebSocket Connections

Get a `WebSocketManager` from the factory, connect, and iterate messages:

```python
import asyncio

from networkpype.factory import ConnectionManagersFactory
from networkpype.throttler.rate_limit import RateLimit
from networkpype.throttler.throttler import AsyncThrottler
from networkpype.websocket.request import WebSocketJSONRequest


async def main():
    throttler = AsyncThrottler(
        rate_limits=[RateLimit(limit_id="default", limit=10, time_interval=1.0)]
    )
    factory = ConnectionManagersFactory(throttler=throttler)

    try:
        ws_manager = await factory.get_ws_manager()
        await ws_manager.connect("wss://stream.example.com/ws")

        # Subscribe to a data stream
        await ws_manager.subscribe(
            WebSocketJSONRequest(
                payload={"method": "SUBSCRIBE", "params": ["btcusdt@trade"]}
            )
        )

        # Process incoming messages
        async for message in ws_manager.iter_messages():
            if message:
                print(message.data)

        await ws_manager.disconnect()
    finally:
        await factory.close()


asyncio.run(main())
```

## Using Rate Limiting

`AsyncThrottler` supports multiple rate limits per factory, with weighted requests and linked limits:

```python
from decimal import Decimal

from networkpype.throttler.rate_limit import LinkedLimitWeightPair, RateLimit
from networkpype.throttler.throttler import AsyncThrottler

throttler = AsyncThrottler(
    rate_limits=[
        # Global pool: 1200 requests per minute
        RateLimit(limit_id="global", limit=1200, time_interval=60.0),
        # Endpoint-specific: 10 requests per second, also consumes from global
        RateLimit(
            limit_id="/api/ticker",
            limit=10,
            time_interval=1.0,
            linked_limits=[LinkedLimitWeightPair(limit_id="global", weight=1)],
        ),
    ],
    safety_margin_pct=0.05,           # 5% safety margin
    limits_share_percentage=Decimal("50"),  # share 50% of limits with other instances
)
```

Requests are throttled automatically inside `execute_request` via the `throttler_limit_id` parameter. You can also use the throttler directly:

```python
async with throttler.execute_task("/api/ticker"):
    # code here runs only when capacity is available
    ...
```

## Next Steps

- [REST Guide](../guide/rest.md) --- Processors, error handling, and advanced patterns
- [WebSocket Guide](../guide/websocket.md) --- Connection lifecycle and message processing
- [Rate Limiting Guide](../guide/throttling.md) --- Linked limits, sharing, and configuration
- [Authentication Guide](../guide/authentication.md) --- Implementing custom auth schemes
