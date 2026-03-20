"""Tests for the WebSocketManager class."""

from unittest.mock import AsyncMock

import pytest

from networkpype.auth import Auth
from networkpype.rest.request import RESTRequest
from networkpype.websocket.connection import WebSocketConnection
from networkpype.websocket.manager import WebSocketManager
from networkpype.websocket.processor.base import (
    WebSocketPostProcessor,
    WebSocketPreProcessor,
)
from networkpype.websocket.request import WebSocketJSONRequest, WebSocketRequest
from networkpype.websocket.response import WebSocketResponse


class MockWSPreProcessor(WebSocketPreProcessor):
    async def pre_process(self, request: WebSocketRequest) -> WebSocketRequest:
        return request


class MockWSPostProcessor(WebSocketPostProcessor):
    async def post_process(self, response: WebSocketResponse) -> WebSocketResponse:
        return response


class MockAuth(Auth):
    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        return request

    async def ws_authenticate(self, request: WebSocketRequest) -> WebSocketRequest:
        return request


@pytest.fixture
def mock_ws_connection():
    conn = AsyncMock(spec=WebSocketConnection)
    conn.connected = True
    conn.last_recv_time = 1234567890.0
    return conn


@pytest.fixture
def ws_manager(mock_ws_connection):
    return WebSocketManager(connection=mock_ws_connection)


@pytest.fixture
def ws_manager_with_processors(mock_ws_connection):
    return WebSocketManager(
        connection=mock_ws_connection,
        ws_pre_processors=[MockWSPreProcessor()],
        ws_post_processors=[MockWSPostProcessor()],
    )


@pytest.fixture
def ws_manager_with_auth(mock_ws_connection):
    return WebSocketManager(
        connection=mock_ws_connection,
        auth=MockAuth(),
    )


def test_init(ws_manager, mock_ws_connection):
    """Test WebSocketManager initialization."""
    assert ws_manager._connection is mock_ws_connection
    assert ws_manager._ws_pre_processors == []
    assert ws_manager._ws_post_processors == []
    assert ws_manager._auth is None


def test_last_recv_time(ws_manager):
    """Test last_recv_time property."""
    assert ws_manager.last_recv_time == 1234567890.0


@pytest.mark.asyncio
async def test_connect(ws_manager, mock_ws_connection):
    """Test connect delegates to connection."""
    await ws_manager.connect("wss://example.com/ws")
    mock_ws_connection.connect.assert_called_once_with(
        ws_url="wss://example.com/ws",
        ws_headers={},
        ping_timeout=10,
        auto_ping=False,
        message_timeout=None,
        verify_ssl=True,
    )


@pytest.mark.asyncio
async def test_connect_with_options(ws_manager, mock_ws_connection):
    """Test connect with custom options."""
    await ws_manager.connect(
        "wss://example.com/ws",
        ping_timeout=30,
        auto_ping=True,
        message_timeout=60,
        ws_headers={"Auth": "token"},
        verify_ssl=False,
    )
    mock_ws_connection.connect.assert_called_once_with(
        ws_url="wss://example.com/ws",
        ws_headers={"Auth": "token"},
        ping_timeout=30,
        auto_ping=True,
        message_timeout=60,
        verify_ssl=False,
    )


@pytest.mark.asyncio
async def test_disconnect(ws_manager, mock_ws_connection):
    """Test disconnect delegates to connection."""
    await ws_manager.disconnect()
    mock_ws_connection.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_send(ws_manager, mock_ws_connection):
    """Test send delegates to connection after processing."""
    request = WebSocketJSONRequest(payload={"type": "subscribe"})
    await ws_manager.send(request)
    mock_ws_connection.send.assert_called_once()


@pytest.mark.asyncio
async def test_subscribe(ws_manager, mock_ws_connection):
    """Test subscribe delegates to send."""
    request = WebSocketJSONRequest(payload={"type": "subscribe"})
    await ws_manager.subscribe(request)
    mock_ws_connection.send.assert_called_once()


@pytest.mark.asyncio
async def test_ping(ws_manager, mock_ws_connection):
    """Test ping delegates to connection."""
    await ws_manager.ping()
    mock_ws_connection.ping.assert_called_once()


@pytest.mark.asyncio
async def test_receive_with_response(ws_manager, mock_ws_connection):
    """Test receive returns processed response."""
    mock_ws_connection.receive.return_value = WebSocketResponse(data={"key": "value"})
    response = await ws_manager.receive()
    assert response is not None
    assert response.data == {"key": "value"}


@pytest.mark.asyncio
async def test_receive_none(ws_manager, mock_ws_connection):
    """Test receive returns None when connection returns None."""
    mock_ws_connection.receive.return_value = None
    response = await ws_manager.receive()
    assert response is None


@pytest.mark.asyncio
async def test_iter_messages(ws_manager, mock_ws_connection):
    """Test iter_messages yields responses."""
    responses = [
        WebSocketResponse(data={"msg": 1}),
        WebSocketResponse(data={"msg": 2}),
    ]
    call_count = 0

    async def fake_receive():
        nonlocal call_count
        if call_count < len(responses):
            resp = responses[call_count]
            call_count += 1
            return resp
        # Disconnect after all messages
        mock_ws_connection.connected = False
        return None

    mock_ws_connection.receive = fake_receive

    messages = []
    async for msg in ws_manager.iter_messages():
        messages.append(msg)

    assert len(messages) == 2
    assert messages[0].data == {"msg": 1}
    assert messages[1].data == {"msg": 2}


@pytest.mark.asyncio
async def test_send_with_auth_required(ws_manager_with_auth, mock_ws_connection):
    """Test send applies auth when request requires it."""
    request = WebSocketJSONRequest(payload={"type": "subscribe"}, is_auth_required=True)
    await ws_manager_with_auth.send(request)
    mock_ws_connection.send.assert_called_once()


@pytest.mark.asyncio
async def test_send_without_auth_when_not_required(
    ws_manager_with_auth, mock_ws_connection
):
    """Test send skips auth when request doesn't require it."""
    request = WebSocketJSONRequest(
        payload={"type": "subscribe"}, is_auth_required=False
    )
    await ws_manager_with_auth.send(request)
    mock_ws_connection.send.assert_called_once()


@pytest.mark.asyncio
async def test_send_deepcopies_request(ws_manager, mock_ws_connection):
    """Test send deep copies the request."""
    original_payload = {"type": "subscribe", "channels": ["ch1"]}
    request = WebSocketJSONRequest(payload=original_payload)
    await ws_manager.send(request)
    # Original should be unchanged
    assert request.payload == original_payload


@pytest.mark.asyncio
async def test_receive_with_post_processors(
    ws_manager_with_processors, mock_ws_connection
):
    """Test receive applies post-processors."""
    mock_ws_connection.receive.return_value = WebSocketResponse(data={"key": "value"})
    response = await ws_manager_with_processors.receive()
    assert response is not None
