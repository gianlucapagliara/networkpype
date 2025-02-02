"""REST request module for handling HTTP requests.

This module provides a data structure for representing REST API requests in a clean
and type-safe manner. It encapsulates all the necessary information needed to make
an HTTP request, including method, URL, parameters, headers, and authentication requirements.

Classes:
    RESTRequest: Data class representing a REST API request.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from networkpype.rest.method import RESTMethod


@dataclass
class RESTRequest:
    """Data class representing a REST API request.

    This class encapsulates all the information needed to make a REST API request.
    It provides a clean interface for specifying request details such as HTTP method,
    URL, query parameters, headers, and authentication requirements.

    The class is designed to be immutable and type-safe, using Python's dataclass
    features to automatically generate appropriate __init__, __repr__, and __eq__ methods.

    Attributes:
        method (RESTMethod): The HTTP method to use for the request (GET, POST, etc.).
        url (str | None): The complete URL for the request. If provided, endpoint_url
            is ignored. Defaults to None.
        endpoint_url (str | None): The endpoint path to append to the base URL. Only
            used if url is None. Defaults to None.
        params (Mapping[str, str] | None): Query parameters to include in the request URL.
            Defaults to None.
        data (Any): The request body data. Can be any type that can be serialized to
            the appropriate format (JSON, form data, etc.). Defaults to None.
        headers (Mapping[str, str] | None): HTTP headers to include with the request.
            Defaults to None.
        is_auth_required (bool): Whether the request requires authentication. If True,
            authentication will be added by the appropriate processor. Defaults to False.
        throttler_limit_id (str | None): Identifier for rate limiting purposes. If provided,
            this request will be counted against the specified rate limit. Defaults to None.

    Example:
        ```python
        request = RESTRequest(
            method=RESTMethod.GET,
            endpoint_url="/api/v1/data",
            params={"filter": "active"},
            headers={"Accept": "application/json"},
            is_auth_required=True
        )
        ```
    """

    method: RESTMethod
    url: str | None = None
    endpoint_url: str | None = None
    params: Mapping[str, str] | None = None
    data: Any = None
    headers: Mapping[str, str] | None = None
    is_auth_required: bool = False
    throttler_limit_id: str | None = None
