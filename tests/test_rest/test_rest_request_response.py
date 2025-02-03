"""Tests for REST request and response classes."""

import json

import aiohttp
import pytest
from aioresponses import aioresponses

from networkpype.rest.method import RESTMethod
from networkpype.rest.request import RESTRequest
from networkpype.rest.response import RESTResponse


def test_rest_request_creation():
    """Test creation of RESTRequest with various configurations."""
    # Test minimal request
    request = RESTRequest(method=RESTMethod.GET)
    assert request.method == RESTMethod.GET
    assert request.url is None
    assert request.endpoint_url is None
    assert request.params is None
    assert request.data is None
    assert request.headers is None
    assert not request.is_auth_required
    assert request.throttler_limit_id is None

    # Test full request
    request = RESTRequest(
        method=RESTMethod.POST,
        url="https://api.example.com/data",
        params={"filter": "active"},
        data={"name": "test"},
        headers={"Content-Type": "application/json"},
        is_auth_required=True,
        throttler_limit_id="api_limit",
    )
    assert request.method == RESTMethod.POST
    assert request.url == "https://api.example.com/data"
    assert request.params == {"filter": "active"}
    assert request.data == {"name": "test"}
    assert request.headers == {"Content-Type": "application/json"}
    assert request.is_auth_required
    assert request.throttler_limit_id == "api_limit"

    # Test with endpoint URL
    request = RESTRequest(
        method=RESTMethod.GET,
        endpoint_url="/v1/users",
    )
    assert request.endpoint_url == "/v1/users"


@pytest.mark.asyncio
async def test_rest_response_properties():
    """Test RESTResponse property access."""
    url = "https://api.example.com/data"
    headers = {"Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        with aioresponses() as m:
            m.get(
                url,
                status=200,
                headers=headers,
                payload={"key": "value"},
            )

            async with session.get(url) as aiohttp_resp:
                response = RESTResponse(aiohttp_resp)

                # Test basic properties
                assert response.url == url
                assert response.method == RESTMethod.GET
                assert response.status == 200
                assert response.headers is not None
                assert response.headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_rest_response_content():
    """Test RESTResponse content retrieval."""
    url = "https://api.example.com/data"
    json_data = {"key": "value"}
    text_data = "Hello, World!"

    async with aiohttp.ClientSession() as session:
        with aioresponses() as m:
            # Test JSON response
            m.get(
                url,
                status=200,
                headers={"Content-Type": "application/json"},
                payload=json_data,
            )

            async with session.get(url) as aiohttp_resp:
                response = RESTResponse(aiohttp_resp)
                result = await response.json()
                assert result == json_data

            # Test text response
            m.get(
                url + "/text",
                status=200,
                headers={"Content-Type": "text/plain"},
                body=text_data,
            )

            async with session.get(url + "/text") as aiohttp_resp:
                response = RESTResponse(aiohttp_resp)
                result = await response.text()
                assert result == text_data


@pytest.mark.asyncio
async def test_rest_response_error_handling():
    """Test RESTResponse error handling."""
    url = "https://api.example.com/data"

    async with aiohttp.ClientSession() as session:
        with aioresponses() as m:
            # Test invalid JSON
            m.get(
                url,
                status=200,
                headers={"Content-Type": "application/json"},
                body="invalid json",  # Send raw invalid JSON string
            )

            async with session.get(url) as aiohttp_resp:
                response = RESTResponse(aiohttp_resp)
                with pytest.raises(json.JSONDecodeError):
                    await response.json()

            # Test error status code
            m.get(
                url + "/error",
                status=404,
                headers={"Content-Type": "application/json"},
                payload={"error": "Not found"},
            )

            async with session.get(url + "/error") as aiohttp_resp:
                response = RESTResponse(aiohttp_resp)
                assert response.status == 404
                error_data = await response.json()
                assert error_data["error"] == "Not found"
