"""Tests for WebSocket request and response classes."""

from typing import Any, Protocol
from unittest.mock import AsyncMock

import pytest

from networkpype.websocket.request import (
    WebSocketJSONRequest,
    WebSocketPlainTextRequest,
)
from networkpype.websocket.response import WebSocketResponse


class WebSocketConnectionProtocol(Protocol):
    """Protocol defining the WebSocket connection interface for testing."""

    async def _send_json(self, payload: dict[str, Any]) -> None:
        """Send JSON data through the WebSocket connection."""
        ...

    async def _send_plain_text(self, payload: str) -> None:
        """Send plain text through the WebSocket connection."""
        ...


class MockWebSocketConnection:
    """Mock WebSocket connection for testing."""

    def __init__(self):
        """Initialize with mock send methods."""
        self._send_json = AsyncMock()
        self._send_plain_text = AsyncMock()


def test_websocket_json_request_creation() -> None:
    """Test creation of WebSocketJSONRequest with various configurations."""
    # Test minimal request
    request = WebSocketJSONRequest(payload={"type": "test"})
    assert request.payload == {"type": "test"}
    assert request.throttler_limit_id is None
    assert not request.is_auth_required

    # Test full request
    request = WebSocketJSONRequest(
        payload={"type": "subscribe", "channel": "market_data"},
        throttler_limit_id="ws_limit",
        is_auth_required=True,
    )
    assert request.payload == {"type": "subscribe", "channel": "market_data"}
    assert request.throttler_limit_id == "ws_limit"
    assert request.is_auth_required


def test_websocket_plain_text_request_creation() -> None:
    """Test creation of WebSocketPlainTextRequest with various configurations."""
    # Test minimal request
    request = WebSocketPlainTextRequest(payload="PING")
    assert request.payload == "PING"
    assert request.throttler_limit_id is None
    assert not request.is_auth_required

    # Test full request
    request = WebSocketPlainTextRequest(
        payload="SUBSCRIBE:channel",
        throttler_limit_id="ws_limit",
        is_auth_required=True,
    )
    assert request.payload == "SUBSCRIBE:channel"
    assert request.throttler_limit_id == "ws_limit"
    assert request.is_auth_required


@pytest.mark.asyncio
async def test_websocket_json_request_send() -> None:
    """Test sending JSON request through WebSocket connection."""
    connection = MockWebSocketConnection()
    payload = {"type": "subscribe", "channel": "market_data"}
    request = WebSocketJSONRequest(payload=payload)

    # Type cast the mock to the protocol to satisfy type checker
    await request.send_with_connection(connection)  # type: ignore
    connection._send_json.assert_called_once_with(payload=payload)


@pytest.mark.asyncio
async def test_websocket_plain_text_request_send() -> None:
    """Test sending plain text request through WebSocket connection."""
    connection = MockWebSocketConnection()
    payload = "PING"
    request = WebSocketPlainTextRequest(payload=payload)

    # Type cast the mock to the protocol to satisfy type checker
    await request.send_with_connection(connection)  # type: ignore
    connection._send_plain_text.assert_called_once_with(payload=payload)


def test_websocket_response_creation() -> None:
    """Test creation of WebSocketResponse with various data types."""
    # Test with JSON data
    json_data = {"type": "market_data", "price": 100.0}
    response = WebSocketResponse(data=json_data)
    assert response.data == json_data

    # Test with text data
    text_data = "PONG"
    response = WebSocketResponse(data=text_data)
    assert response.data == text_data

    # Test with custom object
    class MarketData:
        def __init__(self, symbol: str, price: float):
            self.symbol = symbol
            self.price = price

    market_data = MarketData("BTC", 50000)
    response = WebSocketResponse(data=market_data)
    assert response.data == market_data
    assert response.data.symbol == "BTC"
    assert response.data.price == 50000
