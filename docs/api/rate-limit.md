# RateLimit

`networkpype.throttler.rate_limit`

## RateLimit

Dataclass declaring rate limit rules for an API endpoint or pool.

```python
@dataclass
class RateLimit:
    limit_id: str
    limit: int
    time_interval: float
    weight: int = 1
    linked_limits: list[LinkedLimitWeightPair] = field(default_factory=list)
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `limit_id` | `str` | — | Unique identifier; passed to `execute_task` and `execute_request(throttler_limit_id=...)` |
| `limit` | `int` | — | Maximum weighted requests within `time_interval` |
| `time_interval` | `float` | — | Time window in seconds |
| `weight` | `int` | `1` | How much each request counts against `limit` |
| `linked_limits` | `list[LinkedLimitWeightPair]` | `[]` | Other limits also consumed by requests against this limit |

### Class Methods

---

#### `filter_rate_limits_list`

```python
@classmethod
def filter_rate_limits_list(
    rate_limits: list[RateLimit],
    limit_ids: list[str],
) -> list[RateLimit]
```

Return a new list excluding any `RateLimit` whose `limit_id` is in `limit_ids`.

**Example:**

```python
endpoint_only = RateLimit.filter_rate_limits_list(
    all_limits,
    ["global"],  # exclude global pool
)
```

---

## LinkedLimitWeightPair

Associates a weight with a linked rate limit. Used inside `RateLimit.linked_limits` to declare that consuming one limit also partially consumes another.

```python
@dataclass
class LinkedLimitWeightPair:
    limit_id: str
    weight: int = 1
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `limit_id` | `str` | — | The `limit_id` of the linked `RateLimit` |
| `weight` | `int` | `1` | How many units to consume from the linked limit per request |

---

## TaskLog

Internal dataclass tracking a single rate-limited task execution.

```python
@dataclass
class TaskLog:
    timestamp: float
    rate_limit: RateLimit
    weight: int = 1
```

`TaskLog` instances are created by `AsyncRequestContext.acquire` and stored in the shared task log. The throttler uses them to calculate current capacity usage.

---

## Examples

### Simple endpoint limit

```python
from networkpype.throttler.rate_limit import RateLimit

ticker_limit = RateLimit(
    limit_id="/api/v1/ticker",
    limit=10,
    time_interval=1.0,
)
```

### Weighted request

```python
order_limit = RateLimit(
    limit_id="/api/v1/order",
    limit=100,
    time_interval=60.0,
    weight=5,  # each order consumes 5 units
)
```

### Linked limits

```python
from networkpype.throttler.rate_limit import LinkedLimitWeightPair, RateLimit

limits = [
    RateLimit(limit_id="global", limit=1200, time_interval=60.0),
    RateLimit(
        limit_id="/api/v1/ticker",
        limit=10,
        time_interval=1.0,
        linked_limits=[LinkedLimitWeightPair(limit_id="global", weight=1)],
    ),
    RateLimit(
        limit_id="/api/v1/order",
        limit=5,
        time_interval=1.0,
        linked_limits=[LinkedLimitWeightPair(limit_id="global", weight=10)],
    ),
]
```
