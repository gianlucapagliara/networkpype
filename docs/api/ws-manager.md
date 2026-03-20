# WebSocketManager

`networkpype.websocket.manager`

High-level manager for WebSocket communication. Orchestrates connection lifecycle, pre/post processing, and authentication. Obtain instances via `ConnectionManagersFactory.get_ws_manager()`.

```python
class WebSocketManager
```

## Constructor

```python
WebSocketManager(
    connection: WebSocketConnection,
    ws_pre_processors: list[WebSocketPreProcessor] | None = None,
    ws_post_processors: list[WebSocketPostProcessor] | None = None,
    auth: Auth | None = None,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `connection` | `WebSocketConnection` | — | Underlying connection |
| `ws_pre_processors` | `list[WebSocketPreProcessor] \| None` | `None` | Pre-processors for outgoing messages |
| `ws_post_processors` | `list[WebSocketPostProcessor] \| None` | `None` | Post-processors for incoming messages |
| `auth` | `Auth \| None` | `None` | Authentication handler |

## Properties

---

### `last_recv_time`

```python
@property
def last_recv_time() -> float
```

Unix timestamp (seconds) of the last received data frame from the underlying connection.

## Methods

---

### `connect`

```python
async def connect(
    ws_url: str,
    *,
    ping_timeout: float = 10,
    auto_ping: bool = False,
    message_timeout: float | None = None,
    ws_headers: dict[str, Any] | None = None,
    verify_ssl: bool = True,
) -> None
```

Establish the WebSocket connection. All keyword parameters are forwarded to `WebSocketConnection.connect`.

---

### `disconnect`

```python
async def disconnect() -> None
```

Close the WebSocket connection.

---

### `subscribe`

```python
async def subscribe(request: WebSocketRequest) -> None
```

Send a subscription request. Currently an alias for `send`. Future versions will support automatic re-subscription on reconnection.

---

### `send`

```python
async def send(request: WebSocketRequest) -> None
```

Send a WebSocket message through the full pipeline: pre-process → authenticate (if `is_auth_required`) → send.

**Parameters:**

- `request` — The message to send.

---

### `ping`

```python
async def ping() -> None
```

Send a WebSocket ping frame to keep the connection alive or check health.

---

### `iter_messages`

```python
async def iter_messages() -> AsyncGenerator[WebSocketResponse | None]
```

Async generator that yields messages as they arrive. Runs post-processors on each message. Stops when the connection closes.

**Yields:** `WebSocketResponse | None`

**Example:**

```python
async for message in ws_manager.iter_messages():
    if message:
        handle(message.data)
```

---

### `receive`

```python
async def receive() -> WebSocketResponse | None
```

Receive and post-process a single message.

**Returns:** `WebSocketResponse | None`

## Example

```python
from networkpype.factory import ConnectionManagersFactory
from networkpype.throttler.rate_limit import RateLimit
from networkpype.throttler.throttler import AsyncThrottler
from networkpype.websocket.request import WebSocketJSONRequest

throttler = AsyncThrottler(
    rate_limits=[RateLimit(limit_id="default", limit=10, time_interval=1.0)]
)
factory = ConnectionManagersFactory(throttler=throttler)

ws_manager = await factory.get_ws_manager()
await ws_manager.connect("wss://stream.example.com/ws")

await ws_manager.subscribe(
    WebSocketJSONRequest(
        payload={"method": "SUBSCRIBE", "params": ["btcusdt@trade"]}
    )
)

async for message in ws_manager.iter_messages():
    if message:
        print(message.data)

await ws_manager.disconnect()
await factory.close()
```

## WebSocket Processors

---

### `WebSocketPreProcessor`

```python
class WebSocketPreProcessor(abc.ABC)

@abstractmethod
async def pre_process(request: WebSocketRequest) -> WebSocketRequest
```

Modify outgoing messages before they are sent.

---

### `WebSocketPostProcessor`

```python
class WebSocketPostProcessor(abc.ABC)

@abstractmethod
async def post_process(response: WebSocketResponse) -> WebSocketResponse
```

Transform incoming messages before they reach the application.
