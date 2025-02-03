"""Tests for the WebSocket connection class."""

import json
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from aiohttp import ClientSession, WSMessage, WSMsgType
from aiohttp.client_ws import ClientWebSocketResponse

from networkpype.websocket.connection import WebSocketConnection
from networkpype.websocket.request import (
    WebSocketJSONRequest,
    WebSocketPlainTextRequest,
)


@pytest_asyncio.fixture
async def client_session() -> AsyncGenerator[ClientSession, None]:
    """Fixture providing an aiohttp client session."""
    session = ClientSession()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture
def mock_ws_response() -> Mock:
    """Create a mock WebSocket response."""
    mock = Mock(spec=ClientWebSocketResponse)
    mock._closed = False
    mock.close = AsyncMock()
    mock.ping = AsyncMock()
    mock.send_json = AsyncMock()
    mock.send_str = AsyncMock()
    mock.receive = AsyncMock()

    # Add proper closed property behavior
    def get_closed(self):
        return self._closed

    def close_mock():
        mock._closed = True
        return AsyncMock()()

    mock.close.side_effect = close_mock
    type(mock).closed = property(get_closed)

    return mock


@pytest_asyncio.fixture
async def ws_connection_with_mock(
    client_session: ClientSession, mock_ws_response: Mock
) -> AsyncGenerator[WebSocketConnection, None]:
    """Create a WebSocket connection with a mock response."""
    connection = WebSocketConnection(client_session)
    patcher = patch.object(
        client_session, "ws_connect", AsyncMock(return_value=mock_ws_response)
    )
    patcher.start()
    try:
        await connection.connect("wss://api.example.com/ws")
        yield connection
    finally:
        if connection.connected:
            await connection.disconnect()
        patcher.stop()


@pytest.mark.asyncio
async def test_connection_lifecycle(
    client_session: ClientSession, mock_ws_response: Mock
) -> None:
    """Test WebSocket connection lifecycle (connect/disconnect)."""
    connection = WebSocketConnection(client_session)
    assert not connection.connected

    # Test connect
    with patch.object(
        client_session, "ws_connect", AsyncMock(return_value=mock_ws_response)
    ):
        await connection.connect("wss://api.example.com/ws")
        assert connection.connected
        assert not mock_ws_response.closed

        # Test disconnect
        await connection.disconnect()
        assert not connection.connected
        assert mock_ws_response.close.called


@pytest.mark.asyncio
async def test_connection_send_json(
    ws_connection_with_mock: WebSocketConnection, mock_ws_response: Mock
) -> None:
    """Test sending JSON messages through WebSocket."""
    payload = {"type": "subscribe", "channel": "market_data"}
    request = WebSocketJSONRequest(payload=payload)

    await ws_connection_with_mock.send(request)
    mock_ws_response.send_json.assert_called_once_with(payload)


@pytest.mark.asyncio
async def test_connection_send_text(
    ws_connection_with_mock: WebSocketConnection, mock_ws_response: Mock
) -> None:
    """Test sending text messages through WebSocket."""
    payload = "PING"
    request = WebSocketPlainTextRequest(payload=payload)

    await ws_connection_with_mock.send(request)
    mock_ws_response.send_str.assert_called_once_with(payload)


@pytest.mark.asyncio
async def test_connection_ping(
    ws_connection_with_mock: WebSocketConnection, mock_ws_response: Mock
) -> None:
    """Test sending ping messages."""
    await ws_connection_with_mock.ping()
    mock_ws_response.ping.assert_called_once()


@pytest.mark.asyncio
async def test_connection_receive_json(
    ws_connection_with_mock: WebSocketConnection, mock_ws_response: Mock
) -> None:
    """Test receiving JSON messages."""
    data = {"type": "market_data", "price": 100.0}
    mock_ws_response.receive.return_value = WSMessage(
        type=WSMsgType.TEXT,
        data=json.dumps(data),
        extra=None,
    )

    response = await ws_connection_with_mock.receive()
    assert response is not None
    assert isinstance(response.data, dict)
    assert response.data == data


@pytest.mark.asyncio
async def test_connection_receive_text(
    ws_connection_with_mock: WebSocketConnection, mock_ws_response: Mock
) -> None:
    """Test receiving text messages."""
    data = "PONG"
    mock_ws_response.receive.return_value = WSMessage(
        type=WSMsgType.TEXT,
        data=data,
        extra=None,
    )

    response = await ws_connection_with_mock.receive()
    assert response is not None
    assert isinstance(response.data, str)
    assert response.data == data


@pytest.mark.asyncio
async def test_connection_receive_close(
    ws_connection_with_mock: WebSocketConnection, mock_ws_response: Mock
) -> None:
    """Test receiving close messages."""
    mock_ws_response.receive.return_value = WSMessage(
        type=WSMsgType.CLOSE,
        data=None,
        extra=None,
    )

    # Close messages should raise a ConnectionError
    with pytest.raises(ConnectionError):
        await ws_connection_with_mock.receive()
    assert not ws_connection_with_mock.connected


@pytest.mark.asyncio
async def test_connection_receive_timeout(
    ws_connection_with_mock: WebSocketConnection, mock_ws_response: Mock
) -> None:
    """Test message receive timeout."""
    mock_ws_response.receive.side_effect = TimeoutError()

    with pytest.raises(TimeoutError, match="Message receive timed out."):
        await ws_connection_with_mock.receive()


@pytest.mark.asyncio
async def test_connection_invalid_json(
    ws_connection_with_mock: WebSocketConnection, mock_ws_response: Mock
) -> None:
    """Test handling of invalid JSON messages."""
    mock_ws_response.receive.return_value = WSMessage(
        type=WSMsgType.TEXT,
        data="invalid json",
        extra=None,
    )

    response = await ws_connection_with_mock.receive()
    assert response is not None
    assert isinstance(response.data, str)
    assert response.data == "invalid json"
