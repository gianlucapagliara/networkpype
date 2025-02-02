"""WebSocket client implementation for NetworkPype.

This module provides a complete solution for WebSocket communication with features
like message processing, connection management, and automatic reconnection. It
uses aiohttp for making asynchronous WebSocket connections and supports
customization through processors.

Key Components:
    WebSocketManager: High-level interface for WebSocket communication.
    WebSocketConnection: Low-level WebSocket connection handler.
    WebSocketPreProcessor: Base class for message pre-processors.
    WebSocketPostProcessor: Base class for message post-processors.

Features:
    - Automatic connection management
    - Message pre/post-processing
    - Subscription management
    - Ping/pong handling
    - Automatic reconnection
    - Error handling and logging

Example:
    ```python
    from networkpype.websocket import WebSocketManager, WebSocketConnection
    from networkpype.websocket.processor import JSONProcessor

    # Create a WebSocket client with JSON processing
    connection = WebSocketConnection()
    manager = WebSocketManager(
        connection=connection,
        post_processors=[JSONProcessor()]
    )

    # Connect and send/receive messages
    async with manager.connect("wss://api.example.com/ws"):
        # Subscribe to a channel
        await manager.subscribe("market_data")

        # Send a message
        await manager.send({
            "type": "request",
            "data": {"symbol": "BTC-USD"}
        })

        # Receive messages
        async for message in manager.iter_messages():
            print(f"Received: {message.data}")  # Parsed JSON data
    ```

For more examples and details about processors, see the processor submodule.
"""
