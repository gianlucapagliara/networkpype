"""WebSocket connection module for low-level WebSocket communication.

This module provides a low-level interface for WebSocket communication using the aiohttp
library. It handles the direct communication with WebSocket servers while providing a clean
abstraction over the underlying WebSocket client library.

The module is designed to handle various WebSocket message types (text, binary, ping/pong)
and connection states, providing automatic handling of control messages and connection
lifecycle management.

Classes:
    WebSocketConnection: Low-level WebSocket connection handler.
"""

import logging
import time
from collections.abc import Mapping
from json import JSONDecodeError
from typing import Any

import aiohttp

from networkpype.websocket.request import WebSocketRequest
from networkpype.websocket.response import WebSocketResponse


class WebSocketConnection:
    """Low-level WebSocket connection handler.

    This class provides direct access to WebSocket communication functionality, wrapping
    an aiohttp client session. It handles connection lifecycle, message sending/receiving,
    and automatic handling of WebSocket control frames (ping/pong).

    The connection maintains state about its connectivity and last received message time,
    making it suitable for implementing keep-alive and monitoring functionality.

    Attributes:
        _client_session (aiohttp.ClientSession): The underlying aiohttp client session.
        _connection (aiohttp.ClientWebSocketResponse | None): The active WebSocket connection.
        _connected (bool): Whether the connection is currently established.
        _message_timeout (float | None): Timeout for receiving messages.
        _last_recv_time (float): Timestamp of the last received message.
        _logger (logging.Logger | None): Class-level logger instance.

    Example:
        ```python
        async with aiohttp.ClientSession() as session:
            connection = WebSocketConnection(session)
            await connection.connect("wss://api.example.com/stream")

            # Send a message
            request = WebSocketJSONRequest(payload={"type": "subscribe"})
            await connection.send(request)

            # Receive messages
            while connection.connected:
                if response := await connection.receive():
                    process_message(response.data)
        ```
    """

    _logger = None

    def __init__(self, aiohttp_client_session: aiohttp.ClientSession):
        """Initialize the WebSocketConnection with an aiohttp client session.

        Args:
            aiohttp_client_session (aiohttp.ClientSession): The aiohttp client session
                to use for WebSocket communication.
        """
        self._client_session = aiohttp_client_session
        self._connection: aiohttp.ClientWebSocketResponse | None = None
        self._connected = False
        self._message_timeout: float | None = None
        self._last_recv_time = 0

    @classmethod
    def logger(cls) -> logging.Logger:
        """Get or create a logger instance for the class.

        Returns:
            logging.Logger: The logger instance for this class.
        """
        if cls._logger is None:
            cls._logger = logging.getLogger(__name__)
        return cls._logger

    @property
    def last_recv_time(self) -> float:
        """Get the timestamp of the last received message.

        Returns:
            float: Unix timestamp of the last received message in seconds.
        """
        return self._last_recv_time

    @property
    def connected(self) -> bool:
        """Check if the WebSocket connection is currently established.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._connected

    async def connect(
        self,
        ws_url: str,
        ping_timeout: float = 10,
        auto_ping: bool = False,
        message_timeout: float | None = None,
        ws_headers: dict | None = None,
        verify_ssl: bool = True,
    ):
        """Establish a WebSocket connection.

        Args:
            ws_url (str): The WebSocket URL to connect to.
            ping_timeout (float): Time in seconds to wait for a pong response.
                Defaults to 10.
            auto_ping (bool): Whether to automatically send ping messages.
                Defaults to False.
            message_timeout (float | None): Time in seconds to wait for messages.
                Defaults to None (no timeout).
            ws_headers (dict | None): Additional headers to include in the connection
                request. Defaults to None.
            verify_ssl (bool): Whether to verify SSL certificates. Defaults to True.

        Raises:
            RuntimeError: If already connected.
            aiohttp.ClientError: If there is an error establishing the connection.
        """
        self._ensure_not_connected()
        self._connection = await self._client_session.ws_connect(
            ws_url,
            headers=ws_headers or {},
            autoping=auto_ping,
            heartbeat=ping_timeout,
            verify_ssl=verify_ssl,
        )
        self._message_timeout = message_timeout
        self._connected = True

    async def disconnect(self):
        """Close the WebSocket connection.

        This method will cleanly close the connection if it's open. It is safe to
        call this method multiple times.
        """
        if self._connection is not None and not self._connection.closed:
            await self._connection.close()
        self._connection = None
        self._connected = False

    async def send(self, request: WebSocketRequest):
        """Send a WebSocket message.

        Args:
            request (WebSocketRequest): The message to send.

        Raises:
            RuntimeError: If not connected.
            aiohttp.ClientError: If there is an error sending the message.
        """
        self._ensure_connected()
        await request.send_with_connection(connection=self)

    async def ping(self):
        """Send a WebSocket ping message.

        Raises:
            RuntimeError: If not connected.
            aiohttp.ClientError: If there is an error sending the ping.
        """
        self._ensure_connected()
        if self._connection is None:
            raise RuntimeError("WebSocket connection is not initialized")
        await self._connection.ping()

    async def receive(self) -> WebSocketResponse | None:
        """Receive a WebSocket message.

        This method handles the message receiving pipeline:
        1. Read the raw message
        2. Process control frames (ping/pong/close)
        3. Parse the message content
        4. Build the response object

        Returns:
            WebSocketResponse | None: The received message, or None if the connection
                was closed or a control frame was received.

        Raises:
            RuntimeError: If not connected.
            TimeoutError: If message_timeout is set and no message is received.
            ConnectionError: If the connection is closed unexpectedly.
        """
        self._ensure_connected()
        response = None
        while self._connected:
            msg = await self._read_message()
            if msg is not None:
                msg = await self._process_message(msg)
                if msg is not None:
                    response = self._build_resp(msg)
                    break
        return response

    def _ensure_not_connected(self):
        """Check that the connection is not already established.

        Raises:
            RuntimeError: If already connected.
        """
        if self._connected:
            raise RuntimeError("WebSocket is connected.")

    def _ensure_connected(self):
        """Check that the connection is established.

        Raises:
            RuntimeError: If not connected.
        """
        if not self._connected:
            raise RuntimeError("WebSocket is not connected.")

    async def _read_message(self) -> aiohttp.WSMessage | None:
        """Read a raw message from the WebSocket connection.

        Returns:
            aiohttp.WSMessage | None: The received message, or None if the connection
                is not initialized.

        Raises:
            TimeoutError: If message_timeout is set and no message is received.
            RuntimeError: If the connection is not initialized.
        """
        if self._connection is None:
            raise RuntimeError("WebSocket connection is not initialized")
        try:
            msg = await self._connection.receive(self._message_timeout)
            return msg
        except TimeoutError:
            raise TimeoutError("Message receive timed out.")

    async def _process_message(
        self, msg: aiohttp.WSMessage | None
    ) -> aiohttp.WSMessage | None:
        """Process a raw WebSocket message.

        This method handles control frames and updates the last receive time.

        Args:
            msg (aiohttp.WSMessage | None): The message to process.

        Returns:
            aiohttp.WSMessage | None: The processed message, or None for control frames
                or if the input was None.
        """
        if msg is None:
            return None

        msg = await self._check_msg_types(msg)
        self._update_last_recv_time(msg)
        return msg

    async def _check_msg_types(
        self, msg: aiohttp.WSMessage
    ) -> aiohttp.WSMessage | None:
        """Check and handle different WebSocket message types.

        Args:
            msg (aiohttp.WSMessage): The message to check.

        Returns:
            aiohttp.WSMessage | None: The message if it's a data frame, None otherwise.
        """
        result = await self._check_msg_closed_type(msg)
        if result is None:
            return None

        result = await self._check_msg_ping_type(result)
        if result is None:
            return None

        result = await self._check_msg_pong_type(result)
        return result

    async def _check_msg_closed_type(
        self, msg: aiohttp.WSMessage
    ) -> aiohttp.WSMessage | None:
        """Handle WebSocket close frames.

        Args:
            msg (aiohttp.WSMessage): The message to check.

        Returns:
            aiohttp.WSMessage | None: None if it was a close frame, the message otherwise.

        Raises:
            ConnectionError: If the connection was closed unexpectedly.
        """
        if msg.type in [aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE]:
            if self._connected:
                close_code = self._connection.close_code if self._connection else None
                await self.disconnect()
                raise ConnectionError(
                    f"The WS connection was closed unexpectedly. Close code = {close_code} msg data: {msg.data}"
                )
            return None
        return msg

    async def _check_msg_ping_type(
        self, msg: aiohttp.WSMessage
    ) -> aiohttp.WSMessage | None:
        """Handle WebSocket ping frames.

        Args:
            msg (aiohttp.WSMessage): The message to check.

        Returns:
            aiohttp.WSMessage | None: None if it was a ping frame, the message otherwise.
        """
        if msg.type == aiohttp.WSMsgType.PING:
            if self._connection is not None:
                await self._connection.pong()
            return None
        return msg

    async def _check_msg_pong_type(
        self, msg: aiohttp.WSMessage
    ) -> aiohttp.WSMessage | None:
        """Handle WebSocket pong frames.

        Args:
            msg (aiohttp.WSMessage): The message to check.

        Returns:
            aiohttp.WSMessage | None: None if it was a pong frame, the message otherwise.
        """
        if msg.type == aiohttp.WSMsgType.PONG:
            return None
        return msg

    def _update_last_recv_time(self, _: aiohttp.WSMessage):
        """Update the timestamp of the last received message.

        Args:
            _ (aiohttp.WSMessage): The received message (unused).
        """
        self._last_recv_time = time.time()

    async def _send_json(self, payload: Mapping[str, Any]):
        """Send a JSON message over the WebSocket connection.

        Args:
            payload (Mapping[str, Any]): The JSON data to send.

        Raises:
            RuntimeError: If the connection is not initialized.
            aiohttp.ClientError: If there is an error sending the message.
        """
        if self._connection is None:
            raise RuntimeError("WebSocket connection is not initialized")
        await self._connection.send_json(payload)

    async def _send_plain_text(self, payload: str):
        """Send a text message over the WebSocket connection.

        Args:
            payload (str): The text message to send.

        Raises:
            RuntimeError: If the connection is not initialized.
            aiohttp.ClientError: If there is an error sending the message.
        """
        if self._connection is None:
            raise RuntimeError("WebSocket connection is not initialized")
        await self._connection.send_str(payload)

    @classmethod
    def _build_resp(cls, msg: aiohttp.WSMessage) -> WebSocketResponse:
        """Build a WebSocket response from a raw message.

        This method handles both binary and text messages, attempting to parse
        text messages as JSON when possible.

        Args:
            msg (aiohttp.WSMessage): The raw message to process.

        Returns:
            WebSocketResponse: The processed response.

        Raises:
            Exception: If there is an unexpected error processing the message.
        """
        if msg.type == aiohttp.WSMsgType.BINARY:
            data = msg.data
        else:
            try:
                data = msg.json()
            except JSONDecodeError:
                data = msg.data
            except:
                cls.logger().error(
                    f"Unexpected error while building response for WSMessage({msg.type}, {msg.data}, {msg.extra}).",
                    exc_info=True,
                )
                raise
        response = WebSocketResponse(data)
        return response
