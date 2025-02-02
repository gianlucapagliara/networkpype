"""WebSocket request module for handling WebSocket messages.

This module provides data structures for representing WebSocket requests in a clean
and type-safe manner. It supports different types of WebSocket messages, including
JSON and plain text formats, with a common interface for sending messages through
a WebSocket connection.

The module uses abstract base classes and dataclasses to ensure type safety and
provide a consistent interface across different message types.

Classes:
    WebSocketRequest: Abstract base class for all WebSocket requests.
    WebSocketJSONRequest: Concrete class for JSON-formatted WebSocket messages.
    WebSocketPlainTextRequest: Concrete class for plain text WebSocket messages.
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from networkpype.websocket.connection import WebSocketConnection


@dataclass
class WebSocketRequest(ABC):
    """Abstract base class for all WebSocket requests.

    This class defines the common interface and attributes for all WebSocket requests.
    It provides a foundation for implementing different types of WebSocket messages
    while ensuring consistent handling of authentication and rate limiting.

    Attributes:
        payload (Any): The message payload to be sent. The exact type depends on the
            concrete implementation.
        throttler_limit_id (str | None): Identifier for rate limiting purposes. If provided,
            this request will be counted against the specified rate limit. Defaults to None.
        is_auth_required (bool): Whether the request requires authentication. If True,
            authentication will be added by the appropriate processor. Defaults to False.
    """

    payload: Any
    throttler_limit_id: str | None = None
    is_auth_required: bool = False

    @abstractmethod
    async def send_with_connection(self, connection: "WebSocketConnection"):
        """Send the request through a WebSocket connection.

        This abstract method must be implemented by concrete subclasses to define
        how the message should be sent through the connection.

        Args:
            connection (WebSocketConnection): The WebSocket connection to use for sending
                the message.

        Returns:
            NotImplemented: This is an abstract method.
        """
        return NotImplemented


@dataclass
class WebSocketJSONRequest(WebSocketRequest):
    """WebSocket request for sending JSON-formatted messages.

    This class represents a WebSocket request that sends JSON-formatted data. It ensures
    that the payload is a valid mapping that can be serialized to JSON.

    Attributes:
        payload (Mapping[str, Any]): The JSON message payload to be sent. Must be a
            mapping that can be serialized to JSON.
        throttler_limit_id (str | None): Identifier for rate limiting purposes.
            Defaults to None.
        is_auth_required (bool): Whether the request requires authentication.
            Defaults to False.

    Example:
        ```python
        request = WebSocketJSONRequest(
            payload={"type": "subscribe", "channel": "market_data"},
            is_auth_required=True
        )
        await request.send_with_connection(ws_connection)
        ```
    """

    payload: Mapping[str, Any]
    throttler_limit_id: str | None = None
    is_auth_required: bool = False

    async def send_with_connection(self, connection: "WebSocketConnection"):
        """Send the JSON message through a WebSocket connection.

        Args:
            connection (WebSocketConnection): The WebSocket connection to use for sending
                the JSON message.
        """
        await connection._send_json(payload=self.payload)


@dataclass
class WebSocketPlainTextRequest(WebSocketRequest):
    """WebSocket request for sending plain text messages.

    This class represents a WebSocket request that sends plain text data. It ensures
    that the payload is a string.

    Attributes:
        payload (str): The text message to be sent.
        throttler_limit_id (str | None): Identifier for rate limiting purposes.
            Defaults to None.
        is_auth_required (bool): Whether the request requires authentication.
            Defaults to False.

    Example:
        ```python
        request = WebSocketPlainTextRequest(
            payload="PING",
            is_auth_required=False
        )
        await request.send_with_connection(ws_connection)
        ```
    """

    payload: str
    throttler_limit_id: str | None = None
    is_auth_required: bool = False

    async def send_with_connection(self, connection: "WebSocketConnection"):
        """Send the text message through a WebSocket connection.

        Args:
            connection (WebSocketConnection): The WebSocket connection to use for sending
                the text message.
        """
        await connection._send_plain_text(payload=self.payload)
