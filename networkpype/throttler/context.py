"""Asynchronous context manager for rate-limited task execution.

This module provides the AsyncRequestContext class, which manages the execution of
rate-limited tasks within specified constraints. It ensures that tasks are executed
only when sufficient capacity is available across all relevant rate limits.

Features:
- Automatic task log cleanup for expired entries
- Capacity checking across multiple linked rate limits
- Warning notifications when approaching rate limits
- Asynchronous acquisition of rate limit capacity
- Thread-safe task log management

The context manager is typically created by the AsyncThrottler class and should
not be instantiated directly by users.
"""

import asyncio
import logging
import time
from decimal import Decimal

from networkpype.throttler.rate_limit import RateLimit, TaskLog


class AsyncRequestContext:
    """Asynchronous context manager for rate-limited task execution.

    This class provides a context manager that ensures tasks are executed within
    their rate limits. It manages task logging, capacity checking, and automatic
    retry when limits are reached.

    The context manager is thread-safe and handles multiple related rate limits,
    ensuring that all constraints are satisfied before allowing task execution.

    Attributes:
        MAX_CAPACITY_REACHED_WARNING_INTERVAL (float): Minimum time between
            warning logs about reaching capacity.
        _last_max_cap_warning_ts (float): Timestamp of the last warning.
        _logger (logging.Logger | None): Class-level logger instance.
        _task_logs (list[TaskLog]): Reference to shared task history.
        _rate_limit (RateLimit): Primary rate limit for this context.
        _related_limits (list[tuple[RateLimit, int]]): Related limits and weights.
        _lock (asyncio.Lock): Thread synchronization lock.
        _safety_margin_pct (float): Safety margin for limit calculations.
        _retry_interval (float): Time to wait between capacity checks.

    Example:
        ```python
        # Context is typically created by AsyncThrottler
        async with context:
            # This code will only execute when capacity is available
            await make_api_call()
        ```
    """

    MAX_CAPACITY_REACHED_WARNING_INTERVAL = 30.0

    _last_max_cap_warning_ts: float = 0.0
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
        task_logs: list[TaskLog],
        rate_limit: RateLimit,
        related_limits: list[tuple[RateLimit, int]],
        lock: asyncio.Lock,
        safety_margin_pct: float,
        retry_interval: float = 0.1,
    ):
        """Initialize the AsyncRequestContext.

        Args:
            task_logs (list[TaskLog]): Reference to shared task history.
            rate_limit (RateLimit): Primary rate limit for this context.
            related_limits (list[tuple[RateLimit, int]]): List of tuples containing
                related rate limits and their weights.
            lock (asyncio.Lock): Thread synchronization lock.
            safety_margin_pct (float): Safety margin as percentage to prevent
                limit breaches.
            retry_interval (float): Time in seconds to wait between capacity
                checks. Defaults to 0.1.
        """
        self._task_logs: list[TaskLog] = task_logs
        self._rate_limit: RateLimit = rate_limit
        self._related_limits: list[tuple[RateLimit, int]] = related_limits
        self._lock: asyncio.Lock = lock
        self._safety_margin_pct: float = safety_margin_pct
        self._retry_interval: float = retry_interval

    def flush(self):
        """Remove expired task logs.

        This method removes task logs that are older than their rate limit's
        time window plus the safety margin. This helps maintain an accurate
        view of current capacity usage.
        """
        now: Decimal = Decimal(str(time.time()))
        for task in self._task_logs:
            task_limit: RateLimit = task.rate_limit
            elapsed: Decimal = now - Decimal(str(task.timestamp))
            if elapsed > Decimal(
                str(task_limit.time_interval * (1 + self._safety_margin_pct))
            ):
                self._task_logs.remove(task)

    def within_capacity(self) -> bool:
        """Check if executing a task would exceed any rate limits.

        This method calculates the current capacity usage for all related
        rate limits and checks if adding the new task would exceed any limits.
        It also handles warning logs when approaching capacity limits.

        Returns:
            bool: True if the task can be executed without exceeding limits,
                False otherwise.
        """
        if len(self._related_limits) > 0:
            now: float = self._time()
            for rate_limit, weight in self._related_limits:
                # Calculate effective limit with safety margin
                effective_limit = int(rate_limit.limit * (1 - self._safety_margin_pct))
                capacity_used: int = sum(
                    [
                        task.weight
                        for task in self._task_logs
                        if rate_limit.limit_id == task.rate_limit.limit_id
                        and Decimal(str(now)) - Decimal(str(task.timestamp))
                        <= task.rate_limit.time_interval
                    ]
                )

                if capacity_used + weight > effective_limit:
                    if (
                        self._last_max_cap_warning_ts
                        < now - self.MAX_CAPACITY_REACHED_WARNING_INTERVAL
                    ):
                        msg = (
                            f"API rate limit on {rate_limit.limit_id} ({rate_limit.limit} calls per "
                            f"{rate_limit.time_interval}s) has almost reached. Limits used "
                            f"is {capacity_used} in the last "
                            f"{rate_limit.time_interval} seconds"
                        )
                        self.logger().warning(msg)
                        AsyncRequestContext._last_max_cap_warning_ts = now
                    return False
        return True

    async def acquire(self):
        """Acquire capacity to execute a task.

        This method repeatedly checks for available capacity across all rate
        limits until capacity is available. When capacity is found, it logs
        the task execution in the task history.

        The method is thread-safe and handles the creation of task logs for
        both the primary rate limit and all related limits.
        """
        while True:
            async with self._lock:
                self.flush()

                if self.within_capacity():
                    break
            await asyncio.sleep(self._retry_interval)
        async with self._lock:
            now = time.time()
            # Create task logs for each rate limit
            for limit, weight in self._related_limits:
                task = TaskLog(timestamp=now, rate_limit=limit, weight=weight)
                self._task_logs.append(task)

    async def __aenter__(self):
        """Enter the async context manager.

        This method is called when entering an 'async with' block. It acquires
        the necessary capacity before allowing the block to execute.
        """
        await self.acquire()

    async def __aexit__(self, exc_type, exc, tb):
        """Exit the async context manager.

        This method is called when exiting an 'async with' block. Currently,
        no cleanup is required as task logs are managed by the flush method.

        Args:
            exc_type: The type of any exception that occurred.
            exc: The exception instance that occurred, if any.
            tb: The traceback if an exception occurred.
        """
        pass

    def _time(self):
        """Get the current time.

        This method exists primarily to facilitate testing by allowing
        time to be mocked.

        Returns:
            float: The current Unix timestamp.
        """
        return time.time()
