"""REST API client implementation for NetworkPype.

This module provides a complete solution for making HTTP requests with features
like rate limiting, request/response processing, and connection management. It
uses aiohttp for making asynchronous HTTP requests and supports customization
through processors.

Key Components:
    RESTManager: High-level interface for making HTTP requests.
    RESTConnection: Low-level HTTP connection handler.
    RESTRequest: Request data container with validation.
    RESTResponse: Response data container with validation.
    RESTPreProcessor: Base class for request pre-processors.
    RESTPostProcessor: Base class for response post-processors.

Example:
    ```python
    from networkpype.rest import RESTManager, RESTConnection
    from networkpype.rest.processor import JSONProcessor

    # Create a REST client with JSON processing
    connection = RESTConnection()
    manager = RESTManager(
        connection=connection,
        post_processors=[JSONProcessor()]
    )

    # Make HTTP requests
    async with manager.session():
        # GET request with automatic JSON parsing
        response = await manager.get("https://api.example.com/data")
        data = response.data  # Parsed JSON data

        # POST request with automatic JSON serialization
        response = await manager.post(
            "https://api.example.com/items",
            data={"name": "test"}
        )
    ```
"""
