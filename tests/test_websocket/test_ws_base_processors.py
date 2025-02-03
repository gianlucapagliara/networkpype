"""Tests for WebSocket processors."""

import pytest

from networkpype.websocket.processor.base import (
    WebSocketPostProcessor,
    WebSocketPreProcessor,
)
from networkpype.websocket.request import (
    WebSocketJSONRequest,
    WebSocketPlainTextRequest,
    WebSocketRequest,
)
from networkpype.websocket.response import WebSocketResponse


class MockPreProcessor(WebSocketPreProcessor):
    """Test pre-processor that adds a custom field to JSON messages."""

    async def pre_process(self, request: WebSocketRequest) -> WebSocketRequest:
        """Add a test field to the JSON payload."""
        if isinstance(request, WebSocketJSONRequest):
            request.payload = {**request.payload, "test_field": "test_value"}
        return request


class MockPostProcessor(WebSocketPostProcessor):
    """Test post-processor that adds a custom field to JSON responses."""

    async def post_process(self, response: WebSocketResponse) -> WebSocketResponse:
        """Add a test field to JSON response data."""
        if isinstance(response.data, dict):
            response.data = {**response.data, "processed": True}
        return response


@pytest.mark.asyncio
async def test_pre_processor_json():
    """Test pre-processor with JSON request."""
    processor = MockPreProcessor()
    request = WebSocketJSONRequest(payload={"type": "subscribe"})

    processed = await processor.pre_process(request)
    assert processed.payload == {
        "type": "subscribe",
        "test_field": "test_value",
    }


@pytest.mark.asyncio
async def test_pre_processor_chain():
    """Test chaining multiple pre-processors."""

    class SecondPreProcessor(WebSocketPreProcessor):
        async def pre_process(self, request: WebSocketRequest) -> WebSocketRequest:
            if isinstance(request, WebSocketJSONRequest):
                request.payload = {**request.payload, "second_field": "second_value"}
            return request

    first = MockPreProcessor()
    second = SecondPreProcessor()
    request = WebSocketJSONRequest(payload={"type": "subscribe"})

    processed = await first.pre_process(request)
    processed = await second.pre_process(processed)

    assert processed.payload == {
        "type": "subscribe",
        "test_field": "test_value",
        "second_field": "second_value",
    }


@pytest.mark.asyncio
async def test_post_processor_json():
    """Test post-processor with JSON response."""
    processor = MockPostProcessor()
    response = WebSocketResponse(data={"type": "market_data", "price": 100.0})

    processed = await processor.post_process(response)
    assert processed.data == {
        "type": "market_data",
        "price": 100.0,
        "processed": True,
    }


@pytest.mark.asyncio
async def test_post_processor_chain():
    """Test chaining multiple post-processors."""

    class SecondPostProcessor(WebSocketPostProcessor):
        async def post_process(self, response: WebSocketResponse) -> WebSocketResponse:
            if isinstance(response.data, dict):
                response.data = {**response.data, "second_processed": True}
            return response

    first = MockPostProcessor()
    second = SecondPostProcessor()
    response = WebSocketResponse(data={"type": "market_data", "price": 100.0})

    processed = await first.post_process(response)
    processed = await second.post_process(processed)

    assert processed.data == {
        "type": "market_data",
        "price": 100.0,
        "processed": True,
        "second_processed": True,
    }


@pytest.mark.asyncio
async def test_post_processor_non_json():
    """Test post-processor with non-JSON response."""
    processor = MockPostProcessor()
    response = WebSocketResponse(data="text message")

    processed = await processor.post_process(response)
    assert processed.data == "text message"  # Should not modify non-dict data


@pytest.mark.asyncio
async def test_pre_processor_non_json():
    """Test pre-processor with non-JSON request."""
    processor = MockPreProcessor()
    request = WebSocketPlainTextRequest(payload="text message")

    processed = await processor.pre_process(request)
    assert processed.payload == "text message"  # Should not modify text payload
