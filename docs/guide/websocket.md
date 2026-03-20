# WebSocket

NetworkPype's WebSocket stack mirrors the REST stack: a low-level `WebSocketConnection` wraps aiohttp, and `WebSocketManager` adds the pre/post processing pipeline and authentication.

## Connections

`WebSocketConnection` manages the raw WebSocket lifecycle. It automatically handles control frames:

- **Ping frames** → replies with a pong and discards the frame
- **Pong frames** → discards the frame
- **Close frames** → sets `connected = False` and raises `ConnectionError`

```python
import aiohttp
from networkpype.websocket.connection import WebSocketConnection
from networkpype.websocket.request import WebSocketJSONRequest

async with aiohttp.ClientSession() as session:
    conn = WebSocketConnection(aiohttp_client_session=session)
    await conn.connect(
        ws_url="wss://stream.example.com/ws",
        ping_timeout=10,
        message_timeout=30.0,
    )

    await conn.send(WebSocketJSONRequest(payload={"method": "SUBSCRIBE"}))

    while conn.connected:
        response = await conn.receive()
        if response:
            print(response.data)

    await conn.disconnect()
```

`connect` parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ws_url` | `str` | — | WebSocket endpoint URL |
| `ping_timeout` | `float` | `10` | Seconds to wait for a pong |
| `auto_ping` | `bool` | `False` | Let aiohttp send pings automatically |
| `message_timeout` | `float \| None` | `None` | Max seconds to wait for a message |
| `ws_headers` | `dict \| None` | `None` | Extra connection headers |
| `verify_ssl` | `bool` | `True` | Verify SSL certificates |

## Using WebSocketManager

`WebSocketManager` is the recommended interface. It orchestrates pre/post processors and authentication:

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

# Subscribe
await ws_manager.subscribe(
    WebSocketJSONRequest(
        payload={"method": "SUBSCRIBE", "params": ["btcusdt@trade"]}
    )
)
```

## Sending Messages

Two concrete request types are available:

```python
from networkpype.websocket.request import WebSocketJSONRequest, WebSocketPlainTextRequest

# JSON message
json_req = WebSocketJSONRequest(
    payload={"type": "subscribe", "channel": "orderbook"},
    is_auth_required=True,
)

# Plain text message (e.g., ping protocols)
text_req = WebSocketPlainTextRequest(payload="PING")

await ws_manager.send(json_req)
await ws_manager.send(text_req)
```

`subscribe` is an alias for `send` that will eventually support automatic re-subscription on reconnection.

## Receiving Messages

### Streaming with `iter_messages`

The idiomatic approach for continuous streams:

```python
async for message in ws_manager.iter_messages():
    if message:
        handle(message.data)
```

`iter_messages` loops until the connection closes. Post-processors run on each message before it is yielded.

### Single receive

```python
response = await ws_manager.receive()
if response:
    handle(response.data)
```

## WebSocket Responses

`WebSocketResponse` is a simple dataclass:

```python
from networkpype.websocket.response import WebSocketResponse

response: WebSocketResponse  # received from manager
print(response.data)         # dict (JSON), str (text), or bytes (binary)
```

Text messages are parsed as JSON when possible. Binary messages are returned as raw `bytes`.

## Pre-Processors

Implement `WebSocketPreProcessor` to modify outgoing messages:

```python
from networkpype.websocket.processor.base import WebSocketPreProcessor
from networkpype.websocket.request import WebSocketRequest


class AddTimestampProcessor(WebSocketPreProcessor):
    async def pre_process(self, request: WebSocketRequest) -> WebSocketRequest:
        if isinstance(request.payload, dict):
            request.payload["timestamp"] = 1234567890
        return request
```

## Post-Processors

Implement `WebSocketPostProcessor` to transform incoming messages:

```python
from networkpype.websocket.processor.base import WebSocketPostProcessor
from networkpype.websocket.response import WebSocketResponse


class FilterHeartbeats(WebSocketPostProcessor):
    async def post_process(self, response: WebSocketResponse) -> WebSocketResponse:
        if isinstance(response.data, dict) and response.data.get("type") == "ping":
            response.data = None  # signal to application to ignore
        return response
```

Register both when building the factory:

```python
factory = ConnectionManagersFactory(
    throttler=throttler,
    ws_pre_processors=[AddTimestampProcessor()],
    ws_post_processors=[FilterHeartbeats()],
)
```

## Connection Health

`WebSocketManager.last_recv_time` returns the Unix timestamp of the last received data frame. Use it to implement keep-alive logic:

```python
import time

if time.time() - ws_manager.last_recv_time > 30:
    await ws_manager.ping()
```

## Next Steps

- [Authentication](authentication.md) --- Sign WebSocket messages
- [API Reference: WebSocketManager](../api/ws-manager.md) --- Full method signatures
