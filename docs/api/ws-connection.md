# WebSocketConnection

`networkpype.websocket.connection`

Low-level WebSocket connection handler that wraps an `aiohttp.ClientSession`. Handles connection lifecycle, message sending/receiving, and automatic control frame responses (ping/pong). Obtain instances through `ConnectionsFactory.get_ws_connection()` or use `WebSocketManager` as the higher-level interface.

```python
class WebSocketConnection
```

## Constructor

```python
WebSocketConnection(aiohttp_client_session: aiohttp.ClientSession)
```

**Parameters:**

- `aiohttp_client_session` — The aiohttp session to use for the WebSocket upgrade.

## Properties

---

### `connected`

```python
@property
def connected() -> bool
```

`True` if the WebSocket connection is currently open.

---

### `last_recv_time`

```python
@property
def last_recv_time() -> float
```

Unix timestamp (seconds) of the last received data frame. Returns `0.0` if no message has been received yet.

## Methods

---

### `connect`

```python
async def connect(
    ws_url: str,
    ping_timeout: float = 10,
    auto_ping: bool = False,
    message_timeout: float | None = None,
    ws_headers: dict[str, Any] | None = None,
    verify_ssl: bool = True,
) -> None
```

Establish the WebSocket connection.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ws_url` | `str` | — | WebSocket endpoint URL |
| `ping_timeout` | `float` | `10` | Seconds to wait for a pong response |
| `auto_ping` | `bool` | `False` | Let aiohttp send pings automatically |
| `message_timeout` | `float \| None` | `None` | Max seconds to wait for the next message |
| `ws_headers` | `dict \| None` | `None` | Extra headers for the upgrade request |
| `verify_ssl` | `bool` | `True` | Verify SSL certificates |

**Raises:**

- `RuntimeError` — if already connected
- `aiohttp.ClientError` — if the connection fails

---

### `disconnect`

```python
async def disconnect() -> None
```

Close the WebSocket connection. Safe to call multiple times.

---

### `send`

```python
async def send(request: WebSocketRequest) -> None
```

Send a WebSocket message. Delegates to `request.send_with_connection(self)`.

**Raises:**

- `RuntimeError` — if not connected
- `aiohttp.ClientError` — on send failure

---

### `ping`

```python
async def ping() -> None
```

Send a WebSocket ping frame.

**Raises:** `RuntimeError` if not connected.

---

### `receive`

```python
async def receive() -> WebSocketResponse | None
```

Receive the next data message. Automatically:

- Replies to ping frames with a pong (returns `None` for the ping)
- Discards pong frames (returns `None`)
- Raises `ConnectionError` on unexpected close frames

**Returns:** `WebSocketResponse` or `None` if a control frame was processed.

**Raises:**

- `RuntimeError` — if not connected
- `TimeoutError` — if `message_timeout` expires
- `ConnectionError` — if the connection closes unexpectedly

## Example

```python
import aiohttp
from networkpype.websocket.connection import WebSocketConnection
from networkpype.websocket.request import WebSocketJSONRequest

async with aiohttp.ClientSession() as session:
    conn = WebSocketConnection(aiohttp_client_session=session)
    await conn.connect("wss://stream.example.com/ws", message_timeout=30.0)

    await conn.send(WebSocketJSONRequest(payload={"method": "SUBSCRIBE"}))

    while conn.connected:
        msg = await conn.receive()
        if msg:
            print(msg.data)

    await conn.disconnect()
```
