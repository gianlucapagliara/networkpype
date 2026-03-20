"""Tests for the RESTManager class."""

import json
from unittest.mock import AsyncMock

import pytest

from networkpype.auth import Auth
from networkpype.rest.connection import RESTConnection
from networkpype.rest.manager import RESTManager
from networkpype.rest.method import RESTMethod
from networkpype.rest.processor.base import RESTPostProcessor, RESTPreProcessor
from networkpype.rest.request import RESTRequest
from networkpype.rest.response import RESTResponse
from networkpype.throttler.rate_limit import RateLimit
from networkpype.throttler.throttler import AsyncThrottler


class MockPreProcessor(RESTPreProcessor):
    async def pre_process(self, request: RESTRequest) -> RESTRequest:
        request.headers = request.headers or {}
        request.headers["X-Processed"] = "true"
        return request


class MockPostProcessor(RESTPostProcessor):
    async def post_process(self, response: RESTResponse) -> RESTResponse:
        return response


class MockAuth(Auth):
    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        request.headers = request.headers or {}
        request.headers["Authorization"] = "Bearer token"
        return request

    async def ws_authenticate(self, request):
        return request


@pytest.fixture
def throttler():
    return AsyncThrottler(
        rate_limits=[RateLimit(limit=100, time_interval=1.0, limit_id="test")]
    )


@pytest.fixture
def mock_connection():
    conn = AsyncMock(spec=RESTConnection)
    return conn


@pytest.fixture
def manager(mock_connection, throttler):
    return RESTManager(connection=mock_connection, throttler=throttler)


@pytest.fixture
def manager_with_processors(mock_connection, throttler):
    return RESTManager(
        connection=mock_connection,
        throttler=throttler,
        rest_pre_processors=[MockPreProcessor()],
        rest_post_processors=[MockPostProcessor()],
    )


@pytest.fixture
def manager_with_auth(mock_connection, throttler):
    return RESTManager(
        connection=mock_connection,
        throttler=throttler,
        auth=MockAuth(),
    )


def _make_mock_response(status=200, json_data=None, text_data="", headers=None):
    """Helper to create a mock RESTResponse."""
    resp = AsyncMock(spec=RESTResponse)
    resp.status = status
    resp.headers = headers or {"Content-Type": "application/json"}
    resp.json = AsyncMock(return_value=json_data or {})
    resp.text = AsyncMock(return_value=text_data)
    resp.url = "https://api.example.com/data"
    resp.method = "GET"
    return resp


@pytest.mark.asyncio
async def test_manager_init(manager, mock_connection, throttler):
    """Test RESTManager initialization."""
    assert manager._connection is mock_connection
    assert manager._throttler is throttler
    assert manager._rest_pre_processors == []
    assert manager._rest_post_processors == []
    assert manager._auth is None


@pytest.mark.asyncio
async def test_call_basic(manager, mock_connection):
    """Test basic call without processors or auth."""
    mock_resp = _make_mock_response()
    mock_connection.call.return_value = mock_resp

    request = RESTRequest(method=RESTMethod.GET, url="https://api.example.com/data")
    response = await manager.call(request)

    assert response is mock_resp
    mock_connection.call.assert_called_once()


@pytest.mark.asyncio
async def test_call_with_preprocessors(manager_with_processors, mock_connection):
    """Test call applies pre-processors."""
    mock_resp = _make_mock_response()
    mock_connection.call.return_value = mock_resp

    request = RESTRequest(method=RESTMethod.GET, url="https://api.example.com/data")
    await manager_with_processors.call(request)

    # Verify the pre-processor modified the request
    called_request = (
        mock_connection.call.call_args[1].get("request")
        or mock_connection.call.call_args[0][0]
    )
    assert called_request.headers.get("X-Processed") == "true"


@pytest.mark.asyncio
async def test_call_with_auth_required(manager_with_auth, mock_connection):
    """Test call applies authentication when required."""
    mock_resp = _make_mock_response()
    mock_connection.call.return_value = mock_resp

    request = RESTRequest(
        method=RESTMethod.GET,
        url="https://api.example.com/data",
        is_auth_required=True,
    )
    await manager_with_auth.call(request)

    called_request = mock_connection.call.call_args[0][0]
    assert called_request.headers.get("Authorization") == "Bearer token"


@pytest.mark.asyncio
async def test_call_without_auth_when_not_required(manager_with_auth, mock_connection):
    """Test call skips authentication when not required."""
    mock_resp = _make_mock_response()
    mock_connection.call.return_value = mock_resp

    request = RESTRequest(
        method=RESTMethod.GET,
        url="https://api.example.com/data",
        is_auth_required=False,
    )
    await manager_with_auth.call(request)

    called_request = mock_connection.call.call_args[0][0]
    assert "Authorization" not in (called_request.headers or {})


@pytest.mark.asyncio
async def test_call_deepcopies_request(manager, mock_connection):
    """Test that call deep copies the request to avoid mutation."""
    mock_resp = _make_mock_response()
    mock_connection.call.return_value = mock_resp

    request = RESTRequest(
        method=RESTMethod.GET,
        url="https://api.example.com/data",
        headers={"Original": "true"},
    )
    await manager.call(request)

    # Original request should be unchanged
    assert request.headers == {"Original": "true"}


@pytest.mark.asyncio
async def test_execute_request_get(manager, mock_connection):
    """Test execute_request with GET method."""
    mock_resp = _make_mock_response(json_data={"key": "value"})
    mock_connection.call.return_value = mock_resp

    result = await manager.execute_request(
        url="https://api.example.com/data",
        throttler_limit_id="test",
    )
    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_execute_request_post_sets_content_type(manager, mock_connection):
    """Test execute_request sets JSON content type for POST."""
    mock_resp = _make_mock_response(json_data={"created": True})
    mock_connection.call.return_value = mock_resp

    await manager.execute_request(
        url="https://api.example.com/data",
        throttler_limit_id="test",
        method=RESTMethod.POST,
        data={"name": "test"},
    )

    called_request = (
        mock_connection.call.call_args[1].get("request")
        or mock_connection.call.call_args[0][0]
    )
    assert called_request.headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_execute_request_get_sets_form_content_type(manager, mock_connection):
    """Test execute_request sets form content type for GET."""
    mock_resp = _make_mock_response(json_data={"key": "value"})
    mock_connection.call.return_value = mock_resp

    await manager.execute_request(
        url="https://api.example.com/data",
        throttler_limit_id="test",
        method=RESTMethod.GET,
    )

    called_request = mock_connection.call.call_args[0][0]
    assert called_request.headers["Content-Type"] == "application/x-www-form-urlencoded"


@pytest.mark.asyncio
async def test_execute_request_filters_none_params(manager, mock_connection):
    """Test execute_request filters None values from params."""
    mock_resp = _make_mock_response(json_data={})
    mock_connection.call.return_value = mock_resp

    await manager.execute_request(
        url="https://api.example.com/data",
        throttler_limit_id="test",
        params={"key": "value", "empty": None},
    )

    called_request = mock_connection.call.call_args[0][0]
    assert called_request.params == {"key": "value"}


@pytest.mark.asyncio
async def test_execute_request_filters_none_data(manager, mock_connection):
    """Test execute_request filters None values from data dict."""
    mock_resp = _make_mock_response(json_data={})
    mock_connection.call.return_value = mock_resp

    await manager.execute_request(
        url="https://api.example.com/data",
        throttler_limit_id="test",
        method=RESTMethod.POST,
        data={"name": "test", "empty": None},
    )

    called_request = mock_connection.call.call_args[0][0]
    assert called_request.data == json.dumps({"name": "test"})


@pytest.mark.asyncio
async def test_execute_request_string_data(manager, mock_connection):
    """Test execute_request handles string data."""
    mock_resp = _make_mock_response(json_data={})
    mock_connection.call.return_value = mock_resp

    await manager.execute_request(
        url="https://api.example.com/data",
        throttler_limit_id="test",
        method=RESTMethod.POST,
        data="raw string data",
    )

    called_request = mock_connection.call.call_args[0][0]
    assert called_request.data == "raw string data"


@pytest.mark.asyncio
async def test_execute_request_error_raises(manager, mock_connection):
    """Test execute_request raises OSError on error status."""
    mock_resp = _make_mock_response(status=500, text_data="Internal Server Error")
    mock_connection.call.return_value = mock_resp

    with pytest.raises(OSError, match="Error executing request"):
        await manager.execute_request(
            url="https://api.example.com/data",
            throttler_limit_id="test",
        )


@pytest.mark.asyncio
async def test_execute_request_error_return_err(manager, mock_connection):
    """Test execute_request returns error when return_err=True."""
    mock_resp = _make_mock_response(status=400, json_data={"error": "Bad Request"})
    mock_connection.call.return_value = mock_resp

    result = await manager.execute_request(
        url="https://api.example.com/data",
        throttler_limit_id="test",
        return_err=True,
    )
    assert result == {"error": "Bad Request"}


@pytest.mark.asyncio
async def test_execute_request_error_return_err_fallback(manager, mock_connection):
    """Test execute_request error with content_type fallback."""
    mock_resp = _make_mock_response(status=400)
    # First json() call raises, second with content_type=None succeeds
    mock_resp.json = AsyncMock(
        side_effect=[Exception("parse error"), {"error": "fallback"}]
    )
    mock_connection.call.return_value = mock_resp

    result = await manager.execute_request(
        url="https://api.example.com/data",
        throttler_limit_id="test",
        return_err=True,
    )
    assert result == {"error": "fallback"}


@pytest.mark.asyncio
async def test_execute_request_no_content_type(manager, mock_connection):
    """Test execute_request handles missing Content-Type header."""
    mock_resp = _make_mock_response(json_data={"key": "value"})
    mock_resp.headers = None
    mock_connection.call.return_value = mock_resp

    await manager.execute_request(
        url="https://api.example.com/data",
        throttler_limit_id="test",
    )
    mock_resp.json.assert_called_with(content_type=None)


@pytest.mark.asyncio
async def test_execute_request_put_content_type(manager, mock_connection):
    """Test execute_request sets JSON content type for PUT."""
    mock_resp = _make_mock_response(json_data={})
    mock_connection.call.return_value = mock_resp

    await manager.execute_request(
        url="https://api.example.com/data",
        throttler_limit_id="test",
        method=RESTMethod.PUT,
        data={"name": "test"},
    )

    called_request = mock_connection.call.call_args[0][0]
    assert called_request.headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_execute_request_empty_data_dict(manager, mock_connection):
    """Test execute_request with all-None data dict results in None data."""
    mock_resp = _make_mock_response(json_data={})
    mock_connection.call.return_value = mock_resp

    await manager.execute_request(
        url="https://api.example.com/data",
        throttler_limit_id="test",
        method=RESTMethod.POST,
        data={"empty": None},
    )

    called_request = mock_connection.call.call_args[0][0]
    assert called_request.data is None
