"""Message processors for the WebSocket client.

This module provides processor classes that can modify messages before they are
sent and process messages after they are received. Processors can be used to
implement common functionality like JSON serialization, authentication, logging,
etc.

Key Components:
    WebSocketPreProcessor: Base class for message pre-processors.
    WebSocketPostProcessor: Base class for message post-processors.

Custom Processors:
    To create a custom processor, inherit from WebSocketPreProcessor and/or
    WebSocketPostProcessor and implement the required methods. Pre-processors
    should implement process_message(), while post-processors should
    implement process_message().
"""
