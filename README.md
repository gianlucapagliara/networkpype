# NetworkPype

[![CI](https://github.com/gianlucapagliara/networkpype/actions/workflows/ci.yml/badge.svg)](https://github.com/gianlucapagliara/networkpype/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/gianlucapagliara/networkpype/branch/main/graph/badge.svg)](https://codecov.io/gh/gianlucapagliara/networkpype)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/networkpype)](https://pypi.org/project/networkpype/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://gianlucapagliara.github.io/networkpype/)

A Python library for building efficient network communication pipelines, supporting both REST and WebSocket protocols with built-in rate limiting and time synchronization.

## Features

- 🔄 **Dual Protocol Support**: Unified factory for REST and WebSocket connections
- 🚦 **Async Rate Limiting**: Built-in throttler with multiple concurrent limits and weighted consumption
- ⏰ **Time Synchronization**: Rolling-window server time alignment for timestamp-sensitive APIs
- 🏭 **Factory Pattern**: `ConnectionsFactory` and `ConnectionManagersFactory` for clean lifecycle management
- 🔌 **Processor Pipeline**: Composable pre/post processors for request transformation and response handling
- 🛡️ **Authentication**: Abstract `Auth` base class supporting any scheme (API key, OAuth, HMAC, JWT)
- 🔒 **Type Safe**: Fully typed with MyPy strict mode
- 🧪 **Well Tested**: Comprehensive test suite with high coverage

## Installation

```bash
# Using pip
pip install networkpype

# Using uv
uv add networkpype
```

## Quick Start

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
        url="https://api.example.com/v1/data",
        throttler_limit_id="default",
        method=RESTMethod.GET,
    )
    print(data)

    await factory.close()


asyncio.run(main())
```

## Core Components

- **Factory**: Entry point for creating connections
  - `ConnectionsFactory`: Low-level aiohttp session management
  - `ConnectionManagersFactory`: High-level managers with auth, throttling, and processors

- **REST**: Full HTTP pipeline
  - `RESTConnection`: Raw aiohttp wrapper
  - `RESTManager`: Orchestrates throttling, auth, and pre/post processors
  - `RESTRequest` / `RESTResponse`: Type-safe request and response containers

- **WebSocket**: Persistent connection management
  - `WebSocketConnection`: Low-level connection with ping/pong handling
  - `WebSocketManager`: Message pipeline with auth and processors
  - `WebSocketJSONRequest` / `WebSocketPlainTextRequest`: Typed message types

- **Throttler**: Async rate limiting
  - `AsyncThrottler`: Multi-limit, weighted rate limiter
  - `RateLimit`: Declarative limit configuration with linked limits
  - `AsyncRequestContext`: Context manager for acquiring capacity

- **Auth**: Authentication framework
  - `Auth`: Abstract base — subclass to implement any authentication scheme

- **TimeSynchronizer**: Server time alignment
  - Rolling-window offset with median + weighted-average calculation

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

## Documentation

Full documentation is available at [gianlucapagliara.github.io/networkpype](https://gianlucapagliara.github.io/networkpype/).

## Development

NetworkPype uses [uv](https://docs.astral.sh/uv/) for dependency management and packaging:

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run type checks
uv run mypy networkpype

# Run linting
uv run ruff check .

# Run pre-commit hooks
uv run pre-commit run --all-files
```
