"""Tests for the REST connection class."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from aiohttp import ClientSession
from aioresponses import aioresponses

from networkpype.rest.connection import RESTConnection
from networkpype.rest.method import RESTMethod
from networkpype.rest.request import RESTRequest


@pytest_asyncio.fixture
async def client_session() -> AsyncGenerator[ClientSession, None]:
    """Create a client session for testing."""
    async with ClientSession() as session:
        yield session


@pytest_asyncio.fixture
async def connection(
    client_session: ClientSession,
) -> AsyncGenerator[RESTConnection, None]:
    """Create a REST connection for testing."""
    connection = RESTConnection(client_session)
    yield connection


@pytest.mark.asyncio
async def test_connection_basic_request(connection: RESTConnection) -> None:
    """Test basic request execution through RESTConnection."""
    url = "https://api.example.com/data"
    request = RESTRequest(
        method=RESTMethod.GET,
        url=url,
    )

    with aioresponses() as m:
        m.get(
            url,
            status=200,
            payload={"key": "value"},
            headers={"Content-Type": "application/json"},
        )

        response = await connection.call(request)
        assert response.status == 200
        data = await response.json()
        assert data == {"key": "value"}


@pytest.mark.asyncio
async def test_connection_with_params(connection: RESTConnection) -> None:
    """Test request execution with query parameters."""
    url = "https://api.example.com/data"
    params = {"filter": "active", "page": "1"}
    request = RESTRequest(
        method=RESTMethod.GET,
        url=url,
        params=params,
    )

    with aioresponses() as m:
        m.get(
            f"{url}?filter=active&page=1",
            status=200,
            payload={"filtered": True},
        )

        response = await connection.call(request)
        assert response.status == 200
        data = await response.json()
        assert data == {"filtered": True}


@pytest.mark.asyncio
async def test_connection_with_headers(connection: RESTConnection) -> None:
    """Test request execution with custom headers."""
    url = "https://api.example.com/data"
    headers = {"X-Test-Header": "test_value"}
    request = RESTRequest(
        method=RESTMethod.GET,
        url=url,
        headers=headers,
    )

    with aioresponses() as m:
        m.get(
            url,
            status=200,
            payload={"key": "value"},
            headers={"Content-Type": "application/json"},
        )

        response = await connection.call(request)
        assert response.status == 200
        data = await response.json()
        assert data == {"key": "value"}


@pytest.mark.asyncio
async def test_connection_post_with_data(connection: RESTConnection) -> None:
    """Test POST request with body data."""
    url = "https://api.example.com/data"
    data = {"name": "test", "value": 123}
    request = RESTRequest(
        method=RESTMethod.POST,
        url=url,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    with aioresponses() as m:
        m.post(
            url,
            status=201,
            payload={"created": True},
        )

        response = await connection.call(request)
        assert response.status == 201
        result = await response.json()
        assert result == {"created": True}


@pytest.mark.asyncio
async def test_connection_error_handling(connection: RESTConnection) -> None:
    """Test error handling in connection."""
    url = "https://api.example.com/data"

    # Test with None URL
    with pytest.raises(ValueError, match="Request URL cannot be None"):
        await connection.call(RESTRequest(method=RESTMethod.GET))

    # Test server error
    request = RESTRequest(method=RESTMethod.GET, url=url)
    with aioresponses() as m:
        m.get(
            url,
            status=500,
            payload={"error": "Internal Server Error"},
        )

        response = await connection.call(request)
        assert response.status == 500
        error_data = await response.json()
        assert error_data["error"] == "Internal Server Error"


@pytest.mark.asyncio
async def test_connection_with_encoded_url(connection: RESTConnection) -> None:
    """Test request execution with pre-encoded URLs."""
    # URL with spaces and special characters
    base_url = "https://api.example.com/data with spaces"
    encoded_url = "https://api.example.com/data%20with%20spaces"

    # Test without encoded flag
    request = RESTRequest(method=RESTMethod.GET, url=base_url)
    with aioresponses() as m:
        m.get(encoded_url, status=200, payload={"success": True})
        response = await connection.call(request)
        assert response.status == 200

    # Test with encoded flag
    request = RESTRequest(method=RESTMethod.GET, url=encoded_url)
    with aioresponses() as m:
        m.get(encoded_url, status=200, payload={"success": True})
        response = await connection.call(request, encoded=True)
        assert response.status == 200
