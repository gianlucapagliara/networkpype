# Rate Limiting

NetworkPype's throttler enforces API rate limits asynchronously using a shared task log and an async context manager interface. It supports multiple concurrent limits, weighted requests, and linked limits where one request affects several pools.

## Core Concepts

| Concept | Class | Description |
|---------|-------|-------------|
| Rate limit definition | `RateLimit` | Declares a limit: `N` requests per `T` seconds |
| Linked limits | `LinkedLimitWeightPair` | One request consumes capacity from another limit |
| Task log | `TaskLog` | Records when capacity was consumed |
| Throttler | `AsyncThrottler` | Manages the shared log and enforces limits |
| Context | `AsyncRequestContext` | Awaitable gate that blocks until capacity is free |

## Defining Rate Limits

```python
from networkpype.throttler.rate_limit import RateLimit

# Simple: 10 requests per second
simple = RateLimit(
    limit_id="ticker",
    limit=10,
    time_interval=1.0,
)

# Weighted: each request counts as 2 units
weighted = RateLimit(
    limit_id="order",
    limit=100,
    time_interval=60.0,
    weight=2,
)
```

`limit_id` is the key you pass to `execute_task` (and `execute_request`'s `throttler_limit_id` parameter).

## Linked Limits

Linked limits let a request against one endpoint also consume capacity from a shared global pool:

```python
from networkpype.throttler.rate_limit import LinkedLimitWeightPair, RateLimit

RATE_LIMITS = [
    # Global pool: 1200 requests per minute
    RateLimit(limit_id="global", limit=1200, time_interval=60.0),

    # Endpoint pool: 10 per second, also drains the global pool by 1
    RateLimit(
        limit_id="/api/v1/ticker",
        limit=10,
        time_interval=1.0,
        linked_limits=[LinkedLimitWeightPair(limit_id="global", weight=1)],
    ),

    # Heavy endpoint: 5 per second, drains global pool by 5 each time
    RateLimit(
        limit_id="/api/v1/order",
        limit=5,
        time_interval=1.0,
        linked_limits=[LinkedLimitWeightPair(limit_id="global", weight=5)],
    ),
]
```

## Creating the Throttler

```python
from decimal import Decimal
from networkpype.throttler.throttler import AsyncThrottler

throttler = AsyncThrottler(
    rate_limits=RATE_LIMITS,
    retry_interval=0.1,          # seconds between capacity checks
    safety_margin_pct=0.05,      # use only 95% of declared limits
    limits_share_percentage=Decimal("50"),  # this instance uses 50% of limits
)
```

`limits_share_percentage` is useful when multiple application processes share a single API key. Setting it to `Decimal("50")` halves every limit, so two processes together stay within the full quota.

## Using the Throttler Directly

```python
async with throttler.execute_task("/api/v1/ticker"):
    response = await make_raw_request()
```

`execute_task` blocks until capacity is available, then logs the task and allows the block to run.

## Integration with RESTManager

`RESTManager.execute_request` handles throttling automatically via `throttler_limit_id`:

```python
data = await manager.execute_request(
    url="https://api.example.com/api/v1/ticker",
    throttler_limit_id="/api/v1/ticker",
    method=RESTMethod.GET,
)
```

The manager wraps the network call inside `throttler.execute_task(throttler_limit_id)`, so no manual context manager is needed.

## Safety Margin

The `safety_margin_pct` parameter reserves a fraction of each limit as a buffer. For example, with `limit=100` and `safety_margin_pct=0.05`, the effective limit is 95. This prevents exceeding the declared limit due to clock skew or network latency in the capacity check window.

## Updating Limits at Runtime

You can swap the rate limit list on an existing throttler:

```python
throttler.rate_limits = [
    RateLimit(limit_id="global", limit=600, time_interval=60.0),
]
```

The setter deep-copies the list and rebuilds the internal ID map.

## Next Steps

- [Connection Factory](factory.md) --- Pass the throttler into `ConnectionManagersFactory`
- [API Reference: AsyncThrottler](../api/throttler.md) --- Full API
- [API Reference: RateLimit](../api/rate-limit.md) --- Dataclass fields
