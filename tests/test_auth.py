"""Tests for the Auth base class."""

import pytest

from networkpype.auth import Auth
from networkpype.rest.method import RESTMethod
from networkpype.rest.request import RESTRequest
from networkpype.time_synchronizer import TimeSynchronizer
from networkpype.websocket.request import WebSocketJSONRequest


class ConcreteAuth(Auth):
    """Concrete implementation of Auth for testing."""

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        request.headers = request.headers or {}
        request.headers["Authorization"] = "Bearer test_token"
        return request

    async def ws_authenticate(
        self, request: WebSocketJSONRequest
    ) -> WebSocketJSONRequest:
        return request


def test_auth_init_default_time_provider():
    """Test Auth creates a default TimeSynchronizer."""
    auth = ConcreteAuth()
    assert isinstance(auth.time_provider, TimeSynchronizer)


def test_auth_init_custom_time_provider():
    """Test Auth uses provided TimeSynchronizer."""
    ts = TimeSynchronizer(max_samples=10)
    auth = ConcreteAuth(time_provider=ts)
    assert auth.time_provider is ts


@pytest.mark.asyncio
async def test_rest_authenticate():
    """Test REST authentication adds authorization header."""
    auth = ConcreteAuth()
    request = RESTRequest(method=RESTMethod.GET, url="https://example.com")
    result = await auth.rest_authenticate(request)
    assert result.headers["Authorization"] == "Bearer test_token"


@pytest.mark.asyncio
async def test_ws_authenticate():
    """Test WebSocket authentication."""
    auth = ConcreteAuth()
    request = WebSocketJSONRequest(payload={"type": "subscribe"})
    result = await auth.ws_authenticate(request)
    assert result is request
