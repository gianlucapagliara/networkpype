Quickstart Guide
==============

This guide will help you get started with NetworkPype quickly.

Basic Usage
----------

Here's a simple example of how to use NetworkPype for REST API requests:

.. code-block:: python

    from networkpype.factory import NetworkPypeFactory
    from networkpype.rest import RestConnection
    
    # Create a factory instance
    factory = NetworkPypeFactory()
    
    # Configure a REST connection
    connection = factory.create_rest_connection(
        base_url="https://api.example.com",
        rate_limit=100,  # requests per minute
        time_window=60   # seconds
    )
    
    # Make requests
    async def fetch_data():
        response = await connection.get("/endpoint")
        return response.json()

WebSocket Example
---------------

Here's how to use NetworkPype with WebSocket connections:

.. code-block:: python

    from networkpype.factory import NetworkPypeFactory
    from networkpype.websocket import WebSocketConnection
    
    # Create a factory instance
    factory = NetworkPypeFactory()
    
    # Configure a WebSocket connection
    connection = factory.create_websocket_connection(
        url="wss://ws.example.com",
        rate_limit=100,  # messages per minute
        time_window=60   # seconds
    )
    
    # Handle messages
    async def handle_messages():
        async with connection:
            async for message in connection:
                print(f"Received: {message}")

Rate Limiting
------------

NetworkPype includes built-in rate limiting:

.. code-block:: python

    from networkpype.throttler import RateLimit
    
    # Configure rate limiting
    rate_limit = RateLimit(
        max_requests=100,
        time_window=60
    )
    
    # Apply to connection
    connection = factory.create_rest_connection(
        base_url="https://api.example.com",
        rate_limit=rate_limit
    )

Error Handling
-------------

NetworkPype provides comprehensive error handling:

.. code-block:: python

    try:
        async with connection:
            response = await connection.get("/endpoint")
    except ConnectionError as e:
        print(f"Connection failed: {e}")
    except RateLimitExceeded as e:
        print(f"Rate limit exceeded: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

Next Steps
---------

- Check out the :doc:`API Reference </api/index>` for detailed documentation
- See :doc:`Examples </examples/index>` for more complex examples
- Read the :doc:`Contributing Guide </contributing>` to contribute to the project 