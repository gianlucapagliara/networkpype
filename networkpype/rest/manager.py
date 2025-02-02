"""REST manager module for handling HTTP communication.

This module provides a high-level interface for making HTTP requests with support for
authentication, rate limiting, and request/response processing. It coordinates the
various components of the REST communication system, including connection management,
throttling, and pre/post processing of requests and responses.

The manager is designed to be extensible through processors that can modify requests
before they are sent and responses before they are returned to the caller.

Classes:
    RESTManager: High-level manager for REST API communication.
"""

import json
from asyncio import wait_for
from copy import deepcopy
from typing import Any, cast

from networkpype.auth import Auth
from networkpype.rest.connection import RESTConnection
from networkpype.rest.method import RESTMethod
from networkpype.rest.processor.base import RESTPostProcessor, RESTPreProcessor
from networkpype.rest.request import RESTRequest
from networkpype.rest.response import RESTResponse
from networkpype.throttler.throttler import AsyncThrottler


class RESTManager:
    """High-level manager for REST API communication.

    This class coordinates all aspects of REST API communication, including connection
    management, authentication, rate limiting, and request/response processing. It
    provides a clean interface for making HTTP requests while handling common concerns
    like authentication and rate limiting automatically.

    The manager can be extended with pre-processors and post-processors to modify
    requests before they are sent and responses before they are returned. This allows
    for flexible customization of the request/response pipeline.

    Attributes:
        _connection (RESTConnection): The underlying REST connection.
        _rest_pre_processors (list[RESTPreProcessor]): Processors to run before sending requests.
        _rest_post_processors (list[RESTPostProcessor]): Processors to run after receiving responses.
        _auth (Auth | None): Authentication handler for requests.
        _throttler (AsyncThrottler): Rate limiting handler.

    Example:
        ```python
        # Create a manager with authentication and rate limiting
        manager = RESTManager(
            connection=rest_connection,
            throttler=AsyncThrottler(limits=[RateLimit(10, 1.0)]),
            auth=APIKeyAuth(api_key="your-key"),
            rest_pre_processors=[LoggingProcessor()],
            rest_post_processors=[ErrorHandler()]
        )

        # Make an authenticated request
        data = await manager.execute_request(
            url="https://api.example.com/data",
            throttler_limit_id="main",
            method=RESTMethod.GET,
            is_auth_required=True
        )
        ```
    """

    def __init__(
        self,
        connection: RESTConnection,
        throttler: AsyncThrottler,
        rest_pre_processors: list[RESTPreProcessor] | None = None,
        rest_post_processors: list[RESTPostProcessor] | None = None,
        auth: Auth | None = None,
    ):
        """Initialize the RESTManager with the specified components.

        Args:
            connection (RESTConnection): The underlying REST connection to use.
            throttler (AsyncThrottler): Rate limiting handler for API requests.
            rest_pre_processors (list[RESTPreProcessor] | None): List of processors to run
                before sending requests. Defaults to None.
            rest_post_processors (list[RESTPostProcessor] | None): List of processors to run
                after receiving responses. Defaults to None.
            auth (Auth | None): Authentication handler for requests. Defaults to None.
        """
        self._connection = connection
        self._rest_pre_processors = rest_pre_processors or []
        self._rest_post_processors = rest_post_processors or []
        self._auth = auth
        self._throttler = throttler

    async def execute_request(
        self,
        url: str,
        throttler_limit_id: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        method: RESTMethod = RESTMethod.GET,
        is_auth_required: bool = False,
        return_err: bool = False,
        timeout: float | None = None,
        headers: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute a REST request with full processing and error handling.

        This is the main method for making REST API calls. It handles:
        - Setting appropriate headers based on the request method
        - JSON serialization of request data
        - Rate limiting through the throttler
        - Error handling and response parsing
        - Timeout management

        Args:
            url (str): The URL to send the request to.
            throttler_limit_id (str): Identifier for rate limiting.
            params (dict[str, Any] | None): Query parameters to include. Defaults to None.
            data (dict[str, Any] | None): Request body data. Defaults to None.
            method (RESTMethod): HTTP method to use. Defaults to GET.
            is_auth_required (bool): Whether authentication is needed. Defaults to False.
            return_err (bool): Whether to return error responses instead of raising.
                Defaults to False.
            timeout (float | None): Request timeout in seconds. Defaults to None.
            headers (dict[str, Any] | None): Additional headers to include. Defaults to None.
            **kwargs: Additional arguments to pass to the connection.

        Returns:
            dict[str, Any]: The parsed response data as a JSON object.

        Raises:
            OSError: If the request fails and return_err is False.
            asyncio.TimeoutError: If the request times out.
            json.JSONDecodeError: If the response is not valid JSON.
        """
        headers = headers or {}

        local_headers = {
            "Content-Type": (
                "application/json"
                if method in [RESTMethod.POST, RESTMethod.PUT]
                else "application/x-www-form-urlencoded"
            )
        }
        local_headers.update(headers)

        request_data: str | None = None
        if isinstance(data, dict):
            filtered_data = {k: v for k, v in data.items() if v is not None}
            request_data = json.dumps(filtered_data) if filtered_data else None
        elif isinstance(data, str):
            request_data = data

        request_params = (
            {k: v for k, v in params.items() if v is not None}
            if isinstance(params, dict)
            else None
        )

        request = RESTRequest(
            method=method,
            url=url,
            params=request_params,
            data=request_data,
            headers=local_headers,
            is_auth_required=is_auth_required,
            throttler_limit_id=throttler_limit_id,
        )

        async with self._throttler.execute_task(limit_id=throttler_limit_id):
            response = await self.call(request=request, timeout=timeout, **kwargs)

            if 400 <= response.status:
                if return_err:
                    try:
                        error_response = await response.json()
                    except:
                        error_response = await response.json(content_type=None)
                    return cast(dict[str, Any], error_response)
                else:
                    error_response = await response.text()
                    raise OSError(
                        f"Error executing request {method.name} {url}. HTTP status is {response.status}. "
                        f"Error: {error_response}"
                    )

            content_type = (
                response.headers.get("Content-Type") if response.headers else None
            )
            result = (
                await response.json(content_type.lower())
                if content_type
                else await response.json(content_type=None)
            )
            return cast(dict[str, Any], result)

    async def call(
        self, request: RESTRequest, timeout: float | None = None, **kwargs
    ) -> RESTResponse:
        """Execute a REST request with pre/post processing.

        This method handles the core request execution flow:
        1. Pre-process the request
        2. Authenticate if required
        3. Send the request
        4. Post-process the response

        Args:
            request (RESTRequest): The request to execute.
            timeout (float | None): Request timeout in seconds. Defaults to None.
            **kwargs: Additional arguments to pass to the connection.

        Returns:
            RESTResponse: The processed response.

        Raises:
            asyncio.TimeoutError: If the request times out.
        """
        request = deepcopy(request)
        request = await self._pre_process_request(request)
        request = await self._authenticate(request)
        resp = await wait_for(self._connection.call(request, **kwargs), timeout)
        resp = await self._post_process_response(resp)
        return resp

    async def _pre_process_request(self, request: RESTRequest) -> RESTRequest:
        """Apply all pre-processors to the request.

        Args:
            request (RESTRequest): The request to process.

        Returns:
            RESTRequest: The processed request.
        """
        for pre_processor in self._rest_pre_processors:
            request = await pre_processor.pre_process(request)
        return request

    async def _authenticate(self, request: RESTRequest) -> RESTRequest:
        """Authenticate the request if required.

        Args:
            request (RESTRequest): The request to authenticate.

        Returns:
            RESTRequest: The authenticated request.
        """
        if self._auth is not None and request.is_auth_required:
            request = await self._auth.rest_authenticate(request)
        return request

    async def _post_process_response(self, response: RESTResponse) -> RESTResponse:
        """Apply all post-processors to the response.

        Args:
            response (RESTResponse): The response to process.

        Returns:
            RESTResponse: The processed response.
        """
        for post_processor in self._rest_post_processors:
            response = await post_processor.post_process(response)
        return response
