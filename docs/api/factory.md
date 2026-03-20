# ConnectionManagersFactory

`networkpype.factory`

## ConnectionsFactory

Low-level factory that creates and manages a shared `aiohttp.ClientSession`.

```python
class ConnectionsFactory
```

### Constructor

```python
ConnectionsFactory()
```

Creates the factory with no active session. The session is created lazily on the first connection request.

### Methods

---

#### `get_rest_connection`

```python
async def get_rest_connection() -> RESTConnection
```

Returns a `RESTConnection` backed by the shared aiohttp session. Creates the session if it does not yet exist.

---

#### `get_ws_connection`

```python
async def get_ws_connection(**kwargs: Any) -> WebSocketConnection
```

Returns a `WebSocketConnection` backed by the shared aiohttp session.

**Parameters:**

- `**kwargs` — forwarded to `aiohttp.ClientSession()` if the session has not yet been created.

---

#### `update_cookies`

```python
async def update_cookies(cookies: Any) -> None
```

Updates cookies in the shared session's cookie jar.

---

#### `close`

```python
async def close() -> None
```

Closes the shared aiohttp session and sets it to `None`. Safe to call multiple times.

---

## ConnectionManagersFactory

High-level factory that creates fully configured `RESTManager` and `WebSocketManager` instances.

```python
class ConnectionManagersFactory
```

### Constructor

```python
ConnectionManagersFactory(
    throttler: AsyncThrottler,
    auth: Auth | None = None,
    rest_pre_processors: list[RESTPreProcessor] | None = None,
    rest_post_processors: list[RESTPostProcessor] | None = None,
    ws_pre_processors: list[WebSocketPreProcessor] | None = None,
    ws_post_processors: list[WebSocketPostProcessor] | None = None,
    time_synchronizer: TimeSynchronizer | None = None,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `throttler` | `AsyncThrottler` | — | Rate limiter applied to all REST requests |
| `auth` | `Auth \| None` | `None` | Authentication handler for signed requests |
| `rest_pre_processors` | `list[RESTPreProcessor] \| None` | `None` | Processors run before each REST request |
| `rest_post_processors` | `list[RESTPostProcessor] \| None` | `None` | Processors run after each REST response |
| `ws_pre_processors` | `list[WebSocketPreProcessor] \| None` | `None` | Processors run before each outgoing WS message |
| `ws_post_processors` | `list[WebSocketPostProcessor] \| None` | `None` | Processors run after each incoming WS message |
| `time_synchronizer` | `TimeSynchronizer \| None` | `None` | Time sync component, accessible via the property |

### Properties

---

#### `throttler`

```python
@property
def throttler() -> AsyncThrottler
```

The shared rate limiting throttler.

---

#### `time_synchronizer`

```python
@property
def time_synchronizer() -> TimeSynchronizer | None
```

The time synchronization component if configured, `None` otherwise.

---

#### `auth`

```python
@property
def auth() -> Auth | None
```

The authentication handler if configured, `None` otherwise.

---

### Methods

---

#### `get_rest_manager`

```python
async def get_rest_manager() -> RESTManager
```

Creates a new `RESTManager` using the shared aiohttp session and all configured components (throttler, auth, pre/post processors).

**Returns:** A fully configured `RESTManager`.

---

#### `get_ws_manager`

```python
async def get_ws_manager(**kwargs: Any) -> WebSocketManager
```

Creates a new `WebSocketManager` using the shared aiohttp session and all configured WebSocket components.

**Parameters:**

- `**kwargs` — forwarded to `get_ws_connection` (and thus to `ClientSession` if the session is new).

**Returns:** A fully configured `WebSocketManager`.

---

#### `update_cookies`

```python
async def update_cookies(cookies: Any) -> None
```

Forwards cookie updates to the underlying `ConnectionsFactory`.

---

#### `close`

```python
async def close() -> None
```

Closes all connections managed by the underlying `ConnectionsFactory`.

---

## Auth

Abstract base class for authentication. Subclass this to implement any authentication scheme.

```python
class Auth
```

### Constructor

```python
Auth(time_provider: TimeSynchronizer | None = None)
```

**Parameters:**

- `time_provider` — `TimeSynchronizer` for synchronized timestamps. If `None`, a new `TimeSynchronizer()` is created.

### Abstract Methods

---

#### `rest_authenticate`

```python
@abstractmethod
async def rest_authenticate(request: RESTRequest) -> RESTRequest
```

Authenticate a REST request. Add headers, query parameters, or a body signature as required by your API.

---

#### `ws_authenticate`

```python
@abstractmethod
async def ws_authenticate(request: WebSocketRequest) -> WebSocketRequest
```

Authenticate a WebSocket request. Add connection parameters or message fields as required.
