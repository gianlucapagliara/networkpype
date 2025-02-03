"""Rate limiting module for controlling API request rates.

This module provides asynchronous rate limiting functionality for API requests. It supports
multiple rate limits with different time windows and can handle linked rate limits where
one request affects multiple limits. The throttler ensures that API requests stay within
the defined limits while maximizing throughput.

Features:
- Multiple concurrent rate limits with different time windows
- Linked rate limits with weighted consumption
- Configurable safety margins to prevent limit breaches
- Rate limit sharing between multiple instances
- Automatic request queuing and retry scheduling

Classes:
    AsyncThrottler: Asynchronous rate limiter for API requests.
"""

import asyncio
import copy
import logging
import math
from decimal import Decimal

from networkpype.throttler.context import AsyncRequestContext
from networkpype.throttler.rate_limit import RateLimit, TaskLog


class AsyncThrottler:
    """Asynchronous rate limiter for API requests.

    This class manages rate limiting for API requests, ensuring that requests stay within
    defined limits while maximizing throughput. It supports multiple concurrent rate
    limits with different time windows and can handle linked limits where one request
    affects multiple limits.

    The throttler uses a task log to track request history and provides automatic
    request queuing when limits are reached. It also supports rate limit sharing
    between multiple instances of the application.

    Attributes:
        _task_logs (list[TaskLog]): History of executed tasks within time windows.
        _rate_limits (list[RateLimit]): List of rate limits to enforce.
        _retry_interval (float): Time to wait between retries when limits are reached.
        _safety_margin_pct (float): Extra margin to prevent limit breaches.
        _limits_share_percentage (Decimal | None): Percentage of limits allocated.
        _id_to_limit_map (dict[str, RateLimit]): Mapping of limit IDs to limits.
        _lock (asyncio.Lock): Lock for thread-safe task log access.
        _logger (logging.Logger | None): Class-level logger instance.

    Example:
        ```python
        # Create a throttler with multiple rate limits
        throttler = AsyncThrottler(
            rate_limits=[
                RateLimit(10, 1.0, "per_second"),  # 10 requests per second
                RateLimit(100, 60.0, "per_minute"),  # 100 requests per minute
            ],
            safety_margin_pct=0.05,  # 5% safety margin
            limits_share_percentage=Decimal("50")  # Use 50% of the limits
        )

        # Use the throttler in an async context
        async with throttler.execute_task("per_second"):
            await make_api_request()
        ```
    """

    _logger = None

    @classmethod
    def logger(cls) -> logging.Logger:
        """Get or create a logger instance for the class.

        Returns:
            logging.Logger: The logger instance for this class.
        """
        if cls._logger is None:
            cls._logger = logging.getLogger(__name__)
        return cls._logger

    def __init__(
        self,
        rate_limits: list[RateLimit],
        retry_interval: float = 0.1,
        safety_margin_pct: float = 0.05,
        limits_share_percentage: Decimal | None = None,
    ):
        """Initialize the AsyncThrottler with the specified parameters.

        Args:
            rate_limits (list[RateLimit]): List of rate limits to enforce.
            retry_interval (float): Time in seconds to wait between retries when
                limits are reached. Defaults to 0.1.
            safety_margin_pct (float): Extra margin as a percentage to prevent
                limit breaches. Defaults to 0.05 (5%).
            limits_share_percentage (Decimal | None): Percentage of the rate limits
                to allocate to this throttler instance. Useful when sharing limits
                between multiple instances. Defaults to None (use 100%).
        """
        self._limits_share_percentage: Decimal | None = limits_share_percentage

        # List of TaskLog used to determine the API requests within a set time window.
        self._task_logs: list[TaskLog] = []

        # Throttler Parameters
        self._retry_interval: float = retry_interval
        self._safety_margin_pct: float = safety_margin_pct

        # Shared asyncio.Lock instance to prevent multiple async ContextManager from accessing the _task_logs variable
        self._lock = asyncio.Lock()

        self.rate_limits = rate_limits

    @property
    def rate_limits(self) -> list[RateLimit]:
        """Get the list of rate limits being enforced.

        Returns:
            list[RateLimit]: The current rate limits.
        """
        return self._rate_limits

    @property
    def limits_share_percentage(self) -> Decimal:
        """Get the percentage of rate limits allocated to this throttler.

        Returns:
            Decimal: The percentage as a decimal (e.g., 100 for 100%).
        """
        return (
            self._limits_share_percentage
            if self._limits_share_percentage is not None
            else Decimal("100")
        )

    @limits_share_percentage.setter
    def limits_share_percentage(self, limits_share_percentage: Decimal | None):
        """Set the percentage of rate limits allocated to this throttler.

        Args:
            limits_share_percentage (Decimal | None): The percentage to allocate,
                or None to use 100%.
        """
        self._limits_share_percentage = limits_share_percentage

    @rate_limits.setter
    def rate_limits(self, rate_limits: list[RateLimit]):
        """Set the rate limits to enforce.

        This method also updates the internal limit mapping and applies the
        limits share percentage if configured.

        Args:
            rate_limits (list[RateLimit]): The rate limits to enforce.
        """
        # Rate Limit Definitions
        self._rate_limits: list[RateLimit] = copy.deepcopy(rate_limits)

        # If configured, users can define the percentage of rate limits to allocate to the throttler.
        self.limits_pct: Decimal = self.limits_share_percentage / 100
        for rate_limit in self._rate_limits:
            adjusted_limit = max(
                Decimal("1"),
                math.floor(Decimal(str(rate_limit.limit)) * self.limits_pct),
            )
            rate_limit.limit = int(adjusted_limit)

        # Dictionary of path_url to RateLimit
        self._id_to_limit_map: dict[str, RateLimit] = {
            limit.limit_id: limit for limit in self._rate_limits
        }

    def get_related_limits(
        self, limit_id: str
    ) -> tuple[RateLimit | None, list[tuple[RateLimit, int]]]:
        """Get a rate limit and its related limits by ID.

        This method retrieves a rate limit by its ID and returns it along with any
        related limits. Related limits include the limit itself and any linked limits
        that would be affected by requests against this limit.

        Args:
            limit_id (str): The ID of the rate limit to retrieve.

        Returns:
            tuple[RateLimit | None, list[tuple[RateLimit, int]]]: A tuple containing:
                - The requested rate limit, or None if not found
                - A list of tuples containing related limits and their weights
        """
        rate_limit = next(
            (limit for limit in self._rate_limits if limit.limit_id == limit_id),
            None,
        )

        if rate_limit is None:
            return None, []

        # Get all related limits (including the limit itself)
        related_limits = [(rate_limit, rate_limit.weight)]
        for linked in rate_limit.linked_limits:
            linked_limit = next(
                (
                    limit
                    for limit in self._rate_limits
                    if limit.limit_id == linked.limit_id
                ),
                None,
            )
            if linked_limit is not None:
                related_limits.append((linked_limit, linked.weight))

        return rate_limit, related_limits

    def copy(self) -> "AsyncThrottler":
        """Create a copy of this throttler with the same configuration.

        Returns:
            AsyncThrottler: A new throttler instance with the same settings.
        """
        return AsyncThrottler(
            rate_limits=self.rate_limits,
            retry_interval=self._retry_interval,
            safety_margin_pct=self._safety_margin_pct,
            limits_share_percentage=self._limits_share_percentage,
        )

    def execute_task(self, limit_id: str) -> AsyncRequestContext:
        """Create a context manager for executing a rate-limited task.

        This method creates an AsyncRequestContext that will ensure the task
        execution stays within the specified rate limits. The context manager
        handles waiting for available capacity and logging task execution.

        Args:
            limit_id (str): The ID of the rate limit to use.

        Returns:
            AsyncRequestContext: A context manager for executing the task.

        Raises:
            ValueError: If the rate limit ID is not found.

        Example:
            ```python
            async with throttler.execute_task("api_limit"):
                response = await make_api_call()
            ```
        """
        rate_limit, related_limits = self.get_related_limits(limit_id)
        if rate_limit is None:
            raise ValueError(f"Rate limit not found for ID: {limit_id}")

        return AsyncRequestContext(
            task_logs=self._task_logs,
            rate_limit=rate_limit,
            related_limits=related_limits,
            lock=self._lock,
            safety_margin_pct=self._safety_margin_pct,
            retry_interval=self._retry_interval,
        )
