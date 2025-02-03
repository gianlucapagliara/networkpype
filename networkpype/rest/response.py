"""REST response module for handling HTTP responses.

This module provides a wrapper around HTTP responses, offering a clean and consistent
interface for accessing response data. It abstracts the underlying HTTP client library
(aiohttp) and provides type-safe access to response properties and content.

The module is designed to work asynchronously, providing methods for accessing response
data in both JSON and text formats.

Classes:
    RESTResponse: Wrapper class for HTTP responses.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

import aiohttp

from networkpype.rest.method import RESTMethod


@dataclass(init=False)
class RESTResponse:
    """Wrapper class for HTTP responses.

    This class provides a clean interface for accessing HTTP response data, abstracting
    away the details of the underlying HTTP client library. It offers type-safe access
    to common response properties and methods for retrieving response content.

    The class is designed to work with asynchronous HTTP clients and provides async
    methods for accessing response data in various formats.

    Attributes:
        _aiohttp_response (aiohttp.ClientResponse): The underlying aiohttp response object.

    Example:
        ```python
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.example.com/data") as response:
                rest_response = RESTResponse(response)
                status = rest_response.status
                data = await rest_response.json()
        ```
    """

    url: str
    method: RESTMethod
    status: int
    headers: Optional[Mapping[str, str]]

    def __init__(self, aiohttp_response: aiohttp.ClientResponse):
        """Initialize the RESTResponse with an aiohttp response object.

        Args:
            aiohttp_response (aiohttp.ClientResponse): The underlying aiohttp response object.
        """
        self._aiohttp_response = aiohttp_response

    @property
    def url(self) -> str:
        """Get the URL that was requested.

        Returns:
            str: The URL string of the request.
        """
        url_str = str(self._aiohttp_response.url)
        return url_str

    @property
    def method(self) -> RESTMethod:
        """Get the HTTP method used for the request.

        Returns:
            RESTMethod: The HTTP method enum value.
        """
        method_ = RESTMethod[self._aiohttp_response.method.upper()]
        return method_

    @property
    def status(self) -> int:
        """Get the HTTP status code of the response.

        Returns:
            int: The HTTP status code (e.g., 200, 404, 500).
        """
        status_ = int(self._aiohttp_response.status)
        return status_

    @property
    def headers(self) -> Mapping[str, str] | None:
        """Get the response headers.

        Returns:
            Mapping[str, str] | None: A mapping of header names to values,
                or None if no headers are present.
        """
        headers_ = self._aiohttp_response.headers
        return headers_

    async def json(self, content_type: str | None = "application/json") -> Any:
        """Parse the response body as JSON.

        This method asynchronously reads and parses the response body as JSON data.
        It supports custom content types for APIs that use non-standard JSON mime types.

        Args:
            content_type (str | None): The expected content type of the response.
                Defaults to "application/json".

        Returns:
            Any: The parsed JSON data. The exact type depends on the JSON content
                (could be dict, list, str, int, etc.).

        Raises:
            aiohttp.ContentTypeError: If the response body is not valid JSON.
        """
        json_ = await self._aiohttp_response.json(content_type=content_type)
        return json_

    async def text(self) -> str:
        """Get the response body as text.

        This method asynchronously reads the response body and returns it as a string.

        Returns:
            str: The response body text.
        """
        text_ = await self._aiohttp_response.text()
        return text_
