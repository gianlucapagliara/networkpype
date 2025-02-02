"""REST request and response processor interfaces.

This module defines the base abstract classes for processing REST requests and responses.
These processors can be used to inject custom functionality into the REST communication
pipeline, such as authentication, logging, error handling, or data transformation.

The processors are designed to be composable, allowing multiple processors to be chained
together in a specific order to handle different aspects of the request/response cycle.

Classes:
    RESTPostProcessor: Abstract base class for processing REST responses.
    RESTPreProcessor: Abstract base class for processing REST requests.
"""

import abc

from networkpype.rest.request import RESTRequest
from networkpype.rest.response import RESTResponse


class RESTPostProcessor(abc.ABC):
    """Abstract base class for processing REST responses.

    This interface enables functionality injection into the `RESTManager` for response
    processing. Implementations of this class can modify or transform responses before
    they are returned to the caller.

    Use cases include:
    - Response data transformation
    - Error handling and recovery
    - Response validation
    - Metrics collection
    - Logging and monitoring
    - Cache management

    Example:
        ```python
        class ErrorHandlingProcessor(RESTPostProcessor):
            async def post_process(self, response: RESTResponse) -> RESTResponse:
                if response.status >= 400:
                    # Handle error response
                    return await self.handle_error(response)
                return response
        ```
    """

    @abc.abstractmethod
    async def post_process(self, response: RESTResponse) -> RESTResponse:
        """Process a REST response before it is returned to the caller.

        This method is called after receiving a response from the server but before
        returning it to the caller. It can be used to modify, validate, or transform
        the response data.

        Args:
            response (RESTResponse): The response received from the server.

        Returns:
            RESTResponse: The processed response.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        ...


class RESTPreProcessor(abc.ABC):
    """Abstract base class for processing REST requests.

    This interface enables functionality injection into the `RESTManager` for request
    processing. Implementations of this class can modify or transform requests before
    they are sent to the server.

    Use cases include:
    - Request parameter validation
    - Authentication token injection
    - Request data transformation
    - Headers manipulation
    - Request logging
    - Rate limiting
    - Cache checking

    Example:
        ```python
        class AuthenticationProcessor(RESTPreProcessor):
            async def pre_process(self, request: RESTRequest) -> RESTRequest:
                # Add authentication headers
                request.headers['Authorization'] = f'Bearer {self.get_token()}'
                return request
        ```
    """

    @abc.abstractmethod
    async def pre_process(self, request: RESTRequest) -> RESTRequest:
        """Process a REST request before it is sent to the server.

        This method is called before sending a request to the server. It can be used
        to modify, validate, or transform the request data.

        Args:
            request (RESTRequest): The request to be sent to the server.

        Returns:
            RESTRequest: The processed request.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        ...
