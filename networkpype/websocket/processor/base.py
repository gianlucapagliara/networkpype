"""WebSocket request and response processor interfaces.

This module defines the base abstract classes for processing WebSocket requests and responses.
These processors can be used to inject custom functionality into the WebSocket communication
pipeline, such as authentication, message transformation, logging, or real-time data processing.

The processors are designed to be composable, allowing multiple processors to be chained
together in a specific order to handle different aspects of the WebSocket message cycle.

Classes:
    WebSocketPreProcessor: Abstract base class for processing WebSocket requests.
    WebSocketPostProcessor: Abstract base class for processing WebSocket responses.
"""

import abc

from networkpype.websocket.request import WebSocketRequest
from networkpype.websocket.response import WebSocketResponse


class WebSocketPreProcessor(abc.ABC):
    """Abstract base class for processing WebSocket requests.

    This interface enables functionality injection into the `WebSocketManager` for request
    processing. Implementations of this class can modify or transform WebSocket messages
    before they are sent to the server.

    Use cases include:
    - Message format validation
    - Authentication token injection
    - Message payload transformation
    - Protocol-specific formatting
    - Message logging
    - Rate limiting
    - Connection state management

    Example:
        ```python
        class MessageFormatProcessor(WebSocketPreProcessor):
            async def pre_process(self, request: WebSocketRequest) -> WebSocketRequest:
                # Format message according to protocol requirements
                request.payload = self.format_message(request.payload)
                return request
        ```
    """

    @abc.abstractmethod
    async def pre_process(self, request: WebSocketRequest) -> WebSocketRequest:
        """Process a WebSocket request before it is sent to the server.

        This method is called before sending a message to the WebSocket server.
        It can be used to modify, validate, or transform the message data.

        Args:
            request (WebSocketRequest): The WebSocket request to be sent to the server.

        Returns:
            WebSocketRequest: The processed request.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        ...


class WebSocketPostProcessor(abc.ABC):
    """Abstract base class for processing WebSocket responses.

    This interface enables functionality injection into the `WebSocketManager` for response
    processing. Implementations of this class can modify or transform WebSocket messages
    received from the server before they are passed to the application.

    Use cases include:
    - Message deserialization
    - Error handling and recovery
    - Response validation
    - Real-time data processing
    - Event aggregation
    - Message filtering
    - State tracking

    Example:
        ```python
        class DataStreamProcessor(WebSocketPostProcessor):
            async def post_process(self, response: WebSocketResponse) -> WebSocketResponse:
                # Process real-time data stream
                if response.type == 'market_data':
                    response.data = self.process_market_data(response.data)
                return response
        ```
    """

    @abc.abstractmethod
    async def post_process(self, response: WebSocketResponse) -> WebSocketResponse:
        """Process a WebSocket response before it is returned to the caller.

        This method is called after receiving a message from the WebSocket server but
        before returning it to the application. It can be used to modify, validate,
        or transform the message data.

        Args:
            response (WebSocketResponse): The response received from the server.

        Returns:
            WebSocketResponse: The processed response.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        ...
