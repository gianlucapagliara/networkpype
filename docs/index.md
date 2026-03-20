# NetworkPype

[![CI](https://github.com/gianlucapagliara/networkpype/actions/workflows/ci.yml/badge.svg)](https://github.com/gianlucapagliara/networkpype/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/gianlucapagliara/networkpype/branch/main/graph/badge.svg)](https://codecov.io/gh/gianlucapagliara/networkpype)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/networkpype)](https://pypi.org/project/networkpype/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library for building efficient network communication pipelines, supporting both REST and WebSocket protocols with built-in rate limiting, time synchronization, and an extensible processor architecture.

## Features

- **Dual Protocol Support** --- Unified factory for REST and WebSocket connections built on aiohttp
- **Async Rate Limiting** --- Multi-window throttler with weighted consumption and linked limits
- **Time Synchronization** --- Rolling-window server time alignment for timestamp-sensitive APIs
- **Factory Pattern** --- `ConnectionsFactory` and `ConnectionManagersFactory` for clean session management
- **Processor Pipeline** --- Composable pre/post processors for request transformation and response handling
- **Authentication** --- Abstract `Auth` base class supporting any scheme: API key, OAuth, HMAC, JWT
- **Type Safe** --- Fully typed with MyPy strict mode compliance
- **Well Tested** --- Comprehensive test suite with high coverage

## Quick Example

```python
import asyncio
from decimal import Decimal

from networkpype.factory import ConnectionManagersFactory
from networkpype.rest.method import RESTMethod
from networkpype.throttler.rate_limit import RateLimit
from networkpype.throttler.throttler import AsyncThrottler


async def main():
    throttler = AsyncThrottler(
        rate_limits=[RateLimit(limit_id="default", limit=10, time_interval=1.0)]
    )
    factory = ConnectionManagersFactory(throttler=throttler)

    manager = await factory.get_rest_manager()
    data = await manager.execute_request(
        url="https://api.example.com/v1/prices",
        throttler_limit_id="default",
        method=RESTMethod.GET,
        params={"symbol": "BTCUSDT"},
    )
    print(data)

    await factory.close()


asyncio.run(main())
```

## Architecture Overview

NetworkPype is organized around two factory classes and two protocol-specific manager hierarchies:

- **`ConnectionManagersFactory`** is the primary entry point. It holds shared state (throttler, auth, processors, time synchronizer) and creates `RESTManager` and `WebSocketManager` instances on demand.
- **`RESTManager`** and **`WebSocketManager`** orchestrate the full request/response pipeline: pre-processing, authentication, sending, receiving, and post-processing.
- **`AsyncThrottler`** enforces rate limits across all requests using a shared task log and an async context manager interface.

```
ConnectionManagersFactory
├── RESTManager
│   ├── RESTPreProcessor[]   ── modify requests before sending
│   ├── Auth                 ── sign authenticated requests
│   ├── RESTConnection       ── execute HTTP via aiohttp
│   └── RESTPostProcessor[]  ── transform responses
└── WebSocketManager
    ├── WebSocketPreProcessor[]  ── transform outgoing messages
    ├── Auth                     ── sign authenticated messages
    ├── WebSocketConnection      ── manage WS lifecycle
    └── WebSocketPostProcessor[] ── process incoming messages

AsyncThrottler
└── RateLimit[]  ── multiple windows with linked-limit support
```

## Next Steps

- [Installation](getting-started/installation.md) --- Set up networkpype in your project
- [Quick Start](getting-started/quickstart.md) --- Make your first REST and WebSocket requests
- [User Guide](guide/rest.md) --- Deep dives into each subsystem
- [API Reference](api/factory.md) --- Full API documentation
