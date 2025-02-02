"""REST connection module for low-level HTTP communication.

This module provides a low-level interface for making HTTP requests using the aiohttp
library. It handles the direct communication with HTTP servers while providing a clean
abstraction over the underlying HTTP client library.

The module is designed to work with the RESTRequest and RESTResponse classes to provide
a consistent interface for HTTP communication, regardless of the underlying HTTP client
implementation.

Classes:
    RESTConnection: Low-level HTTP connection handler.
"""

import aiohttp
from yarl import URL

from networkpype.rest.request import RESTRequest
from networkpype.rest.response import RESTResponse


class RESTConnection:
    """Low-level HTTP connection handler.

    This class provides direct access to HTTP communication functionality, wrapping
    an aiohttp client session. It handles the conversion between the networkpype
    request/response types and the underlying aiohttp types.

    The connection is designed to be reused across multiple requests to take advantage
    of connection pooling and other HTTP/1.1 and HTTP/2 optimizations.

    Attributes:
        _client_session (aiohttp.ClientSession): The underlying aiohttp client session.

    Example:
        ```python
        async with aiohttp.ClientSession() as session:
            connection = RESTConnection(session)
            request = RESTRequest(
                method=RESTMethod.GET,
                url="https://api.example.com/data"
            )
            response = await connection.call(request)
            data = await response.json()
        ```
    """

    def __init__(self, aiohttp_client_session: aiohttp.ClientSession):
        """Initialize the RESTConnection with an aiohttp client session.

        Args:
            aiohttp_client_session (aiohttp.ClientSession): The aiohttp client session
                to use for making HTTP requests.
        """
        self._client_session = aiohttp_client_session

    async def call(
        self, request: RESTRequest, encoded: bool = False, **kwargs
    ) -> RESTResponse:
        """Execute an HTTP request.

        This method converts the networkpype request into an aiohttp request,
        executes it, and wraps the response in a networkpype response object.

        Args:
            request (RESTRequest): The request to execute.
            encoded (bool): Whether the URL is already percent-encoded. If True,
                no additional encoding will be performed. Defaults to False.
            **kwargs: Additional arguments to pass to aiohttp.ClientSession.request().

        Returns:
            RESTResponse: The response from the server.

        Raises:
            aiohttp.ClientError: If there is an error making the request.
            asyncio.TimeoutError: If the request times out.
            ValueError: If the request URL is None.
        """
        if request.url is None:
            raise ValueError("Request URL cannot be None")

        aiohttp_resp = await self._client_session.request(
            method=request.method.value,
            url=URL(request.url, encoded=encoded),
            params=request.params,
            data=request.data,
            headers=request.headers,
            **kwargs,
        )

        resp = await self._build_resp(aiohttp_resp)
        return resp

    @staticmethod
    async def _build_resp(aiohttp_resp: aiohttp.ClientResponse) -> RESTResponse:
        """Build a networkpype response from an aiohttp response.

        Args:
            aiohttp_resp (aiohttp.ClientResponse): The aiohttp response to wrap.

        Returns:
            RESTResponse: The wrapped response.
        """
        resp = RESTResponse(aiohttp_resp)
        return resp
