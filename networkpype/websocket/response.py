"""WebSocket response module for handling WebSocket messages.

This module provides a data structure for representing WebSocket responses in a clean
and type-safe manner. It encapsulates the data received from a WebSocket connection,
providing a consistent interface for accessing message content regardless of the
underlying data format.

The module uses Python's dataclass feature to automatically generate appropriate
__init__, __repr__, and __eq__ methods, making the response objects easy to work with.

Classes:
    WebSocketResponse: Data class representing a WebSocket response message.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class WebSocketResponse:
    """Data class representing a WebSocket response message.

    This class encapsulates data received from a WebSocket connection. It provides
    a simple interface for accessing the message content, supporting various data
    types including JSON objects, text messages, and binary data.

    The class is designed to be immutable and type-safe, using Python's dataclass
    features to automatically generate appropriate __init__, __repr__, and __eq__ methods.

    Attributes:
        data (Any): The message content received from the WebSocket connection.
            The type depends on the message format and any processing applied by
            WebSocket post-processors.

    Example:
        ```python
        # JSON message
        response = WebSocketResponse(data={"type": "market_data", "price": 100.0})

        # Text message
        response = WebSocketResponse(data="PONG")

        # Processed market data
        response = WebSocketResponse(data=MarketData(symbol="BTC", price=50000))
        ```
    """

    data: Any
