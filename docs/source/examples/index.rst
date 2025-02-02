Examples
========

This section provides detailed examples of how to use NetworkPype in various scenarios.

Basic Examples
-------------

REST API Example
~~~~~~~~~~~~~~

Here's a complete example of using NetworkPype with a REST API:

.. code-block:: python

    import asyncio
    from networkpype.factory import NetworkPypeFactory
    from networkpype.rest import RestConnection
    from networkpype.throttler import RateLimit

    async def main():
        # Create factory
        factory = NetworkPypeFactory()
        
        # Configure rate limiting
        rate_limit = RateLimit(
            max_requests=100,
            time_window=60
        )
        
        # Create connection
        connection = factory.create_rest_connection(
            base_url="https://api.example.com",
            rate_limit=rate_limit
        )
        
        # Use the connection
        async with connection:
            # GET request
            response = await connection.get("/users")
            users = response.json()
            
            # POST request
            new_user = {"name": "John Doe", "email": "john@example.com"}
            response = await connection.post("/users", json=new_user)
            
            # PUT request
            updated_user = {"name": "John Smith"}
            response = await connection.put("/users/1", json=updated_user)
            
            # DELETE request
            response = await connection.delete("/users/1")

    if __name__ == "__main__":
        asyncio.run(main())

WebSocket Example
~~~~~~~~~~~~~~~

Example of using NetworkPype with WebSocket connections:

.. code-block:: python

    import asyncio
    from networkpype.factory import NetworkPypeFactory
    from networkpype.websocket import WebSocketConnection
    from networkpype.throttler import RateLimit

    async def main():
        factory = NetworkPypeFactory()
        
        # Configure rate limiting
        rate_limit = RateLimit(
            max_requests=100,
            time_window=60
        )
        
        # Create connection
        connection = factory.create_websocket_connection(
            url="wss://ws.example.com",
            rate_limit=rate_limit
        )
        
        async def message_handler(message):
            print(f"Received: {message}")
            
            # Process message and send response
            response = {"status": "received"}
            await connection.send(response)
        
        # Use the connection
        async with connection:
            connection.on_message(message_handler)
            
            # Keep connection alive
            while True:
                await asyncio.sleep(1)

    if __name__ == "__main__":
        asyncio.run(main())

Advanced Examples
---------------

Time Synchronization
~~~~~~~~~~~~~~~~~~

Example of using time synchronization with REST requests:

.. code-block:: python

    from networkpype.factory import NetworkPypeFactory
    from networkpype.rest import RestConnection
    from networkpype.time_synchronizer import TimeSynchronizer

    async def main():
        factory = NetworkPypeFactory()
        
        # Create time synchronizer
        time_sync = TimeSynchronizer()
        
        # Create connection with time synchronization
        connection = factory.create_rest_connection(
            base_url="https://api.example.com",
            time_synchronizer=time_sync
        )
        
        async with connection:
            # This request will be time-synchronized
            response = await connection.get("/time-sensitive-endpoint")

Custom Rate Limiting
~~~~~~~~~~~~~~~~~~

Example of implementing custom rate limiting:

.. code-block:: python

    from networkpype.factory import NetworkPypeFactory
    from networkpype.throttler import RateLimit, Context

    class CustomRateLimit(RateLimit):
        def __init__(self, max_requests: int, time_window: int):
            super().__init__(max_requests, time_window)
        
        async def acquire(self, context: Context) -> bool:
            # Custom rate limiting logic
            if context.priority == "high":
                return True
            return await super().acquire(context)

    async def main():
        factory = NetworkPypeFactory()
        
        # Use custom rate limiting
        rate_limit = CustomRateLimit(
            max_requests=100,
            time_window=60
        )
        
        connection = factory.create_rest_connection(
            base_url="https://api.example.com",
            rate_limit=rate_limit
        )

Error Handling
~~~~~~~~~~~~~

Example of comprehensive error handling:

.. code-block:: python

    from networkpype.factory import NetworkPypeFactory
    from networkpype.rest import RestConnection, ConnectionError
    from networkpype.throttler import RateLimitExceeded

    async def main():
        factory = NetworkPypeFactory()
        connection = factory.create_rest_connection(
            base_url="https://api.example.com"
        )
        
        try:
            async with connection:
                try:
                    response = await connection.get("/endpoint")
                except ConnectionError as e:
                    print(f"Connection failed: {e}")
                except RateLimitExceeded as e:
                    print(f"Rate limit exceeded: {e}")
                    # Implement retry logic
                    await asyncio.sleep(60)
                    response = await connection.get("/endpoint")
                except Exception as e:
                    print(f"Unexpected error: {e}")
                else:
                    print("Request successful!")
        finally:
            await connection.close()

These examples demonstrate the main features and capabilities of NetworkPype. For more specific use cases or detailed API documentation, please refer to the :doc:`API Reference </api/index>`. 