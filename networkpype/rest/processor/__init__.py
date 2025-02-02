"""Request and response processors for the REST client.

This module provides processor classes that can modify requests before they are
sent and process responses before they are returned to the caller. Processors
can be used to implement common functionality like JSON serialization,
authentication, logging, etc.

Key Components:
    RESTPreProcessor: Base class for request pre-processors.
    RESTPostProcessor: Base class for response post-processors.
    JSONProcessor: Processor for JSON request/response handling.
    AuthProcessor: Base class for authentication processors.


Custom Processors:
    To create a custom processor, inherit from RESTPreProcessor and/or
    RESTPostProcessor and implement the required methods. Pre-processors
    should implement process_request(), while post-processors should
    implement process_response().
"""
