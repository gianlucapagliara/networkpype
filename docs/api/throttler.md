# AsyncThrottler

`networkpype.throttler.throttler`

Asynchronous rate limiter for API requests. Manages a shared task log and blocks execution until capacity is available across all relevant rate limits.

```python
class AsyncThrottler
```

## Constructor

```python
AsyncThrottler(
    rate_limits: list[RateLimit],
    retry_interval: float = 0.1,
    safety_margin_pct: float = 0.05,
    limits_share_percentage: Decimal | None = None,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rate_limits` | `list[RateLimit]` | — | Rate limits to enforce |
| `retry_interval` | `float` | `0.1` | Seconds between capacity checks when limits are full |
| `safety_margin_pct` | `float` | `0.05` | Reserve this fraction of each limit as a buffer (e.g. `0.05` = 5%) |
| `limits_share_percentage` | `Decimal \| None` | `None` | Use this percentage of each limit (useful for multi-process deployments); `None` means 100% |

## Properties

---

### `rate_limits`

```python
@property
def rate_limits() -> list[RateLimit]
```

Get the current rate limit list. The setter deep-copies the list, applies `limits_share_percentage`, and rebuilds the internal ID map.

---

### `limits_share_percentage`

```python
@property
def limits_share_percentage() -> Decimal
```

The percentage of limits allocated to this throttler instance. Returns `Decimal("100")` if not set.

## Methods

---

### `execute_task`

```python
def execute_task(limit_id: str) -> AsyncRequestContext
```

Return an async context manager that blocks until capacity is available for the specified rate limit, then logs the task.

**Parameters:**

- `limit_id` — Must match a `RateLimit.limit_id` registered with this throttler.

**Returns:** `AsyncRequestContext`

**Raises:** `ValueError` if `limit_id` is not found.

**Example:**

```python
async with throttler.execute_task("ticker"):
    response = await make_api_call()
```

---

### `get_related_limits`

```python
def get_related_limits(
    limit_id: str,
) -> tuple[RateLimit | None, list[tuple[RateLimit, int]]]
```

Return the primary `RateLimit` for `limit_id` and a list of `(limit, weight)` tuples for that limit plus all linked limits.

**Returns:** `(rate_limit, related_limits)` — `rate_limit` is `None` if not found.

---

### `copy`

```python
def copy() -> AsyncThrottler
```

Create a new `AsyncThrottler` with the same configuration. Useful when you need an independent throttler for a different context.

## AsyncRequestContext

`networkpype.throttler.context`

The context manager returned by `execute_task`. Manages capacity checking and task logging.

```python
class AsyncRequestContext
```

### Key Methods

---

#### `flush`

```python
def flush() -> None
```

Remove expired entries from the task log (entries older than `time_interval * (1 + safety_margin_pct)`).

---

#### `within_capacity`

```python
def within_capacity() -> bool
```

Check whether executing a new task would stay within all related rate limits. Returns `False` if any limit would be exceeded.

---

#### `acquire`

```python
async def acquire() -> None
```

Wait until capacity is available, then log the task. Called automatically by `__aenter__`.

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `MAX_CAPACITY_REACHED_WARNING_INTERVAL` | `30.0` | Minimum seconds between "capacity reached" log warnings |

## Example

```python
from decimal import Decimal
from networkpype.throttler.throttler import AsyncThrottler
from networkpype.throttler.rate_limit import RateLimit, LinkedLimitWeightPair

throttler = AsyncThrottler(
    rate_limits=[
        RateLimit(limit_id="global", limit=1200, time_interval=60.0),
        RateLimit(
            limit_id="/v1/ticker",
            limit=10,
            time_interval=1.0,
            linked_limits=[LinkedLimitWeightPair(limit_id="global", weight=1)],
        ),
    ],
    safety_margin_pct=0.05,
    limits_share_percentage=Decimal("100"),
)

async with throttler.execute_task("/v1/ticker"):
    # guaranteed to run within limits
    data = await fetch_ticker()
```
