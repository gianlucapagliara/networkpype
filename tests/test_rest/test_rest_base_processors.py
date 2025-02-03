"""Tests for REST processors."""

import json
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import ClientResponse

from networkpype.rest.method import RESTMethod
from networkpype.rest.processor.base import RESTPostProcessor, RESTPreProcessor
from networkpype.rest.request import RESTRequest
from networkpype.rest.response import RESTResponse


class MockPreProcessor(RESTPreProcessor):
    """Test pre-processor that adds custom headers to requests."""

    async def pre_process(self, request: RESTRequest) -> RESTRequest:
        """Add test headers to the request."""
        headers = request.headers or {}
        request.headers = {
            **headers,
            "X-Test": "test_value",
        }
        return request


class MockPostProcessor(RESTPostProcessor):
    """Test post-processor that adds custom fields to JSON responses."""

    async def post_process(self, response: RESTResponse) -> RESTResponse:
        """Add test fields to JSON response data."""
        data = await response.json()
        if isinstance(data, dict):
            data = {**data, "processed": True}
            # Mock the json method to return our modified data
            response._aiohttp_response.json = AsyncMock(return_value=data)
        return response


def create_mock_response(
    status: int = 200,
    data: dict | str | None = None,
    headers: dict | None = None,
    method: str = "GET",
    url: str = "https://api.example.com/test",
) -> RESTResponse:
    """Create a mock REST response for testing."""
    mock_response = Mock(spec=ClientResponse)
    mock_response.status = status
    mock_response.headers = headers or {}
    mock_response.method = method
    mock_response.url = url

    if isinstance(data, dict):
        mock_response.json = AsyncMock(return_value=data)
        mock_response.text = AsyncMock(return_value=json.dumps(data))
    else:
        mock_response.json = AsyncMock(side_effect=ValueError("Not JSON"))
        mock_response.text = AsyncMock(return_value=data or "")

    return RESTResponse(mock_response)


@pytest.mark.asyncio
async def test_pre_processor_headers():
    """Test pre-processor header modification."""
    processor = MockPreProcessor()
    request = RESTRequest(
        method=RESTMethod.GET,
        url="https://api.example.com/test",
        headers={"Content-Type": "application/json"},
    )

    processed = await processor.pre_process(request)
    assert processed.headers == {
        "Content-Type": "application/json",
        "X-Test": "test_value",
    }


@pytest.mark.asyncio
async def test_pre_processor_chain():
    """Test chaining multiple pre-processors."""

    class SecondPreProcessor(RESTPreProcessor):
        async def pre_process(self, request: RESTRequest) -> RESTRequest:
            headers = request.headers or {}
            request.headers = {
                **headers,
                "X-Second": "second_value",
            }
            return request

    first = MockPreProcessor()
    second = SecondPreProcessor()
    request = RESTRequest(
        method=RESTMethod.GET,
        url="https://api.example.com/test",
        headers={"Content-Type": "application/json"},
    )

    processed = await first.pre_process(request)
    processed = await second.pre_process(processed)

    assert processed.headers == {
        "Content-Type": "application/json",
        "X-Test": "test_value",
        "X-Second": "second_value",
    }


@pytest.mark.asyncio
async def test_post_processor_json():
    """Test post-processor with JSON response."""
    processor = MockPostProcessor()
    response = create_mock_response(
        status=200,
        data={"result": "success", "value": 42},
    )

    processed = await processor.post_process(response)
    processed_data = await processed.json()
    assert processed_data == {
        "result": "success",
        "value": 42,
        "processed": True,
    }


@pytest.mark.asyncio
async def test_post_processor_chain():
    """Test chaining multiple post-processors."""

    class SecondPostProcessor(RESTPostProcessor):
        async def post_process(self, response: RESTResponse) -> RESTResponse:
            data = await response.json()
            if isinstance(data, dict):
                data = {**data, "second_processed": True}
                response._aiohttp_response.json = AsyncMock(return_value=data)
            return response

    first = MockPostProcessor()
    second = SecondPostProcessor()
    response = create_mock_response(
        status=200,
        data={"result": "success", "value": 42},
    )

    processed = await first.post_process(response)
    processed = await second.post_process(processed)
    processed_data = await processed.json()

    assert processed_data == {
        "result": "success",
        "value": 42,
        "processed": True,
        "second_processed": True,
    }


@pytest.mark.asyncio
async def test_pre_processor_with_params():
    """Test pre-processor with query parameters."""
    processor = MockPreProcessor()
    request = RESTRequest(
        method=RESTMethod.GET,
        url="https://api.example.com/test",
        headers={"Content-Type": "application/json"},
        params={"key": "value"},
    )

    processed = await processor.pre_process(request)
    assert processed.params == {"key": "value"}  # Should not modify params


@pytest.mark.asyncio
async def test_pre_processor_with_json():
    """Test pre-processor with JSON body."""
    processor = MockPreProcessor()
    request = RESTRequest(
        method=RESTMethod.POST,
        url="https://api.example.com/test",
        headers={"Content-Type": "application/json"},
        data={"data": "test"},
    )

    processed = await processor.pre_process(request)
    assert processed.data == {"data": "test"}  # Should not modify JSON body


@pytest.mark.asyncio
async def test_post_processor_with_headers():
    """Test post-processor preserves response headers."""
    processor = MockPostProcessor()
    response = create_mock_response(
        status=200,
        data={"result": "success"},
        headers={"Content-Type": "application/json"},
    )

    processed = await processor.post_process(response)
    assert processed.headers == {"Content-Type": "application/json"}


@pytest.mark.asyncio
async def test_post_processor_with_status():
    """Test post-processor preserves response status."""
    processor = MockPostProcessor()
    response = create_mock_response(
        status=201,
        data={"result": "created"},
    )

    processed = await processor.post_process(response)
    assert processed.status == 201
