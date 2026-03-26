"""Time synchronization module for server-client time alignment.

This module provides functionality to synchronize the local client time with a server's time.
It is particularly useful in scenarios where timestamp-based signatures are required for
authentication or when precise time synchronization is needed for operations.

The module uses a weighted average and median approach to calculate time offsets,
maintaining a rolling window of samples for improved accuracy.

Classes:
    TimeSynchronizer: Handles time synchronization between client and server.
"""

import asyncio
import inspect
import logging
import time
from collections import deque
from collections.abc import Awaitable

import numpy as np


class TimeSynchronizer:
    """Time synchronization handler for aligning local time with server time.

    This class provides mechanisms to synchronize the local system time with a server's time.
    It is particularly useful when timestamp-based signatures are required for authentication
    or when precise time synchronization is needed for operations.

    The synchronizer maintains a rolling window of time offset samples and uses a combination
    of median and weighted average calculations to determine the current time offset.

    Attributes:
        _time_offset_ms (deque[float]): A rolling window of time offset samples in milliseconds.
        _logger (logging.Logger | None): Class-level logger instance.

    Example:
        ```python
        synchronizer = TimeSynchronizer(max_samples=5)
        await synchronizer.update_server_time_offset_with_time_provider(get_server_time())
        current_time = synchronizer.time()
        ```
    """

    _logger = None

    def __init__(self, max_samples: int = 5):
        """Initialize the TimeSynchronizer with a specified sample window size.

        Args:
            max_samples (int): Maximum number of time offset samples to maintain.
                Defaults to 5.
        """
        self._time_offset_ms: deque[float] = deque(maxlen=max_samples)
        self._init_lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    def logger(cls) -> logging.Logger:
        """Get or create a logger instance for the class.

        Returns:
            logging.Logger: The logger instance for this class.
        """
        if cls._logger is None:
            cls._logger = logging.getLogger(__name__)
        return cls._logger

    @property
    def time_offset_ms(self) -> float:
        """Calculate the current time offset in milliseconds.

        This property calculates the time offset using a combination of median and
        weighted average of stored samples. If no samples are available, it calculates
        a basic offset using system time functions.

        Returns:
            float: The calculated time offset in milliseconds.
        """
        if not self._time_offset_ms:
            offset = (self._time() - self._current_seconds_counter()) * 1e3
        else:
            median = float(np.median(self._time_offset_ms))
            weighted_average = float(
                np.average(
                    self._time_offset_ms,
                    weights=range(1, len(self._time_offset_ms) * 2 + 1, 2),
                )
            )
            offset = float(np.mean([median, weighted_average]))

        return offset

    def add_time_offset_ms_sample(self, offset: float) -> None:
        """Add a new time offset sample to the rolling window.

        Args:
            offset (float): Time offset value in milliseconds to add.
        """
        self._time_offset_ms.append(offset)

    def clear_time_offset_ms_samples(self) -> None:
        """Clear all stored time offset samples."""
        self._time_offset_ms.clear()

    def time(self) -> float:
        """Get the current synchronized time in seconds.

        Returns:
            float: The current synchronized time in seconds since the epoch.
        """
        return self._current_seconds_counter() + self.time_offset_ms * 1e-3

    async def update_server_time_offset_with_time_provider(
        self, time_provider: Awaitable[float]
    ) -> None:
        """Update the time offset using a server time provider.

        This method calculates and stores a new time offset sample by comparing
        local time with server time. It uses a before/after measurement approach
        to account for network latency.

        Args:
            time_provider (Awaitable[float]): An awaitable that resolves to the server's
                current time in milliseconds.

        Raises:
            asyncio.CancelledError: If the operation is cancelled.
            Exception: If there's an error getting the server time.
        """
        try:
            local_before_ms: float = self._current_seconds_counter() * 1e3
            server_time_ms: float = await time_provider
            local_after_ms: float = self._current_seconds_counter() * 1e3
            local_server_time_pre_image_ms: float = (
                local_before_ms + local_after_ms
            ) / 2.0
            time_offset_ms: float = server_time_ms - local_server_time_pre_image_ms
            self.add_time_offset_ms_sample(time_offset_ms)
        except asyncio.CancelledError:
            raise
        except Exception:
            self.logger().error("Error getting server time.", exc_info=True)
            raise

    async def update_server_time_if_not_initialized(
        self, time_provider: Awaitable[float]
    ) -> None:
        """Update the time offset only if no samples exist.

        This method updates the time offset only if there are no existing samples,
        preventing unnecessary updates when synchronization is already established.

        Uses a lock to prevent a race where many concurrent requests each trigger
        the time provider before the first completes, which can exhaust rate limits.

        Args:
            time_provider (Awaitable[float]): An awaitable that resolves to the server's
                current time in milliseconds.
        """
        awaited = False
        try:
            async with self._init_lock:
                if not self._time_offset_ms:
                    await self.update_server_time_offset_with_time_provider(
                        time_provider
                    )
                    awaited = True
                else:
                    if inspect.iscoroutine(time_provider):
                        time_provider.close()
        finally:
            # If cancelled before awaiting (e.g. while waiting for lock), clean up
            # to avoid "coroutine was never awaited"
            if not awaited and inspect.iscoroutine(time_provider):
                try:
                    time_provider.close()
                except RuntimeError:
                    pass  # Already closed or consumed

    def _current_seconds_counter(self) -> float:
        """Get the current monotonic time in seconds.

        Returns:
            float: The current monotonic time in seconds.
        """
        return time.perf_counter()

    def _time(self) -> float:
        """Get the current system time in seconds since the epoch.

        Returns:
            float: The current system time in seconds since the epoch.
        """
        return time.time()
