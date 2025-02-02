"""Authentication module for REST and WebSocket requests.

This module provides the base authentication class that can be used to implement
various authentication schemes for both REST and WebSocket connections. It supports
time-synchronized authentication methods and can be extended to implement specific
authentication protocols.

Classes:
    Auth: Abstract base class for implementing authentication schemes.
"""

from abc import abstractmethod

from networkpype.rest.request import RESTRequest
from networkpype.time_synchronizer import TimeSynchronizer
from networkpype.websocket.request import WebSocketRequest


class Auth:
    """Abstract base class for authentication objects used by ConnectionManagersFactory.

    This class provides the foundation for implementing various authentication schemes.
    It can be used to authenticate both REST and WebSocket requests, and supports
    time-synchronized authentication methods.

    The class can be extended to implement specific authentication protocols such as:
    - API Key authentication
    - OAuth
    - JWT
    - HMAC signatures
    - Custom authentication schemes

    Attributes:
        time_provider (TimeSynchronizer): Component for handling time synchronization
            in authentication operations.

    Note:
        If the authentication requires a simple REST request to acquire information from the
        server that is required in the message signature, this class can be passed a
        `RESTConnection` object that it can use to that end.
    """

    def __init__(
        self,
        time_provider: TimeSynchronizer | None = None,
    ):
        """Initialize the Auth instance with an optional time synchronizer.

        Args:
            time_provider (TimeSynchronizer | None): Component for handling time
                synchronization. If None, a new TimeSynchronizer instance will be created.
        """
        self.time_provider = time_provider or TimeSynchronizer()

    @abstractmethod
    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """Authenticate a REST request.

        This method should be implemented by subclasses to add authentication
        information to REST requests (e.g., headers, query parameters, etc.).

        Args:
            request (RESTRequest): The REST request to authenticate.

        Returns:
            RESTRequest: The authenticated request with added authentication information.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        ...

    @abstractmethod
    async def ws_authenticate(self, request: WebSocketRequest) -> WebSocketRequest:
        """Authenticate a WebSocket request.

        This method should be implemented by subclasses to add authentication
        information to WebSocket requests (e.g., connection parameters, headers, etc.).

        Args:
            request (WebSocketRequest): The WebSocket request to authenticate.

        Returns:
            WebSocketRequest: The authenticated request with added authentication information.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        ...
