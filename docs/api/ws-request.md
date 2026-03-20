# WebSocket Requests and Responses

`networkpype.websocket.request` · `networkpype.websocket.response`

## WebSocketRequest

Abstract base dataclass for all WebSocket requests.

```python
@dataclass
class WebSocketRequest(ABC):
    payload: Any
    throttler_limit_id: str | None = None
    is_auth_required: bool = False
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `payload` | `Any` | — | Message content (type depends on subclass) |
| `throttler_limit_id` | `str \| None` | `None` | Rate limit ID (for future use) |
| `is_auth_required` | `bool` | `False` | If `True`, `Auth.ws_authenticate` is called |

### Abstract Method

```python
@abstractmethod
async def send_with_connection(connection: WebSocketConnection) -> None
```

Subclasses implement this to define how the message is transmitted.

---

## WebSocketJSONRequest

Concrete request for sending JSON-formatted messages.

```python
@dataclass
class WebSocketJSONRequest(WebSocketRequest):
    payload: Mapping[str, Any]
    throttler_limit_id: str | None = None
    is_auth_required: bool = False
```

Serializes `payload` to JSON and sends via `connection._send_json`.

### Example

```python
from networkpype.websocket.request import WebSocketJSONRequest

request = WebSocketJSONRequest(
    payload={"method": "SUBSCRIBE", "params": ["btcusdt@trade"], "id": 1},
    is_auth_required=False,
)
await ws_manager.send(request)
```

---

## WebSocketPlainTextRequest

Concrete request for sending plain text messages.

```python
@dataclass
class WebSocketPlainTextRequest(WebSocketRequest):
    payload: str
    throttler_limit_id: str | None = None
    is_auth_required: bool = False
```

Sends `payload` as a raw text frame via `connection._send_plain_text`.

### Example

```python
from networkpype.websocket.request import WebSocketPlainTextRequest

ping = WebSocketPlainTextRequest(payload="PING")
await ws_manager.send(ping)
```

---

## WebSocketResponse

Dataclass wrapping a received WebSocket message.

```python
@dataclass
class WebSocketResponse:
    data: Any
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `data` | `Any` | Message content: `dict` for JSON, `str` for text, `bytes` for binary |

### Parsing Behaviour

`WebSocketConnection._build_resp` attempts to parse text messages as JSON. If parsing fails, the raw string is stored in `data`. Binary frames are stored as `bytes`.

### Example

```python
response = await ws_manager.receive()
if response:
    if isinstance(response.data, dict):
        print(f"JSON message: {response.data}")
    elif isinstance(response.data, str):
        print(f"Text message: {response.data}")
    elif isinstance(response.data, bytes):
        print(f"Binary message: {len(response.data)} bytes")
```
