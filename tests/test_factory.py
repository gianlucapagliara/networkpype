"""Tests for the ConnectionsFactory and ConnectionManagersFactory classes."""

import pytest

from networkpype.auth import Auth
from networkpype.factory import ConnectionManagersFactory, ConnectionsFactory
from networkpype.rest.connection import RESTConnection
from networkpype.rest.manager import RESTManager
from networkpype.rest.processor.base import RESTPostProcessor, RESTPreProcessor
from networkpype.rest.request import RESTRequest
from networkpype.throttler.rate_limit import RateLimit
from networkpype.throttler.throttler import AsyncThrottler
from networkpype.time_synchronizer import TimeSynchronizer
from networkpype.websocket.connection import WebSocketConnection
from networkpype.websocket.manager import WebSocketManager
from networkpype.websocket.processor.base import (
    WebSocketPostProcessor,
    WebSocketPreProcessor,
)
from networkpype.websocket.request import WebSocketRequest

# --- ConnectionsFactory Tests ---


def test_connections_factory_init():
    """Test ConnectionsFactory initialization."""
    factory = ConnectionsFactory()
    assert factory._shared_client is None


@pytest.mark.asyncio
async def test_connections_factory_get_rest_connection():
    """Test getting a REST connection."""
    factory = ConnectionsFactory()
    conn = await factory.get_rest_connection()
    assert isinstance(conn, RESTConnection)
    assert factory._shared_client is not None
    await factory.close()


@pytest.mark.asyncio
async def test_connections_factory_get_ws_connection():
    """Test getting a WebSocket connection."""
    factory = ConnectionsFactory()
    conn = await factory.get_ws_connection()
    assert isinstance(conn, WebSocketConnection)
    assert factory._shared_client is not None
    await factory.close()


@pytest.mark.asyncio
async def test_connections_factory_shared_client():
    """Test that factory reuses the shared client session."""
    factory = ConnectionsFactory()
    await factory.get_rest_connection()
    client = factory._shared_client
    await factory.get_rest_connection()
    assert factory._shared_client is client
    await factory.close()


@pytest.mark.asyncio
async def test_connections_factory_update_cookies():
    """Test updating cookies in the shared client session."""
    factory = ConnectionsFactory()
    await factory.update_cookies({"session": "abc123"})
    assert factory._shared_client is not None
    await factory.close()


@pytest.mark.asyncio
async def test_connections_factory_close():
    """Test closing the factory."""
    factory = ConnectionsFactory()
    await factory.get_rest_connection()
    assert factory._shared_client is not None
    await factory.close()
    assert factory._shared_client is None


@pytest.mark.asyncio
async def test_connections_factory_close_without_client():
    """Test closing the factory when no client was created."""
    factory = ConnectionsFactory()
    await factory.close()  # Should not raise
    assert factory._shared_client is None


# --- ConnectionManagersFactory Tests ---


@pytest.fixture
def throttler():
    return AsyncThrottler(
        rate_limits=[RateLimit(limit=100, time_interval=1.0, limit_id="test")]
    )


class ConcreteAuth(Auth):
    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        return request

    async def ws_authenticate(self, request: WebSocketRequest) -> WebSocketRequest:
        return request


def test_connection_managers_factory_init(throttler):
    """Test ConnectionManagersFactory initialization."""
    factory = ConnectionManagersFactory(throttler=throttler)
    assert factory.throttler is throttler
    assert factory.auth is None
    assert factory.time_synchronizer is None


def test_connection_managers_factory_with_all_params(throttler):
    """Test ConnectionManagersFactory with all optional params."""
    auth = ConcreteAuth()
    ts = TimeSynchronizer()

    class TestPreProcessor(RESTPreProcessor):
        async def pre_process(self, request):
            return request

    class TestPostProcessor(RESTPostProcessor):
        async def post_process(self, response):
            return response

    class TestWSPreProcessor(WebSocketPreProcessor):
        async def pre_process(self, request):
            return request

    class TestWSPostProcessor(WebSocketPostProcessor):
        async def post_process(self, response):
            return response

    factory = ConnectionManagersFactory(
        throttler=throttler,
        auth=auth,
        rest_pre_processors=[TestPreProcessor()],
        rest_post_processors=[TestPostProcessor()],
        ws_pre_processors=[TestWSPreProcessor()],
        ws_post_processors=[TestWSPostProcessor()],
        time_synchronizer=ts,
    )

    assert factory.throttler is throttler
    assert factory.auth is auth
    assert factory.time_synchronizer is ts
    assert len(factory._rest_pre_processors) == 1
    assert len(factory._rest_post_processors) == 1
    assert len(factory._ws_pre_processors) == 1
    assert len(factory._ws_post_processors) == 1


@pytest.mark.asyncio
async def test_connection_managers_factory_get_rest_manager(throttler):
    """Test getting a REST manager."""
    factory = ConnectionManagersFactory(throttler=throttler)
    manager = await factory.get_rest_manager()
    assert isinstance(manager, RESTManager)
    await factory.close()


@pytest.mark.asyncio
async def test_connection_managers_factory_get_ws_manager(throttler):
    """Test getting a WebSocket manager."""
    factory = ConnectionManagersFactory(throttler=throttler)
    manager = await factory.get_ws_manager()
    assert isinstance(manager, WebSocketManager)
    await factory.close()


@pytest.mark.asyncio
async def test_connection_managers_factory_update_cookies(throttler):
    """Test updating cookies through the factory."""
    factory = ConnectionManagersFactory(throttler=throttler)
    await factory.update_cookies({"session": "abc123"})
    await factory.close()


@pytest.mark.asyncio
async def test_connection_managers_factory_close(throttler):
    """Test closing the factory."""
    factory = ConnectionManagersFactory(throttler=throttler)
    await factory.get_rest_manager()
    await factory.close()
    assert factory._connections_factory._shared_client is None
