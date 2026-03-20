# TimeSynchronizer

`networkpype.time_synchronizer`

Aligns local client time with server time using a rolling window of offset samples. Combines median and weighted-average statistics to produce a stable, drift-resistant estimate.

```python
class TimeSynchronizer
```

## Constructor

```python
TimeSynchronizer(max_samples: int = 5)
```

**Parameters:**

- `max_samples` — Maximum number of offset samples to keep. Older samples are discarded automatically (FIFO). Defaults to `5`.

## Properties

---

### `time_offset_ms`

```python
@property
def time_offset_ms() -> float
```

The current best estimate of the server-client time offset in milliseconds.

Calculation:
1. Compute the median of stored samples.
2. Compute the weighted average (more-recent samples have higher weight).
3. Return the mean of (1) and (2).

If no samples exist, falls back to `time.time() - time.perf_counter()` in milliseconds.

## Methods

---

### `time`

```python
def time() -> float
```

Return the current synchronized time in seconds since the epoch.

`synchronized_time = perf_counter() + time_offset_ms / 1000`

---

### `add_time_offset_ms_sample`

```python
def add_time_offset_ms_sample(offset: float) -> None
```

Append a raw offset sample (in milliseconds) to the rolling window.

---

### `clear_time_offset_ms_samples`

```python
def clear_time_offset_ms_samples() -> None
```

Discard all stored samples. Forces re-synchronization on the next call to `update_server_time_if_not_initialized`.

---

### `update_server_time_offset_with_time_provider`

```python
async def update_server_time_offset_with_time_provider(
    time_provider: Awaitable[float],
) -> None
```

Fetch the server time and compute a new offset sample.

Uses a before/after local timestamp approach to account for network latency:

```
offset_ms = server_time_ms - (local_before_ms + local_after_ms) / 2
```

**Parameters:**

- `time_provider` — An awaitable that resolves to the server time in **milliseconds**.

**Raises:**

- `asyncio.CancelledError` — propagated if the task is cancelled
- Other exceptions are caught and logged; the sample is not added on error.

---

### `update_server_time_if_not_initialized`

```python
async def update_server_time_if_not_initialized(
    time_provider: Awaitable[float],
) -> None
```

Call `update_server_time_offset_with_time_provider` only if no samples exist. If samples are present and `time_provider` is an `asyncio.Task`, it is cancelled to avoid resource leaks.

Used by `TimeSynchronizerRESTPreProcessor` to lazily initialize synchronization before the first request.

---

## Example

```python
import asyncio
from networkpype.time_synchronizer import TimeSynchronizer


async def fetch_server_time_ms() -> float:
    # Query your API's server time endpoint (returns ms)
    return 1_700_000_000_123.0


async def main():
    sync = TimeSynchronizer(max_samples=5)

    # Initial synchronization
    await sync.update_server_time_offset_with_time_provider(
        fetch_server_time_ms()
    )

    print(f"Offset: {sync.time_offset_ms:.1f} ms")
    print(f"Current synchronized time: {sync.time():.3f} s")

    # Periodic resync
    for _ in range(3):
        await asyncio.sleep(10)
        await sync.update_server_time_offset_with_time_provider(
            fetch_server_time_ms()
        )
        print(f"Updated offset: {sync.time_offset_ms:.1f} ms")


asyncio.run(main())
```
