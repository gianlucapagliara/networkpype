"""Rate limit definitions and task logging for API request throttling.

This module provides data structures for defining and tracking API rate limits. It supports
complex rate limiting scenarios including:
- Multiple concurrent rate limits with different time windows
- Weighted rate limits where some requests count more than others
- Linked rate limits where one request affects multiple limits
- Task logging for tracking request history

The module uses Pydantic models to ensure type safety and validation of rate limit
configurations.

Classes:
    LinkedLimitWeightPair: Associates a weight with a linked rate limit.
    TaskLog: Records the execution of a rate-limited task.
    RateLimit: Defines an API endpoint's rate limit rules.
"""

from typing import Self

from pydantic import BaseModel, Field


class LinkedLimitWeightPair(BaseModel):
    """Associates a weight with a linked rate limit.

    This class represents a connection between two rate limits, where an action that
    consumes one rate limit also affects another limit with a specified weight.
    This is useful for complex API rate limiting scenarios where one request might
    count differently against different limits.

    Attributes:
        limit_id (str): The ID of the linked rate limit.
        weight (int): The weight to apply to the linked limit when consumed.
            Must be non-negative.

    Example:
        ```python
        # Define a rate limit that affects both "global" and "endpoint" limits
        endpoint_limit = RateLimit(
            limit_id="endpoint",
            limit=100,
            time_interval=60.0,
            linked_limits=[
                LinkedLimitWeightPair(
                    limit_id="global",
                    weight=2  # Each endpoint request counts as 2 global requests
                )
            ]
        )
        ```
    """

    limit_id: str = Field(
        description="The rate limit id to be linked to the current rate limit",
    )
    weight: int = Field(
        description="The weight of the linked rate limit",
        ge=0,
    )


class TaskLog(BaseModel):
    """Records the execution of a rate-limited task.

    This class maintains a record of when a rate-limited task was executed and how
    much of the rate limit it consumed. These logs are used to determine whether
    new tasks can be executed within the rate limits.

    Attributes:
        timestamp (float): Unix timestamp when the task was executed.
        rate_limit (RateLimit): The rate limit that was consumed.
        weight (int): How much of the rate limit was consumed.
            Must be non-negative.

    Example:
        ```python
        # Record a task execution
        log = TaskLog(
            timestamp=time.time(),
            rate_limit=endpoint_limit,
            weight=1  # Standard request weight
        )
        ```
    """

    timestamp: float = Field(
        description="The timestamp of the task execution",
    )
    rate_limit: "RateLimit" = Field(
        description="The rate limit that was used to execute the task",
    )
    weight: int = Field(
        description="The weight of the rate limit that was used to execute the task",
    )


class RateLimit(BaseModel):
    """Defines rate limit rules for an API endpoint.

    This class represents a rate limit configuration that specifies how many requests
    can be made within a given time window. It supports weighted requests and can be
    linked to other rate limits to handle complex limiting scenarios.

    Attributes:
        limit_id (str): Unique identifier for this rate limit, typically an API path.
        limit (int): Maximum number of weighted requests allowed within the time window.
            Must be non-negative.
        time_interval (float): The time window in seconds.
            Must be non-negative.
        weight (int): Default weight for requests against this limit.
            Must be non-negative.
        linked_limits (list[LinkedLimitWeightPair]): Other rate limits affected by
            requests against this limit.

    Example:
        ```python
        # Define a rate limit of 100 requests per minute
        rate_limit = RateLimit(
            limit_id="/api/endpoint",
            limit=100,
            time_interval=60.0,
            weight=1,
            linked_limits=[
                LinkedLimitWeightPair(
                    limit_id="global",
                    weight=1
                )
            ]
        )
        ```
    """

    limit_id: str = Field(
        description="A unique identifier for this RateLimit object, this is usually an API request path url",
    )
    limit: int = Field(
        description="A total number of calls * weight permitted within time_interval period",
        ge=0,
    )
    time_interval: float = Field(
        description="The time interval in seconds",
        ge=0.0,
    )
    weight: int = Field(
        description="The weight (in integer) of each call. Defaults to 1",
        ge=0,
    )
    linked_limits: list[LinkedLimitWeightPair] = Field(
        default_factory=list,
        description="Optional list of LinkedLimitWeightPairs. Used to associate a weight to the linked rate limit.",
    )

    def __repr__(self) -> str:
        """Create a string representation of the rate limit.

        Returns:
            str: A human-readable string showing the rate limit configuration.
        """
        return (
            f"limit_id: {self.limit_id}, limit: {self.limit}, time interval: {self.time_interval}, "
            f"weight: {self.weight}, linked_limits: {self.linked_limits}"
        )

    @classmethod
    def filter_rate_limits_list(
        cls, rate_limits: list[Self], limit_ids: list[str]
    ) -> list[Self]:
        """Filter a list of rate limits to exclude specific limit IDs.

        This method creates a new list containing only the rate limits whose IDs
        are not in the provided list of limit IDs to filter out.

        Args:
            rate_limits (list[RateLimit]): The list of rate limits to filter.
            limit_ids (list[str]): The list of limit IDs to exclude.

        Returns:
            list[RateLimit]: A new list containing only the rate limits whose IDs
                are not in limit_ids.

        Example:
            ```python
            # Filter out global rate limits
            endpoint_limits = RateLimit.filter_rate_limits_list(
                all_limits,
                ["global", "auth"]
            )
            ```
        """
        filtered_list = []
        for limit in rate_limits:
            if limit.limit_id not in limit_ids:
                filtered_list.append(limit)
        return filtered_list
