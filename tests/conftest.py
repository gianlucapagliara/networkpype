"""Common test fixtures and configuration for NetworkPype tests.

This module contains shared pytest fixtures that can be used across all test modules.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from aiohttp import ClientSession
from aioresponses import aioresponses

from networkpype.rest.connection import RESTConnection
from networkpype.websocket.connection import WebSocketConnection


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for testing."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    if loop.is_running():
        loop.call_soon(loop.stop)
    pending = asyncio.all_tasks(loop)
    loop.run_until_complete(asyncio.gather(*pending))
    loop.close()


@pytest_asyncio.fixture
async def client_session() -> AsyncGenerator[ClientSession, None]:
    """Create an aiohttp ClientSession for testing."""
    session = ClientSession()
    try:
        yield session
    finally:
        if not session.closed:
            await session.close()


@pytest.fixture
def mock_aioresponse() -> Generator[aioresponses, None, None]:
    """Create a mock aiohttp response."""
    with aioresponses() as m:
        yield m


@pytest.fixture
def base_url() -> str:
    """Return a base URL for testing."""
    return "https://api.example.com"


@pytest.fixture
def api_key() -> str:
    """Return a dummy API key for testing."""
    return "test_api_key_12345"


@pytest_asyncio.fixture
async def connection(
    client_session: ClientSession,
) -> AsyncGenerator[RESTConnection, None]:
    """Create a REST connection for testing."""
    connection = RESTConnection(client_session)
    yield connection


@pytest_asyncio.fixture
async def ws_connection(
    client_session: ClientSession,
) -> AsyncGenerator[WebSocketConnection, None]:
    """Create a WebSocket connection for testing."""
    connection = WebSocketConnection(client_session)
    try:
        yield connection
    finally:
        if connection.connected:
            await connection.disconnect()
