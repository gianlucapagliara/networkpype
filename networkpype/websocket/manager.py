"""WebSocket manager module for handling WebSocket communication.

This module provides a high-level interface for WebSocket communication with support
for authentication, message processing, and connection management. It coordinates
the various components of the WebSocket system, including connection lifecycle,
message processing pipeline, and subscription handling.

The manager is designed to be extensible through processors that can modify messages
before they are sent and after they are received, similar to middleware in web frameworks.

Classes:
    WebSocketManager: High-level manager for WebSocket communication.
"""

from collections.abc import AsyncGenerator
from copy import deepcopy

from networkpype.auth import Auth
from networkpype.websocket.connection import WebSocketConnection
from networkpype.websocket.processor.base import (
    WebSocketPostProcessor,
    WebSocketPreProcessor,
)
from networkpype.websocket.request import WebSocketRequest
from networkpype.websocket.response import WebSocketResponse


class WebSocketManager:
    """High-level manager for WebSocket communication.

    This class coordinates all aspects of WebSocket communication, including connection
    lifecycle, message processing, and authentication. It provides a clean interface
    for establishing WebSocket connections and exchanging messages while handling
    common concerns like authentication and message transformation automatically.

    The manager can be extended with pre-processors and post-processors to modify
    messages before they are sent and after they are received. This allows for
    flexible customization of the message processing pipeline.

    Attributes:
        _connection (WebSocketConnection): The underlying WebSocket connection.
        _ws_pre_processors (list[WebSocketPreProcessor]): Processors to run before sending messages.
        _ws_post_processors (list[WebSocketPostProcessor]): Processors to run after receiving messages.
        _auth (Auth | None): Authentication handler for messages.

    Example:
        ```python
        # Create a manager with authentication and message processors
        manager = WebSocketManager(
            connection=ws_connection,
            auth=APIKeyAuth(api_key="your-key"),
            ws_pre_processors=[MessageValidator()],
            ws_post_processors=[EventHandler()]
        )

        # Connect and subscribe to a data stream
        await manager.connect("wss://api.example.com/stream")
        await manager.subscribe(WebSocketJSONRequest(
            payload={"type": "subscribe", "channel": "market_data"}
        ))

        # Process incoming messages
        async for message in manager.iter_messages():
            if message:
                process_market_data(message.data)
        ```
    """

    def __init__(
        self,
        connection: WebSocketConnection,
        ws_pre_processors: list[WebSocketPreProcessor] | None = None,
        ws_post_processors: list[WebSocketPostProcessor] | None = None,
        auth: Auth | None = None,
    ):
        """Initialize the WebSocketManager with the specified components.

        Args:
            connection (WebSocketConnection): The underlying WebSocket connection to use.
            ws_pre_processors (list[WebSocketPreProcessor] | None): List of processors
                to run before sending messages. Defaults to None.
            ws_post_processors (list[WebSocketPostProcessor] | None): List of processors
                to run after receiving messages. Defaults to None.
            auth (Auth | None): Authentication handler for messages. Defaults to None.
        """
        self._connection = connection
        self._ws_pre_processors = ws_pre_processors or []
        self._ws_post_processors = ws_post_processors or []
        self._auth = auth

    @property
    def last_recv_time(self) -> float:
        """Get the timestamp of the last received message.

        Returns:
            float: Unix timestamp of the last received message in seconds.
        """
        return self._connection.last_recv_time

    async def connect(
        self,
        ws_url: str,
        *,
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
            aiohttp.ClientError: If there is an error establishing the connection.
            asyncio.TimeoutError: If the connection times out.
        """
        await self._connection.connect(
            ws_url=ws_url,
            ws_headers=ws_headers or {},
            ping_timeout=ping_timeout,
            auto_ping=auto_ping,
            message_timeout=message_timeout,
            verify_ssl=verify_ssl,
        )

    async def disconnect(self):
        """Close the WebSocket connection.

        This method will cleanly close the connection and clean up any resources.
        It is safe to call this method multiple times.
        """
        await self._connection.disconnect()

    async def subscribe(self, request: WebSocketRequest):
        """Subscribe to a WebSocket stream.

        This method is a wrapper around send() that will eventually support automatic
        re-subscription on reconnection.

        Args:
            request (WebSocketRequest): The subscription request to send.
        """
        await self.send(request)

    async def send(self, request: WebSocketRequest):
        """Send a WebSocket message.

        This method handles the message sending pipeline:
        1. Pre-process the message
        2. Authenticate if required
        3. Send the message

        Args:
            request (WebSocketRequest): The message to send.

        Raises:
            aiohttp.ClientError: If there is an error sending the message.
        """
        request = deepcopy(request)
        request = await self._pre_process_request(request)
        request = await self._authenticate(request)
        await self._connection.send(request)

    async def ping(self):
        """Send a WebSocket ping message.

        This method can be used to check the connection health or keep it alive.

        Raises:
            aiohttp.ClientError: If there is an error sending the ping.
            asyncio.TimeoutError: If no pong is received within the timeout.
        """
        await self._connection.ping()

    async def iter_messages(self) -> AsyncGenerator[WebSocketResponse | None, None]:
        """Iterate over incoming WebSocket messages.

        This method provides an async iterator for processing incoming messages.
        It will continue yielding messages until the connection is closed.

        Yields:
            WebSocketResponse | None: The next message received, or None if the
                connection was closed while waiting.

        Example:
            ```python
            async for message in manager.iter_messages():
                if message:
                    process_message(message.data)
            ```
        """
        while self._connection.connected:
            response = await self._connection.receive()
            if response is not None:
                response = await self._post_process_response(response)
                yield response

    async def receive(self) -> WebSocketResponse | None:
        """Receive a single WebSocket message.

        This method receives and processes a single message from the WebSocket connection.

        Returns:
            WebSocketResponse | None: The received message, or None if the connection
                was closed while waiting.

        Raises:
            aiohttp.ClientError: If there is an error receiving the message.
        """
        response = await self._connection.receive()
        if response is not None:
            response = await self._post_process_response(response)
        return response

    async def _pre_process_request(self, request: WebSocketRequest) -> WebSocketRequest:
        """Apply all pre-processors to the request.

        Args:
            request (WebSocketRequest): The request to process.

        Returns:
            WebSocketRequest: The processed request.
        """
        for pre_processor in self._ws_pre_processors:
            request = await pre_processor.pre_process(request)
        return request

    async def _authenticate(self, request: WebSocketRequest) -> WebSocketRequest:
        """Authenticate the request if required.

        Args:
            request (WebSocketRequest): The request to authenticate.

        Returns:
            WebSocketRequest: The authenticated request.
        """
        if self._auth is not None and request.is_auth_required:
            request = await self._auth.ws_authenticate(request)
        return request

    async def _post_process_response(
        self, response: WebSocketResponse
    ) -> WebSocketResponse:
        """Apply all post-processors to the response.

        Args:
            response (WebSocketResponse): The response to process.

        Returns:
            WebSocketResponse: The processed response.
        """
        for post_processor in self._ws_post_processors:
            response = await post_processor.post_process(response)
        return response
