"""Network communication factory module for REST and WebSocket connections.

This module provides factory classes for creating and managing network connections,
both for REST and WebSocket protocols. It abstracts the underlying network library
(aiohttp) and provides a clean interface for connection management.

Classes:
    ConnectionsFactory: Creates and manages low-level network connections.
    ConnectionManagersFactory: Creates and manages high-level connection managers with additional features.
"""

import aiohttp

from networkpype.auth import Auth
from networkpype.rest.connection import RESTConnection
from networkpype.rest.manager import RESTManager
from networkpype.rest.processor.base import RESTPostProcessor, RESTPreProcessor
from networkpype.throttler.throttler import AsyncThrottler
from networkpype.time_synchronizer import TimeSynchronizer
from networkpype.websocket.connection import WebSocketConnection
from networkpype.websocket.manager import WebSocketManager
from networkpype.websocket.processor.base import (
    WebSocketPostProcessor,
    WebSocketPreProcessor,
)


class ConnectionsFactory:
    """Factory class for creating and managing network connections.

    This class is a thin wrapper around the underlying REST and WebSocket third-party library.
    It isolates the general `connection_manager` infrastructure from the underlying library
    (in this case, `aiohttp`) to enable dependency change with minimal refactoring of the code.

    Attributes:
        _shared_client (aiohttp.ClientSession | None): Shared HTTP client session for all connections.
    """

    def __init__(self):
        """Initialize the ConnectionsFactory with no active client session."""
        self._shared_client: aiohttp.ClientSession | None = None

    async def get_rest_connection(self) -> RESTConnection:
        """Create or retrieve a REST connection using the shared client session.

        Returns:
            RESTConnection: A connection object for making REST API calls.
        """
        shared_client = await self._get_shared_client()
        connection = RESTConnection(aiohttp_client_session=shared_client)
        return connection

    async def get_ws_connection(self, **kwargs) -> WebSocketConnection:
        """Create or retrieve a WebSocket connection using the shared client session.

        Args:
            **kwargs: Additional arguments to pass to the client session.

        Returns:
            WebSocketConnection: A connection object for WebSocket communication.
        """
        shared_client = await self._get_shared_client(**kwargs)
        connection = WebSocketConnection(aiohttp_client_session=shared_client)
        return connection

    async def _get_shared_client(self, **kwargs) -> aiohttp.ClientSession:
        """Get or create a shared aiohttp client session.

        Args:
            **kwargs: Additional arguments to pass to ClientSession constructor.

        Returns:
            aiohttp.ClientSession: The shared client session.
        """
        self._shared_client = self._shared_client or aiohttp.ClientSession(**kwargs)
        return self._shared_client

    async def update_cookies(self, cookies):
        """Update the cookies in the shared client session.

        Args:
            cookies: Cookie data to update in the session.
        """
        shared_client = await self._get_shared_client()
        shared_client.cookie_jar.update_cookies(cookies)

    async def close(self):
        """Close the shared client session and clean up resources."""
        if self._shared_client:
            await self._shared_client.close()
            self._shared_client = None


class ConnectionManagersFactory:
    """Factory class for creating and managing high-level connection managers.

    This class creates connection managers that handle authentication, rate limiting,
    request/response processing, and time synchronization for both REST and WebSocket
    connections.

    Attributes:
        _connections_factory (ConnectionsFactory): Factory for creating base connections.
        _rest_pre_processors (list[RESTPreProcessor]): Processors to run before REST requests.
        _rest_post_processors (list[RESTPostProcessor]): Processors to run after REST responses.
        _ws_pre_processors (list[WebSocketPreProcessor]): Processors to run before WS messages.
        _ws_post_processors (list[WebSocketPostProcessor]): Processors to run after WS messages.
        _auth (Auth | None): Authentication handler.
        _throttler (AsyncThrottler): Rate limiting handler.
        _time_synchronizer (TimeSynchronizer | None): Time synchronization handler.
    """

    def __init__(
        self,
        throttler: AsyncThrottler,
        auth: Auth | None = None,
        rest_pre_processors: list[RESTPreProcessor] | None = None,
        rest_post_processors: list[RESTPostProcessor] | None = None,
        ws_pre_processors: list[WebSocketPreProcessor] | None = None,
        ws_post_processors: list[WebSocketPostProcessor] | None = None,
        time_synchronizer: TimeSynchronizer | None = None,
    ):
        """Initialize the ConnectionManagersFactory with the specified components.

        Args:
            throttler (AsyncThrottler): Rate limiting component for API requests.
            auth (Auth | None): Authentication handler for requests. Defaults to None.
            rest_pre_processors (list[RESTPreProcessor] | None): List of processors to run before REST requests.
                Defaults to None.
            rest_post_processors (list[RESTPostProcessor] | None): List of processors to run after REST responses.
                Defaults to None.
            ws_pre_processors (list[WebSocketPreProcessor] | None): List of processors to run before WebSocket messages.
                Defaults to None.
            ws_post_processors (list[WebSocketPostProcessor] | None): List of processors to run after WebSocket messages.
                Defaults to None.
            time_synchronizer (TimeSynchronizer | None): Component for handling time synchronization.
                Defaults to None.
        """
        self._connections_factory = ConnectionsFactory()
        self._rest_pre_processors = rest_pre_processors or []
        self._rest_post_processors = rest_post_processors or []
        self._ws_pre_processors = ws_pre_processors or []
        self._ws_post_processors = ws_post_processors or []
        self._auth = auth
        self._throttler = throttler
        self._time_synchronizer = time_synchronizer

    @property
    def throttler(self) -> AsyncThrottler:
        """Get the rate limiting throttler.

        Returns:
            AsyncThrottler: The throttler instance used for rate limiting.
        """
        return self._throttler

    @property
    def time_synchronizer(self) -> TimeSynchronizer | None:
        """Get the time synchronization component.

        Returns:
            TimeSynchronizer | None: The time synchronizer instance if configured, None otherwise.
        """
        return self._time_synchronizer

    @property
    def auth(self) -> Auth | None:
        """Get the authentication handler.

        Returns:
            Auth | None: The authentication instance if configured, None otherwise.
        """
        return self._auth

    async def get_rest_manager(self) -> RESTManager:
        """Create a new REST connection manager with all configured components.

        Returns:
            RESTManager: A fully configured REST connection manager with authentication,
                rate limiting, and request/response processing capabilities.
        """
        connection = await self._connections_factory.get_rest_connection()
        assistant = RESTManager(
            connection=connection,
            throttler=self._throttler,
            rest_pre_processors=self._rest_pre_processors,
            rest_post_processors=self._rest_post_processors,
            auth=self._auth,
        )
        return assistant

    async def get_ws_manager(self, **kwargs) -> WebSocketManager:
        """Create a new WebSocket connection manager with all configured components.

        Args:
            **kwargs: Additional arguments to pass to the WebSocket connection.

        Returns:
            WebSocketManager: A fully configured WebSocket connection manager with
                authentication and message processing capabilities.
        """
        connection = await self._connections_factory.get_ws_connection(**kwargs)
        assistant = WebSocketManager(
            connection, self._ws_pre_processors, self._ws_post_processors, self._auth
        )
        return assistant

    async def update_cookies(self, cookies):
        """Update the cookies in the shared client session.

        Args:
            cookies: Cookie data to update in the session.
        """
        await self._connections_factory.update_cookies(cookies)

    async def close(self):
        """Close all connections and clean up resources."""
        await self._connections_factory.close()
