"""Tests for the AsyncRequestContext class."""

import asyncio
import time

import pytest
from pytest import FixtureRequest

from networkpype.throttler.context import AsyncRequestContext
from networkpype.throttler.rate_limit import RateLimit, TaskLog


@pytest.fixture
def rate_limit(request: FixtureRequest) -> RateLimit:
    """Fixture providing a basic rate limit for testing."""
    return RateLimit(limit_id="test", limit=10, time_interval=1.0)


@pytest.fixture
def task_logs(request: FixtureRequest) -> list[TaskLog]:
    """Fixture providing an empty task log list."""
    return []


@pytest.mark.asyncio
async def test_context_basic_execution(rate_limit: RateLimit, task_logs: list[TaskLog]):
    """Test basic execution of a task within the context."""
    context = AsyncRequestContext(
        task_logs=task_logs,
        rate_limit=rate_limit,
        related_limits=[(rate_limit, 1)],
        retry_interval=0.1,
        safety_margin_pct=0.05,
        lock=asyncio.Lock(),
    )

    async with context:
        # Each related limit creates its own task log
        assert len(task_logs) == len(context._related_limits)


@pytest.mark.asyncio
async def test_context_rate_limiting(rate_limit: RateLimit, task_logs: list[TaskLog]):
    """Test rate limiting behavior of the context."""
    context = AsyncRequestContext(
        task_logs=task_logs,
        rate_limit=rate_limit,
        related_limits=[(rate_limit, 1)],
        retry_interval=0.1,
        safety_margin_pct=0.05,
        lock=asyncio.Lock(),
    )

    # Fill up the rate limit
    start_time = time.time()
    tasks = []
    for _ in range(15):  # More than the limit
        tasks.append(execute_context_task(context))
    await asyncio.gather(*tasks)
    duration = time.time() - start_time

    # Should take at least 1 second due to rate limiting
    assert duration >= 1.0
    # Each task creates a log for each related limit
    assert len(task_logs) == 15 * len(context._related_limits)


@pytest.mark.asyncio
async def test_context_with_safety_margin(
    rate_limit: RateLimit, task_logs: list[TaskLog]
):
    """Test context behavior with safety margin."""
    # Set a high safety margin
    context = AsyncRequestContext(
        task_logs=task_logs,
        rate_limit=rate_limit,
        related_limits=[(rate_limit, 1)],
        retry_interval=0.1,
        safety_margin_pct=0.5,  # 50% safety margin
        lock=asyncio.Lock(),
    )

    # Try to execute tasks up to the effective limit (5 with 50% safety margin)
    start_time = time.time()
    tasks = []
    for _ in range(7):  # More than the effective limit
        tasks.append(execute_context_task(context))
    await asyncio.gather(*tasks)
    duration = time.time() - start_time

    # Should take time due to safety margin limiting
    assert duration >= 1.0


@pytest.mark.asyncio
async def test_context_cleanup(rate_limit: RateLimit, task_logs: list[TaskLog]):
    """Test cleanup of old task logs."""
    # Create some old task logs
    old_time = time.time() - 2.0  # Older than the time interval
    task_logs.extend(
        [TaskLog(timestamp=old_time, rate_limit=rate_limit) for _ in range(5)]
    )

    context = AsyncRequestContext(
        task_logs=task_logs,
        rate_limit=rate_limit,
        related_limits=[(rate_limit, 1)],
        retry_interval=0.1,
        safety_margin_pct=0.05,
        lock=asyncio.Lock(),
    )

    async with context:
        # Old logs should be cleaned up
        current_logs = [log for log in task_logs if log.timestamp > time.time() - 1.0]
        # Only the new logs from the current execution should remain
        assert len(current_logs) == len(context._related_limits)


@pytest.mark.asyncio
async def test_context_limit_one_no_concurrent_breach():
    """Test that limit=1 does not allow concurrent tasks to both pass capacity check."""
    rate_limit = RateLimit(limit_id="strict", limit=1, time_interval=0.5)
    task_logs: list[TaskLog] = []
    lock = asyncio.Lock()

    concurrent_count = 0
    max_concurrent = 0

    async def guarded_task():
        nonlocal concurrent_count, max_concurrent
        context = AsyncRequestContext(
            task_logs=task_logs,
            rate_limit=rate_limit,
            related_limits=[(rate_limit, 1)],
            retry_interval=0.05,
            safety_margin_pct=0.05,
            lock=lock,
        )
        async with context:
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.05)
            concurrent_count -= 1

    # Launch several concurrent tasks against limit=1
    tasks = [asyncio.create_task(guarded_task()) for _ in range(5)]
    await asyncio.gather(*tasks)

    # Only one task should ever be inside the context at a time
    assert max_concurrent == 1


@pytest.mark.asyncio
async def test_context_limit_one_with_safety_margin():
    """Test that limit=1 with safety margin still allows requests (max(1, ...) floor)."""
    rate_limit = RateLimit(limit_id="single", limit=1, time_interval=0.5)
    task_logs: list[TaskLog] = []
    lock = asyncio.Lock()

    context = AsyncRequestContext(
        task_logs=task_logs,
        rate_limit=rate_limit,
        related_limits=[(rate_limit, 1)],
        retry_interval=0.05,
        safety_margin_pct=0.5,  # 50% margin — would make effective_limit=0 without floor
        lock=lock,
    )

    # Should complete without hanging — the max(1, ...) floor ensures progress
    async with asyncio.timeout(2.0):
        async with context:
            pass

    assert len(task_logs) == 1


async def execute_context_task(context: AsyncRequestContext):
    """Helper function to execute a task within the context."""
    async with context:
        await asyncio.sleep(0.01)  # Simulate some work
