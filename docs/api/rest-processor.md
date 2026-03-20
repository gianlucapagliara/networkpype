# REST Processors

`networkpype.rest.processor.base` · `networkpype.rest.processor.time_synchronizer`

Processors inject custom logic into the `RESTManager` pipeline. Pre-processors run before a request is sent; post-processors run after a response is received.

## RESTPreProcessor

Abstract base class for request processors.

```python
class RESTPreProcessor(abc.ABC)
```

### Abstract Method

```python
@abstractmethod
async def pre_process(request: RESTRequest) -> RESTRequest
```

Modify or validate the request before it is sent.

**Parameters:**

- `request` — The outgoing `RESTRequest`.

**Returns:** The (possibly modified) `RESTRequest`.

### Example

```python
from networkpype.rest.processor.base import RESTPreProcessor
from networkpype.rest.request import RESTRequest


class RequestLogger(RESTPreProcessor):
    async def pre_process(self, request: RESTRequest) -> RESTRequest:
        print(f"-> {request.method} {request.url}")
        return request
```

## RESTPostProcessor

Abstract base class for response processors.

```python
class RESTPostProcessor(abc.ABC)
```

### Abstract Method

```python
@abstractmethod
async def post_process(response: RESTResponse) -> RESTResponse
```

Modify or inspect the response before it reaches the caller.

**Parameters:**

- `response` — The `RESTResponse` from the server.

**Returns:** The (possibly modified) `RESTResponse`.

### Example

```python
from networkpype.rest.processor.base import RESTPostProcessor
from networkpype.rest.response import RESTResponse


class StatusLogger(RESTPostProcessor):
    async def post_process(self, response: RESTResponse) -> RESTResponse:
        print(f"<- {response.status} {response.url}")
        return response
```

## TimeSynchronizerRESTPreProcessor

Built-in pre-processor that ensures the `TimeSynchronizer` has at least one server time sample before any request is sent. Useful for APIs that reject requests with stale timestamps.

```python
class TimeSynchronizerRESTPreProcessor(RESTPreProcessor)
```

### Constructor

```python
TimeSynchronizerRESTPreProcessor(
    synchronizer: TimeSynchronizer,
    time_provider: Callable[..., Any],
)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `synchronizer` | `TimeSynchronizer` | The shared time synchronizer |
| `time_provider` | `Callable[..., Any]` | Zero-argument callable returning an awaitable that resolves to the server time in milliseconds |

### Example

```python
from networkpype.rest.processor.time_synchronizer import TimeSynchronizerRESTPreProcessor
from networkpype.time_synchronizer import TimeSynchronizer
from networkpype.factory import ConnectionManagersFactory
from networkpype.throttler.throttler import AsyncThrottler
from networkpype.throttler.rate_limit import RateLimit


async def get_server_time_ms() -> float:
    # Call your API's server time endpoint
    ...


synchronizer = TimeSynchronizer(max_samples=5)
pre_processor = TimeSynchronizerRESTPreProcessor(
    synchronizer=synchronizer,
    time_provider=get_server_time_ms,
)

factory = ConnectionManagersFactory(
    throttler=AsyncThrottler(
        rate_limits=[RateLimit(limit_id="default", limit=10, time_interval=1.0)]
    ),
    rest_pre_processors=[pre_processor],
    time_synchronizer=synchronizer,
)
```

## Registering Processors

Pass lists of processors to `ConnectionManagersFactory`:

```python
factory = ConnectionManagersFactory(
    throttler=throttler,
    rest_pre_processors=[RequestLogger(), pre_processor],
    rest_post_processors=[StatusLogger()],
)
```

Processors execute in list order. Pre-processors run before authentication; post-processors run after the response is received from the server.
